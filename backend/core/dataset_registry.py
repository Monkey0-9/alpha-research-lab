"""
Immutable Dataset Registry and Versioning Engine.
Every research dataset is registered with a cryptographic SHA-256 fingerprint,
schema hash, git code version, and quality status.
"""
from __future__ import annotations

import hashlib
import json
import logging
import subprocess
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, Union
import pandas as pd
import pyarrow as pa
import polars as pl

logger = logging.getLogger(__name__)

DATA_STORE_DIR = Path(__file__).resolve().parents[2] / "data" / "registry"
DATA_STORE_DIR.mkdir(parents=True, exist_ok=True)


def get_git_commit_hash() -> str:
    """Retrieve current git HEAD commit hash if available."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "UNKNOWN_COMMIT"


@dataclass
class DatasetVersionManifest:
    dataset_id: str
    version: int
    provider: str
    effective_start: str
    effective_end: str
    schema_hash: str
    content_hash: str
    code_version: str
    quality_status: str  # "PASS", "WARN", "FAIL"
    security_count: int = 0
    record_count: int = 0
    storage_path: str = ""
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    # Backward compatibility aliases
    @property
    def checksum_sha256(self) -> str:
        return self.content_hash

    @property
    def coverage_start(self) -> str:
        return self.effective_start

    @property
    def coverage_end(self) -> str:
        return self.effective_end

    @property
    def schema_version(self) -> str:
        return f"v{self.version}.0"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["checksum_sha256"] = self.content_hash
        d["coverage_start"] = self.effective_start
        d["coverage_end"] = self.effective_end
        d["schema_version"] = f"v{self.version}.0"
        return d


class DatasetRegistry:
    """Registry maintaining immutable versions of quantitative research datasets."""

    def __init__(self, registry_dir: Optional[Path] = None):
        self.registry_dir = registry_dir or DATA_STORE_DIR
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.registry_dir / "datasets_manifest.json"
        self._manifests: Dict[str, DatasetVersionManifest] = self._load_manifests()

    def _load_manifests(self) -> Dict[str, DatasetVersionManifest]:
        if not self.manifest_file.exists():
            return {}
        try:
            with open(self.manifest_file, "r", encoding="utf-8") as f:
                raw = json.load(f)
            manifests = {}
            for k, v in raw.items():
                content_hash = v.get("content_hash") or v.get("checksum_sha256", "")
                eff_start = v.get("effective_start") or v.get("coverage_start", "")
                eff_end = v.get("effective_end") or v.get("coverage_end", "")
                ver_val = v.get("version", 1)
                if isinstance(ver_val, str):
                    try:
                        ver_int = int(ver_val.replace("v", "").split(".")[0])
                    except Exception:
                        ver_int = 1
                else:
                    ver_int = int(ver_val)

                manifests[k] = DatasetVersionManifest(
                    dataset_id=v.get("dataset_id", k.split(":")[0]),
                    version=ver_int,
                    provider=v.get("provider", "UNKNOWN"),
                    effective_start=eff_start,
                    effective_end=eff_end,
                    schema_hash=v.get("schema_hash", ""),
                    content_hash=content_hash,
                    code_version=v.get("code_version", "UNKNOWN"),
                    quality_status=v.get("quality_status", "PASS"),
                    security_count=v.get("security_count", 0),
                    record_count=v.get("record_count", 0),
                    storage_path=v.get("storage_path", ""),
                    created_at=v.get("created_at", datetime.now(timezone.utc).isoformat()),
                )
            return manifests
        except Exception as e:
            logger.warning(f"Failed to load dataset registry manifest: {e}")
            return {}

    def _save_manifests(self) -> None:
        raw = {k: v.to_dict() for k, v in self._manifests.items()}
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    @staticmethod
    def compute_content_hash(file_path: Union[str, Path]) -> str:
        """Compute SHA-256 digest of file contents."""
        p = Path(file_path)
        sha256 = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def compute_schema_hash(df_or_table: Union[pd.DataFrame, pa.Table, pl.DataFrame]) -> str:
        """Compute deterministic SHA-256 hash of dataset column names and data types."""
        if isinstance(df_or_table, pd.DataFrame):
            schema_pairs = sorted([(col, str(dtype)) for col, dtype in df_or_table.dtypes.items()])
        elif isinstance(df_or_table, pa.Table):
            schema_pairs = sorted([(field.name, str(field.type)) for field in df_or_table.schema])
        elif isinstance(df_or_table, pl.DataFrame):
            schema_pairs = sorted([(name, str(dtype)) for name, dtype in df_or_table.schema.items()])
        else:
            schema_pairs = []

        schema_str = ";".join(f"{name}:{dtype}" for name, dtype in schema_pairs)
        return hashlib.sha256(schema_str.encode("utf-8")).hexdigest()

    def get_next_version(self, dataset_id: str) -> int:
        """Determine next incremental integer version for this dataset_id."""
        matching = [v.version for v in self._manifests.values() if v.dataset_id == dataset_id]
        return max(matching) + 1 if matching else 1

    def register_dataset(
        self,
        dataset_id: str,
        df: Union[pd.DataFrame, pa.Table, pl.DataFrame],
        provider: str,
        file_path: Path,
        quality_status: str = "PASS",
        code_version: Optional[str] = None,
        version: Optional[int] = None,
    ) -> DatasetVersionManifest:
        """Register a dataset file, compute cryptographic content/schema hashes, and record metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file does not exist at {file_path}")

        content_hash = self.compute_content_hash(file_path)
        schema_hash = self.compute_schema_hash(df)
        code_ver = code_version or get_git_commit_hash()
        ver_int = version or self.get_next_version(dataset_id)

        # Determine dates and counts
        if isinstance(df, pd.DataFrame):
            n_records = len(df)
            if "date" in df.columns:
                dates = pd.to_datetime(df["date"]).sort_values()
                eff_start, eff_end = str(dates.iloc[0].date()), str(dates.iloc[-1].date())
            elif "observation_time" in df.columns:
                dates = pd.to_datetime(df["observation_time"]).sort_values()
                eff_start, eff_end = str(dates.iloc[0].date()), str(dates.iloc[-1].date())
            else:
                eff_start, eff_end = "UNKNOWN", "UNKNOWN"

            if "security_id" in df.columns:
                sec_count = len(df["security_id"].unique())
            elif "ticker" in df.columns:
                sec_count = len(df["ticker"].unique())
            else:
                sec_count = 1
        else:
            n_records = len(df)
            eff_start, eff_end = "UNKNOWN", "UNKNOWN"
            sec_count = 1

        manifest = DatasetVersionManifest(
            dataset_id=dataset_id,
            version=ver_int,
            provider=provider,
            effective_start=eff_start,
            effective_end=eff_end,
            schema_hash=schema_hash,
            content_hash=content_hash,
            code_version=code_ver,
            quality_status=quality_status,
            security_count=sec_count,
            record_count=n_records,
            storage_path=str(file_path.resolve()),
        )

        composite_key = f"{dataset_id}:v{ver_int}"
        self._manifests[composite_key] = manifest
        self._save_manifests()
        logger.info(f"Registered {composite_key} with content_hash={content_hash[:12]}...")
        return manifest

    def get_manifest(
        self, dataset_id: str, version: Optional[Union[str, int]] = None
    ) -> Optional[DatasetVersionManifest]:
        if version is not None:
            v_str = str(version).replace("v", "")
            key = f"{dataset_id}:v{v_str}"
            if key in self._manifests:
                return self._manifests[key]
            # Try plain match
            return self._manifests.get(f"{dataset_id}:{version}")
        candidates = [v for v in self._manifests.values() if v.dataset_id == dataset_id]
        if not candidates:
            return None
        return sorted(candidates, key=lambda x: x.version)[-1]

    def verify_integrity(self, dataset_id: str, version: Union[str, int]) -> bool:
        """Verify that the dataset on disk strictly matches its registered content hash."""
        manifest = self.get_manifest(dataset_id, version)
        if not manifest:
            return False
        p = Path(manifest.storage_path)
        if not p.exists():
            return False
        actual_hash = self.compute_content_hash(p)
        return actual_hash == manifest.content_hash


dataset_registry = DatasetRegistry()

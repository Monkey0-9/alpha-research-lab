"""
Immutable Dataset Registry and Versioning Engine.
Every research dataset is registered with a cryptographic SHA-256 fingerprint,
strict schema version, and immutable metadata.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)

DATA_STORE_DIR = Path(__file__).resolve().parents[2] / "data" / "registry"
DATA_STORE_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class DatasetVersionManifest:
    dataset_id: str
    version: str
    provider: str
    coverage_start: str
    coverage_end: str
    security_count: int
    record_count: int
    schema_version: str
    checksum_sha256: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    storage_path: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
            return {k: DatasetVersionManifest(**v) for k, v in raw.items()}
        except Exception as e:
            logger.warning(f"Failed to load dataset registry manifest: {e}")
            return {}

    def _save_manifests(self) -> None:
        raw = {k: v.to_dict() for k, v in self._manifests.items()}
        with open(self.manifest_file, "w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2)

    def register_dataset(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        provider: str,
        file_path: Path,
        schema_version: str = "v1.0"
    ) -> DatasetVersionManifest:
        """Register a dataset file, compute its cryptographic hash, and persist metadata."""
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file does not exist at {file_path}")

        # Compute SHA-256 of file bytes
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        digest = sha256.hexdigest()

        # Extract dates and symbols
        if "date" in df.columns:
            dates = pd.to_datetime(df["date"]).sort_values()
            cov_start = str(dates.iloc[0].date())
            cov_end = str(dates.iloc[-1].date())
        elif isinstance(df.index, pd.MultiIndex) and "date" in df.index.names:
            dates = pd.to_datetime(df.index.get_level_values("date")).sort_values()
            cov_start = str(dates[0].date())
            cov_end = str(dates[-1].date())
        else:
            cov_start = "UNKNOWN"
            cov_end = "UNKNOWN"

        if "ticker" in df.columns:
            sec_count = len(df["ticker"].unique())
        elif isinstance(df.index, pd.MultiIndex) and "ticker" in df.index.names:
            sec_count = len(df.index.get_level_values("ticker").unique())
        else:
            sec_count = 1

        version_str = datetime.now(timezone.utc).strftime("v%Y.%m.%d")
        composite_key = f"{dataset_id}:{version_str}"

        manifest = DatasetVersionManifest(
            dataset_id=dataset_id,
            version=version_str,
            provider=provider,
            coverage_start=cov_start,
            coverage_end=cov_end,
            security_count=sec_count,
            record_count=len(df),
            schema_version=schema_version,
            checksum_sha256=digest,
            storage_path=str(file_path.resolve())
        )

        self._manifests[composite_key] = manifest
        self._save_manifests()
        return manifest

    def get_manifest(self, dataset_id: str, version: Optional[str] = None) -> Optional[DatasetVersionManifest]:
        if version:
            return self._manifests.get(f"{dataset_id}:{version}")
        # Return latest registered
        candidates = [v for k, v in self._manifests.items() if v.dataset_id == dataset_id]
        if not candidates:
            return None
        return sorted(candidates, key=lambda x: x.created_at)[-1]

    def verify_integrity(self, dataset_id: str, version: str) -> bool:
        """Verify that the dataset on disk strictly matches its registered checksum."""
        manifest = self.get_manifest(dataset_id, version)
        if not manifest:
            return False
        p = Path(manifest.storage_path)
        if not p.exists():
            return False

        sha256 = hashlib.sha256()
        with open(p, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest() == manifest.checksum_sha256


dataset_registry = DatasetRegistry()

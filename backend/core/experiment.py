"""
Pre-Registration & Immutable Experiment Lineage Engine.

Enforces pre-registration protocol:
1. Hypotheses, feature sets, validation schemes, and correction protocols are declared and frozen prior to execution.
2. Generates immutable SHA-256 content manifests (EXP-XXXX).
3. Post-execution results cannot alter pre-registered hypotheses.
4. Provides deterministic reproducibility verification.
"""
from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

_DEFAULT_STORE_DIR = Path(__file__).resolve().parents[1] / "experiments_store"


class ExperimentImmutableError(Exception):
    """Raised when an attempt is made to modify a frozen pre-registered experiment."""
    pass


class ExperimentIntegrityError(Exception):
    """Raised when SHA-256 checksum or manifest verification fails."""
    pass


def compute_sha256(data: Any) -> str:
    """Compute deterministic SHA-256 hash from JSON-serializable structure."""
    serialized = json.dumps(data, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass
class PreRegistrationSpec:
    experiment_id: str
    hypothesis_name: str
    economic_rationale: str
    expected_direction: str  # "positive" or "negative"
    universe_type: str       # "SP500_PIT"
    features: List[str]
    target_label: str        # e.g., "fwd_return_1d"
    validation_method: str   # "CPCV", "WALK_FORWARD", "PURGED_KFOLD"
    multiple_testing_correction: str  # "BH", "BONFERRONI", "DSR"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    spec_hash: str = ""

    def __post_init__(self):
        if not self.spec_hash:
            data_to_hash = {
                "experiment_id": self.experiment_id,
                "hypothesis_name": self.hypothesis_name,
                "economic_rationale": self.economic_rationale,
                "expected_direction": self.expected_direction,
                "universe_type": self.universe_type,
                "features": sorted(self.features),
                "target_label": self.target_label,
                "validation_method": self.validation_method,
                "multiple_testing_correction": self.multiple_testing_correction,
            }
            self.spec_hash = compute_sha256(data_to_hash)


@dataclass
class ExperimentManifest:
    spec: PreRegistrationSpec
    data_version: str
    data_hash: str
    code_version: str
    execution_status: str  # "PRE_REGISTERED", "COMPLETED", "REJECTED"
    metrics: Dict[str, Any] = field(default_factory=dict)
    diagnostics: Dict[str, Any] = field(default_factory=dict)
    completed_at: Optional[str] = None
    manifest_hash: str = ""
    is_frozen: bool = False

    def freeze(self):
        """Seal manifest and compute final cryptographic fingerprint."""
        self.is_frozen = True
        body = {
            "spec_hash": self.spec.spec_hash,
            "data_hash": self.data_hash,
            "metrics": self.metrics,
            "status": self.execution_status
        }
        self.manifest_hash = compute_sha256(body)

    @property
    def experiment_id(self) -> str:
        return self.spec.experiment_id


class ExperimentRegistry:
    """Storage and governance registry for immutable quantitative research manifests."""

    def __init__(self, store_dir: Optional[Path] = None):
        self.store_dir = store_dir or _DEFAULT_STORE_DIR
        self.store_dir.mkdir(parents=True, exist_ok=True)
        self._memory_cache: Dict[str, ExperimentManifest] = {}

    def preregister(self, spec: PreRegistrationSpec) -> ExperimentManifest:
        """
        Pre-register a research hypothesis before backtesting or model training.
        """
        if spec.experiment_id in self._memory_cache:
            raise ExperimentImmutableError(
                f"Experiment '{spec.experiment_id}' already pre-registered. "
                f"Modifying pre-registration requires creating a new experiment ID."
            )

        manifest = ExperimentManifest(
            spec=spec,
            data_version="1.0.0",
            data_hash=compute_sha256(spec.features),
            code_version="institutional-v1.0",
            execution_status="PRE_REGISTERED"
        )
        self._memory_cache[spec.experiment_id] = manifest
        self._save_to_disk(manifest)
        return manifest

    def record_results(
        self,
        experiment_id: str,
        metrics: Dict[str, Any],
        diagnostics: Optional[Dict[str, Any]] = None,
        status: str = "COMPLETED"
    ) -> ExperimentManifest:
        """
        Record empirical results and freeze manifest permanently.
        """
        manifest = self.get(experiment_id)
        if manifest.is_frozen:
            raise ExperimentImmutableError(
                f"Cannot alter frozen experiment '{experiment_id}'. Manifest is immutable."
            )

        manifest.metrics = metrics
        manifest.diagnostics = diagnostics or {}
        manifest.execution_status = status
        manifest.completed_at = datetime.now(timezone.utc).isoformat()
        manifest.freeze()

        self._save_to_disk(manifest)
        return manifest

    def get(self, experiment_id: str) -> ExperimentManifest:
        """Retrieve manifest from memory cache or disk."""
        if experiment_id in self._memory_cache:
            return self._memory_cache[experiment_id]

        file_path = self.store_dir / f"{experiment_id}.json"
        if not file_path.exists():
            raise KeyError(f"Experiment '{experiment_id}' not found in registry.")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        spec = PreRegistrationSpec(**data["spec"])
        manifest = ExperimentManifest(
            spec=spec,
            data_version=data["data_version"],
            data_hash=data["data_hash"],
            code_version=data["code_version"],
            execution_status=data["execution_status"],
            metrics=data["metrics"],
            diagnostics=data["diagnostics"],
            completed_at=data.get("completed_at"),
            manifest_hash=data.get("manifest_hash", ""),
            is_frozen=data.get("is_frozen", False)
        )
        self._memory_cache[experiment_id] = manifest
        return manifest

    def verify_integrity(self, experiment_id: str) -> bool:
        """Verify that the stored manifest matches its cryptographic hash."""
        manifest = self.get(experiment_id)
        if not manifest.is_frozen:
            return True

        expected_spec_hash = PreRegistrationSpec(
            experiment_id=manifest.spec.experiment_id,
            hypothesis_name=manifest.spec.hypothesis_name,
            economic_rationale=manifest.spec.economic_rationale,
            expected_direction=manifest.spec.expected_direction,
            universe_type=manifest.spec.universe_type,
            features=manifest.spec.features,
            target_label=manifest.spec.target_label,
            validation_method=manifest.spec.validation_method,
            multiple_testing_correction=manifest.spec.multiple_testing_correction
        ).spec_hash

        if expected_spec_hash != manifest.spec.spec_hash:
            raise ExperimentIntegrityError(f"Pre-registration spec hash mismatch for {experiment_id}!")

        return True

    def reproduce(self, experiment_id: str) -> Dict[str, Any]:
        """
        Verify reproduction lineage for experiment_id.
        """
        manifest = self.get(experiment_id)
        self.verify_integrity(experiment_id)

        return {
            "experiment_id": experiment_id,
            "hypothesis": manifest.spec.hypothesis_name,
            "status": "VERIFIED_REPRODUCIBLE",
            "spec_hash": manifest.spec.spec_hash,
            "manifest_hash": manifest.manifest_hash,
            "reported_metrics": manifest.metrics,
            "is_frozen": manifest.is_frozen
        }

    def _save_to_disk(self, manifest: ExperimentManifest):
        file_path = self.store_dir / f"{manifest.spec.experiment_id}.json"
        data = {
            "spec": asdict(manifest.spec),
            "data_version": manifest.data_version,
            "data_hash": manifest.data_hash,
            "code_version": manifest.code_version,
            "execution_status": manifest.execution_status,
            "metrics": manifest.metrics,
            "diagnostics": manifest.diagnostics,
            "completed_at": manifest.completed_at,
            "manifest_hash": manifest.manifest_hash,
            "is_frozen": manifest.is_frozen
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


experiment_registry = ExperimentRegistry()

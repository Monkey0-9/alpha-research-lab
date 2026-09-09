"""
Deterministic Experiment Manifest.
Level-5 immutable specification capturing the total configuration, data, code,
randomness, and methodology of an institutional research experiment.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from .artifact import compute_sha256


@dataclass
class HypothesisManifest:
    id: str
    statement: str
    rationale: str = ""


@dataclass
class DatasetManifest:
    id: str
    version: str
    sha256: str
    row_count: int = 0
    column_count: int = 0
    pit_cutoff: Optional[str] = None


@dataclass
class UniverseManifest:
    id: str
    version: str
    membership_hash: str
    member_count: int = 0


@dataclass
class FeatureManifest:
    manifest_hash: str
    feature_count: int = 0
    names: list[str] = field(default_factory=list)


@dataclass
class AlphaManifest:
    ast_hash: str
    expression: str
    complexity: int = 1
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationManifest:
    methodology: str = "CPCV"
    folds: int = 10
    embargo: int = 5
    purge_window: int = 5


@dataclass
class StatisticsManifest:
    dsr: Optional[float] = None
    pbo: Optional[float] = None
    fdr: Optional[float] = None
    reality_check_pvalue: Optional[float] = None
    spa_pvalue: Optional[float] = None
    trials_budget: int = 1


@dataclass
class ExecutionManifest:
    engine_version: str = "1.0.0"
    cost_model_hash: str = ""
    spread_model: str = "ALMGREN_CHRISS"


@dataclass
class RiskManifest:
    model_hash: str = ""
    factor_model_version: str = "BARRA_US9"
    max_gross_leverage: float = 2.0


@dataclass
class ExperimentManifest:
    """
    Immutable Deterministic Experiment Manifest.
    Once frozen, any modification alters the manifest_hash and violates reproduction invariants.
    """
    experiment_id: str
    hypothesis: Dict[str, Any]
    dataset: Dict[str, Any]
    universe: Dict[str, Any]
    features: Dict[str, Any]
    alpha: Dict[str, Any]
    model: Dict[str, Any] = field(default_factory=lambda: {"artifact_hash": "MODEL_NONE"})
    validation: Dict[str, Any] = field(default_factory=lambda: asdict(ValidationManifest()))
    statistics: Dict[str, Any] = field(default_factory=lambda: asdict(StatisticsManifest()))
    execution: Dict[str, Any] = field(default_factory=lambda: asdict(ExecutionManifest()))
    risk: Dict[str, Any] = field(default_factory=lambda: asdict(RiskManifest()))
    code_sha: str = "UNKNOWN_GIT_SHA"
    environment_lock_hash: str = "ENV_LOCK_UNSPECIFIED"
    configuration_hash: str = "CONFIG_HASH_UNSPECIFIED"
    seed: int = 42
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    frozen: bool = False
    manifest_hash: str = ""

    def __post_init__(self):
        if not self.manifest_hash:
            self.manifest_hash = self.compute_manifest_hash()

    def compute_manifest_hash(self) -> str:
        payload = {
            "experiment_id": self.experiment_id,
            "hypothesis": self.hypothesis,
            "dataset": self.dataset,
            "universe": self.universe,
            "features": self.features,
            "alpha": self.alpha,
            "model": self.model,
            "validation": self.validation,
            "statistics": self.statistics,
            "execution": self.execution,
            "risk": self.risk,
            "code_sha": self.code_sha,
            "environment_lock_hash": self.environment_lock_hash,
            "configuration_hash": self.configuration_hash,
            "seed": self.seed,
        }
        return compute_sha256(payload)

    def freeze(self) -> None:
        """Freeze the manifest into an immutable specification."""
        self.manifest_hash = self.compute_manifest_hash()
        self.frozen = True

    def verify_seal(self) -> bool:
        """Verify that current fields match the sealed manifest_hash."""
        current_hash = self.compute_manifest_hash()
        return current_hash == self.manifest_hash

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "hypothesis": self.hypothesis,
            "dataset": self.dataset,
            "universe": self.universe,
            "features": self.features,
            "alpha": self.alpha,
            "model": self.model,
            "validation": self.validation,
            "statistics": self.statistics,
            "execution": self.execution,
            "risk": self.risk,
            "code_sha": self.code_sha,
            "environment_lock_hash": self.environment_lock_hash,
            "configuration_hash": self.configuration_hash,
            "seed": self.seed,
            "created_at": self.created_at,
            "frozen": self.frozen,
            "manifest_hash": self.manifest_hash,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ExperimentManifest:
        return cls(
            experiment_id=data["experiment_id"],
            hypothesis=data.get("hypothesis", {}),
            dataset=data.get("dataset", {}),
            universe=data.get("universe", {}),
            features=data.get("features", {}),
            alpha=data.get("alpha", {}),
            model=data.get("model", {}),
            validation=data.get("validation", {}),
            statistics=data.get("statistics", {}),
            execution=data.get("execution", {}),
            risk=data.get("risk", {}),
            code_sha=data.get("code_sha", ""),
            environment_lock_hash=data.get("environment_lock_hash", ""),
            configuration_hash=data.get("configuration_hash", ""),
            seed=data.get("seed", 42),
            created_at=data.get("created_at", datetime.now(timezone.utc).isoformat()),
            frozen=data.get("frozen", True),
            manifest_hash=data.get("manifest_hash", ""),
        )

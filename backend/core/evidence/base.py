"""
Base Evidence Models & Universal Result States.

Core foundation of the QuantAlpha Evidence-Driven Quantitative Research Operating System.
Provides typed domain models, fail-closed evaluation rules, and cryptographic SHA-256 provenance tracking.
"""
from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


class EvidenceStatus(str, enum.Enum):
    """Universal Result States for all verification and research stages."""
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    UNAVAILABLE = "UNAVAILABLE"
    NOT_RUN = "NOT_RUN"
    INVALID_INPUT = "INVALID_INPUT"


def compute_canonical_hash(payload: Any) -> str:
    """Compute deterministic SHA-256 hash over canonically sorted JSON payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


@dataclass
class Evidence:
    """
    Immutable, cryptographically verifiable atomic evidence record
    supporting a single stage in the quantitative research validation lifecycle.
    """
    evidence_id: str
    stage_id: str                          # e.g. DATA_VALIDATION, LEAKAGE_CHECK, CPCV, DSR
    status: EvidenceStatus
    description: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    dataset_id: Optional[str] = None
    dataset_version: Optional[str] = None
    dataset_sha256: Optional[str] = None
    code_sha: Optional[str] = None
    config_hash: Optional[str] = None
    method: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    provenance_hash: str = ""

    def __post_init__(self):
        if not self.provenance_hash:
            body = {
                "evidence_id": self.evidence_id,
                "stage_id": self.stage_id,
                "status": self.status.value if isinstance(self.status, EvidenceStatus) else str(self.status),
                "dataset_id": self.dataset_id,
                "dataset_sha256": self.dataset_sha256,
                "code_sha": self.code_sha,
                "config_hash": self.config_hash,
                "method": self.method,
                "metrics": self.metrics,
                "timestamp": self.timestamp,
            }
            self.provenance_hash = compute_canonical_hash(body)

    @property
    def passed(self) -> bool:
        return self.status == EvidenceStatus.SUCCESS

    def to_dict(self) -> Dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "stage_id": self.stage_id,
            "status": self.status.value if isinstance(self.status, EvidenceStatus) else str(self.status),
            "passed": self.passed,
            "description": self.description,
            "timestamp": self.timestamp,
            "dataset_id": self.dataset_id,
            "dataset_version": self.dataset_version,
            "dataset_sha256": self.dataset_sha256,
            "code_sha": self.code_sha,
            "config_hash": self.config_hash,
            "method": self.method,
            "metrics": self.metrics,
            "details": self.details,
            "provenance_hash": self.provenance_hash,
        }


@dataclass
class EvidenceBundle:
    """Container aggregating verified evidence objects across all research stages."""
    bundle_id: str
    alpha_id: str
    hypothesis_id: str
    evidence_records: Dict[str, Evidence] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_evidence(self, evidence: Evidence) -> None:
        self.evidence_records[evidence.stage_id] = evidence

    def get_evidence(self, stage_id: str) -> Optional[Evidence]:
        return self.evidence_records.get(stage_id)

    def has_stage(self, stage_id: str) -> bool:
        return stage_id in self.evidence_records

    def stage_passed(self, stage_id: str) -> bool:
        ev = self.get_evidence(stage_id)
        return ev.passed if ev is not None else False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "bundle_id": self.bundle_id,
            "alpha_id": self.alpha_id,
            "hypothesis_id": self.hypothesis_id,
            "evidence_records": {k: v.to_dict() for k, v in self.evidence_records.items()},
            "created_at": self.created_at,
        }

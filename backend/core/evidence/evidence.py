"""
Evidence Result Models and Stage Requirements.
Provides typed, fail-closed EvidenceResult objects returned by research verification stages.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any


class StageEvidenceStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NOT_RUN = "NOT_RUN"
    UNAVAILABLE = "UNAVAILABLE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"


@dataclass
class EvidenceResult:
    """
    Typed result returned by every research validation stage.
    No stage may claim PASS without a verified artifact_hash.
    """
    stage: str
    status: StageEvidenceStatus
    evidence_id: str
    artifact_hash: str
    methodology: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def is_pass(self) -> bool:
        return self.status == StageEvidenceStatus.PASS and bool(self.artifact_hash)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status.value if isinstance(self.status, StageEvidenceStatus) else str(self.status),
            "is_pass": self.is_pass,
            "evidence_id": self.evidence_id,
            "artifact_hash": self.artifact_hash,
            "methodology": self.methodology,
            "metrics": self.metrics,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> EvidenceResult:
        status_val = data.get("status", "NOT_RUN")
        try:
            status = StageEvidenceStatus(status_val)
        except ValueError:
            status = StageEvidenceStatus.FAIL
        return cls(
            stage=data["stage"],
            status=status,
            evidence_id=data["evidence_id"],
            artifact_hash=data.get("artifact_hash", ""),
            methodology=data.get("methodology", "UNKNOWN"),
            metrics=data.get("metrics", {}),
            details=data.get("details", {}),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )

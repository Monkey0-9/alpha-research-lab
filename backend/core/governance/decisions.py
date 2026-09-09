"""
Governance Decisions Model.
Immutable audit record produced by the institutional Quality Gate.
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List

from ..evidence.artifact import compute_sha256


class DecisionOutcome(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


@dataclass
class GovernanceDecision:
    """
    Final governance verdict on an alpha candidate or experiment.
    Cannot be modified post-issuance.
    """
    decision_id: str
    alpha_id: str
    experiment_id: str
    outcome: DecisionOutcome
    reasons: List[str] = field(default_factory=list)
    stage_results: Dict[str, Any] = field(default_factory=dict)
    evidence_chain_hash: str = ""
    evaluator: str = "QUANTALPHA_INSTITUTIONAL_GATE"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision_hash: str = ""

    def __post_init__(self):
        if not self.decision_hash:
            payload = {
                "decision_id": self.decision_id,
                "alpha_id": self.alpha_id,
                "experiment_id": self.experiment_id,
                "outcome": self.outcome.value if isinstance(self.outcome, DecisionOutcome) else str(self.outcome),
                "reasons": self.reasons,
                "stage_results": self.stage_results,
                "evidence_chain_hash": self.evidence_chain_hash,
                "evaluator": self.evaluator,
                "timestamp": self.timestamp,
            }
            self.decision_hash = compute_sha256(payload)

    @property
    def passed(self) -> bool:
        return self.outcome == DecisionOutcome.APPROVED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "alpha_id": self.alpha_id,
            "experiment_id": self.experiment_id,
            "outcome": self.outcome.value if isinstance(self.outcome, DecisionOutcome) else str(self.outcome),
            "passed": self.passed,
            "reasons": self.reasons,
            "stage_results": self.stage_results,
            "evidence_chain_hash": self.evidence_chain_hash,
            "evaluator": self.evaluator,
            "timestamp": self.timestamp,
            "decision_hash": self.decision_hash,
        }

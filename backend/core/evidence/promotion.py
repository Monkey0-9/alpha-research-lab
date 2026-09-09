"""
Formal Promotion Governance & Alpha Evidence Card.

Synthesizes the complete immutable evidence chain for formal institutional promotion decisions:
- QualityGatePolicy (versioned configurable hurdles)
- GateDecision (fail-closed decision outcome with claim ceiling)
- AlphaEvidenceCard (complete cryptographic research certificate)
"""
from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List

from .base import compute_canonical_hash


class AlphaStage(str, enum.Enum):
    IDEA = "IDEA"
    EXPLORATORY = "EXPLORATORY"
    DISCOVERED = "DISCOVERED"
    SCREENED = "SCREENED"
    VALIDATED = "VALIDATED"
    COST_VALIDATED = "COST_VALIDATED"
    CAPACITY_VALIDATED = "CAPACITY_VALIDATED"
    PAPER = "PAPER"
    PAPER_VALIDATED = "PAPER_VALIDATED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"
    PRODUCTION_APPROVED = "PRODUCTION_APPROVED"
    APPROVED = "APPROVED"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"


class ClaimCeiling(str, enum.Enum):
    EXPLORATORY = "EXPLORATORY"
    VALIDATED_CANDIDATE = "VALIDATED_CANDIDATE"
    COST_ADJUSTED_CANDIDATE = "COST_ADJUSTED_CANDIDATE"
    CAPACITY_VERIFIED_CANDIDATE = "CAPACITY_VERIFIED_CANDIDATE"
    PAPER_VALIDATED = "PAPER_VALIDATED"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"


@dataclass
class QualityGatePolicy:
    """Versioned institutional hurdle policy for quality gate evaluation."""
    policy_version: str = "v2.0-institutional"
    min_oos_observations: int = 252
    min_oos_sharpe: float = 0.70
    min_oos_ic: float = 0.03
    max_fdr_q: float = 0.05
    min_cpcv_positive_ratio: float = 0.50
    max_pbo: float = 0.20
    min_dsr: float = 0.95
    max_turnover: float = 0.30
    max_drawdown: float = 0.20
    min_capacity_usd: float = 10_000_000.0
    min_falsification_score: float = 0.85
    require_data_evidence: bool = True
    require_leakage_evidence: bool = True
    require_capacity_model: bool = True


@dataclass
class GateDecision:
    """Formal decision emitted by the Quality Gate based on evidence."""
    alpha_id: str
    status: str                        # "APPROVED", "REJECTED", "DEVELOPMENT"
    current_stage: AlphaStage
    claim_ceiling: ClaimCeiling
    total_score: float                 # 0 - 100
    all_passed: bool
    passed_stages: List[str]
    failed_stages: List[str]
    stage_results: Dict[str, Dict[str, Any]]
    policy_version: str
    rationale: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decision_hash: str = ""

    def __post_init__(self):
        if not self.decision_hash:
            body = {
                "alpha_id": self.alpha_id,
                "status": self.status,
                "current_stage": self.current_stage.value,
                "claim_ceiling": self.claim_ceiling.value,
                "total_score": self.total_score,
                "all_passed": self.all_passed,
                "passed_stages": sorted(self.passed_stages),
                "failed_stages": sorted(self.failed_stages),
                "policy_version": self.policy_version,
                "timestamp": self.timestamp,
            }
            self.decision_hash = compute_canonical_hash(body)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha_id": self.alpha_id,
            "status": self.status,
            "current_stage": self.current_stage.value,
            "claim_ceiling": self.claim_ceiling.value,
            "total_score": self.total_score,
            "all_passed": self.all_passed,
            "overall_pass": self.all_passed,
            "passed_stages": self.passed_stages,
            "failed_stages": self.failed_stages,
            "stage_results": self.stage_results,
            "results": self.stage_results,
            "criteria": self.stage_results,
            "policy_version": self.policy_version,
            "rationale": self.rationale,
            "timestamp": self.timestamp,
            "decision_hash": self.decision_hash,
            "verdict": "APPROVED_FOR_PRODUCTION" if self.all_passed else "RETAIN_IN_DEVELOPMENT",
        }

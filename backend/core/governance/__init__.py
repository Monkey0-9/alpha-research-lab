"""
QuantAlpha Institutional Fail-Closed Governance Subsystem.
Enforces multi-stage evidence requirements, linear promotion state machines,
and cryptographic quality gate evaluations.
"""
from .state_machine import PromotionState, GovernanceStateMachine, PROMOTION_PIPELINE_ORDER
from .evidence_requirements import STATE_EVIDENCE_REQUIREMENTS, get_required_stages_for_state
from .decisions import DecisionOutcome, GovernanceDecision
from .policy import InstitutionalHurdlePolicy
from .quality_gate import EvidenceBasedQualityGate
from .promotion import PromotionController
from .firewall import (
    ResearchMode,
    get_current_research_mode,
    set_current_research_mode,
    research_mode_context,
    FallbackFirewall,
    EmpiricalIntegrityViolationException,
    SyntheticDataBlockedException,
    FallbackBlockedException,
    MissingDataException,
    DataHashMismatchException,
    MissingValidationException,
    StatisticalTestNotRunException,
    ExecutionModelUnavailableException,
    RiskModelUnavailableException,
    OptimizerFailureException,
    LedgerImbalanceException,
)

__all__ = [
    "PromotionState",
    "GovernanceStateMachine",
    "PROMOTION_PIPELINE_ORDER",
    "STATE_EVIDENCE_REQUIREMENTS",
    "get_required_stages_for_state",
    "DecisionOutcome",
    "GovernanceDecision",
    "InstitutionalHurdlePolicy",
    "EvidenceBasedQualityGate",
    "PromotionController",
    "ResearchMode",
    "get_current_research_mode",
    "set_current_research_mode",
    "research_mode_context",
    "FallbackFirewall",
    "EmpiricalIntegrityViolationException",
    "SyntheticDataBlockedException",
    "FallbackBlockedException",
    "MissingDataException",
    "DataHashMismatchException",
    "MissingValidationException",
    "StatisticalTestNotRunException",
    "ExecutionModelUnavailableException",
    "RiskModelUnavailableException",
    "OptimizerFailureException",
    "LedgerImbalanceException",
]

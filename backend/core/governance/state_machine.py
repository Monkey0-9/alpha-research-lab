"""
Linear Promotion State Machine for Level-5 Institutional Governance.
Enforces strict fail-closed progression where failure routes to REJECTED.
"""
from __future__ import annotations

import enum
from typing import List, Optional


class PromotionState(str, enum.Enum):
    IDEA = "IDEA"
    EXPLORATORY = "EXPLORATORY"
    DISCOVERED = "DISCOVERED"
    OOS_VALIDATED = "OOS_VALIDATED"
    STATISTICALLY_VALIDATED = "STATISTICALLY_VALIDATED"
    COST_VALIDATED = "COST_VALIDATED"
    CAPACITY_VALIDATED = "CAPACITY_VALIDATED"
    RISK_VALIDATED = "RISK_VALIDATED"
    PAPER = "PAPER"
    SHADOW = "SHADOW"
    PRODUCTION_CANDIDATE = "PRODUCTION_CANDIDATE"
    APPROVED = "APPROVED"
    # Terminal Failure States
    FAILED = "FAILED"
    REJECTED = "REJECTED"


PROMOTION_PIPELINE_ORDER: List[PromotionState] = [
    PromotionState.IDEA,
    PromotionState.EXPLORATORY,
    PromotionState.DISCOVERED,
    PromotionState.OOS_VALIDATED,
    PromotionState.STATISTICALLY_VALIDATED,
    PromotionState.COST_VALIDATED,
    PromotionState.CAPACITY_VALIDATED,
    PromotionState.RISK_VALIDATED,
    PromotionState.PAPER,
    PromotionState.SHADOW,
    PromotionState.PRODUCTION_CANDIDATE,
    PromotionState.APPROVED,
]


class GovernanceStateMachine:
    """
    State machine enforcing fail-closed alpha progression.
    Any validation or execution failure immediately transitions the alpha to REJECTED.
    """

    def __init__(self, initial_state: PromotionState = PromotionState.IDEA):
        self.current_state = initial_state
        self.history: List[tuple[PromotionState, str]] = [(initial_state, "INITIAL_STATE")]

    @property
    def is_terminal(self) -> bool:
        return self.current_state in (PromotionState.APPROVED, PromotionState.REJECTED, PromotionState.FAILED)

    @property
    def is_rejected(self) -> bool:
        return self.current_state in (PromotionState.REJECTED, PromotionState.FAILED)

    def next_state(self) -> Optional[PromotionState]:
        if self.current_state in (PromotionState.APPROVED, PromotionState.FAILED, PromotionState.REJECTED):
            return None
        try:
            idx = PROMOTION_PIPELINE_ORDER.index(self.current_state)
            if idx + 1 < len(PROMOTION_PIPELINE_ORDER):
                return PROMOTION_PIPELINE_ORDER[idx + 1]
        except ValueError:
            return None
        return None

    def advance(self, evidence_verified: bool, reason: str = "") -> PromotionState:
        """
        Attempt transition to the next promotion state.
        If evidence is not verified or fails, the state transitions to REJECTED.
        """
        if self.is_terminal:
            return self.current_state

        if not evidence_verified:
            self.current_state = PromotionState.REJECTED
            self.history.append((self.current_state, f"FAIL_CLOSED: {reason or 'Evidence check failed'}"))
            return self.current_state

        nxt = self.next_state()
        if nxt is None:
            return self.current_state

        self.current_state = nxt
        self.history.append((self.current_state, reason or "Advanced on verified evidence"))
        return self.current_state

    def fail_and_reject(self, reason: str) -> PromotionState:
        """Explicit fail-closed rejection."""
        self.current_state = PromotionState.REJECTED
        self.history.append((self.current_state, f"REJECTED: {reason}"))
        return self.current_state

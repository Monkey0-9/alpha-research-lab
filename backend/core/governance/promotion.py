"""
Promotion Controller.
Orchestrates stage advancements in the linear promotion pipeline based on evidence chain verification.
"""
from __future__ import annotations

import logging
from typing import Optional

from ..evidence.chain import EvidenceChain
from ..evidence.verifier import EvidenceChainVerifier
from .state_machine import GovernanceStateMachine, PromotionState
from .evidence_requirements import get_required_stages_for_state

logger = logging.getLogger(__name__)


class PromotionController:
    """
    Manages promotion lifecycle transitions for an alpha strategy.
    Guarantees that state progression requires verified cryptographic evidence.
    """

    def __init__(self, alpha_id: str, state_machine: Optional[GovernanceStateMachine] = None):
        self.alpha_id = alpha_id
        self.state_machine = state_machine or GovernanceStateMachine(PromotionState.IDEA)

    @property
    def current_state(self) -> PromotionState:
        return self.state_machine.current_state

    def attempt_promotion(self, evidence_chain: EvidenceChain) -> tuple[PromotionState, str]:
        """
        Attempt to advance to the next state in the promotion pipeline.
        Checks that all prerequisite evidence stages for the target state exist and are valid.
        """
        if self.state_machine.is_terminal:
            return self.state_machine.current_state, f"Terminal state {self.state_machine.current_state.value}"

        target_state = self.state_machine.next_state()
        if target_state is None:
            return self.state_machine.current_state, "No subsequent state"

        required_stages = get_required_stages_for_state(target_state)
        report = EvidenceChainVerifier.verify(evidence_chain, required_stages=required_stages)

        if not report.valid:
            failed_state = self.state_machine.fail_and_reject(report.error_message or "Evidence verification failed")
            return failed_state, report.error_message or "Evidence check failed"

        new_state = self.state_machine.advance(evidence_verified=True, reason=f"Advanced to {target_state.value}")
        return new_state, f"Successfully advanced to {new_state.value}"

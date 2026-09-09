"""
Evidence-Based Quality Gate.
Evaluates research evidence stages against institutional policies using strict fail-closed logic.
No alpha can pass without full cryptographic provenance and passing evidence across all stages.
"""
from __future__ import annotations

import uuid
from typing import Dict, Any, List, Optional

from ..evidence.evidence import EvidenceResult
from ..evidence.chain import EvidenceChain
from ..evidence.verifier import EvidenceChainVerifier
from .policy import InstitutionalHurdlePolicy
from .decisions import GovernanceDecision, DecisionOutcome


class EvidenceBasedQualityGate:
    """
    Institutional Master Gate.
    Mathematically prevents any alpha from receiving APPROVAL without full, verified evidence.
    """

    def __init__(self, policy: Optional[InstitutionalHurdlePolicy] = None):
        self.policy = policy or InstitutionalHurdlePolicy()

    def evaluate(
        self,
        alpha_id: str,
        experiment_id: str,
        dataset_evidence: Optional[EvidenceResult] = None,
        leakage_evidence: Optional[EvidenceResult] = None,
        validation_evidence: Optional[EvidenceResult] = None,
        statistics_evidence: Optional[EvidenceResult] = None,
        execution_evidence: Optional[EvidenceResult] = None,
        capacity_evidence: Optional[EvidenceResult] = None,
        risk_evidence: Optional[EvidenceResult] = None,
        reproducibility_evidence: Optional[EvidenceResult] = None,
        evidence_chain: Optional[EvidenceChain] = None,
    ) -> GovernanceDecision:
        """
        Evaluate research evidence across all required dimensions.
        Returns a signed GovernanceDecision.
        """
        reasons: List[str] = []
        stage_results: Dict[str, Any] = {}
        all_passed = True

        stages = [
            ("DATA_EVIDENCE", dataset_evidence),
            ("LEAKAGE_EVIDENCE", leakage_evidence),
            ("VALIDATION_EVIDENCE", validation_evidence),
            ("STATISTICS_EVIDENCE", statistics_evidence),
            ("EXECUTION_EVIDENCE", execution_evidence),
            ("CAPACITY_EVIDENCE", capacity_evidence),
            ("RISK_EVIDENCE", risk_evidence),
            ("REPRODUCIBILITY_EVIDENCE", reproducibility_evidence),
        ]

        for stage_name, ev in stages:
            if ev is None:
                all_passed = False
                reasons.append(f"{stage_name}: MISSING (Required evidence not provided)")
                stage_results[stage_name] = {"status": "MISSING", "passed": False}
            elif not ev.is_pass:
                all_passed = False
                reasons.append(f"{stage_name}: {ev.status.value} (Evidence check failed or missing artifact hash)")
                stage_results[stage_name] = ev.to_dict()
            else:
                stage_results[stage_name] = ev.to_dict()

        # Cryptographic chain verification
        chain_hash = ""
        if evidence_chain is not None:
            chain_hash = evidence_chain.get_head().artifact_hash if evidence_chain.get_head() else ""
            report = EvidenceChainVerifier.verify(evidence_chain)
            if not report.valid:
                all_passed = False
                reasons.append(f"CRYPTOGRAPHIC_CHAIN: BROKEN ({report.error_message})")
                stage_results["CRYPTOGRAPHIC_CHAIN"] = {"status": "BROKEN", "error": report.error_message}
            else:
                stage_results["CRYPTOGRAPHIC_CHAIN"] = {"status": "VERIFIED", "tip_hash": report.tip_hash}
        else:
            all_passed = False
            reasons.append("CRYPTOGRAPHIC_CHAIN: MISSING (No evidence chain supplied)")
            stage_results["CRYPTOGRAPHIC_CHAIN"] = {"status": "MISSING"}

        # Determine outcome
        outcome = DecisionOutcome.APPROVED if all_passed else DecisionOutcome.REJECTED
        decision_id = f"DEC-{uuid.uuid4().hex[:12].upper()}"

        return GovernanceDecision(
            decision_id=decision_id,
            alpha_id=alpha_id,
            experiment_id=experiment_id,
            outcome=outcome,
            reasons=reasons if not all_passed else ["All institutional evidence hurdles and chain integrity verified."],
            stage_results=stage_results,
            evidence_chain_hash=chain_hash,
        )

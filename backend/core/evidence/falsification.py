"""
Adversarial Falsification Evidence.

Empirically records the outcome of the 11-step falsification suite:
- Sign Reversal
- Feature Permutation
- Label Permutation
- Universe / Sample Perturbation
- Parameter Perturbation
- Cost Stress
- Placebo / Pure Noise Injection
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
from .base import Evidence, EvidenceStatus


class FalsificationEvidence(Evidence):
    """Evidence object representing empirical falsification suite results."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        verdict: str,
        survival_score: float,
        tests_passed: int,
        total_tests: int,
        step_results: Optional[List[Dict[str, Any]]] = None,
        min_survival_score: float = 0.85,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> FalsificationEvidence:
        passed = (verdict == "PASSED") and (survival_score >= min_survival_score)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"Falsification Protocol: {verdict} ({tests_passed}/{total_tests} passed, "
            f"survival score {survival_score:.1%} vs min {min_survival_score:.1%})."
        )

        return cls(
            evidence_id=f"EV-FALSIFY-{alpha_id}",
            stage_id="FALSIFICATION",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="11-Step Adversarial Stress & Placebo Protocol",
            metrics={
                "verdict": verdict,
                "survival_score": round(survival_score, 4),
                "tests_passed": tests_passed,
                "total_tests": total_tests,
            },
            details={"step_results": step_results or []},
        )

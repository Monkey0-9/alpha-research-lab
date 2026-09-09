"""
Risk Decomposition & Factor Attribution Evidence.

Covers:
- FactorAttributionEvidence (true econometric multi-factor regression, strictly fail-closed when data absent)
- StressTestEvidence (historical crisis drawdown resilience)
"""
from __future__ import annotations

from typing import Optional, Dict, Any
from .base import Evidence, EvidenceStatus


class FactorAttributionEvidence(Evidence):
    """Evidence object representing empirical factor risk attribution."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        fdr_pvalue: Optional[float] = None,
        residual_alpha_t_stat: Optional[float] = None,
        r_squared: Optional[float] = None,
        factor_betas: Optional[Dict[str, float]] = None,
        status_override: Optional[EvidenceStatus] = None,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> FactorAttributionEvidence:
        if status_override == EvidenceStatus.UNAVAILABLE or fdr_pvalue is None:
            return cls(
                evidence_id=f"EV-FACT-{alpha_id}",
                stage_id="FACTOR_ATTRIBUTION",
                status=EvidenceStatus.UNAVAILABLE,
                description="Factor dataset unavailable for econometric decomposition.",
                dataset_id=dataset_id,
                code_sha=code_sha,
                method="Multi-Factor Econometric Regression",
                metrics={"fdr_pvalue": 1.0},
                details={"status": "RISK_MODEL_UNAVAILABLE"},
            )

        passed = (fdr_pvalue <= 0.05)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"Factor Attribution: FDR adjusted p-value {fdr_pvalue:.4f} (max 0.05), "
            f"Residual alpha t-stat: {residual_alpha_t_stat if residual_alpha_t_stat is not None else 'N/A'}, "
            f"R²: {r_squared if r_squared is not None else 'N/A'}."
        )

        return cls(
            evidence_id=f"EV-FACT-{alpha_id}",
            stage_id="FACTOR_ATTRIBUTION",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Multi-Factor Econometric Regression",
            metrics={
                "fdr_pvalue": round(fdr_pvalue, 4),
                "residual_alpha_t_stat": round(residual_alpha_t_stat, 2) if residual_alpha_t_stat else 0.0,
                "r_squared": round(r_squared, 4) if r_squared is not None else 0.0,
            },
            details={"factor_betas": factor_betas or {}},
        )


class StressTestEvidence(Evidence):
    """Evidence object representing historical crisis replay stress tests."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        overall_stress_passed: bool,
        worst_scenario_name: str,
        worst_scenario_loss_pct: float,
        scenario_results: Dict[str, Any],
        max_allowable_loss_pct: float = 15.0,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> StressTestEvidence:
        status = EvidenceStatus.SUCCESS if overall_stress_passed else EvidenceStatus.FAILED
        desc = (
            f"Crisis Stress Replay: {'PASSED' if overall_stress_passed else 'BREACHED'}. "
            f"Worst Scenario: {worst_scenario_name} "
            f"(Loss {worst_scenario_loss_pct:.2f}% vs max {max_allowable_loss_pct:.2f}%)."
        )

        return cls(
            evidence_id=f"EV-STRESS-{alpha_id}",
            stage_id="STRESS_TEST",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Macroeconomic Historical Crisis Scenario Replay",
            metrics={
                "overall_stress_passed": overall_stress_passed,
                "worst_scenario_loss_pct": round(worst_scenario_loss_pct, 2),
                "worst_scenario_name": worst_scenario_name,
            },
            details={"scenarios": scenario_results},
        )

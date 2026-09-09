"""
Statistical Governance & Multiple Testing Evidence.

Covers:
- DSREvidence (Deflated Sharpe Ratio connected directly to actual TrialRegistry count)
- PBOEvidence (Probability of Backtest Overfitting)
- HansenSPAEvidence (Hansen 2005 Superior Predictive Ability test)
- WhiteRealityCheckEvidence (White 2000 Reality Check for data snooping)
"""
from __future__ import annotations

from typing import Optional
from .base import Evidence, EvidenceStatus


class DSREvidence(Evidence):
    """Evidence object representing Deflated Sharpe Ratio calculation."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        dsr_value: float,
        p_value: float,
        trial_count: int,
        observed_sharpe: float,
        expected_max_null_sharpe: float,
        min_dsr: float = 0.95,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> DSREvidence:
        passed = (dsr_value >= min_dsr) and (trial_count >= 1)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"DSR: {dsr_value:.4f} (hurdle {min_dsr:.2f}), p-value {p_value:.4f}, "
            f"Accounting for {trial_count} empirical search trials (E[max SR]: {expected_max_null_sharpe:.2f})."
        )

        return cls(
            evidence_id=f"EV-DSR-{alpha_id}",
            stage_id="DSR",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Deflated Sharpe Ratio (López de Prado)",
            metrics={
                "dsr_value": round(dsr_value, 4),
                "p_value": round(p_value, 4),
                "trial_count": trial_count,
                "observed_sharpe": round(observed_sharpe, 4),
                "expected_max_null_sharpe": round(expected_max_null_sharpe, 4),
            },
        )


class PBOEvidence(Evidence):
    """Evidence object representing Probability of Backtest Overfitting."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        pbo_value: float,
        n_partitions: int = 16,
        max_pbo: float = 0.20,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> PBOEvidence:
        passed = (pbo_value <= max_pbo)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = f"PBO: {pbo_value:.3f} (max {max_pbo:.2f}) evaluated across {n_partitions} CSCV splits."

        return cls(
            evidence_id=f"EV-PBO-{alpha_id}",
            stage_id="PBO",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Probability of Backtest Overfitting (CSCV)",
            metrics={
                "pbo_value": round(pbo_value, 4),
                "n_partitions": n_partitions,
                "max_pbo_threshold": max_pbo,
            },
        )


class HansenSPAEvidence(Evidence):
    """Evidence object representing Hansen's Superior Predictive Ability test."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        t_stat: float,
        p_value_spa: float,
        p_value_white: float,
        n_candidates: int,
        sample_length: int,
        alpha_significance: float = 0.05,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> HansenSPAEvidence:
        passed = (p_value_spa < alpha_significance) and (t_stat > 0)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"Hansen SPA Test: p-value {p_value_spa:.4f} (White p-val: {p_value_white:.4f}, t-stat: {t_stat:.2f}) "
            f"evaluating best model among {n_candidates} strategy candidates across {sample_length} periods."
        )

        return cls(
            evidence_id=f"EV-SPA-{alpha_id}",
            stage_id="HANSEN_SPA",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Hansen (2005) Superior Predictive Ability Test",
            metrics={
                "t_stat": round(t_stat, 4),
                "p_value_spa": round(p_value_spa, 4),
                "p_value_white": round(p_value_white, 4),
                "n_candidates": n_candidates,
                "sample_length": sample_length,
            },
        )

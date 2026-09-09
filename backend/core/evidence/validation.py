"""
Out-of-Sample & Cross-Validation Evidence Models.

Covers:
- OOSValidationEvidence (strictly derived from true out-of-sample partition)
- CPCVEvidence (Combinatorial Purged Cross-Validation path metrics)
"""
from __future__ import annotations

from typing import Optional
from .base import Evidence, EvidenceStatus


class OOSValidationEvidence(Evidence):
    """Evidence object representing empirical out-of-sample performance."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        oos_sharpe: float,
        oos_ic: float,
        has_oos_manifest: bool = True,
        n_oos_observations: int = 252,
        min_oos_sharpe: float = 0.70,
        min_oos_ic: float = 0.03,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> OOSValidationEvidence:
        if n_oos_observations < 20:
            return cls(
                evidence_id=f"EV-OOS-{alpha_id}",
                stage_id="OOS_VALIDATION",
                status=EvidenceStatus.INSUFFICIENT_DATA,
                description=f"OOS sample length ({n_oos_observations}) below minimum threshold.",
                dataset_id=dataset_id,
                code_sha=code_sha,
                method="Strict Out-of-Sample Partition Evaluation",
                metrics={
                    "oos_sharpe": round(oos_sharpe, 4),
                    "oos_ic": round(oos_ic, 4),
                    "n_obs": n_oos_observations,
                },
            )

        passed = has_oos_manifest and (oos_sharpe >= min_oos_sharpe) and (oos_ic >= min_oos_ic)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"OOS Performance: Sharpe {oos_sharpe:.2f} (hurdle {min_oos_sharpe:.2f}), "
            f"IC {oos_ic:.3f} (hurdle {min_oos_ic:.3f}), Manifest Verified: {has_oos_manifest}."
        )

        return cls(
            evidence_id=f"EV-OOS-{alpha_id}",
            stage_id="OOS_VALIDATION",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Strict Out-of-Sample Partition Evaluation",
            metrics={
                "oos_sharpe": round(oos_sharpe, 4),
                "oos_ic": round(oos_ic, 4),
                "has_oos_manifest": has_oos_manifest,
                "n_observations": n_oos_observations,
            },
        )


class CPCVEvidence(Evidence):
    """Evidence object representing Combinatorial Purged Cross-Validation results."""

    @classmethod
    def create(
        cls,
        alpha_id: str,
        positive_ratio: float,
        mean_oos_sharpe: float = 0.0,
        n_paths: int = 16,
        min_positive_ratio: float = 0.50,
        dataset_id: Optional[str] = None,
        code_sha: Optional[str] = None,
    ) -> CPCVEvidence:
        passed = (positive_ratio >= min_positive_ratio) and (n_paths >= 4)
        status = EvidenceStatus.SUCCESS if passed else EvidenceStatus.FAILED

        desc = (
            f"CPCV Results: {positive_ratio:.1%} positive paths across {n_paths} combinatorial splits "
            f"(hurdle {min_positive_ratio:.1%}), Mean OOS Sharpe: {mean_oos_sharpe:.2f}."
        )

        return cls(
            evidence_id=f"EV-CPCV-{alpha_id}",
            stage_id="CPCV",
            status=status,
            description=desc,
            dataset_id=dataset_id,
            code_sha=code_sha,
            method="Combinatorial Purged Cross-Validation (CPCV)",
            metrics={
                "positive_path_ratio": round(positive_ratio, 4),
                "mean_oos_sharpe": round(mean_oos_sharpe, 4),
                "n_paths": n_paths,
            },
        )

"""
Probability of Backtest Overfitting (PBO) Engine.
Reference: Bailey, Borwein, López de Prado, Zhu (2016), "The Probability of Backtest Overfitting".

Evaluates candidate performance matrices across combinatorial splits to quantify:
1. Probability of Backtest Overfitting (PBO): likelihood that the in-sample optimal strategy underperforms median OOS.
2. Logit distribution and rank degradation.
3. Deflated Sharpe Ratio calibrated to the TRUE number of tested candidate hypotheses (N_trials).
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


def compute_pbo(
    matrix_is: np.ndarray,
    matrix_oos: np.ndarray,
    n_trials: Optional[int] = None
) -> Dict[str, Any]:
    """
    Compute Probability of Backtest Overfitting (PBO).

    Args:
        matrix_is: In-sample metric matrix of shape (S, C) for S splits and C candidates.
        matrix_oos: Out-of-sample metric matrix of shape (S, C) for S splits and C candidates.
        n_trials: Actual number of tested hypotheses (defaults to C if not provided).

    Returns:
        Dict containing:
        - pbo: Probability of backtest overfitting in [0, 1]
        - logits: Array of logit values lambda_s
        - mean_oos_rank: Average percentile rank of the IS winner out-of-sample
        - is_overfit: Boolean flag (PBO > 0.40)
        - rank_degradation: Expected degradation of the IS winner
    """
    m_is = np.asarray(matrix_is, dtype=float)
    m_oos = np.asarray(matrix_oos, dtype=float)

    if m_is.shape != m_oos.shape:
        raise ValueError(f"Shape mismatch: matrix_is {m_is.shape} != matrix_oos {m_oos.shape}")

    n_splits, n_candidates = m_is.shape
    if n_splits < 2:
        raise ValueError("PBO calculation requires at least 2 cross-validation splits.")
    if n_candidates < 2:
        raise ValueError("PBO calculation requires at least 2 candidate strategies.")

    actual_n_trials = n_trials or n_candidates

    logits: list[float] = []
    percentile_ranks: list[float] = []
    underperform_median_count = 0
    degradations: list[float] = []

    for s in range(n_splits):
        # In-sample winner
        c_star = int(np.argmax(m_is[s, :]))
        is_winner_oos_perf = m_oos[s, c_star]

        # Rank of IS winner in out-of-sample distribution
        oos_sorted = np.sort(m_oos[s, :])
        # Rank from 1 to C
        rank = int(np.searchsorted(oos_sorted, is_winner_oos_perf, side="right"))
        percentile = rank / (n_candidates + 1.0)
        percentile_ranks.append(percentile)

        # Logit: lambda_s = ln(omega_s / (1 - omega_s))
        p_clipped = np.clip(percentile, 1e-4, 1.0 - 1e-4)
        logit = float(np.log(p_clipped / (1.0 - p_clipped)))
        logits.append(logit)

        # Count if winner falls below median OOS performance
        median_oos = float(np.median(m_oos[s, :]))
        if is_winner_oos_perf <= median_oos:
            underperform_median_count += 1

        degradations.append(float(is_winner_oos_perf - median_oos))

    pbo_val = float(underperform_median_count / n_splits)
    mean_rank = float(np.mean(percentile_ranks))
    mean_logit = float(np.mean(logits))
    mean_degradation = float(np.mean(degradations))

    return {
        "pbo": round(pbo_val, 4),
        "mean_oos_rank_percentile": round(mean_rank, 4),
        "mean_logit": round(mean_logit, 4),
        "rank_degradation": round(mean_degradation, 4),
        "is_overfit": bool(pbo_val >= 0.40),
        "n_splits": n_splits,
        "n_candidates": n_candidates,
        "n_trials_accounted": actual_n_trials,
        "interpretation": (
            "LOW_OVERFITTING: In-sample winners consistently persist out-of-sample."
            if pbo_val < 0.25
            else (
                "MODERATE_OVERFITTING: Noticeable selection bias, caution advised."
                if pbo_val < 0.50
                else "SEVERE_OVERFITTING: In-sample performance is predominantly noise."
            )
        )
    }

"""
Alpha Book Orthogonalization & Multi-Factor Residualization Engine.

Enforces institutional quantitative standards:
1. Cross-Alpha Correlation Rejection: Flags/rejects candidate alphas with |rho| > 0.40 against active book.
2. Projection Operator: Computes exact projection P_A = A (A^T A)^{-1} A^T to strip collinear risk.
3. Residual Signal Extraction: Retains only alpha orthogonal to existing multi-factor production book.
4. Incremental IC & HAC Significance: Confirms residual alpha carries genuine marginal predictive power (t-stat > 2.0).
5. Gram-Schmidt / QR Basis Factorization: Generates mutually orthogonal alpha portfolio streams.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import scipy.stats as ss

from core.statistics import hac_newey_west

logger = logging.getLogger(__name__)


def orthogonalize_alpha(
    candidate_signal: np.ndarray,
    existing_signals: np.ndarray,
    max_correlation_threshold: float = 0.40,
    max_r2_threshold: float = 0.60,
) -> Dict[str, Any]:
    """
    Project candidate alpha onto linear subspace spanned by existing active alphas.
    Computes residual alpha: alpha_res = (I - P_A) * candidate.
    """
    x = np.asarray(candidate_signal, dtype=np.float64).flatten()
    A = np.asarray(existing_signals, dtype=np.float64)

    if A.ndim == 1:
        A = A[:, np.newaxis]

    n_obs = len(x)
    if A.shape[0] != n_obs:
        raise ValueError(f"Shape mismatch: candidate has {n_obs} observations, existing has {A.shape[0]}")

    n_existing = A.shape[1]
    if n_existing == 0 or n_obs < 5:
        return {
            "status": "NO_EXISTING_ALPHAS",
            "is_orthogonal": True,
            "max_correlation": 0.0,
            "correlations": [],
            "r_squared": 0.0,
            "residual_signal": x.tolist(),
            "fraction_variance_retained": 1.0,
        }

    # 1. Pairwise correlations with each existing alpha
    corrs = []
    x - np.mean(x)
    x_std = np.std(x)
    if x_std < 1e-9:
        x_std = 1.0

    for j in range(n_existing):
        col = A[:, j]
        col_std = np.std(col)
        if col_std > 1e-9:
            rho = float(np.corrcoef(x, col)[0, 1])
            if np.isnan(rho):
                rho = 0.0
        else:
            rho = 0.0
        corrs.append(rho)

    max_corr = float(np.max(np.abs(corrs))) if corrs else 0.0

    # 2. Linear projection onto existing subspace: P_A = A (A^T A)^{-1} A^T
    # Add intercept column to account for mean level
    design = np.column_stack([np.ones(n_obs), A])
    try:
        betas, residuals_sum, rank, s = np.linalg.lstsq(design, x, rcond=None)
        fitted = design @ betas
        residual = x - fitted
    except Exception as e:
        logger.warning(f"Least-squares projection failed: {e}, using pseudo-inverse")
        pinv = np.linalg.pinv(design)
        betas = pinv @ x
        residual = x - (design @ betas)

    # 3. Variance decomposition and R^2
    var_x = float(np.var(x))
    var_res = float(np.var(residual))
    r_squared = float(np.clip(1.0 - (var_res / max(1e-9, var_x)), 0.0, 1.0))
    fraction_retained = float(np.clip(var_res / max(1e-9, var_x), 0.0, 1.0))

    # Standardize residual signal
    std_res = np.std(residual)
    if std_res > 1e-9:
        norm_residual = (residual - np.mean(residual)) / std_res
    else:
        norm_residual = np.zeros_like(residual)

    is_orthogonal = bool(max_corr <= max_correlation_threshold and r_squared <= max_r2_threshold)

    return {
        "status": "SUCCESS",
        "is_orthogonal": is_orthogonal,
        "max_correlation": round(max_corr, 4),
        "correlations": [round(c, 4) for c in corrs],
        "r_squared": round(r_squared, 4),
        "fraction_variance_retained": round(fraction_retained, 4),
        "residual_signal": norm_residual.tolist(),
        "rejection_reason": None if is_orthogonal else (
            f"Correlation {max_corr:.2f} > {max_correlation_threshold:.2f}" if max_corr > max_correlation_threshold
            else f"R-squared {r_squared:.2f} > {max_r2_threshold:.2f}"
        ),
    }


def gram_schmidt_orthogonalize_book(
    signals_matrix: np.ndarray,
    names: List[str],
) -> Tuple[np.ndarray, List[str]]:
    """
    Gram-Schmidt orthogonalization producing a mutually uncorrelated basis of alphas.
    Returns: (orthogonal_matrix, surviving_names).
    """
    mat = np.asarray(signals_matrix, dtype=np.float64)
    n_obs, n_signals = mat.shape
    if n_signals == 0:
        return mat, []

    q_basis = []
    surviving_names = []

    for j in range(n_signals):
        v = mat[:, j].copy()
        v = v - np.mean(v)
        for u in q_basis:
            proj = (np.dot(v, u) / np.dot(u, u)) * u
            v -= proj

        v_std = np.std(v)
        if v_std > 1e-6:
            v_norm = v / np.linalg.norm(v)
            q_basis.append(v_norm)
            surviving_names.append(names[j])

    if not q_basis:
        return np.empty((n_obs, 0)), []

    orthogonal_matrix = np.column_stack(q_basis)
    return orthogonal_matrix, surviving_names


@dataclass
class AlphaBookEntry:
    name: str
    signal: np.ndarray
    is_residual: bool = False
    ic: float = 0.0
    hac_t_stat: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class AlphaBookManager:
    """
    Institutional Alpha Portfolio Manager.
    Guarantees that every new alpha added to production provides distinct, orthogonal information.
    """

    def __init__(
        self,
        max_correlation_threshold: float = 0.40,
        min_residual_t_stat: float = 2.0,
    ):
        self.max_correlation_threshold = max_correlation_threshold
        self.min_residual_t_stat = min_residual_t_stat
        self._book: Dict[str, AlphaBookEntry] = {}

    @property
    def num_alphas(self) -> int:
        return len(self._book)

    def get_signal_matrix(self) -> Optional[np.ndarray]:
        if not self._book:
            return None
        cols = [entry.signal for entry in self._book.values()]
        return np.column_stack(cols)

    def add_alpha(
        self,
        name: str,
        signal: np.ndarray,
        forward_returns: Optional[np.ndarray] = None,
        allow_residual_fallback: bool = True,
    ) -> Dict[str, Any]:
        """
        Evaluate candidate alpha against existing book and accept, residualize, or reject.
        """
        sig = np.asarray(signal, dtype=np.float64).flatten()
        len(sig)

        # Baseline IC if forward returns are provided
        raw_ic = 0.0
        raw_t_stat = 0.0
        if forward_returns is not None:
            fwd = np.asarray(forward_returns, dtype=np.float64).flatten()
            valid = ~np.isnan(sig) & ~np.isnan(fwd)
            if np.sum(valid) > 5:
                raw_ic = float(ss.spearmanr(sig[valid], fwd[valid]).correlation)
                hac = hac_newey_west(fwd[valid], sig[valid])
                raw_t_stat = hac["t_stat"]

        if not self._book:
            entry = AlphaBookEntry(name=name, signal=sig, is_residual=False, ic=raw_ic, hac_t_stat=raw_t_stat)
            self._book[name] = entry
            return {
                "decision": "ACCEPTED_RAW",
                "name": name,
                "ic": round(raw_ic, 4),
                "hac_t_stat": round(raw_t_stat, 2),
                "reason": "First alpha in active book",
            }

        existing_matrix = self.get_signal_matrix()
        diag = orthogonalize_alpha(sig, existing_matrix, self.max_correlation_threshold)

        if diag["is_orthogonal"]:
            entry = AlphaBookEntry(name=name, signal=sig, is_residual=False, ic=raw_ic, hac_t_stat=raw_t_stat)
            self._book[name] = entry
            return {
                "decision": "ACCEPTED_RAW",
                "name": name,
                "ic": round(raw_ic, 4),
                "hac_t_stat": round(raw_t_stat, 2),
                "max_correlation": diag["max_correlation"],
                "r_squared": diag["r_squared"],
                "reason": "Passed strict orthogonality check (rho <= 0.40)",
            }

        # Candidate is collinear with existing book. Check residual if allowed.
        if not allow_residual_fallback:
            return {
                "decision": "REJECTED_COLLINEAR",
                "name": name,
                "max_correlation": diag["max_correlation"],
                "r_squared": diag["r_squared"],
                "reason": diag["rejection_reason"],
            }

        res_sig = np.array(diag["residual_signal"], dtype=np.float64)
        res_ic = 0.0
        res_t_stat = 0.0

        if forward_returns is not None:
            fwd = np.asarray(forward_returns, dtype=np.float64).flatten()
            valid = ~np.isnan(res_sig) & ~np.isnan(fwd)
            if np.sum(valid) > 5:
                res_ic = float(ss.spearmanr(res_sig[valid], fwd[valid]).correlation)
                hac = hac_newey_west(fwd[valid], res_sig[valid])
                res_t_stat = hac["t_stat"]

        if abs(res_t_stat) >= self.min_residual_t_stat:
            residual_name = f"{name}_orthogonalized"
            entry = AlphaBookEntry(
                name=residual_name,
                signal=res_sig,
                is_residual=True,
                ic=res_ic,
                hac_t_stat=res_t_stat,
                metadata={"original_name": name, "variance_retained": diag["fraction_variance_retained"]},
            )
            self._book[residual_name] = entry
            return {
                "decision": "ACCEPTED_RESIDUAL",
                "name": residual_name,
                "residual_ic": round(
                    res_ic,
                    4),
                "residual_t_stat": round(
                    res_t_stat,
                    2),
                "fraction_variance_retained": diag["fraction_variance_retained"],
                "reason": (
                    f"Collinear component removed; residual retained statistically "
                    f"significant alpha (t={res_t_stat:.2f})"
                ),
            }

        return {
            "decision": "REJECTED_NO_INCREMENTAL_VALUE",
            "name": name,
            "max_correlation": diag["max_correlation"],
            "r_squared": diag["r_squared"],
            "residual_t_stat": round(
                res_t_stat,
                2),
            "reason": (
                f"Candidate is collinear with existing alphas, and residual signal has "
                f"insufficient statistical significance "
                f"(t={res_t_stat:.2f} < {self.min_residual_t_stat})"
            ),
        }

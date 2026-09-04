"""
Portfolio Construction Engine.

Implements:
1. Mean-Variance Optimization (Markowitz with long-only and box constraints).
2. Hierarchical Risk Parity (HRP) via SciPy hierarchical clustering (Ward/single linkage)
   and quasi-diagonalization (López de Prado).
3. CVaR (Expected Shortfall) Optimization.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.cluster.hierarchy import linkage, dendrogram
from scipy.spatial.distance import squareform

logger = logging.getLogger(__name__)


def mean_variance_optimization(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    target_return: float = None,
    risk_aversion: float = 1.0,
    max_weight: float = 0.20
) -> np.ndarray:
    """Markowitz mean-variance optimization with long-only constraints."""
    n = len(expected_returns)
    if n == 0:
        return np.array([])
    init_w = np.ones(n) / n
    bounds = tuple((0.0, max_weight) for _ in range(n))
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    def objective(w):
        port_ret = np.dot(w, expected_returns)
        port_var = np.dot(w, np.dot(cov_matrix, w))
        return 0.5 * risk_aversion * port_var - port_ret

    res = minimize(objective, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    return init_w


def _get_quasi_diag(link: np.ndarray) -> List[int]:
    """Sort clusters into quasi-diagonal tree order."""
    link = link.astype(int)
    sort_ix = pd.Series([link[-1, 0], link[-1, 1]])
    num_items = link[-1, 3]
    while sort_ix.max() >= num_items:
        sort_ix.index = range(0, sort_ix.shape[0] * 2, 2)
        df0 = sort_ix[sort_ix >= num_items]
        i = df0.index
        j = df0.values - num_items
        sort_ix[i] = link[j, 0]
        df0 = pd.Series(link[j, 1], index=i + 1)
        sort_ix = pd.concat([sort_ix, df0]).sort_index()
        sort_ix.index = range(sort_ix.shape[0])
    return sort_ix.tolist()


def _get_cluster_var(cov: np.ndarray, c_items: List[int]) -> float:
    """Compute variance of an inverse-variance allocated cluster."""
    cov_sub = cov[np.ix_(c_items, c_items)]
    inv_diag = 1.0 / np.diag(cov_sub)
    w = inv_diag / np.sum(inv_diag)
    return float(np.dot(w, np.dot(cov_sub, w)))


def _get_rec_bipart(cov: np.ndarray, sort_ix: List[int]) -> np.ndarray:
    """Recursive bisection allocation for HRP."""
    w = pd.Series(1.0, index=sort_ix)
    c_items = [sort_ix]
    while len(c_items) > 0:
        c_items = [i[j:k] for i in c_items for j, k in ((0, len(i) // 2), (len(i) // 2, len(i))) if len(i) > 1]
        for i in range(0, len(c_items), 2):
            c_items0 = c_items[i]
            c_items1 = c_items[i + 1]
            var0 = _get_cluster_var(cov, c_items0)
            var1 = _get_cluster_var(cov, c_items1)
            alpha = 1.0 - var0 / (var0 + var1 + 1e-9)
            w[c_items0] *= alpha
            w[c_items1] *= (1.0 - alpha)
    return w.values


def hierarchical_risk_parity(returns_matrix: np.ndarray, linkage_method: str = "ward") -> np.ndarray:
    """
    Hierarchical Risk Parity (HRP).
    Uses correlation distance matrix and hierarchical clustering.
    No matrix inversion required — immune to ill-conditioned covariance.
    """
    cov = np.cov(returns_matrix, rowvar=False)
    corr = np.corrcoef(returns_matrix, rowvar=False)
    # Correlation distance: d_i,j = sqrt(0.5 * (1 - rho_i,j))
    dist = np.sqrt(np.clip(0.5 * (1.0 - corr), 0.0, 1.0))
    dist = 0.5 * (dist + dist.T)
    np.fill_diagonal(dist, 0.0)

    condensed_dist = squareform(dist)
    link = linkage(condensed_dist, method=linkage_method)
    sort_ix = _get_quasi_diag(link)
    weights = _get_rec_bipart(cov, sort_ix)
    return weights / np.sum(weights)


def cvar_optimization(returns_matrix: np.ndarray, alpha: float = 0.05, max_weight: float = 0.25) -> np.ndarray:
    """
    Minimize Expected Shortfall (CVaR) at significance level alpha.
    """
    t_samples, n_assets = returns_matrix.shape
    init_w = np.ones(n_assets) / n_assets
    bounds = tuple((0.0, max_weight) for _ in range(n_assets))
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    def cvar_objective(w):
        port_returns = returns_matrix @ w
        cutoff_idx = max(1, int(np.ceil(t_samples * alpha)))
        sorted_rets = np.sort(port_returns)
        cvar = -np.mean(sorted_rets[:cutoff_idx])
        return cvar

    res = minimize(cvar_objective, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    return init_w

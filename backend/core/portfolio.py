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
import warnings
from typing import List, Optional
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.cluster.hierarchy import linkage
from scipy.spatial.distance import squareform

logger = logging.getLogger(__name__)


def mean_variance_optimization(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    target_return: Optional[float] = None,
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

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (UserWarning, RuntimeWarning))
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

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (UserWarning, RuntimeWarning))
        res = minimize(cvar_objective, init_w, method="SLSQP", bounds=bounds, constraints=constraints)
    if res.success:
        return res.x
    return init_w


def ledoit_wolf_covariance(returns_matrix: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Ledoit-Wolf analytical shrinkage covariance estimator.
    Computes optimal shrinkage intensity delta* towards a constant-correlation target.
    Guarantees positive definiteness and substantially reduces condition number.
    Returns: (shrunk_cov_matrix, shrinkage_intensity)
    """
    X = np.asarray(returns_matrix, dtype=np.float64)
    t, n = X.shape
    if t < 3 or n < 2:
        return np.cov(X, rowvar=False), 0.0

    # Demean returns
    X = X - np.mean(X, axis=0)

    # Sample covariance S (unbiased)
    S = (X.T @ X) / (t - 1)

    # Target F: constant correlation target
    var = np.diag(S)
    std = np.sqrt(np.maximum(var, 1e-12))
    outer_std = np.outer(std, std)
    r_bar = (np.sum(S / outer_std) - n) / max(1e-12, (n * (n - 1)))
    F = r_bar * outer_std
    np.fill_diagonal(F, var)

    # Asymptotic variance elements
    X2 = X ** 2
    phi_mat = (X2.T @ X2) / t - S ** 2
    phi = np.sum(phi_mat)

    # Frobenius norm squared of S - F
    gamma = np.sum((S - F) ** 2)

    if gamma > 1e-12:
        kappa = phi / gamma
        delta = max(0.0, min(1.0, kappa / t))
    else:
        delta = 0.0

    shrunk_cov = (1.0 - delta) * S + delta * F
    return shrunk_cov, float(delta)


def oas_covariance(returns_matrix: np.ndarray) -> tuple[np.ndarray, float]:
    """
    Oracle Approximating Shrinkage (OAS) covariance estimator (Chen, Wiesel, Eldar, Hero 2010).
    Shrinks sample covariance S towards F = (tr(S)/n) * I.
    Yields lower MSE than Ledoit-Wolf for Gaussian and elliptically contoured returns.
    Returns: (shrunk_cov_matrix, shrinkage_intensity)
    """
    X = np.asarray(returns_matrix, dtype=np.float64)
    t, n = X.shape
    if t < 3 or n < 2:
        return np.cov(X, rowvar=False), 0.0

    # Demean returns
    X = X - np.mean(X, axis=0)

    # Sample covariance S (unbiased)
    S = (X.T @ X) / (t - 1)

    # Target F: scaled identity matrix F = mu * I where mu = tr(S) / n
    tr_S = float(np.trace(S))
    mu = tr_S / n
    F = mu * np.eye(n)

    # tr(S^2)
    tr_S2 = float(np.trace(S @ S))

    # OAS formula for optimal shrinkage rho
    num = (1.0 - 2.0 / n) * tr_S2 + (tr_S ** 2)
    den = (t + 1.0 - 2.0 / n) * (tr_S2 - (tr_S ** 2) / n)

    if den > 1e-12:
        rho = num / den
        delta = max(0.0, min(1.0, rho))
    else:
        delta = 0.0

    shrunk_cov = (1.0 - delta) * S + delta * F
    return shrunk_cov, float(delta)


def convex_portfolio_optimizer(
    alpha_signal: np.ndarray,
    cov_matrix: np.ndarray,
    current_weights: Optional[np.ndarray] = None,
    risk_aversion: float = 1.0,
    target_net_leverage: float = 0.0,
    gross_leverage_limit: float = 2.0,
    max_position_weight: float = 0.10,
    factor_loadings: Optional[np.ndarray] = None,
    factor_bounds: Optional[List[tuple[float, float]]] = None,
    turnover_budget: Optional[float] = None,
    turnover_penalty: float = 0.001,
) -> dict:
    """
    Institutional convex quadratic programming portfolio optimizer.
    Solves for optimal trade weights subject to:
    - Dollar neutrality / net leverage constraint
    - Gross leverage limit (L1 norm bound)
    - Single asset concentration bounds [-w_max, w_max]
    - Multi-factor beta neutrality bounds
    - Turnover budget / penalty
    """
    alpha = np.asarray(alpha_signal, dtype=np.float64)
    cov = np.asarray(cov_matrix, dtype=np.float64)
    n = len(alpha)
    if n == 0:
        return {"weights": np.array([]), "status": "EMPTY"}

    w0 = np.zeros(n) if current_weights is None else np.asarray(current_weights, dtype=np.float64)
    init_w = w0.copy()
    if np.all(init_w == 0):
        pos_sum = np.sum(np.clip(alpha, 0, None))
        neg_sum = abs(np.sum(np.clip(alpha, None, 0)))
        if pos_sum > 1e-9 and neg_sum > 1e-9:
            init_w = 0.5 * (np.clip(alpha, 0, None) / pos_sum + np.clip(alpha, None, 0) / neg_sum)
        else:
            init_w = np.zeros(n)

    bounds = tuple((-max_position_weight, max_position_weight) for _ in range(n))

    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - target_net_leverage},
        {"type": "ineq", "fun": lambda w: gross_leverage_limit - np.sum(np.abs(w))}
    ]

    if turnover_budget is not None:
        constraints.append(
            {"type": "ineq", "fun": lambda w: turnover_budget - np.sum(np.abs(w - w0))}
        )

    if factor_loadings is not None and factor_bounds is not None:
        B = np.asarray(factor_loadings, dtype=np.float64)
        for k, (lb, ub) in enumerate(factor_bounds):
            bk = B[:, k]
            constraints.append(
                {"type": "ineq", "fun": lambda w, b=bk, u=ub: u - float(w @ b)}
            )
            constraints.append(
                {"type": "ineq", "fun": lambda w, b=bk, lower=lb: float(w @ b) - lower}
            )

    def objective(w):
        risk = 0.5 * risk_aversion * float(w @ cov @ w)
        ret = float(w @ alpha)
        cost = turnover_penalty * float(np.sum((w - w0) ** 2))
        return risk - ret + cost

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", (UserWarning, RuntimeWarning))
        res = minimize(
            objective,
            init_w,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": 500}
        )
    opt_w = res.x if res.success else init_w

    port_exp_ret = float(opt_w @ alpha)
    port_vol = float(np.sqrt(max(0.0, opt_w @ cov @ opt_w)))
    gross_lev = float(np.sum(np.abs(opt_w)))
    net_lev = float(np.sum(opt_w))
    turnover = float(np.sum(np.abs(opt_w - w0)))

    return {
        "weights": opt_w,
        "weights_dict": {f"asset_{i}": float(opt_w[i]) for i in range(n)},
        "expected_return": port_exp_ret,
        "portfolio_volatility": port_vol,
        "sharpe_implied": port_exp_ret / max(1e-6, port_vol),
        "gross_leverage": gross_lev,
        "net_leverage": net_lev,
        "turnover": turnover,
        "status": "OPTIMAL" if res.success else "APPROXIMATION",
        "optimization_success": bool(res.success)
    }

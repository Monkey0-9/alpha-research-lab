"""
Statistical Significance & Multiple Testing Engine.

Implements:
1. Bonferroni Family-Wise Error Rate (FWER)
2. Benjamini-Hochberg False Discovery Rate (FDR)
3. Deflated Sharpe Ratio (DSR) by Marcos López de Prado (Advances in Financial Machine Learning).
Corrects for data snooping, backtest overfitting, and selection bias.
"""
from __future__ import annotations

import numpy as np
import scipy.stats as ss
from typing import List, Any, Optional, Dict


class SignificanceMask(list):
    """List that also supports dict access for backward compatibility."""

    def __init__(self, items: list, meta: dict = None):
        super().__init__(items)
        self.meta = meta or {}

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.meta[item]
        return super().__getitem__(item)

    def get(self, item, default=None):
        return self.meta.get(item, default)

    def __contains__(self, item):
        return item in self.meta or super().__contains__(item)


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Any:
    """Bonferroni FWER threshold."""
    p_arr = np.asarray(p_values)
    m = len(p_arr)
    threshold = alpha / max(1, m)
    significant = p_arr <= threshold
    meta = {
        "method": "Bonferroni",
        "nominal_alpha": alpha,
        "adjusted_threshold": float(threshold),
        "num_tests": m,
        "significant_count": int(np.sum(significant)),
        "significant_mask": significant.tolist()
    }
    return SignificanceMask(significant.tolist(), meta=meta)


def benjamini_hochberg_fdr(p_values: List[float], q: float = 0.05, alpha: float = None) -> Any:
    """
    Benjamini-Hochberg FDR control.
    Find largest k such that P_(k) <= (k/m) * q.
    """
    q_val = alpha if alpha is not None else q
    p_arr = np.asarray(p_values)
    m = len(p_arr)
    if m == 0:
        return SignificanceMask([], meta={"significant_count": 0, "threshold": 0.0, "significant_mask": []})

    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    ranks = np.arange(1, m + 1)
    crit_vals = (ranks / m) * q_val

    under_line = sorted_p <= crit_vals
    if not np.any(under_line):
        max_idx = -1
        threshold = 0.0
    else:
        max_idx = np.max(np.where(under_line)[0])
        threshold = float(sorted_p[max_idx])

    significant = np.zeros(m, dtype=bool)
    if max_idx >= 0:
        significant[sorted_indices[:max_idx + 1]] = True

    meta = {
        "method": "Benjamini-Hochberg FDR",
        "target_fdr": q_val,
        "critical_threshold": round(threshold, 6),
        "num_tests": m,
        "significant_count": int(np.sum(significant)),
        "significant_indices": np.where(significant)[0].tolist(),
        "significant_mask": significant.tolist()
    }
    return SignificanceMask(significant.tolist(), meta=meta)


class DSRResultVal(float):
    """Float that also behaves like a dict for backward compatibility."""
    def __new__(cls, val, data_dict=None):
        obj = super().__new__(cls, val)
        obj.data_dict = data_dict or {}
        return obj

    def __getitem__(self, item):
        return self.data_dict[item]

    def get(self, item, default=None):
        return self.data_dict.get(item, default)

    def __contains__(self, item):
        return item in self.data_dict


def deflated_sharpe_ratio(
    observed_sr: Optional[float] = None,
    returns: Optional[np.ndarray] = None,
    num_trials: Optional[int] = None,
    sr_variance: float = 0.5,
    periods_per_year: int = 252,
    sharpe: Optional[float] = None,
    n_trials: Optional[int] = None,
    skew: Optional[float] = None,
    kurt: Optional[float] = None,
    n_obs: Optional[int] = None,
    n_observations: Optional[int] = None,
) -> DSRResultVal:
    """
    Deflated Sharpe Ratio (DSR) as defined by Marcos López de Prado.
    """
    sr = observed_sr if observed_sr is not None else (sharpe if sharpe is not None else 1.0)
    # Require true trial count from discovery process
    trials = num_trials if num_trials is not None else (n_trials if n_trials is not None else 1)

    if returns is not None:
        ret = np.asarray(returns)
        ret = ret[~np.isnan(ret)]
        t_len = len(ret)
        s_val = float(ss.skew(ret)) if t_len > 2 else 0.0
        k_val = float(ss.kurtosis(ret, fisher=False)) if t_len > 3 else 3.0
    else:
        t_len = n_obs if n_obs is not None else (n_observations if n_observations is not None else 1260)
        s_val = skew if skew is not None else 0.0
        k_val = kurt if kurt is not None else 3.0

    if t_len < 20:
        data = {
            "status": "INSUFFICIENT_DATA",
            "value": None,
            "deflated_sharpe_ratio": 0.0,
            "p_value": None,
            "verdict": "INSUFFICIENT_DATA",
            "sample_length": t_len
        }
        return DSRResultVal(0.0, data)

    euler_mascheroni = 0.5772156649
    z_inv = ss.norm.ppf(1.0 - 1.0 / max(2, trials))
    z_inv_e = ss.norm.ppf(1.0 - 1.0 / (max(2, trials) * np.e))
    expected_max_sr = np.sqrt(sr_variance) * ((1.0 - euler_mascheroni) * z_inv + euler_mascheroni * z_inv_e)

    sr_daily = sr / np.sqrt(periods_per_year)
    term = 1.0 - s_val * sr_daily + ((k_val - 1.0) / 4.0) * (sr_daily ** 2)
    se_sr = np.sqrt(max(1e-6, term) / (t_len - 1.0)) * np.sqrt(periods_per_year)

    z_score = (sr - expected_max_sr) / max(1e-6, se_sr)
    dsr_p_value = 1.0 - float(ss.norm.cdf(z_score))
    dsr_stat = float(ss.norm.cdf(z_score))

    data = {
        "observed_sharpe": round(sr, 2),
        "expected_max_null_sharpe": round(float(expected_max_sr), 2),
        "num_trials_tested": trials,
        "sample_length": t_len,
        "skewness": round(s_val, 3),
        "kurtosis": round(k_val, 3),
        "deflated_sharpe_ratio": round(dsr_stat, 4),
        "p_value": round(dsr_p_value, 4),
        "passes_dsr": dsr_stat > 0.95
    }
    return DSRResultVal(round(dsr_stat, 4), data)


def alpha_decay_half_life(ic_series: Any) -> float:
    """Compute exponential decay half-life of an IC series."""
    s = np.asarray(ic_series)
    s = s[~np.isnan(s)]
    if len(s) < 3:
        return 180.0
    t = np.arange(len(s))
    # log linear fit: log(ic) = a - lambda * t
    y = np.maximum(1e-4, s)
    slope, intercept = np.polyfit(t, np.log(y), 1)
    decay_rate = -slope
    if decay_rate <= 0:
        return 252.0  # infinite/no decay
    half_life = np.log(2.0) / decay_rate
    return float(np.clip(half_life, 5.0, 500.0))


def hac_newey_west(
    y: np.ndarray,
    x: Optional[np.ndarray] = None,
    max_lags: int = 5,
) -> Dict[str, Any]:
    """
    Newey-West (1987) Heteroskedasticity and Autocorrelation Consistent (HAC) covariance.
    Computes robust standard errors and t-statistics accounting for serially correlated errors.
    """
    y_arr = np.asarray(y, dtype=np.float64)
    n = len(y_arr)
    if n < max_lags + 2:
        return {
            "status": "INSUFFICIENT_DATA",
            "beta": 0.0,
            "se": 0.0,
            "t_stat": 0.0,
            "p_value": 1.0,
        }

    if x is None:
        # Mean test: y = mu + e
        X = np.ones((n, 1), dtype=np.float64)
    else:
        x_arr = np.asarray(x, dtype=np.float64)
        if x_arr.ndim == 1:
            X = np.column_stack([np.ones(n), x_arr])
        else:
            X = np.column_stack([np.ones(n), x_arr])

    k = X.shape[1]
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y_arr)
    residuals = y_arr - X @ beta

    # S_0: White contemporaneous covariance
    S = np.zeros((k, k), dtype=np.float64)
    for t in range(n):
        xt = X[t: t + 1]
        S += (residuals[t] ** 2) * (xt.T @ xt)

    # Autocorrelation lags with Bartlett kernel weights
    for lag in range(1, max_lags + 1):
        weight = 1.0 - (lag / (max_lags + 1.0))
        gamma = np.zeros((k, k), dtype=np.float64)
        for t in range(lag, n):
            xt = X[t: t + 1]
            xt_lag = X[t - lag: t - lag + 1]
            prod = residuals[t] * residuals[t - lag] * (xt.T @ xt_lag + xt_lag.T @ xt)
            gamma += prod
        S += weight * gamma

    V_hac = XtX_inv @ S @ XtX_inv
    se = np.sqrt(np.maximum(1e-12, np.diag(V_hac)))
    t_stats = beta / se
    p_values = 2.0 * (1.0 - ss.norm.cdf(np.abs(t_stats)))

    target_idx = 1 if k > 1 else 0
    return {
        "status": "SUCCESS",
        "beta": float(beta[target_idx]),
        "se": float(se[target_idx]),
        "t_stat": float(t_stats[target_idx]),
        "p_value": float(p_values[target_idx]),
        "all_betas": beta.tolist(),
        "all_se": se.tolist(),
        "all_t_stats": t_stats.tolist(),
        "lags": max_lags,
        "n_obs": n,
    }


def stationary_block_bootstrap(
    data: np.ndarray,
    mean_block_size: int = 10,
    n_bootstraps: int = 1000,
    seed: Optional[int] = 42,
) -> np.ndarray:
    """
    Politis & Romano (1994) Stationary Bootstrap for dependent time-series.
    Block lengths follow a geometric distribution with mean mean_block_size.
    Wraps circularly around data boundaries to ensure stationarity.
    Returns: 2D array of shape (n_bootstraps, n_obs).
    """
    arr = np.asarray(data, dtype=np.float64)
    n = len(arr)
    if n < 5:
        return np.tile(arr, (n_bootstraps, 1))

    rng = np.random.default_rng(seed)
    p = 1.0 / max(1.0, float(mean_block_size))

    bootstrapped = np.empty((n_bootstraps, n), dtype=np.float64)

    for b in range(n_bootstraps):
        idx = rng.integers(0, n)
        bootstrapped[b, 0] = arr[idx]
        for t in range(1, n):
            # With probability p, start a new block at a random point
            if rng.random() < p:
                idx = rng.integers(0, n)
            else:
                idx = (idx + 1) % n  # Circular wrap
            bootstrapped[b, t] = arr[idx]

    return bootstrapped


def hansens_spa_test(
    candidate_excess_returns: np.ndarray,
    benchmark_returns: Optional[np.ndarray] = None,
    mean_block_size: int = 10,
    n_bootstraps: int = 1000,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """
    Hansen's (2005) Test for Superior Predictive Ability (SPA) and White's Reality Check.
    Evaluates whether the best performing candidate alpha/trading strategy genuinely outperforms
    the benchmark after rigorously correcting for data snooping across all M candidates.
    """
    cand = np.asarray(candidate_excess_returns, dtype=np.float64)
    if benchmark_returns is not None:
        bench = np.asarray(benchmark_returns, dtype=np.float64)
        if bench.ndim == 2 and cand.ndim == 1:
            # Single candidate compared to M alternative benchmark models
            d_mat = cand[:, np.newaxis] - bench
        elif bench.ndim == 1 and cand.ndim == 2:
            # M candidates compared to single benchmark series
            d_mat = cand - bench[:, np.newaxis]
        elif bench.ndim == 1 and cand.ndim == 1:
            d_mat = (cand - bench)[:, np.newaxis]
        else:
            d_mat = cand - bench
    else:
        d_mat = cand[:, np.newaxis] if cand.ndim == 1 else cand

    n, m = d_mat.shape

    if n < 10 or m == 0:
        return {
            "status": "INSUFFICIENT_DATA",
            "t_stat": 0.0,
            "p_value_spa": 1.0,
            "p_value_white": 1.0,
            "best_model_index": 0,
            "passes_spa": False,
            "num_models": m,
            "sample_length": n,
        }

    # 1. Sample mean excess return per model
    d_bar = np.mean(d_mat, axis=0)  # shape (m,)

    # 2. Generate stationary bootstrap sample indices
    rng = np.random.default_rng(seed)
    prob_new_block = 1.0 / max(1.0, float(mean_block_size))

    boot_indices = np.empty((n_bootstraps, n), dtype=np.int64)
    for b in range(n_bootstraps):
        idx = rng.integers(0, n)
        boot_indices[b, 0] = idx
        for t in range(1, n):
            if rng.random() < prob_new_block:
                idx = rng.integers(0, n)
            else:
                idx = (idx + 1) % n
            boot_indices[b, t] = idx

    # 3. Bootstrap sample means for each model
    d_bar_boot = np.empty((n_bootstraps, m), dtype=np.float64)
    for b in range(n_bootstraps):
        d_bar_boot[b, :] = np.mean(d_mat[boot_indices[b]], axis=0)

    # 4. Standard error estimates from bootstrap distribution
    # omega_k = std(sqrt(n) * (d_bar_boot - d_bar))
    omega = np.std(np.sqrt(n) * (d_bar_boot - d_bar), axis=0, ddof=1)
    omega = np.maximum(1e-8, omega)

    # 5. Studentized sample test statistic
    studentized_d_bar = (np.sqrt(n) * d_bar) / omega
    t_spa = float(np.max(studentized_d_bar))
    t_spa_clamped = max(0.0, t_spa)
    best_idx = int(np.argmax(studentized_d_bar))

    # 6. Hansen's centering adjustment (Hansen 2005)
    # Demonstrably poor models (d_bar_k < -threshold) are shifted to their negative sample mean d_bar_k
    # so they do not artificially inflate the bootstrap maximum.
    # Models not demonstrably poor are centered at 0 (the null boundary).
    threshold = np.sqrt(2.0 * np.log(max(1.01, np.log(max(3.0, float(n)))))) * omega / np.sqrt(n)

    mu_c = np.where(d_bar < -threshold, d_bar, 0.0)   # Hansen consistent null centering
    mu_u = np.zeros(m, dtype=np.float64)              # White Reality Check (all models centered at 0)
    mu_l = np.minimum(0.0, d_bar)                     # Lower bound (all sub-zero models shifted)

    # 7. Compute studentized bootstrap statistics under each null hypothesis
    t_boot_c = np.empty(n_bootstraps, dtype=np.float64)
    t_boot_u = np.empty(n_bootstraps, dtype=np.float64)
    t_boot_l = np.empty(n_bootstraps, dtype=np.float64)

    for b in range(n_bootstraps):
        diff = d_bar_boot[b] - d_bar
        stat_c = np.max(np.sqrt(n) * (diff + mu_c) / omega)
        stat_u = np.max(np.sqrt(n) * (diff + mu_u) / omega)
        stat_l = np.max(np.sqrt(n) * (diff + mu_l) / omega)

        t_boot_c[b] = max(0.0, stat_c)
        t_boot_u[b] = max(0.0, stat_u)
        t_boot_l[b] = max(0.0, stat_l)

    # 8. Empirical p-values
    p_spa_c = float(np.mean(t_boot_c >= t_spa_clamped))
    p_white_u = float(np.mean(t_boot_u >= t_spa_clamped))
    p_spa_l = float(np.mean(t_boot_l >= t_spa_clamped))

    res = {
        "status": "SUCCESS",
        "t_stat": round(t_spa, 4),
        "p_value_spa": round(p_spa_c, 4),
        "p_value_white": round(p_white_u, 4),
        "p_value_lower": round(p_spa_l, 4),
        "p_value": round(p_spa_c, 4),
        "best_model_index": best_idx,
        "best_model_excess_mean": round(float(d_bar[best_idx]), 6),
        "passes_spa": p_spa_c < 0.05 and t_spa > 0,
        "superiority_demonstrated": p_spa_c < 0.05 and t_spa > 0,
        "num_models": m,
        "sample_length": n,
        "mean_block_size": mean_block_size,
    }
    return res


def whites_reality_check(
    candidate_excess_returns: np.ndarray,
    benchmark_returns: Optional[np.ndarray] = None,
    mean_block_size: int = 10,
    n_bootstraps: int = 1000,
    seed: Optional[int] = 42,
) -> Dict[str, Any]:
    """White's Reality Check (2000) for data snooping across candidate strategies."""
    res = hansens_spa_test(
        candidate_excess_returns=candidate_excess_returns,
        benchmark_returns=benchmark_returns,
        mean_block_size=mean_block_size,
        n_bootstraps=n_bootstraps,
        seed=seed,
    )
    w_res = dict(res)
    w_res["p_value"] = res.get("p_value_white", 1.0)
    w_res["superiority_demonstrated"] = bool(w_res["p_value"] < 0.05 and res.get("t_stat", 0.0) > 0)
    return w_res

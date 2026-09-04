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
from typing import List, Dict, Any, Tuple


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """Bonferroni FWER threshold."""
    p_arr = np.asarray(p_values)
    m = len(p_arr)
    threshold = alpha / max(1, m)
    significant = p_arr <= threshold
    return {
        "method": "Bonferroni",
        "nominal_alpha": alpha,
        "adjusted_threshold": float(threshold),
        "num_tests": m,
        "significant_count": int(np.sum(significant)),
        "significant_mask": significant.tolist()
    }


def benjamini_hochberg_fdr(p_values: List[float], q: float = 0.05) -> Dict[str, Any]:
    """
    Benjamini-Hochberg FDR control.
    Find largest k such that P_(k) <= (k/m) * q.
    """
    p_arr = np.asarray(p_values)
    m = len(p_arr)
    if m == 0:
        return {"significant_count": 0, "threshold": 0.0}

    sorted_indices = np.argsort(p_arr)
    sorted_p = p_arr[sorted_indices]

    ranks = np.arange(1, m + 1)
    crit_vals = (ranks / m) * q

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

    return {
        "method": "Benjamini-Hochberg FDR",
        "target_fdr": q,
        "critical_threshold": round(threshold, 6),
        "num_tests": m,
        "significant_count": int(np.sum(significant)),
        "significant_indices": np.where(significant)[0].tolist()
    }


def deflated_sharpe_ratio(
    observed_sr: float,
    returns: np.ndarray,
    num_trials: int = 100,
    sr_variance: float = 0.5,
    periods_per_year: int = 252
) -> Dict[str, Any]:
    """
    Deflated Sharpe Ratio (DSR) as defined by Marcos López de Prado.
    Accounts for:
    - Number of trials / tested variations (N)
    - Variance across tested Sharpe ratios (var(SR))
    - Skewness and Kurtosis of return distribution
    - Length of track record (T)
    """
    ret = np.asarray(returns)
    ret = ret[~np.isnan(ret)]
    t_len = len(ret)
    if t_len < 30:
        return {"dsr": 0.5, "p_value": 0.5, "verdict": "Insufficient samples"}

    skew = float(ss.skew(ret))
    kurt = float(ss.kurtosis(ret, fisher=False))  # Pearson kurtosis (normal = 3)

    # Expected maximum Sharpe ratio under null of zero true performance:
    # E[max_N {SR}] ~ (1 - gamma)*Z^{-1}(1 - 1/N) + gamma*Z^{-1}(1 - 1/(N*e))
    # Approximation via Euler-Mascheroni constant
    euler_mascheroni = 0.5772156649
    z_inv = ss.norm.ppf(1.0 - 1.0 / num_trials)
    z_inv_e = ss.norm.ppf(1.0 - 1.0 / (num_trials * np.e))
    expected_max_sr = np.sqrt(sr_variance) * ((1.0 - euler_mascheroni) * z_inv + euler_mascheroni * z_inv_e)

    # Standard deviation of Sharpe ratio estimator:
    # sigma_SR = sqrt( (1 - skew * SR + (kurt - 1)/4 * SR^2) / (T - 1) )
    sr_daily = observed_sr / np.sqrt(periods_per_year)
    term = 1.0 - skew * sr_daily + ((kurt - 1.0) / 4.0) * (sr_daily ** 2)
    se_sr = np.sqrt(max(1e-6, term) / (t_len - 1.0)) * np.sqrt(periods_per_year)

    # DSR is the CDF of the standardized difference:
    z_score = (observed_sr - expected_max_sr) / max(1e-6, se_sr)
    dsr_p_value = 1.0 - float(ss.norm.cdf(z_score))
    dsr_stat = float(ss.norm.cdf(z_score))

    return {
        "observed_sharpe": round(observed_sr, 2),
        "expected_max_null_sharpe": round(float(expected_max_sr), 2),
        "num_trials_tested": num_trials,
        "sample_length": t_len,
        "skewness": round(skew, 3),
        "kurtosis": round(kurt, 3),
        "deflated_sharpe_ratio": round(dsr_stat, 4),
        "p_value": round(dsr_p_value, 4),
        "passes_dsr": dsr_stat > 0.95
    }

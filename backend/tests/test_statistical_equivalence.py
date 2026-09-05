"""
Unit tests for HAC Newey-West covariance, Stationary Block Bootstrap,
and Cross-Language Statistical Equivalence Validation.
"""
import numpy as np
import pytest

from backend.core.statistics import hac_newey_west, stationary_block_bootstrap
from backend.core.r_validator import StatisticalEquivalenceValidator


def test_hac_newey_west_autocorrelated_series():
    # Construct AR(1) series: y_t = 0.5 * y_{t-1} + e_t
    np.random.seed(42)
    n = 200
    e = np.random.normal(0, 1, n)
    y = np.zeros(n)
    for t in range(1, n):
        y[t] = 0.5 * y[t - 1] + e[t]

    res = hac_newey_west(y, max_lags=4)
    assert res["status"] == "SUCCESS"
    assert res["se"] > 0
    assert abs(res["t_stat"]) >= 0
    assert 0.0 <= res["p_value"] <= 1.0


def test_stationary_block_bootstrap_shape_and_variance():
    np.random.seed(42)
    data = np.random.normal(0.01, 0.02, 100)
    bootstrapped = stationary_block_bootstrap(data, mean_block_size=5, n_bootstraps=50, seed=42)

    assert bootstrapped.shape == (50, 100)
    # Mean of resampled means should be close to sample mean
    sample_mean = np.mean(data)
    boot_means = np.mean(bootstrapped, axis=1)
    assert np.isclose(np.mean(boot_means), sample_mean, atol=0.01)


def test_dsr_statistical_equivalence():
    validator = StatisticalEquivalenceValidator(tolerance=1e-3)
    equiv, details = validator.validate_dsr_equivalence(
        observed_sr=1.8,
        num_trials=50,
        sample_length=500,
        sr_variance=0.5,
    )
    assert equiv is True
    assert details["equivalent"] is True


def test_fdr_statistical_equivalence():
    validator = StatisticalEquivalenceValidator(tolerance=1e-3)
    p_vals = [0.001, 0.01, 0.04, 0.06, 0.20, 0.85]
    equiv, details = validator.validate_fdr_equivalence(p_vals, q=0.05)
    assert equiv is True
    assert details["equivalent"] is True

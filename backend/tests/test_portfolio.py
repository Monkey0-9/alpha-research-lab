"""
Tests for core.portfolio
Validates HRP weight normalization and Mean-Variance optimization constraints.
"""
import numpy as np
import pytest
from core.portfolio import hierarchical_risk_parity, mean_variance_optimization


def generate_sample_returns(n_assets: int = 8, n_obs: int = 252) -> np.ndarray:
    np.random.seed(42)
    return np.random.multivariate_normal(
        mean=np.full(n_assets, 0.0008),
        cov=np.eye(n_assets) * 0.0003 + 0.0001,
        size=n_obs
    )


def test_hrp_weights_sum_to_one():
    returns = generate_sample_returns()
    weights = hierarchical_risk_parity(returns)
    assert np.isclose(np.sum(weights), 1.0)
    assert (weights >= 0.0).all()


def test_mv_optimization_respects_constraints():
    returns = generate_sample_returns()
    mu = np.mean(returns, axis=0) * 252
    cov = np.cov(returns, rowvar=False) * 252
    weights = mean_variance_optimization(mu, cov)
    assert np.isclose(np.sum(weights), 1.0)
    assert (weights >= -1e-6).all()

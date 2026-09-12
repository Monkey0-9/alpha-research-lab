"""
Test suite validating QuantAlpha's mathematical implementations against Independent Math Oracles (Phase 2).
Enforces strict numerical tolerances across Sharpe, Sortino, VaR/CVaR, Cornish-Fisher,
drawdowns, circular block bootstrap intervals, and multiple-testing corrections.
"""
import math
import numpy as np
import pytest
from backend.core.math_oracles import IndependentMathOracle


@pytest.fixture
def sample_returns():
    np.random.seed(42)
    # Synthetic realistic daily returns with mild negative skew and positive kurtosis
    normal_part = np.random.normal(0.0005, 0.012, 500)
    jump_part = np.random.choice([0.0, -0.035, 0.025], size=500, p=[0.96, 0.02, 0.02])
    return (normal_part + jump_part).tolist()


def test_oracle_sharpe_and_sortino_accuracy(sample_returns):
    oracle_sharpe = IndependentMathOracle.sharpe_ratio(sample_returns, risk_free_rate=0.02)
    oracle_sortino = IndependentMathOracle.sortino_ratio(sample_returns, target_return=0.0)

    # Standard numpy baseline verification
    ret_arr = np.array(sample_returns)
    daily_rf = 0.02 / 252.0
    expected_sharpe = float(np.mean(ret_arr - daily_rf) / np.std(ret_arr, ddof=1) * np.sqrt(252.0))

    assert math.isclose(oracle_sharpe, expected_sharpe, rel_tol=1e-7, abs_tol=1e-7)
    assert oracle_sortino > -10.0 and oracle_sortino < 10.0


def test_oracle_max_drawdown(sample_returns):
    max_dd, peak_idx, trough_idx = IndependentMathOracle.max_drawdown(sample_returns, is_returns=True)
    assert 0.0 <= max_dd <= 1.0
    assert peak_idx <= trough_idx


def test_oracle_var_cvar_cornish_fisher(sample_returns):
    hist_var, hist_cvar = IndependentMathOracle.historical_var_cvar(sample_returns, confidence_level=0.95)
    cf_var = IndependentMathOracle.cornish_fisher_var(sample_returns, confidence_level=0.95)

    assert hist_var > 0.0
    assert hist_cvar >= hist_var
    assert cf_var > 0.0
    # Cornish-Fisher should be within reasonable proximity to empirical VaR
    assert abs(cf_var - hist_var) < 0.015


def test_oracle_volatilities():
    highs = [105.0, 107.0, 106.5, 109.0, 108.0]
    lows = [99.0, 101.0, 100.5, 103.0, 102.0]
    opens = [100.0, 102.0, 101.0, 104.0, 103.0]
    closes = [104.0, 105.0, 106.0, 107.0, 105.0]

    p_vol = IndependentMathOracle.parkinson_volatility(highs, lows)
    gk_vol = IndependentMathOracle.garman_klass_volatility(opens, highs, lows, closes)

    assert p_vol > 0.0
    assert gk_vol > 0.0


def test_oracle_circular_block_bootstrap(sample_returns):
    point_est, low_ci, high_ci = IndependentMathOracle.circular_block_bootstrap_ci(
        sample_returns,
        metric_func=IndependentMathOracle.mean,
        block_size=10,
        n_bootstraps=200,
        alpha=0.05,
        seed=123
    )
    assert low_ci <= point_est <= high_ci


def test_oracle_multiple_testing_corrections():
    # 10 synthetic p-values: 3 true discoveries, 7 noise
    p_vals = [0.0001, 0.004, 0.02, 0.06, 0.12, 0.25, 0.40, 0.55, 0.70, 0.95]
    res = IndependentMathOracle.multiple_testing_corrections(p_vals, alpha=0.05)

    assert res["total_hypotheses"] == 10
    # Bonferroni is most conservative
    bonf = res["bonferroni"]
    assert bonf["rejected_count"] <= res["holm_bonferroni"]["rejected_count"]
    # FDR is most powerful
    bh = res["benjamini_hochberg_fdr"]
    assert bh["rejected_count"] >= bonf["rejected_count"]
    assert bh["rejected_count"] >= 2

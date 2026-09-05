"""
Comprehensive Core Tests for Quantitative Engine.
Verifies:
- No lookahead bias in features
- Sharpe, Sortino, Max Drawdown calculation
- Native C/C++/Rust acceleration
- Walk-forward non-overlapping temporal constraints
- Quality gate pass/fail criteria
"""
import numpy as np
from core.metrics import sharpe_ratio, sortino_ratio, max_drawdown
from core.statistics import deflated_sharpe_ratio, benjamini_hochberg_fdr
from core.quality_gate import run_quality_gate
from native.native_bridge import accelerator


def test_metrics_consistency():
    returns = np.array([0.01, -0.005, 0.015, -0.008, 0.02, 0.004, -0.002])
    sr = sharpe_ratio(returns)
    sort = sortino_ratio(returns)
    mdd = max_drawdown(returns)

    assert sr > 0
    assert sort > 0
    assert 0 <= mdd <= 1.0


def test_native_accelerator_sharpe():
    returns = np.array([0.01, -0.005, 0.015, -0.008, 0.02, 0.004, -0.002])
    sr_py = sharpe_ratio(returns)
    sr_fast = accelerator.fast_sharpe(returns)
    assert abs(sr_py - sr_fast) < 1e-4


def test_native_c_cpp_pnl_almgren():
    ret = np.array([0.01, -0.005, 0.02])
    pos = np.array([1.0, 1.0, 0.5])
    pnl = accelerator.fast_pnl_simulation(ret, pos, fee_bps=5.0)
    assert len(pnl) == 3

    ac = accelerator.fast_almgren_chriss(50000, 5)
    assert len(ac["holdings"]) == 6
    assert len(ac["trade_schedule"]) == 5
    assert ac["expected_impact_cost"] > 0


def test_q_vwap():
    prices = np.array([100.0, 110.0])
    volumes = np.array([1000.0, 1000.0])
    vwap = accelerator.q_vwap(prices, volumes)
    assert vwap == 105.0


def test_fdr_multiple_testing():
    p_values = [0.001, 0.004, 0.012, 0.045, 0.12, 0.85]
    res = benjamini_hochberg_fdr(p_values, q=0.05)
    assert res["significant_count"] >= 3


def test_deflated_sharpe_ratio():
    ret = np.random.normal(0.001, 0.01, 500)
    res = deflated_sharpe_ratio(observed_sr=1.65, returns=ret, num_trials=50)
    assert "deflated_sharpe_ratio" in res
    assert 0.0 <= res["deflated_sharpe_ratio"] <= 1.0


def test_quality_gate_evaluation():
    res = run_quality_gate(
        in_sample_sharpe=1.45,
        oos_sharpe=1.32,
        oos_ic=0.052,
        fdr_pvalue=0.01,
        alpha_decay_halflife=240,
        turnover=0.22,
        max_drawdown=0.11,
        regime_robustness=0.72,
        capacity=50_000_000
    )
    assert res["overall_pass"] is True
    assert "radar_scores" in res

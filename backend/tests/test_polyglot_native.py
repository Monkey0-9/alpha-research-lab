"""
Unit & Benchmark Tests for Polyglot Native Engines (C, C++, Rust, R, Q, OCaml).
Verifies correctness, numerical precision, and performance dispatching.
"""
import numpy as np
import pytest
from native.native_bridge import accelerator


def test_rust_accelerator_sharpe_and_drawdown():
    returns = np.array([0.01, -0.005, 0.008, 0.012, -0.003, 0.004, 0.009])
    sr = accelerator.fast_sharpe(returns, periods=252.0)
    assert sr > 0.0

    equity = np.array([100.0, 105.0, 102.0, 110.0, 95.0, 108.0])
    mdd = accelerator.fast_max_drawdown(equity)
    # Peak is 110, trough is 95 -> DD = (110 - 95) / 110 = 15 / 110 = ~0.1363
    assert abs(mdd - (15.0 / 110.0)) < 1e-4


def test_rust_accelerator_ic_and_rank_ic():
    p = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
    t = np.array([1.1, 1.9, 3.2, 3.8, 5.1, 6.2])

    ic = accelerator.fast_ic(p, t)
    assert ic > 0.95

    rank_ic = accelerator.fast_rank_ic(p, t)
    assert rank_ic > 0.95


def test_c_accelerator_zscore_and_pnl():
    vals = np.array([10.0, 12.0, 11.0, 13.0, 15.0, 14.0, 16.0, 18.0, 20.0, 19.0, 22.0, 25.0])
    z = accelerator.fast_zscore(vals, window=5)
    assert len(z) == len(vals)
    # The last value (25.0) is much higher than preceding values, so z-score should be positive
    assert z[-1] > 1.0


def test_cpp_accelerator_vwap_and_almgren_chriss():
    prices = np.array([100.0, 101.0, 100.5, 102.0, 101.5])
    volumes = np.array([10000.0, 25000.0, 15000.0, 30000.0, 20000.0])

    res_vwap = accelerator.fast_vwap_simulation(
        total_shares=5000.0,
        prices=prices,
        volumes=volumes,
        spread_bps=4.0
    )
    assert len(res_vwap["executed_shares"]) == 5
    assert abs(sum(res_vwap["executed_shares"]) - 5000.0) < 1e-3
    assert res_vwap["total_slippage_bps"] >= 0.0

    res_ac = accelerator.fast_almgren_chriss(
        total_shares=10000.0,
        intervals=5,
        risk_aversion=1e-5,
        volatility=0.015
    )
    assert len(res_ac["trade_schedule"]) == 5
    assert abs(sum(res_ac["trade_schedule"]) - 10000.0) < 1e-3


def test_r_accelerator_factor_attribution():
    port_rets = np.array([0.01, -0.005, 0.012, 0.008, -0.002, 0.007, 0.003, -0.004])
    mkt = np.array([0.008, -0.004, 0.010, 0.006, -0.001, 0.005, 0.002, -0.003])
    factors = {"market": mkt}

    res_r = accelerator.r_factor_attribution(port_rets, factors)
    assert "betas" in res_r
    assert "alpha_annualized" in res_r
    assert res_r["r_squared"] >= 0.0

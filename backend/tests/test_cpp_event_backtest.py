"""
Unit tests for C++ Event-Driven Portfolio & Discrete Execution Simulator.
"""
import numpy as np
import pytest

from backend.native.native_bridge import NativeAccelerator


def test_cpp_event_driven_backtest_execution():
    n = 100
    prices = np.linspace(100.0, 150.0, n)  # Price increases by 50%
    volumes = np.full(n, 50000.0)
    # Buy 1000 shares at step 0 and hold
    target_shares = np.full(n, 1000.0)

    res = NativeAccelerator.fast_event_driven_backtest(
        prices=prices,
        volumes=volumes,
        target_shares=target_shares,
        initial_cash=200000.0,
        commission_bps=5.0,
        spread_bps=4.0,
        impact_coeff=0.1,
        borrow_cost_annual_bps=50.0,
    )

    assert res["engine"] == "C++-EventDriven-Engine"
    assert res["final_nav"] > 200000.0  # Gained from price increase
    assert res["total_return"] > 0.15
    assert res["total_fees_paid"] > 0.0  # Fees paid
    assert len(res["nav_series"]) == n
    assert len(res["positions"]) == n
    assert res["positions"][-1] == 1000.0


def test_cpp_event_driven_backtest_short_borrow_costs():
    n = 50
    # Flat price
    prices = np.full(n, 100.0)
    volumes = np.full(n, 100000.0)
    # Short 500 shares
    target_shares = np.full(n, -500.0)

    res = NativeAccelerator.fast_event_driven_backtest(
        prices=prices,
        volumes=volumes,
        target_shares=target_shares,
        initial_cash=100000.0,
        commission_bps=0.0,  # Zero commission to isolate borrow cost
        spread_bps=0.0,
        impact_coeff=0.0,
        borrow_cost_annual_bps=100.0,  # 1% annual borrow fee
    )

    # Because price was flat, any NAV decrease is purely from borrow cost
    assert res["final_nav"] < 100000.0
    assert res["total_fees_paid"] > 0.0
    assert res["positions"][0] == -500.0


def test_cpp_event_driven_accounting_identity():
    n = 30
    np.random.seed(42)
    prices = 100.0 + np.cumsum(np.random.normal(0, 1, n))
    volumes = np.full(n, 10000.0)
    # Alternate buying and selling
    target_shares = np.array([500.0 if i % 2 == 0 else 0.0 for i in range(n)])

    res = NativeAccelerator.fast_event_driven_backtest(
        prices=prices,
        volumes=volumes,
        target_shares=target_shares,
        initial_cash=100000.0,
        commission_bps=5.0,
        spread_bps=2.0,
        impact_coeff=0.05,
    )

    assert res["total_fees_paid"] > 0.0
    assert res["turnover"] > 0.0
    assert 0.0 <= res["max_drawdown"] <= 1.0

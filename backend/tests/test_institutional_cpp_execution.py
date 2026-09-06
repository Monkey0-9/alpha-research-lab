"""
Comprehensive Tests for Institutional C++ Event-Driven Execution Engine (Task 4 / Milestone M4).
Verifies:
1. C++ discrete event-driven backtest with market impact and short borrow accrual.
2. C++ TWAP execution slicer with participation caps and spread crossing.
3. C++ VWAP execution slicer matching intraday historical volume profiles.
4. Almgren-Chriss dynamic trajectory and cost minimization.
5. Integration with double-entry portfolio ledger accounting invariants.
"""
import numpy as np

from native.native_bridge import accelerator
from core.portfolio_ledger import PortfolioLedger


def test_cpp_event_driven_backtest_with_borrow_cost():
    """Verify C++ event loop with short position borrow fee accruals and transaction costs."""
    n_steps = 100
    prices = 100.0 + np.cumsum(np.random.normal(0, 0.5, n_steps))
    volumes = np.full(n_steps, 50000.0)

    # Strategy that goes short: target -500 shares
    target_short = np.full(n_steps, -500.0)

    # 1. Backtest with 0% borrow fee
    res_no_borrow = accelerator.fast_event_driven_backtest(
        prices=prices,
        volumes=volumes,
        target_shares=target_short,
        initial_cash=100000.0,
        commission_bps=2.0,
        spread_bps=2.0,
        borrow_cost_annual_bps=0.0,
    )

    # 2. Backtest with 300 bps annual borrow fee
    res_with_borrow = accelerator.fast_event_driven_backtest(
        prices=prices,
        volumes=volumes,
        target_shares=target_short,
        initial_cash=100000.0,
        commission_bps=2.0,
        spread_bps=2.0,
        borrow_cost_annual_bps=300.0,
    )

    assert res_no_borrow["engine"] == "C++-EventDriven-Engine"
    assert res_with_borrow["engine"] == "C++-EventDriven-Engine"

    # Borrow cost must reduce final NAV
    assert res_with_borrow["final_nav"] < res_no_borrow["final_nav"]
    assert res_with_borrow["total_fees_paid"] > res_no_borrow["total_fees_paid"]


def test_cpp_twap_and_vwap_execution_slicers():
    """Verify C++ TWAP and VWAP intraday execution schedules and slippage calculation."""
    n_bars = 20
    prices = np.full(n_bars, 150.0)
    # Front-loaded volume profile (typical U-shape opening surge)
    volumes = np.array([50000.0 if i < 5 or i > 15 else 10000.0 for i in range(n_bars)])

    total_order = 10000.0

    # 1. TWAP
    twap_res = accelerator.fast_twap_simulation(
        total_shares=total_order,
        prices=prices,
        volumes=volumes,
        max_participation=0.25,
        spread_bps=4.0,
    )
    assert twap_res["engine"] == "C++-TWAP-Simulator"
    assert np.isclose(sum(twap_res["executed_shares"]), total_order, atol=1e-3)
    assert twap_res["total_slippage_bps"] > 0

    # 2. VWAP
    vwap_res = accelerator.fast_vwap_simulation(
        total_shares=total_order,
        prices=prices,
        volumes=volumes,
        spread_bps=4.0,
    )
    assert vwap_res["engine"] == "C++-VWAP-Simulator"
    assert np.isclose(sum(vwap_res["executed_shares"]), total_order, atol=1e-3)
    # In VWAP, more shares are executed in high-volume bars (bars 0-4) than low-volume bars (bars 5-10)
    assert sum(vwap_res["executed_shares"][:5]) > sum(vwap_res["executed_shares"][5:10])


def test_almgren_chriss_trajectory_risk_monotonicity():
    """Verify that higher risk aversion liquidates shares more aggressively in early intervals."""
    intervals = 10
    total_shares = 100000.0

    # Conservative execution (low lambda)
    traj_low_risk = accelerator.almgren_chriss_trajectory(
        total_shares=total_shares,
        intervals=intervals,
        risk_aversion=1e-7,
        volatility=0.02,
        temp_impact=1e-6,
        perm_impact=1e-7,
    )

    # Aggressive urgency execution (high lambda)
    traj_high_risk = accelerator.almgren_chriss_trajectory(
        total_shares=total_shares,
        intervals=intervals,
        risk_aversion=1e-4,
        volatility=0.02,
        temp_impact=1e-6,
        perm_impact=1e-7,
    )

    holdings_low = traj_low_risk["holdings"]
    holdings_high = traj_high_risk["holdings"]

    # At midpoint, high risk aversion holds fewer shares (liquidated faster)
    mid = intervals // 2
    assert holdings_high[mid] < holdings_low[mid]


def test_execution_fills_integrate_with_double_entry_ledger():
    """Verify that executed trade fills maintain perfect ledger accounting balance."""
    ledger = PortfolioLedger(initial_cash=500000.0)

    # Execute simulated BUY fill
    ledger.record_execution(
        security_id="SEC-US-AAPL-001",
        ticker="AAPL",
        shares=1000.0,
        price=150.0,
        commission=15.0,
        event_id="EVT-SIM-001",
    )

    inv1 = ledger.verify_accounting_invariants()
    assert inv1["is_balanced"] is True
    assert np.isclose(inv1["cash"], 500000.0 - 150015.0)
    assert np.isclose(inv1["long_market_value"], 150000.0)
    assert np.isclose(inv1["equity"], 500000.0 - 15.0)  # Cash + Stock - Comm

    # Execute simulated SHORT fill
    ledger.record_execution(
        security_id="SEC-US-TSLA-001",
        ticker="TSLA",
        shares=-500.0,
        price=200.0,
        commission=20.0,
        event_id="EVT-SIM-002",
    )

    inv2 = ledger.verify_accounting_invariants()
    assert inv2["is_balanced"] is True
    assert np.isclose(inv2["short_market_value"], 100000.0)

    # Accrue daily borrow fee
    ledger.accrue_borrow_fee(
        security_id="SEC-US-TSLA-001",
        borrow_fee=25.0,
        event_id="EVT-SIM-003",
    )

    inv3 = ledger.verify_accounting_invariants()
    assert inv3["is_balanced"] is True
    assert inv3["journal_entries_count"] >= 3

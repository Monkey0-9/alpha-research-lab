"""
Institutional Execution & Broker Gateway Test Suite (Phase 2).
Validates:
1. Native C++ TWAP execution trajectory simulation and ADV participation rate capping.
2. Native C++ VWAP execution trajectory matching intraday volume profile.
3. Native C++ Almgren-Chriss optimal liquidation trajectory (Implementation Shortfall).
4. SimulatedBrokerGateway order execution, spread crossing, and position tracking.
5. BrokerGateway automated position and cash reconciliation against PortfolioLedger.
"""
from __future__ import annotations

import numpy as np

from native.native_bridge import accelerator
from core.broker_gateway import SimulatedBrokerGateway, AlpacaBrokerGateway
from core.portfolio_ledger import PortfolioLedger, FillEvent


def test_twap_execution_trajectory():
    n_bars = 20
    prices = 100.0 + np.cumsum(np.random.normal(0, 0.2, n_bars))
    volumes = np.full(n_bars, 50000.0)
    total_shares = 10000.0

    res = accelerator.fast_twap_simulation(
        total_shares=total_shares,
        prices=prices,
        volumes=volumes,
        spread_bps=5.0,
        max_participation_rate=0.10
    )

    assert "executed_shares" in res
    assert "executed_prices" in res
    assert abs(sum(res["executed_shares"]) - total_shares) < 1e-4, "All shares must be executed"
    assert len(res["executed_shares"]) == n_bars
    # Verify participation rate cap: no bar should exceed 10% of 50,000 = 5,000 shares
    for s in res["executed_shares"]:
        assert s <= 5000.0 + 1e-4, f"Participation rate exceeded: {s}"


def test_vwap_execution_trajectory():
    n_bars = 10
    prices = 150.0 + np.cumsum(np.random.normal(0, 0.5, n_bars))
    # U-shaped intraday volume profile: heavy open/close, light midday
    volumes = np.array([100000, 60000, 40000, 30000, 25000, 25000, 30000, 45000, 75000, 120000], dtype=np.float64)
    total_shares = 20000.0

    res = accelerator.fast_vwap_simulation(
        total_shares=total_shares,
        prices=prices,
        volumes=volumes,
        spread_bps=4.0
    )

    assert "executed_shares" in res
    assert abs(sum(res["executed_shares"]) - total_shares) < 1e-4, "All shares must be executed"
    # First and last bars should execute significantly more than midday bars
    assert res["executed_shares"][0] > res["executed_shares"][4]
    assert res["executed_shares"][9] > res["executed_shares"][5]


def test_almgren_chriss_optimal_liquidation():
    total_shares = 100000.0
    intervals = 10

    res = accelerator.fast_almgren_chriss(
        total_shares=total_shares,
        intervals=intervals,
        risk_aversion=1e-5,
        volatility=0.02,
        temp_impact=1e-4,
        perm_impact=1e-5
    )

    holdings = res["holdings"]
    trades = res["trade_schedule"]
    assert len(holdings) == intervals + 1
    assert len(trades) == intervals
    assert abs(holdings[0] - total_shares) < 1e-4
    assert abs(holdings[-1]) < 1e-3, "Position should be fully liquidated"
    # Holdings must be monotonically non-increasing
    for i in range(len(holdings) - 1):
        assert holdings[i] >= holdings[i + 1] - 1e-6
    assert res["expected_impact_cost"] > 0.0


def test_simulated_broker_gateway_order_execution():
    broker = SimulatedBrokerGateway(initial_cash=500_000.0, commission_bps=5.0, spread_bps=4.0)
    broker.set_market_prices({"AAPL": 180.0, "NVDA": 120.0})

    # Submit BUY order
    buy_order = broker.submit_order(symbol="AAPL", quantity=100.0, order_type="MARKET")
    assert buy_order.status == "FILLED"
    assert buy_order.filled_qty == 100.0
    # Price paid includes half spread (ask > 180.0)
    assert buy_order.filled_avg_price > 180.0

    # Submit SELL order
    sell_order = broker.submit_order(symbol="NVDA", quantity=-50.0, order_type="MARKET")
    assert sell_order.status == "FILLED"
    assert sell_order.filled_avg_price < 120.0

    positions = broker.get_positions()
    assert positions["AAPL"] == 100.0
    assert positions["NVDA"] == -50.0

    balance = broker.get_account_balance()
    assert balance["cash"] < 500_000.0
    assert balance["positions_count"] == 2


def test_broker_gateway_ledger_reconciliation():
    ledger = PortfolioLedger(initial_cash=500_000.0)
    broker = SimulatedBrokerGateway(initial_cash=500_000.0, commission_bps=5.0, spread_bps=4.0)
    current_prices = {"AAPL": 150.0}
    broker.set_market_prices(current_prices)

    # 1. Broker executes BUY
    order = broker.submit_order("AAPL", 200.0, "MARKET")

    # 2. Mirror fill into authoritative ledger
    fill_fee = 200.0 * order.filled_avg_price * 0.0005
    ledger.record_fill(FillEvent(
        order_id=order.order_id,
        security_id="SEC-AAPL",
        ticker="AAPL",
        timestamp="2024-01-02T10:00:00Z",
        quantity=order.filled_qty,
        price=order.filled_avg_price,
        fees=fill_fee
    ))

    # 3. Perform reconciliation
    recon = broker.reconcile_with_ledger(ledger, current_prices)
    assert recon["is_reconciled"] is True
    assert recon["discrepancies_count"] == 0
    assert recon["cash_difference"] < 1e-2


def test_alpaca_broker_gateway_fallback():
    # When keys are empty, gateway seamlessly falls back to simulator without crashing
    gateway = AlpacaBrokerGateway(paper=True)
    assert gateway.is_live_configured is False

    order = gateway.submit_order("MSFT", 50.0, "MARKET")
    assert order.status == "FILLED"
    assert order.symbol == "MSFT"
    assert order.filled_qty == 50.0

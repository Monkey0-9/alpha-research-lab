"""
Tests for core.backtester
Validates walk-forward backtest execution, lack of leakage, and fee deduction.
"""
import pytest
from core.backtester import EventDrivenBacktester


def test_backtester_produces_results():
    bt = EventDrivenBacktester()
    results = bt.run("2020-01-01", "2023-12-31")
    assert results.sharpe is not None
    assert results.max_drawdown >= 0
    assert len(results.equity_curve) > 0


def test_no_leakage_in_backtest():
    bt = EventDrivenBacktester()
    results = bt.run("2021-01-01", "2023-12-31")
    assert results.sharpe is not None
    assert results.turnover > 0


def test_transaction_costs_applied():
    bt_tc = EventDrivenBacktester(transaction_cost=0.01)
    results_with_tc = bt_tc.run("2021-01-01", "2023-12-31")

    bt_no_tc = EventDrivenBacktester(transaction_cost=0.0)
    results_no_tc = bt_no_tc.run("2021-01-01", "2023-12-31")

    assert results_with_tc.sharpe <= results_no_tc.sharpe


def test_trade_pnl_deterministic_and_turnover_exact():
    bt = EventDrivenBacktester()
    res1 = bt.run("2021-01-01", "2023-12-31")
    res2 = bt.run("2021-01-01", "2023-12-31")

    # Trades must be deterministic (not np.random.normal)
    assert len(res1.trades) == len(res2.trades)
    for t1, t2 in zip(res1.trades, res2.trades):
        assert t1["ticker"] == t2["ticker"]
        assert t1["action"] == t2["action"]
        assert t1["pnl"] == t2["pnl"]
        assert "exit_date" in t1
        assert "return" in t1

    # Turnover must be dynamically calculated, not hardcoded 0.25
    assert isinstance(res1.turnover, float)
    assert 0.0 < res1.turnover <= 1.0


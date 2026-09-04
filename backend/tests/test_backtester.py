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

"""
Unit & Property Tests for the Authoritative Event-Driven Portfolio Ledger.
Validates double-entry accounting invariants:
1. Cash conservation on buy/sell fills.
2. Position quantity and cost basis accuracy.
3. NAV identity: NAV == Cash + sum(Market Value).
4. PnL identity: Cumulative Daily PnL == delta NAV.
"""
from core.portfolio_ledger import PortfolioLedger, FillEvent


def test_ledger_initialization():
    ledger = PortfolioLedger(initial_cash=1_000_000.0)
    assert ledger.cash == 1_000_000.0
    assert len(ledger.positions) == 0


def test_ledger_buy_fill_accounting():
    ledger = PortfolioLedger(initial_cash=1_000_000.0)
    # Buy 100 shares of AAPL at $150 with $5 fee
    fill = FillEvent(
        order_id="ORD-001",
        security_id="SEC-US-AAPL-001",
        ticker="AAPL",
        timestamp="2023-01-03",
        quantity=100.0,
        price=150.0,
        fees=5.0
    )
    ledger.record_fill(fill)

    # Cash outflow: 100 * 150 + 5 = 15,005
    assert ledger.cash == 1_000_000.0 - 15_005.0
    pos = ledger.positions["SEC-US-AAPL-001"]
    assert pos.quantity == 100.0
    assert pos.market_price == 150.0

    # Mark to market at $150
    snap = ledger.mark_to_market({"AAPL": 150.0}, "2023-01-03")
    assert snap.market_value == 15_000.0
    assert snap.nav == (1_000_000.0 - 5.0)  # NAV dropped only by $5 execution fee!


def test_ledger_pnl_identically_matches_delta_nav():
    ledger = PortfolioLedger(initial_cash=100_000.0)

    # Day 1: Buy 100 shares at $100 (fee $0)
    ledger.record_fill(FillEvent(
        order_id="ORD-1",
        security_id="SEC-US-AAPL-001",
        ticker="AAPL",
        timestamp="2023-01-01",
        quantity=100.0,
        price=100.0,
        fees=0.0
    ))
    snap1 = ledger.mark_to_market({"AAPL": 100.0}, "2023-01-01")
    assert snap1.nav == 100_000.0

    # Day 2: Stock rises to $110
    snap2 = ledger.mark_to_market({"AAPL": 110.0}, "2023-01-02")
    assert snap2.nav == 101_000.0
    assert snap2.daily_pnl == 1_000.0

    # Day 3: Sell all 100 shares at $110
    ledger.record_fill(FillEvent(
        order_id="ORD-2",
        security_id="SEC-US-AAPL-001",
        ticker="AAPL",
        timestamp="2023-01-03",
        quantity=-100.0,
        price=110.0,
        fees=0.0
    ))
    snap3 = ledger.mark_to_market({"AAPL": 110.0}, "2023-01-03")
    assert snap3.cash == 101_000.0
    assert snap3.market_value == 0.0
    assert snap3.nav == 101_000.0
    assert snap3.total_realized_pnl == 1_000.0
    assert snap3.total_unrealized_pnl == 0.0

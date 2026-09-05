"""
Authoritative Event-Driven Portfolio Ledger.
Implements double-entry quantitative portfolio accounting where:
Fills -> Positions & Cash -> NAV & Return.
Guarantees that Trade P&L identically matches Portfolio P&L (Trade P&L == delta NAV).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class FillEvent:
    order_id: str
    security_id: str
    ticker: str
    timestamp: str  # ISO-8601 or YYYY-MM-DD
    quantity: float  # > 0 for BUY, < 0 for SELL
    price: float     # Fill execution price
    fees: float      # Commissions + exchange fees in base currency
    currency: str = "USD"
    venue: str = "SIMULATED_EXCHANGE"


@dataclass
class Position:
    security_id: str
    ticker: str
    quantity: float = 0.0
    cost_basis: float = 0.0
    market_price: float = 0.0
    realized_pnl: float = 0.0

    @property
    def market_value(self) -> float:
        return self.quantity * self.market_price

    @property
    def unrealized_pnl(self) -> float:
        if abs(self.quantity) < 1e-8:
            return 0.0
        return self.market_value - (self.quantity * self.cost_basis)


@dataclass
class PortfolioSnapshot:
    timestamp: str
    cash: float
    market_value: float
    nav: float
    daily_pnl: float
    total_realized_pnl: float
    total_unrealized_pnl: float
    positions_count: int
    gross_exposure: float
    net_exposure: float


class PortfolioLedger:
    """
    Authoritative double-entry portfolio ledger.
    Every fill modifies Cash and Position simultaneously, eliminating reconciliation drift.
    """

    def __init__(self, initial_cash: float = 1_000_000.0, base_currency: str = "USD"):
        self.initial_cash = initial_cash
        self.cash = initial_cash
        self.base_currency = base_currency
        self.positions: Dict[str, Position] = {}  # security_id -> Position
        self.fills_history: List[FillEvent] = []
        self.history: List[PortfolioSnapshot] = []
        self._prev_nav = initial_cash

    def record_fill(self, fill: FillEvent) -> None:
        """Process a trade fill event using strict average cost accounting."""
        self.fills_history.append(fill)

        # 1. Cash Accounting: outflow for BUY, inflow for SELL, minus fees
        trade_cash_flow = -(fill.quantity * fill.price) - fill.fees
        self.cash += trade_cash_flow

        # 2. Position Accounting
        sid = fill.security_id
        if sid not in self.positions:
            self.positions[sid] = Position(
                security_id=sid,
                ticker=fill.ticker,
                quantity=0.0,
                cost_basis=0.0,
                market_price=fill.price
            )

        pos = self.positions[sid]
        old_qty = pos.quantity
        new_qty = old_qty + fill.quantity

        if abs(new_qty) < 1e-8:
            # Position closed
            realized = (fill.price - pos.cost_basis) * old_qty if old_qty > 0 else (pos.cost_basis - fill.price) * abs(old_qty)
            pos.realized_pnl += (realized - fill.fees)
            pos.quantity = 0.0
            pos.cost_basis = 0.0
            pos.market_price = fill.price
        elif (old_qty >= 0 and fill.quantity > 0) or (old_qty <= 0 and fill.quantity < 0):
            # Increasing position: update weighted average cost basis
            total_cost = (pos.cost_basis * abs(old_qty)) + (fill.price * abs(fill.quantity)) + fill.fees
            pos.cost_basis = total_cost / abs(new_qty)
            pos.quantity = new_qty
            pos.market_price = fill.price
        else:
            # Reducing position: realize P&L on the closed portion
            closed_qty = min(abs(old_qty), abs(fill.quantity))
            if old_qty > 0:
                realized = (fill.price - pos.cost_basis) * closed_qty
            else:
                realized = (pos.cost_basis - fill.price) * closed_qty
            pos.realized_pnl += (realized - fill.fees)

            if (old_qty > 0 and new_qty < 0) or (old_qty < 0 and new_qty > 0):
                # Flipped from long to short or short to long
                pos.quantity = new_qty
                pos.cost_basis = fill.price
            else:
                pos.quantity = new_qty
            pos.market_price = fill.price

    def mark_to_market(self, current_prices: Dict[str, float], timestamp: str) -> PortfolioSnapshot:
        """
        Mark all open positions to current market prices and record an authoritative NAV snapshot.
        """
        total_market_value = 0.0
        total_realized = 0.0
        total_unrealized = 0.0
        gross_exp = 0.0
        active_pos_count = 0

        for sid, pos in self.positions.items():
            if pos.ticker in current_prices:
                pos.market_price = current_prices[pos.ticker]
            elif sid in current_prices:
                pos.market_price = current_prices[sid]

            mv = pos.market_value
            total_market_value += mv
            total_realized += pos.realized_pnl
            total_unrealized += pos.unrealized_pnl
            gross_exp += abs(mv)
            if abs(pos.quantity) > 1e-8:
                active_pos_count += 1

        nav = self.cash + total_market_value
        daily_pnl = nav - self._prev_nav
        self._prev_nav = nav

        snapshot = PortfolioSnapshot(
            timestamp=timestamp,
            cash=round(self.cash, 2),
            market_value=round(total_market_value, 2),
            nav=round(nav, 2),
            daily_pnl=round(daily_pnl, 2),
            total_realized_pnl=round(total_realized, 2),
            total_unrealized_pnl=round(total_unrealized, 2),
            positions_count=active_pos_count,
            gross_exposure=round(gross_exp, 2),
            net_exposure=round(total_market_value, 2)
        )
        self.history.append(snapshot)
        return snapshot

    def get_equity_curve(self) -> pd.DataFrame:
        if not self.history:
            return pd.DataFrame()
        records = [
            {
                "date": s.timestamp,
                "cash": s.cash,
                "market_value": s.market_value,
                "nav": s.nav,
                "daily_pnl": s.daily_pnl,
                "positions": s.positions_count,
                "gross_exposure": s.gross_exposure
            }
            for s in self.history
        ]
        return pd.DataFrame(records)

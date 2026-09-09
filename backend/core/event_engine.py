"""
Canonical Event-Driven Execution Engine.
Processes event queues through:
Signal -> Target Position -> Risk Check -> Order -> OMS -> Execution Simulator -> Fill -> Ledger -> NAV.
"""
from __future__ import annotations

import enum
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Any

from .ledger.journal import LedgerJournal


class EventType(str, enum.Enum):
    MARKET = "MARKET"
    SIGNAL = "SIGNAL"
    ORDER = "ORDER"
    RISK = "RISK"
    ACK = "ACK"
    REJECT = "REJECT"
    CANCEL = "CANCEL"
    FILL = "FILL"
    CORPORATE_ACTION = "CORPORATE_ACTION"
    FUNDING = "FUNDING"
    BORROW = "BORROW"


@dataclass
class MarketEvent:
    timestamp: str
    security_id: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    event_type: EventType = EventType.MARKET


@dataclass
class SignalEvent:
    timestamp: str
    alpha_id: str
    security_id: str
    target_weight: float
    target_shares: float
    event_type: EventType = EventType.SIGNAL


@dataclass
class OrderEvent:
    order_id: str
    timestamp: str
    security_id: str
    quantity: float  # > 0 Buy, < 0 Sell
    order_type: str = "MKT"
    event_type: EventType = EventType.ORDER


@dataclass
class FillEvent:
    fill_id: str
    order_id: str
    timestamp: str
    security_id: str
    quantity: float
    fill_price: float
    commission: float
    venue: str = "CANONICAL_SIMULATOR"
    event_type: EventType = EventType.FILL


@dataclass
class RiskEvent:
    order_id: str
    passed: bool
    reason: str
    event_type: EventType = EventType.RISK


class EventDrivenExecutionPipeline:
    """
    Canonical Event-Driven Execution Engine.
    Executes trades through rigorous risk inspection and updates the double-entry ledger.
    """

    def __init__(self, initial_cash: float = 1_000_000.0):
        self.journal = LedgerJournal(initial_cash=initial_cash)
        self.event_queue: List[Any] = []
        self.processed_fills: List[FillEvent] = []
        self.latest_prices: Dict[str, float] = {}

    def on_market_event(self, event: MarketEvent) -> None:
        self.latest_prices[event.security_id] = event.close

    def on_signal_event(self, signal: SignalEvent) -> Optional[OrderEvent]:
        """Convert signal to order after preliminary sanity checks."""
        if abs(signal.target_shares) < 1e-4:
            return None
        order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
        return OrderEvent(
            order_id=order_id,
            timestamp=signal.timestamp,
            security_id=signal.security_id,
            quantity=signal.target_shares,
        )

    def on_order_risk_check(self, order: OrderEvent, max_order_val: float = 500_000.0) -> RiskEvent:
        """Pre-trade risk gate."""
        price = self.latest_prices.get(order.security_id, 100.0)
        order_val = abs(order.quantity) * price
        if order_val > max_order_val:
            return RiskEvent(order_id=order.order_id, passed=False, reason="Order exceeds single-ticket limit")
        return RiskEvent(order_id=order.order_id, passed=True, reason="Risk check passed")

    def execute_order(self, order: OrderEvent, slippage_bps: float = 5.0) -> FillEvent:
        """Execution simulator with linear spread/impact."""
        raw_price = self.latest_prices.get(order.security_id, 100.0)
        impact = (slippage_bps / 10000.0) * (1.0 if order.quantity > 0 else -1.0)
        fill_price = raw_price * (1.0 + impact)
        commission = min(max(abs(order.quantity) * 0.005, 1.0), abs(order.quantity) * fill_price * 0.001)

        fill = FillEvent(
            fill_id=f"FIL-{uuid.uuid4().hex[:8].upper()}",
            order_id=order.order_id,
            timestamp=order.timestamp,
            security_id=order.security_id,
            quantity=order.quantity,
            fill_price=fill_price,
            commission=commission,
        )

        # Record directly in authoritative double-entry journal
        self.journal.record_trade(
            transaction_id=fill.fill_id,
            security_id=fill.security_id,
            quantity=fill.quantity,
            price=fill.fill_price,
            fees=fill.commission,
            timestamp=fill.timestamp,
        )

        self.processed_fills.append(fill)
        return fill

    def get_current_nav(self) -> float:
        return self.journal.get_nav(self.latest_prices)

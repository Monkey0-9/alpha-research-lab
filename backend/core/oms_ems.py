"""
QuantAlpha Institutional Order Management System (OMS) & Execution Management System (EMS).
Implements:
1. Strict Order State Machine with transition verification.
2. Pre-Trade Risk Filter (Notional, ADV participation %, Fat-finger collars).
3. Algorithmic Slicing: TWAP, VWAP, and Almgren-Chriss Optimal Liquidation Trajectory.
4. Post-Trade Transaction Cost Analysis (TCA) with Implementation Shortfall (Perold 1988).
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import math
from typing import Dict, List, Optional, Tuple
import uuid


class OrderStatus(str, Enum):
    NEW = "NEW"
    PENDING_NEW = "PENDING_NEW"
    SUBMITTED = "SUBMITTED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    PENDING_CANCEL = "PENDING_CANCEL"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    TWAP = "TWAP"
    VWAP = "VWAP"
    ALMGREN_CHRISS = "ALMGREN_CHRISS"


class PreTradeRiskViolation(Exception):
    """Raised when an order breaches pre-trade risk thresholds."""
    pass


class InvalidOrderStateTransition(Exception):
    """Raised on illegal order state transitions."""
    pass


@dataclass
class Order:
    order_id: str
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    price: Optional[float] = None
    status: OrderStatus = OrderStatus.NEW
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    parent_order_id: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def leaves_quantity(self) -> float:
        return max(0.0, self.quantity - self.filled_quantity)


class OrderManagementSystem:
    """Institutional OMS tracking order lifecycles and enforcing strict transitions."""

    # Valid State Transitions
    VALID_TRANSITIONS: Dict[OrderStatus, List[OrderStatus]] = {
        OrderStatus.NEW: [OrderStatus.PENDING_NEW, OrderStatus.REJECTED],
        OrderStatus.PENDING_NEW: [OrderStatus.SUBMITTED, OrderStatus.REJECTED],
        OrderStatus.SUBMITTED: [
            OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED,
            OrderStatus.PENDING_CANCEL, OrderStatus.REJECTED, OrderStatus.EXPIRED
        ],
        OrderStatus.PARTIALLY_FILLED: [
            OrderStatus.PARTIALLY_FILLED, OrderStatus.FILLED,
            OrderStatus.PENDING_CANCEL, OrderStatus.EXPIRED
        ],
        OrderStatus.PENDING_CANCEL: [OrderStatus.CANCELLED, OrderStatus.FILLED, OrderStatus.PARTIALLY_FILLED],
        OrderStatus.FILLED: [],  # Terminal
        OrderStatus.CANCELLED: [],  # Terminal
        OrderStatus.REJECTED: [],  # Terminal
        OrderStatus.EXPIRED: [],  # Terminal
    }

    def __init__(self):
        self._orders: Dict[str, Order] = {}
        self._client_id_map: Dict[str, str] = {}  # cl_ord_id -> order_id

    def create_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        client_order_id: Optional[str] = None,
        parent_order_id: Optional[str] = None
    ) -> Order:
        if quantity <= 0:
            raise ValueError("Order quantity must be strictly positive.")
        if order_type == OrderType.LIMIT and (price is None or price <= 0):
            raise ValueError("Limit orders require a positive limit price.")

        cl_id = client_order_id or f"CL-{uuid.uuid4().hex[:12]}"
        if cl_id in self._client_id_map:
            raise ValueError(f"Duplicate client order ID: {cl_id}")

        ord_id = f"ORD-{uuid.uuid4().hex[:12]}"
        order = Order(
            order_id=ord_id,
            client_order_id=cl_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            parent_order_id=parent_order_id
        )
        self._orders[ord_id] = order
        self._client_id_map[cl_id] = ord_id
        return order

    def transition(self, order_id: str, new_status: OrderStatus, reason: Optional[str] = None) -> Order:
        order = self._orders.get(order_id)
        if not order:
            raise KeyError(f"Order {order_id} not found.")

        allowed = self.VALID_TRANSITIONS.get(order.status, [])
        if new_status not in allowed:
            raise InvalidOrderStateTransition(
                f"Cannot transition order {order_id} from {order.status} to {new_status}"
            )

        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        if reason:
            order.rejection_reason = reason
        return order

    def apply_fill(self, order_id: str, fill_qty: float, fill_price: float) -> Order:
        order = self._orders.get(order_id)
        if not order:
            raise KeyError(f"Order {order_id} not found.")
        if order.status not in (OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED, OrderStatus.PENDING_CANCEL):
            raise InvalidOrderStateTransition(f"Cannot apply fill to order in status {order.status}")
        if fill_qty <= 0:
            raise ValueError("Fill quantity must be positive.")
        if fill_qty > order.leaves_quantity:
            raise ValueError(f"Fill quantity {fill_qty} exceeds leaves quantity {order.leaves_quantity}")

        # Update VWAP fill price
        total_prev_val = order.filled_quantity * order.avg_fill_price
        new_total_qty = order.filled_quantity + fill_qty
        order.avg_fill_price = (total_prev_val + (fill_qty * fill_price)) / new_total_qty
        order.filled_quantity = new_total_qty
        order.updated_at = datetime.now(timezone.utc)

        if math.isclose(order.filled_quantity, order.quantity, rel_tol=1e-5):
            order.status = OrderStatus.FILLED
        else:
            order.status = OrderStatus.PARTIALLY_FILLED

        return order

    def get_order(self, order_id: str) -> Optional[Order]:
        return self._orders.get(order_id)


class PreTradeRiskFilter:
    """Enforces institutional pre-trade limits before orders reach exchange."""

    def __init__(
        self,
        max_order_notional: float = 1_000_000.0,
        max_adv_pct: float = 0.10,  # Max 10% of 30-day Average Daily Volume
        price_collar_pct: float = 0.05  # Max 5% deviation from reference price
    ):
        self.max_order_notional = max_order_notional
        self.max_adv_pct = max_adv_pct
        self.price_collar_pct = price_collar_pct

    def validate(self, order: Order, reference_price: float, adv: float) -> None:
        effective_price = order.price if order.price else reference_price
        notional = order.quantity * effective_price

        # 1. Notional limit
        if notional > self.max_order_notional:
            raise PreTradeRiskViolation(
                f"Order notional ${notional:,.2f} exceeds max allowed ${self.max_order_notional:,.2f}"
            )

        # 2. ADV participation limit
        if adv > 0 and (order.quantity / adv) > self.max_adv_pct:
            pct_part = order.quantity / adv
            raise PreTradeRiskViolation(
                f"Order quantity {order.quantity} represents {pct_part:.1%} of ADV, exceeding {self.max_adv_pct:.1%}"
            )

        # 3. Fat-finger price collar for limit orders
        if order.order_type == OrderType.LIMIT and order.price is not None:
            pct_dev = abs(order.price - reference_price) / reference_price
            if pct_dev > self.price_collar_pct:
                raise PreTradeRiskViolation(
                    f"Limit price ${order.price:.2f} deviates {pct_dev:.1%} from reference ${reference_price:.2f}, "
                    f"exceeding collar threshold of {self.price_collar_pct:.1%}"
                )


class ExecutionManagementSystem:
    """EMS slicing strategies: TWAP, VWAP, and Almgren-Chriss Optimal Liquidation."""

    @staticmethod
    def slice_twap(parent_order: Order, num_slices: int) -> List[float]:
        """Equal-volume time slicing."""
        if num_slices <= 0:
            raise ValueError("num_slices must be >= 1")
        slice_size = parent_order.quantity / num_slices
        return [slice_size] * num_slices

    @staticmethod
    def slice_vwap(parent_order: Order, volume_profile: List[float]) -> List[float]:
        """Volume curve-weighted slicing."""
        total_weight = sum(volume_profile)
        if total_weight <= 0:
            raise ValueError("Volume profile weights must sum to > 0")
        return [(w / total_weight) * parent_order.quantity for w in volume_profile]

    @staticmethod
    def slice_almgren_chriss(
        total_quantity: float,
        num_intervals: int,
        daily_volatility: float,
        daily_volume: float,
        risk_aversion: float = 1e-5,
        temp_impact_eta: float = 0.1,
        perm_impact_gamma: float = 0.05
    ) -> List[float]:
        """
        Closed-form Almgren-Chriss (2000) optimal execution trajectory.
        Minimizes: E[Cost] + lambda * Var[Cost].
        """
        if num_intervals <= 0:
            raise ValueError("num_intervals must be >= 1")
        if total_quantity <= 0:
            return []

        # Half-life / decay parameter kappa
        # kappa_tilde^2 approx lambda * sigma^2 / eta
        variance = daily_volatility ** 2
        kappa_sq = (risk_aversion * variance) / max(temp_impact_eta, 1e-8)
        kappa = math.sqrt(max(kappa_sq, 1e-6))

        tau = 1.0  # Normalized unit interval
        T = num_intervals * tau

        # Trajectory x_j: remaining shares at interval j
        # x_j = sinh(kappa * (T - t_j)) / sinh(kappa * T) * X
        denom = math.sinh(min(kappa * T, 50.0))  # Avoid float overflow
        remaining = []
        for j in range(num_intervals + 1):
            t_j = j * tau
            numer = math.sinh(min(kappa * (T - t_j), 50.0))
            x_j = (numer / denom) * total_quantity if denom > 0 else 0.0
            remaining.append(x_j)

        # Slice trades n_j = x_{j-1} - x_j
        trades = []
        for j in range(1, num_intervals + 1):
            trades.append(max(0.0, remaining[j - 1] - remaining[j]))

        # Normalize to exact total quantity to prevent rounding leakage
        curr_sum = sum(trades)
        if curr_sum > 0:
            trades = [(t / curr_sum) * total_quantity for t in trades]

        return trades


class TransactionCostAnalysis:
    """Institutional TCA: Implementation Shortfall decomposition (Perold 1988)."""

    @dataclass
    class TCAMetrics:
        decision_price: float
        arrival_price: float
        execution_vwap: float
        delay_cost_bps: float
        trading_cost_bps: float
        total_is_bps: float

    @classmethod
    def compute(
        cls,
        side: OrderSide,
        decision_price: float,
        arrival_price: float,
        fills: List[Tuple[float, float]]  # List of (qty, price)
    ) -> TCAMetrics:
        if not fills:
            raise ValueError("Cannot compute TCA without fills.")
        if decision_price <= 0 or arrival_price <= 0:
            raise ValueError("Prices must be positive.")

        total_qty = sum(q for q, _ in fills)
        exec_vwap = sum(q * p for q, p in fills) / total_qty

        # Direction multiplier: +1 for BUY, -1 for SELL
        dir_mult = 1.0 if side == OrderSide.BUY else -1.0

        # Delay cost: (Arrival - Decision) * dir / Decision * 10,000 bps
        delay_cost_bps = ((arrival_price - decision_price) * dir_mult / decision_price) * 10_000.0

        # Trading cost / Slippage: (Exec - Arrival) * dir / Decision * 10,000 bps
        trading_cost_bps = ((exec_vwap - arrival_price) * dir_mult / decision_price) * 10_000.0

        total_is_bps = delay_cost_bps + trading_cost_bps

        return cls.TCAMetrics(
            decision_price=decision_price,
            arrival_price=arrival_price,
            execution_vwap=exec_vwap,
            delay_cost_bps=round(delay_cost_bps, 2),
            trading_cost_bps=round(trading_cost_bps, 2),
            total_is_bps=round(total_is_bps, 2)
        )

"""
QuantAlpha Deterministic Microstructure Exchange Simulator.
Implements:
1. Continuous Price-Time Priority Limit Order Book (LOB).
2. Multi-level depth matching with partial fills and queue degradation.
3. FIX 4.2 Application Message Processing:
   - 35=D (NewOrderSingle) -> Generates 35=8 (ExecutionReport)
   - 35=F (OrderCancelRequest) -> Generates 35=8 (Cancelled ExecutionReport)
4. Deterministic fills with zero synthetic random artifacts.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Dict, List, Optional, Tuple
from backend.core.fix_engine import FixMessage, FixMsgType


@dataclass
class BookOrder:
    order_id: str
    cl_ord_id: str
    side: str  # "1" = BUY, "2" = SELL
    price: float
    quantity: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_empty(self) -> bool:
        return self.quantity <= 0.0


class LimitOrderBook:
    """Continuous Price-Time Priority Double Auction Book."""

    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: List[BookOrder] = []  # Sorted: highest price first, earliest first
        self.asks: List[BookOrder] = []  # Sorted: lowest price first, earliest first

    def insert_limit(
        self,
        order_id: str,
        cl_ord_id: str,
        side: str,
        price: float,
        quantity: float
    ) -> Tuple[List[Tuple[float, float]], float]:
        """
        Attempt to cross book. Residual quantity rests on the book.
        Returns: (fills [(qty, price)], remaining_qty)
        """
        fills: List[Tuple[float, float]] = []
        rem_qty = quantity

        if side == "1":  # BUY order crosses against ASKs <= price
            self.asks.sort(key=lambda x: (x.price, x.timestamp))
            for ask in list(self.asks):
                if ask.price <= price and rem_qty > 0:
                    fill_amt = min(rem_qty, ask.quantity)
                    fills.append((fill_amt, ask.price))
                    rem_qty -= fill_amt
                    ask.quantity -= fill_amt
                    if ask.is_empty:
                        self.asks.remove(ask)
                else:
                    break

            if rem_qty > 0:
                self.bids.append(BookOrder(order_id, cl_ord_id, side, price, rem_qty))
                self.bids.sort(key=lambda x: (-x.price, x.timestamp))

        elif side == "2":  # SELL order crosses against BIDs >= price
            self.bids.sort(key=lambda x: (-x.price, x.timestamp))
            for bid in list(self.bids):
                if bid.price >= price and rem_qty > 0:
                    fill_amt = min(rem_qty, bid.quantity)
                    fills.append((fill_amt, bid.price))
                    rem_qty -= fill_amt
                    bid.quantity -= fill_amt
                    if bid.is_empty:
                        self.bids.remove(bid)
                else:
                    break

            if rem_qty > 0:
                self.asks.append(BookOrder(order_id, cl_ord_id, side, price, rem_qty))
                self.asks.sort(key=lambda x: (x.price, x.timestamp))

        return fills, rem_qty

    def execute_market(self, side: str, quantity: float) -> Tuple[List[Tuple[float, float]], float]:
        """Walk depth of book for market execution."""
        fills: List[Tuple[float, float]] = []
        rem_qty = quantity

        if side == "1":  # Buy consumes Asks
            self.asks.sort(key=lambda x: (x.price, x.timestamp))
            for ask in list(self.asks):
                if rem_qty <= 0:
                    break
                fill_amt = min(rem_qty, ask.quantity)
                fills.append((fill_amt, ask.price))
                rem_qty -= fill_amt
                ask.quantity -= fill_amt
                if ask.is_empty:
                    self.asks.remove(ask)

        elif side == "2":  # Sell consumes Bids
            self.bids.sort(key=lambda x: (-x.price, x.timestamp))
            for bid in list(self.bids):
                if rem_qty <= 0:
                    break
                fill_amt = min(rem_qty, bid.quantity)
                fills.append((fill_amt, bid.price))
                rem_qty -= fill_amt
                bid.quantity -= fill_amt
                if bid.is_empty:
                    self.bids.remove(bid)

        return fills, rem_qty

    def cancel(self, cl_ord_id: str) -> Optional[BookOrder]:
        for b in list(self.bids):
            if b.cl_ord_id == cl_ord_id:
                self.bids.remove(b)
                return b
        for a in list(self.asks):
            if a.cl_ord_id == cl_ord_id:
                self.asks.remove(a)
                return a
        return None

    def get_best_bid(self) -> Optional[float]:
        return self.bids[0].price if self.bids else None

    def get_best_ask(self) -> Optional[float]:
        return self.asks[0].price if self.asks else None


class ExchangeSimulator:
    """FIX-compatible deterministic exchange matching engine."""

    def __init__(self, exchange_id: str = "EXCHANGE_SIM"):
        self.exchange_id = exchange_id
        self.books: Dict[str, LimitOrderBook] = {}
        self.out_seq_num = 1
        self.orders: Dict[str, Dict] = {}  # cl_ord_id -> state

    def seed_liquidity(
        self,
        symbol: str,
        bid_depth: List[Tuple[float, float]],
        ask_depth: List[Tuple[float, float]]
    ) -> None:
        """Seed initial depth of book: (price, qty) levels."""
        book = self.books.setdefault(symbol, LimitOrderBook(symbol))
        for p, q in bid_depth:
            book.insert_limit(f"SEED-B-{p}", f"CL-SEED-B-{p}", "1", p, q)
        for p, q in ask_depth:
            book.insert_limit(f"SEED-A-{p}", f"CL-SEED-A-{p}", "2", p, q)

    def process_new_order_single(self, fix_msg: FixMessage) -> List[FixMessage]:
        """Process 35=D message and return 35=8 Execution Reports."""
        cl_ord_id = fix_msg.get(11)
        symbol = fix_msg.get(55)
        side = fix_msg.get(54)
        qty = float(fix_msg.get(38, "0"))
        ord_type = fix_msg.get(40, "2")
        price = float(fix_msg.get(44, "0")) if fix_msg.get(44) else None

        book = self.books.setdefault(symbol, LimitOrderBook(symbol))
        order_id = f"EX-{uuid.uuid4().hex[:10]}"

        reports: List[FixMessage] = []

        if ord_type == "1":  # Market Order
            fills, unfilled = book.execute_market(side, qty)
        else:  # Limit Order
            fills, unfilled = book.insert_limit(order_id, cl_ord_id, side, price or 0.0, qty)

        cum_qty = sum(f[0] for f in fills)
        leaves_qty = unfilled

        # Record state
        self.orders[cl_ord_id] = {
            "order_id": order_id,
            "symbol": symbol,
            "side": side,
            "cum_qty": cum_qty,
            "leaves_qty": leaves_qty,
            "total_qty": qty
        }

        # Generate 35=8 Execution Report
        rep = FixMessage(
            msg_type=FixMsgType.EXECUTION_REPORT,
            sender_comp_id=self.exchange_id,
            target_comp_id=fix_msg.sender_comp_id,
            msg_seq_num=self.out_seq_num
        )
        self.out_seq_num += 1

        rep.set(37, order_id)
        rep.set(11, cl_ord_id)
        rep.set(55, symbol)
        rep.set(54, side)
        rep.set(14, str(cum_qty))
        rep.set(151, str(leaves_qty))

        if cum_qty == 0:
            rep.set(39, "0")  # New
            rep.set(150, "0")
            rep.set(6, "0.0")
        elif leaves_qty == 0:
            avg_px = sum(f[0] * f[1] for f in fills) / cum_qty
            rep.set(39, "2")  # Filled
            rep.set(150, "2")
            rep.set(6, f"{avg_px:.4f}")
        else:
            avg_px = sum(f[0] * f[1] for f in fills) / cum_qty
            rep.set(39, "1")  # PartiallyFilled
            rep.set(150, "1")
            rep.set(6, f"{avg_px:.4f}")

        reports.append(rep)
        return reports

    def process_order_cancel_request(self, fix_msg: FixMessage) -> FixMessage:
        """Process 35=F message and return 35=8 Cancelled report."""
        orig_cl_ord_id = fix_msg.get(41) or fix_msg.get(11)
        symbol = fix_msg.get(55)

        book = self.books.get(symbol)
        if book:
            book.cancel(orig_cl_ord_id)

        rep = FixMessage(
            msg_type=FixMsgType.EXECUTION_REPORT,
            sender_comp_id=self.exchange_id,
            target_comp_id=fix_msg.sender_comp_id,
            msg_seq_num=self.out_seq_num
        )
        self.out_seq_num += 1

        order_info = self.orders.get(orig_cl_ord_id, {})
        rep.set(37, order_info.get("order_id", "UNKNOWN"))
        rep.set(11, fix_msg.get(11))
        rep.set(41, orig_cl_ord_id)
        rep.set(55, symbol)
        rep.set(39, "4")  # Cancelled
        rep.set(150, "4")
        rep.set(151, "0.0")
        rep.set(14, str(order_info.get("cum_qty", 0.0)))
        return rep

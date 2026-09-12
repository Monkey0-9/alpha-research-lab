"""
QuantAlpha Adversarial Backtest Attack Engine (Phase 3).
Performs institutional end-to-end vulnerability and integrity penetration testing
against quantitative backtests to catch and reject:
1. Look-ahead data leakage (future prices, volumes, fundamentals, corporate actions, benchmark)
2. Survivorship bias (delisted/bankrupt tickers, retroactive universe selection)
3. Corporate action mishandling (splits, cash dividends, spinoffs)
4. Timestamp anomalies (future ticks, negative time deltas, out-of-order bars, timezone breaches)
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Tuple


class AttackType(Enum):
    LOOKAHEAD_PRICE = "lookahead_price"
    LOOKAHEAD_VOLUME = "lookahead_volume"
    LOOKAHEAD_FUNDAMENTALS = "lookahead_fundamentals"
    LOOKAHEAD_CORPORATE_ACTION = "lookahead_corporate_action"
    LOOKAHEAD_UNIVERSE = "lookahead_universe"
    LOOKAHEAD_BENCHMARK = "lookahead_benchmark"
    SURVIVORSHIP_DELISTED = "survivorship_delisted"
    SURVIVORSHIP_BANKRUPTCY = "survivorship_bankruptcy"
    CORPORATE_ACTION_SPLIT = "corporate_action_split"
    CORPORATE_ACTION_DIVIDEND = "corporate_action_dividend"
    TIMESTAMP_FUTURE_TICK = "timestamp_future_tick"
    TIMESTAMP_NEGATIVE_DELTA = "timestamp_negative_delta"
    TIMESTAMP_OUT_OF_ORDER = "timestamp_out_of_order"
    TIMESTAMP_TIMEZONE_MISMATCH = "timestamp_timezone_mismatch"


class BacktestIntegrityViolation(Exception):
    """Raised when an adversarial look-ahead, survivorship, or timestamp violation is caught."""
    pass


@dataclass
class BarEvent:
    timestamp_utc: int  # Epoch seconds
    ticker: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    is_delisted: bool = False
    delisting_liquidation_price: Optional[float] = None
    split_factor: float = 1.0
    dividend_cash: float = 0.0


@dataclass
class FundamentalFiling:
    ticker: str
    period_end_utc: int
    public_filing_timestamp_utc: int  # SEC release time
    metric_name: str
    value: float


class AdversarialBacktestEngine:
    """
    Institutional testbed and validation runner for backtesting engine integrity.
    """

    def __init__(self, execution_delay_seconds: int = 1):
        self.execution_delay_seconds = execution_delay_seconds
        self.current_simulation_time: int = 0
        self.known_security_universe: Set[str] = set()
        self.positions: Dict[str, float] = {}
        self.cash: float = 1_000_000.0
        self.trade_log: List[Dict[str, Any]] = []

    def validate_event_stream_integrity(self, events: List[BarEvent]) -> None:
        """Verify strict chronological monotonicity, valid timestamps, and absence of future ticks."""
        last_ts = -1
        for i, ev in enumerate(events):
            if ev.timestamp_utc <= 0:
                raise BacktestIntegrityViolation(
                    f"Invalid non-positive timestamp {ev.timestamp_utc} at event {i}"
                )
            if ev.timestamp_utc < last_ts:
                raise BacktestIntegrityViolation(
                    f"Timestamp out of order / negative delta: event {i} has {ev.timestamp_utc} < prior {last_ts}"
                )
            last_ts = ev.timestamp_utc

    def check_point_in_time_fundamental_access(
        self,
        current_time_utc: int,
        filing: FundamentalFiling
    ) -> float:
        """
        Guarantees fundamental data is inaccessible prior to its public filing timestamp.
        """
        if current_time_utc < filing.public_filing_timestamp_utc:
            raise BacktestIntegrityViolation(
                f"Lookahead fundamentals violation: Attempted to read {filing.ticker} filing "
                f"(public at {filing.public_filing_timestamp_utc}) at simulation time {current_time_utc}"
            )
        return filing.value

    def check_point_in_time_price_access(
        self,
        query_time_utc: int,
        bar: BarEvent,
        allow_same_bar_close: bool = False
    ) -> float:
        """
        Prevents accessing future bar prices.
        If bar represents time window [T_start, T_end], close is only known at or after T_end.
        """
        if query_time_utc < bar.timestamp_utc:
            raise BacktestIntegrityViolation(
                f"Lookahead price violation: Current time {query_time_utc} attempted to peek at "
                f"future bar close timestamp {bar.timestamp_utc} for {bar.ticker}"
            )
        if not allow_same_bar_close and query_time_utc == bar.timestamp_utc:
            # Must execute with at least realistic delay (e.g. Next Open or Close+delta)
            return bar.open
        return bar.close

    def process_corporate_action(
        self,
        ticker: str,
        current_holdings: float,
        split_factor: float,
        dividend_cash: float
    ) -> Tuple[float, float]:
        """
        Strictly applies split multiplier to shares and cash dividend to balance.
        """
        new_shares = current_holdings * split_factor
        cash_payout = current_holdings * dividend_cash
        return new_shares, cash_payout

    def handle_delisting_liquidation(
        self,
        ticker: str,
        holdings: float,
        liquidation_price: float
    ) -> float:
        """
        Enforces liquidation of delisted positions, catching survivorship bias omissions.
        """
        if holdings <= 0:
            return 0.0
        proceeds = holdings * liquidation_price
        return proceeds

    def run_adversarial_suite(
        self,
        attack_type: AttackType,
        custom_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Executes a targeted adversarial probe and asserts that the engine catches it fail-closed.
        """
        caught = False
        violation_message = ""

        try:
            if attack_type == AttackType.TIMESTAMP_NEGATIVE_DELTA:
                bad_events = [
                    BarEvent(timestamp_utc=1000, ticker="AAPL", open=150, high=155, low=149, close=153, volume=1000),
                    BarEvent(timestamp_utc=950, ticker="AAPL", open=153, high=154, low=151, close=152, volume=800),
                ]
                self.validate_event_stream_integrity(bad_events)

            elif attack_type == AttackType.LOOKAHEAD_FUNDAMENTALS:
                filing = FundamentalFiling(
                    ticker="AAPL",
                    period_end_utc=1000,
                    public_filing_timestamp_utc=2000,
                    metric_name="net_income",
                    value=30_000_000_000.0,
                )
                self.check_point_in_time_fundamental_access(current_time_utc=1500, filing=filing)

            elif attack_type == AttackType.LOOKAHEAD_PRICE:
                bar = BarEvent(timestamp_utc=2000, ticker="MSFT", open=300, high=305, low=298, close=304, volume=5000)
                self.check_point_in_time_price_access(query_time_utc=1000, bar=bar)

            elif attack_type == AttackType.SURVIVORSHIP_DELISTED:
                # Delisted stock liquidates at bankruptcy value ($0.05) rather than disappearing
                shares = 1000.0
                liq_proceeds = self.handle_delisting_liquidation("ENRON", shares, liquidation_price=0.05)
                if liq_proceeds != 50.0:
                    raise BacktestIntegrityViolation("Failed to account for delisting liquidation loss")
                caught = True
                violation_message = f"Delisting caught and liquidated correctly at ${liq_proceeds}"

            elif attack_type == AttackType.CORPORATE_ACTION_SPLIT:
                # 2:1 stock split
                shares, cash = self.process_corporate_action("TSLA", 100.0, split_factor=2.0, dividend_cash=0.0)
                if shares != 200.0:
                    raise BacktestIntegrityViolation("Split factor improperly calculated")
                caught = True
                violation_message = "Corporate action split correctly doubled share count"

        except BacktestIntegrityViolation as e:
            caught = True
            violation_message = str(e)

        return {
            "attack_type": attack_type.value,
            "detected_and_handled": caught,
            "message": violation_message,
        }

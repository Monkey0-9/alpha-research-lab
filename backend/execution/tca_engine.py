"""
QuantAlpha Execution Microstructure & Transaction Cost Analysis (TCA) Engine (Phase 12).
Simulates realistic algorithmic execution and computes post-trade transaction cost metrics:
- Market Order, TWAP, VWAP, Percentage-of-Volume (POV)
- Almgren-Chriss market impact modeling (permanent + temporary impact)
- Implementation Shortfall (IS) decomposition: Arrival Slippage + Spread Cost + Delay Cost
"""
from dataclasses import dataclass
from enum import Enum
import math
from typing import Any, Dict, List, Optional


class ExecutionAlgorithm(Enum):
    MARKET = "MARKET"
    TWAP = "TWAP"
    VWAP = "VWAP"
    POV = "POV"
    LIMIT = "LIMIT"


@dataclass
class TCAReport:
    order_id: str
    ticker: str
    target_shares: float
    filled_shares: float
    arrival_price: float
    average_fill_price: float
    benchmark_vwap: float
    implementation_shortfall_bps: float
    spread_cost_bps: float
    market_impact_bps: float
    delay_cost_bps: float
    total_cost_dollars: float


class TransactionCostAnalysisEngine:
    """
    Evaluates order execution performance against benchmark prices and models microstructure slippage.
    """

    def __init__(self, half_spread_bps: float = 2.5, almgren_gamma: float = 0.1, almgren_eta: float = 0.05):
        self.half_spread_bps = half_spread_bps
        self.almgren_gamma = almgren_gamma  # Permanent impact parameter
        self.almgren_eta = almgren_eta      # Temporary impact parameter

    def simulate_execution_and_tca(
        self,
        order_id: str,
        ticker: str,
        side: str,  # 'BUY' or 'SELL'
        shares: float,
        arrival_price: float,
        daily_volume: float,
        daily_volatility: float = 0.015,
        algo: ExecutionAlgorithm = ExecutionAlgorithm.TWAP,
        participation_rate: float = 0.05
    ) -> TCAReport:
        """
        Simulates algorithmic execution, calculates realistic market impact, and returns full TCA report.
        """
        if shares <= 0:
            raise ValueError("Shares must be positive")

        pct_volume = shares / daily_volume if daily_volume > 0 else 0.01

        # 1. Spread cost
        spread_bps = self.half_spread_bps

        # 2. Almgren-Chriss market impact:
        # Temporary impact = eta * sigma * sqrt(rate)
        # Permanent impact = gamma * sigma * (shares / DailyVolume)
        temp_impact_bps = self.almgren_eta * daily_volatility * math.sqrt(participation_rate) * 10000.0
        perm_impact_bps = self.almgren_gamma * daily_volatility * pct_volume * 10000.0
        total_impact_bps = temp_impact_bps + 0.5 * perm_impact_bps

        # Algorithm discount: TWAP/VWAP reduce impact compared to aggressive MARKET
        if algo == ExecutionAlgorithm.MARKET:
            total_impact_bps *= 2.0
            delay_bps = 0.0
        elif algo == ExecutionAlgorithm.LIMIT:
            total_impact_bps *= 0.4
            delay_bps = 1.0
        else:  # TWAP / VWAP / POV
            total_impact_bps *= 1.0
            delay_bps = 0.5

        total_slippage_bps = spread_bps + total_impact_bps + delay_bps

        sign = 1.0 if side.upper() == "BUY" else -1.0
        avg_fill_price = arrival_price * (1.0 + sign * (total_slippage_bps / 10000.0))
        benchmark_vwap = arrival_price * (1.0 + sign * 0.0002)

        # Total implementation shortfall
        is_bps = ((avg_fill_price - arrival_price) / arrival_price * 10000.0) if side.upper() == "BUY" else \
                 ((arrival_price - avg_fill_price) / arrival_price * 10000.0)

        total_cost_usd = abs(avg_fill_price - arrival_price) * shares

        return TCAReport(
            order_id=order_id,
            ticker=ticker,
            target_shares=shares,
            filled_shares=shares,
            arrival_price=round(arrival_price, 4),
            average_fill_price=round(avg_fill_price, 4),
            benchmark_vwap=round(benchmark_vwap, 4),
            implementation_shortfall_bps=round(is_bps, 2),
            spread_cost_bps=round(spread_bps, 2),
            market_impact_bps=round(total_impact_bps, 2),
            delay_cost_bps=round(delay_bps, 2),
            total_cost_dollars=round(total_cost_usd, 2),
        )

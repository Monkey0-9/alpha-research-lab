"""
Capacity Analysis & Market Impact Curve Engine.
Evaluates strategy performance degradation across increasing AUM tiers:
AUM -> Turnover -> ADV Participation -> Market Impact -> Net Sharpe.
Determines maximum sustainable capacity at target net Sharpe threshold.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Any
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class CapacityTierResult:
    aum: float
    turnover_annual: float
    participation_pct: float
    slippage_bps: float
    market_impact_bps: float
    total_drag_bps: float
    gross_return_pct: float
    net_return_pct: float
    gross_sharpe: float
    net_sharpe: float
    is_viable: bool


class CapacityModel:
    """
    Evaluates market impact curves and capacity limits under Almgren-Chriss square-root law.
    """

    def __init__(
        self,
        avg_daily_volume_dollars: float = 50_000_000.0,
        daily_volatility: float = 0.015,
        min_net_sharpe_hurdle: float = 1.0
    ):
        self.adv = avg_daily_volume_dollars
        self.vol = daily_volatility
        self.hurdle = min_net_sharpe_hurdle

    def evaluate_capacity(
        self,
        gross_annual_return: float,
        annual_volatility: float,
        annual_turnover: float,
        aum_tiers: List[float] = None
    ) -> Dict[str, Any]:
        """
        Evaluate net metrics across AUM tiers and calculate maximum sustainable capacity.
        """
        tiers = aum_tiers or [1_000_000.0, 5_000_000.0, 10_000_000.0, 25_000_000.0, 50_000_000.0, 100_000_000.0]
        results: List[CapacityTierResult] = []

        gross_sharpe = gross_annual_return / max(annual_volatility, 1e-4)
        max_viable_aum = 0.0

        for aum in tiers:
            # Daily traded volume = AUM * annual_turnover / 252
            daily_traded = (aum * annual_turnover) / 252.0
            participation = (daily_traded / max(self.adv, 1.0)) * 100.0

            # Almgren-Chriss impact model: Impact_bps = gamma * sigma * sqrt(Q / ADV) * 10000
            # Base half-spread slippage: 3.0 bps
            base_slippage_bps = 3.0
            impact_bps = 0.5 * self.vol * np.sqrt(daily_traded / max(self.adv, 1.0)) * 10_000.0
            total_drag_bps = base_slippage_bps + impact_bps

            # Total annual cost in return % = (annual_turnover * total_drag_bps) / 10000
            annual_cost_pct = (annual_turnover * total_drag_bps) / 10000.0
            net_return = gross_annual_return - annual_cost_pct
            net_sharpe = net_return / max(annual_volatility, 1e-4)

            is_viable = bool(net_sharpe >= self.hurdle)
            if is_viable:
                max_viable_aum = max(max_viable_aum, aum)

            results.append(CapacityTierResult(
                aum=aum,
                turnover_annual=round(annual_turnover, 2),
                participation_pct=round(participation, 3),
                slippage_bps=round(base_slippage_bps, 2),
                market_impact_bps=round(impact_bps, 2),
                total_drag_bps=round(total_drag_bps, 2),
                gross_return_pct=round(gross_annual_return * 100.0, 2),
                net_return_pct=round(net_return * 100.0, 2),
                gross_sharpe=round(gross_sharpe, 2),
                net_sharpe=round(net_sharpe, 2),
                is_viable=is_viable
            ))

        return {
            "max_sustainable_capacity_aum": max_viable_aum,
            "min_net_sharpe_hurdle": self.hurdle,
            "gross_sharpe": round(gross_sharpe, 2),
            "tiers": [
                {
                    "aum": r.aum,
                    "participation_pct": r.participation_pct,
                    "market_impact_bps": r.market_impact_bps,
                    "total_drag_bps": r.total_drag_bps,
                    "net_return_pct": r.net_return_pct,
                    "net_sharpe": r.net_sharpe,
                    "is_viable": r.is_viable
                }
                for r in results
            ]
        }


capacity_model = CapacityModel()

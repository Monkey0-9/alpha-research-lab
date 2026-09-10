"""
Independent Reference Oracle: Algorithmic Execution & TCA.
Implements:
1. Almgren-Chriss (2000) closed-form continuous optimal liquidation trajectory.
2. Perold (1988) Implementation Shortfall analytical decomposition.
Zero production imports permitted.
"""
import math
from typing import List, Tuple


class OracleExecution:
    """Independent reference implementation for trade scheduling and execution cost math."""

    @staticmethod
    def almgren_chriss_optimal_trajectory(
        total_shares: float,
        num_intervals: int,
        daily_vol: float,
        risk_aversion: float,
        temp_impact: float = 0.1
    ) -> List[float]:
        """
        Analytical solution to the Euler-Lagrange calculus of variations:
          x(t) = sinh(kappa * (T - t)) / sinh(kappa * T) * X_0
        Returns trade slices: n_j = x(t_{j-1}) - x(t_j).
        """
        if num_intervals <= 0:
            return []
        if total_shares <= 0:
            return [0.0] * num_intervals

        sigma_sq = daily_vol ** 2
        kappa = math.sqrt(max((risk_aversion * sigma_sq) / max(temp_impact, 1e-8), 1e-6))

        tau = 1.0
        T = num_intervals * tau

        denom = math.sinh(min(kappa * T, 50.0))
        rem = []
        for j in range(num_intervals + 1):
            t_j = j * tau
            numer = math.sinh(min(kappa * (T - t_j), 50.0))
            rem.append((numer / denom) * total_shares if denom > 0 else 0.0)

        trades = [max(0.0, rem[j - 1] - rem[j]) for j in range(1, num_intervals + 1)]
        total = sum(trades)
        if total > 0:
            trades = [(t / total) * total_shares for t in trades]
        return trades

    @staticmethod
    def implementation_shortfall_breakdown(
        is_buy: bool,
        p_decision: float,
        p_arrival: float,
        fills: List[Tuple[float, float]]  # (qty, price)
    ) -> Tuple[float, float, float, float]:
        """
        Perold (1988) reference decomposition:
        Returns: (exec_vwap, delay_cost_bps, trading_cost_bps, total_is_bps)
        """
        if not fills or p_decision <= 0:
            return 0.0, 0.0, 0.0, 0.0

        total_qty = sum(q for q, _ in fills)
        exec_vwap = sum(q * p for q, p in fills) / total_qty

        direction = 1.0 if is_buy else -1.0
        delay_cost_bps = ((p_arrival - p_decision) * direction / p_decision) * 10_000.0
        trading_cost_bps = ((exec_vwap - p_arrival) * direction / p_decision) * 10_000.0
        total_is_bps = delay_cost_bps + trading_cost_bps

        return (
            round(exec_vwap, 4),
            round(delay_cost_bps, 2),
            round(trading_cost_bps, 2),
            round(total_is_bps, 2)
        )

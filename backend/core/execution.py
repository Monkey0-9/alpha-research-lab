"""
Optimal Execution & Market Impact Engine.

Implements:
1. Almgren-Chriss Optimal Liquidation Trajectory (accelerated via C++ native engine).
2. Institutional Slippage & Spread Modeling.
3. TWAP & VWAP Algorithm Simulator with dynamic participation constraints.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List
import numpy as np

from native.native_bridge import accelerator

logger = logging.getLogger(__name__)


def almgren_chriss_impact(
    order_size: float,
    adv: float,
    volatility: float = 0.02,
    urgency: float = 1.0,
    intervals: int = 10
) -> Dict[str, Any]:
    """
    Optimal execution trajectory minimizing expected cost + risk penalty.
    """
    risk_aversion = 1e-6 * urgency
    participation = order_size / max(1.0, adv)
    temp_impact = 2.5e-6 * (1.0 + participation * 2.0)
    perm_impact = 2.5e-7

    # Dispatch to high-speed C++ engine
    res = accelerator.fast_almgren_chriss(
        total_shares=order_size,
        intervals=intervals,
        risk_aversion=risk_aversion,
        volatility=volatility,
        temp_impact=temp_impact,
        perm_impact=perm_impact
    )
    return res


def estimate_slippage(
    spread_bps: float,
    volatility: float,
    order_size: float,
    adv: float
) -> float:
    """
    Estimate execution slippage in basis points (bps).
    Half-spread + square-root law of market impact:
    Impact_bps = spread_bps / 2 + Y * sigma * sqrt(OrderSize / ADV) * 10000
    """
    half_spread = spread_bps * 0.5
    participation = min(1.0, order_size / max(1.0, adv))
    sqrt_impact = 0.6 * volatility * np.sqrt(participation) * 10000.0
    return float(round(half_spread + sqrt_impact, 2))


def simulate_twap_vwap(
    order_size: float,
    benchmark_price: float = 150.0,
    adv: float = 5_000_000.0,
    intervals: int = 10,
    algo: str = "TWAP"
) -> Dict[str, Any]:
    """
    Simulate execution fills across intervals.
    """
    # Simulate realistic volume profile (U-shaped intraday profile)
    u_curve = np.array([1.5, 1.2, 0.9, 0.7, 0.6, 0.6, 0.7, 0.9, 1.2, 1.7])
    u_curve = u_curve / np.sum(u_curve)
    interval_adv = adv / intervals

    prices = []
    volumes = []
    curr_price = benchmark_price

    for w in u_curve:
        curr_price += np.random.normal(0, 0.002) * curr_price
        prices.append(curr_price)
        volumes.append(interval_adv * w)

    prices_arr = np.array(prices)
    volumes_arr = np.array(volumes)

    if algo.upper() == "VWAP":
        weights = volumes_arr / np.sum(volumes_arr)
    else:
        weights = np.ones(intervals) / intervals

    exec_shares = order_size * weights
    slippage_bps = estimate_slippage(2.5, 0.018, order_size, adv)
    avg_price = float(np.sum(prices_arr * exec_shares) / order_size) * (1.0 + slippage_bps / 10000.0)

    fills = []
    for i in range(intervals):
        fills.append({
            "interval": i + 1,
            "shares": round(float(exec_shares[i]), 1),
            "price": round(float(prices_arr[i]), 2),
            "volume_participation": round(float(exec_shares[i] / volumes_arr[i] * 100), 2)
        })

    return {
        "algo": algo,
        "total_shares": order_size,
        "benchmark_price": benchmark_price,
        "average_execution_price": round(avg_price, 2),
        "slippage_bps": slippage_bps,
        "fills": fills
    }

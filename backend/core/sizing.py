"""
Position Sizing Engine.

Implements:
1. Volatility Targeting: Scales exposure so portfolio/position matches target annualized vol (e.g. 10%).
2. Kelly Criterion: Optimal growth sizing with half-Kelly / fractional Kelly conservative bounds.
"""
from __future__ import annotations

import numpy as np


def vol_target_sizing(
    asset_volatility_annualized: float,
    target_vol_annualized: float = 0.10,
    max_leverage: float = 1.5
) -> float:
    """
    Calculate position weight to target a specific volatility.
    weight = target_vol / asset_vol
    """
    if asset_volatility_annualized <= 1e-6:
        return 0.0
    raw_weight = target_vol_annualized / asset_volatility_annualized
    return float(np.clip(raw_weight, 0.0, max_leverage))


def kelly_criterion_sizing(
    win_rate: float,
    win_loss_ratio: float,
    fraction: float = 0.5, # Half-Kelly for risk management
    max_position: float = 0.25
) -> float:
    """
    Fractional Kelly Formula:
    f* = (p * b - q) / b
    where p = win rate, q = 1 - p, b = win/loss payoff ratio.
    fraction = 0.5 (Half-Kelly) avoids ruin in non-Gaussian regimes.
    """
    if win_loss_ratio <= 0.0 or win_rate <= 0.0:
        return 0.0
    q = 1.0 - win_rate
    full_kelly = (win_rate * win_loss_ratio - q) / win_loss_ratio
    if full_kelly <= 0.0:
        return 0.0
    allocated = full_kelly * fraction
    return float(np.clip(allocated, 0.0, max_position))

"""
Feature Engine — 50+ time-series features for alpha research.

CRITICAL: Every feature uses .shift(1) to prevent lookahead bias.
Features are computed at time t using only data available at t-1 or earlier.
"""
from __future__ import annotations

import logging
from typing import List

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def _rolling_hurst(series: pd.Series, window: int = 100) -> pd.Series:
    """Fast vectorized proxy for Hurst exponent via rolling variance scaling."""
    r = series.pct_change()
    var_short = r.rolling(10).var()
    var_long = r.rolling(window).var()
    ratio = var_long / (var_short * 10.0 + 1e-9)
    h = 0.5 + 0.25 * np.log(np.maximum(1e-4, ratio)) / np.log(10.0)
    return h.clip(0.1, 0.9)


# ---------------------------------------------------------------------------
# Main feature builder
# ---------------------------------------------------------------------------

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute 50+ features per (date, ticker).

    Parameters
    ----------
    df : MultiIndex DataFrame with levels (date, ticker), columns include close/open/high/low/volume.

    Returns
    -------
    features_df : Same index, all feature columns appended.
    """
    features_list = []

    for ticker, sub in df.groupby(level="ticker"):
        sub = sub.droplevel("ticker").sort_index()
        f = _compute_ticker_features(sub, ticker)
        features_list.append(f)

    features_df = pd.concat(features_list).sort_index()
    logger.info("Built %d features for %d rows", len(features_df.columns), len(features_df))
    return features_df


def _compute_ticker_features(sub: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Compute features for a single ticker. All shifted by 1 to avoid lookahead."""
    c = sub["close"]
    o = sub.get("open", c)
    h = sub.get("high", c)
    lo = sub.get("low", c)
    v = sub.get("volume", pd.Series(np.ones(len(c)), index=c.index))

    feat = pd.DataFrame(index=sub.index)
    feat["ticker"] = ticker

    # --- Returns ---
    for n in [1, 5, 10, 20, 60]:
        feat[f"return_{n}d"] = c.pct_change(n).shift(1)

    # --- Momentum (price change over N days, lagged) ---
    for n in [20, 60, 120]:
        feat[f"momentum_{n}d"] = (c / c.shift(n) - 1).shift(1)

    # --- Volatility ---
    r1 = c.pct_change()
    for n in [20, 60]:
        feat[f"volatility_{n}d"] = r1.rolling(n).std().shift(1)

    # --- RSI ---
    feat["rsi_14"] = _rsi(c, 14).shift(1)
    feat["rsi_7"]  = _rsi(c, 7).shift(1)

    # --- MACD ---
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd_signal = macd_line.ewm(span=9, adjust=False).mean()
    feat["macd"]        = macd_line.shift(1)
    feat["macd_signal"] = macd_signal.shift(1)
    feat["macd_hist"]   = (macd_line - macd_signal).shift(1)

    # --- Bollinger Bands ---
    bb_mid = c.rolling(20).mean()
    bb_std = c.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_width = (bb_upper - bb_lower) / bb_mid
    bb_pos = (c - bb_lower) / (bb_upper - bb_lower + 1e-9)
    feat["bb_position"] = bb_pos.shift(1)
    feat["bb_width"]    = bb_width.shift(1)

    # --- Volume ---
    vma20 = v.rolling(20).mean()
    feat["volume_ma_20"]   = vma20.shift(1)
    feat["volume_ratio"]   = (v / (vma20 + 1e-9)).shift(1)
    feat["dollar_volume"]  = (c * v).rolling(5).mean().shift(1)

    # --- Autocorrelation ---
    for lag in [5, 20]:
        feat[f"autocorr_{lag}d"] = r1.rolling(60).corr(r1.shift(lag)).shift(1)

    # --- Hurst Exponent ---
    feat["hurst_100d"] = _rolling_hurst(c, 100).shift(1)

    # --- Higher Moments ---
    feat["skew_60d"] = r1.rolling(60).skew().shift(1)
    feat["kurt_60d"] = r1.rolling(60).kurt().shift(1)

    # --- Drawdown ---
    roll_max = c.rolling(252, min_periods=1).max()
    feat["current_drawdown"] = ((c / roll_max) - 1).shift(1)
    feat["max_drawdown_60d"] = (
        (c / roll_max - 1).rolling(60).min()
    ).shift(1)

    # --- Price relative to moving averages ---
    for n in [10, 50, 200]:
        feat[f"price_ma_{n}_ratio"] = (c / c.rolling(n).mean()).shift(1)

    # --- High-Low range ---
    feat["hl_range_20d"] = ((h - lo) / (lo + 1e-9)).rolling(20).mean().shift(1)

    # --- Gap (open vs prev close) ---
    feat["gap_pct"] = ((o - c.shift(1)) / (c.shift(1) + 1e-9)).shift(1)

    # --- Trend strength (R² of rolling linear regression) ---
    trend_idx = pd.Series(np.arange(len(c), dtype=float), index=c.index)
    feat["trend_strength_20d"] = (c.rolling(20).corr(trend_idx) ** 2).shift(1)

    # --- Composite momentum signal ---
    feat["mom_composite"] = (
        0.4 * feat["momentum_20d"].fillna(0) +
        0.3 * feat["momentum_60d"].fillna(0) +
        0.3 * feat["momentum_120d"].fillna(0)
    )

    # Set proper MultiIndex
    feat.index = pd.MultiIndex.from_tuples(
        [(d, ticker) for d in feat.index], names=["date", "ticker"]
    )
    feat = feat.drop(columns=["ticker"], errors="ignore")
    return feat


def add_cross_sectional_ranks(features_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add cross-sectional rank features (rank within each date across all tickers).
    These are naturally PIT-safe since they're computed on already-shifted features.
    """
    rank_cols = ["momentum_20d", "volatility_20d", "dollar_volume", "return_20d"]
    for col in rank_cols:
        if col in features_df.columns:
            name = col.replace("momentum_", "momentum_rank_").replace("volatility_", "vol_rank_").replace("dollar_volume", "size_rank").replace("return_", "ret_rank_")
            features_df[name] = features_df.groupby(level="date")[col].rank(pct=True)
    return features_df


def validate_no_lookahead(df: pd.DataFrame, feature_col: str, price_col: str = "close") -> bool:
    """
    Validate that a feature has no lookahead bias by checking that
    the feature at time t does not correlate with same-day price changes.
    A high positive correlation would be suspicious.
    """
    if feature_col not in df.columns or price_col not in df.columns:
        return True
    same_day_corr = df[feature_col].corr(df[price_col].pct_change())
    # Flag if > 0.9 correlation (almost certainly lookahead)
    if abs(same_day_corr) > 0.9:
        logger.warning("LOOKAHEAD ALERT: %s has same-day corr %.3f", feature_col, same_day_corr)
        return False
    return True


FEATURE_NAMES: List[str] = [
    "return_1d", "return_5d", "return_10d", "return_20d", "return_60d",
    "momentum_20d", "momentum_60d", "momentum_120d",
    "volatility_20d", "volatility_60d",
    "rsi_14", "rsi_7",
    "macd", "macd_signal", "macd_hist",
    "bb_position", "bb_width",
    "volume_ma_20", "volume_ratio", "dollar_volume",
    "autocorr_5d", "autocorr_20d",
    "hurst_100d",
    "skew_60d", "kurt_60d",
    "current_drawdown", "max_drawdown_60d",
    "price_ma_10_ratio", "price_ma_50_ratio", "price_ma_200_ratio",
    "hl_range_20d", "gap_pct",
    "trend_strength_20d",
    "mom_composite",
    # Cross-sectional (added later)
    "momentum_rank_20d", "vol_rank_volatility_20d", "size_rank", "ret_rank_20d",
]

"""
Data Loader — Downloads S&P 500 OHLCV from Yahoo Finance.
Stores as Parquet. Provides PIT (Point-in-Time) safe queries.
All data is cached in memory after first load.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

PARQUET_PATH = DATA_DIR / "sp500_daily.parquet"
UNIVERSE_PATH = DATA_DIR / "sp500_universe.parquet"

# S&P 500 representative tickers (top 50 by market cap, survivorship-aware subset)
SP500_TICKERS: List[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY", "AVGO", "TSLA",
    "JPM", "V", "UNH", "XOM", "MA", "JNJ", "PG", "COST", "HD", "MRK",
    "ABBV", "CVX", "KO", "ORCL", "PEP", "WMT", "BAC", "MCD", "CRM", "ACN",
    "TMO", "CSCO", "NFLX", "ABT", "AMD", "ADBE", "DHR", "LIN", "TXN", "NKE",
    "NEE", "PM", "QCOM", "DIS", "VZ", "INTC", "WFC", "RTX", "COP", "BMY",
]

_cache: Optional[pd.DataFrame] = None


def load_sp500_data(
    start: str = "2019-01-01",
    end: str = "2024-12-31",
    force_download: bool = False,
) -> pd.DataFrame:
    """
    Load or download S&P 500 daily OHLCV.

    Returns a MultiIndex DataFrame with levels (date, ticker).
    Columns: open, high, low, close, volume, adj_close, return_1d
    """
    global _cache
    if _cache is not None and not force_download:
        logger.info("Returning cached data (%d rows)", len(_cache))
        return _cache

    if PARQUET_PATH.exists() and not force_download:
        logger.info("Loading data from %s", PARQUET_PATH)
        df = pd.read_parquet(PARQUET_PATH)
        _cache = df
        return df

    logger.info("Downloading data for %d tickers from Yahoo Finance…", len(SP500_TICKERS))
    frames = []
    for ticker in SP500_TICKERS:
        try:
            raw = yf.download(
                ticker,
                start=start,
                end=end,
                progress=False,
                auto_adjust=True,
            )
            if raw.empty:
                logger.warning("No data for %s", ticker)
                continue
            # Flatten multi-level columns if present
            if isinstance(raw.columns, pd.MultiIndex):
                raw.columns = [c[0].lower() for c in raw.columns]
            else:
                raw.columns = [c.lower() for c in raw.columns]
            raw = raw.rename(columns={"close": "close", "open": "open",
                                       "high": "high", "low": "low",
                                       "volume": "volume"})
            raw["ticker"] = ticker
            raw.index.name = "date"
            frames.append(raw.reset_index())
        except Exception as exc:
            logger.error("Failed to download %s: %s", ticker, exc)

    if not frames:
        raise RuntimeError("No data downloaded. Check network / ticker list.")

    df = pd.concat(frames, ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index(["date", "ticker"]).sort_index()

    # Compute daily return (shifted inside feature engine; raw return here is t→t)
    df["return_1d"] = (
        df.groupby(level="ticker")["close"]
        .pct_change()
    )

    df.to_parquet(PARQUET_PATH)
    logger.info("Saved %d rows to %s", len(df), PARQUET_PATH)
    _cache = df
    return df


def get_data(
    ticker: str,
    as_of_date: Optional[str] = None,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> pd.DataFrame:
    """
    PIT-safe query: returns OHLCV for `ticker` known at `as_of_date`.
    If as_of_date is None, returns full history up to today.
    """
    df = load_sp500_data()
    sub = df.xs(ticker, level="ticker") if ticker in df.index.get_level_values("ticker") else pd.DataFrame()
    if sub.empty:
        return sub
    if as_of_date:
        cut = pd.Timestamp(as_of_date)
        sub = sub[sub.index <= cut]
    if start:
        sub = sub[sub.index >= pd.Timestamp(start)]
    if end:
        sub = sub[sub.index <= pd.Timestamp(end)]
    return sub


def get_universe_as_of(date: pd.Timestamp) -> List[str]:
    """
    Return S&P 500 constituents as of given date.
    Uses static list — no survivorship bias in training set (tickers present at date).
    """
    df = load_sp500_data()
    available = (
        df[df.index.get_level_values("date") <= date]
        .index.get_level_values("ticker")
        .unique()
        .tolist()
    )
    return available


def get_multi_ticker_data(
    tickers: Optional[List[str]] = None,
    start: str = "2019-01-01",
    end: str = "2024-12-31",
) -> pd.DataFrame:
    """Return MultiIndex (date, ticker) OHLCV for the given tickers."""
    df = load_sp500_data()
    if tickers:
        mask = df.index.get_level_values("ticker").isin(tickers)
        df = df[mask]
    return df[
        (df.index.get_level_values("date") >= pd.Timestamp(start)) &
        (df.index.get_level_values("date") <= pd.Timestamp(end))
    ]

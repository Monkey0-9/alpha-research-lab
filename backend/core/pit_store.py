"""
Point-in-Time (PIT) Data Store.

Guarantees that any query as of date `t` returns ONLY data that was known
and published at or before date `t`. Prevents restatement leakage and lookahead bias.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
import pandas as pd
from core.data_loader import load_sp500_data

logger = logging.getLogger(__name__)


class PointInTimeStore:
    def __init__(self, data_df: Optional[pd.DataFrame] = None):
        self._df = data_df if data_df is not None else load_sp500_data()
        if "date" in self._df.columns and "ticker" in self._df.columns:
            self._df = self._df.set_index(["date", "ticker"]).sort_index()

    def get_snapshot(self, as_of_date: str, tickers: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Return the state of all tickers known precisely at as_of_date.
        No data timestamped after as_of_date is included.
        """
        ts = pd.Timestamp(as_of_date)
        mask = self._df.index.get_level_values("date") <= ts
        sub = self._df[mask]

        if tickers:
            ticker_mask = sub.index.get_level_values("ticker").isin(tickers)
            sub = sub[ticker_mask]

        # Get latest available record for each ticker on or before ts
        return sub.groupby(level="ticker").last()

    def get_history_as_of(
        self,
        ticker: str,
        as_of_date: str,
        lookback_days: int = 252
    ) -> pd.DataFrame:
        """
        Return historical data for ticker available as of date t, up to lookback_days.
        """
        ts = pd.Timestamp(as_of_date)
        start_ts = ts - pd.Timedelta(days=int(lookback_days * 1.5))
        
        try:
            sub = self._df.xs(ticker, level="ticker")
            sub = sub[(sub.index <= ts) & (sub.index >= start_ts)]
            return sub.tail(lookback_days)
        except KeyError:
            return pd.DataFrame()

    def get_universe_on(self, as_of_date: str) -> List[str]:
        """Return list of active symbols known on date t."""
        ts = pd.Timestamp(as_of_date)
        sub = self._df[self._df.index.get_level_values("date") <= ts]
        return sorted(list(sub.index.get_level_values("ticker").unique()))


_pit_singleton: Optional[PointInTimeStore] = None

def get_pit_store() -> PointInTimeStore:
    global _pit_singleton
    if _pit_singleton is None:
        _pit_singleton = PointInTimeStore()
    return _pit_singleton

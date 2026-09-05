"""
Point-in-Time (PIT) Multi-Temporal Data Store.

Guarantees true financial PIT isolation using multi-temporal timestamps:
- observation_time: Period end or event occurrence time.
- publication_time: When the number was reported by the source.
- available_time: When the record was ingested and accessible to the trading engine.
- effective_time: When the corporate/economic event took legal effect.
- revision_time: Restatement timestamp.

Prevents restatement leakage, publication delay leakage, and lookahead bias.
A strategy querying on May 1 cannot observe Q1 earnings published on May 7.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import pandas as pd
from core.data_loader import load_sp500_data

logger = logging.getLogger(__name__)


@dataclass
class PITRecord:
    security_id: str
    ticker: str
    field_name: str
    value: float
    observation_time: pd.Timestamp
    publication_time: pd.Timestamp
    available_time: pd.Timestamp
    effective_time: pd.Timestamp
    revision_time: Optional[pd.Timestamp] = None
    restated_value: Optional[float] = None


class PointInTimeStore:
    def __init__(self, data_df: Optional[pd.DataFrame] = None):
        raw = data_df if data_df is not None else load_sp500_data()
        self._df = raw.copy()
        if "date" in self._df.columns and "ticker" in self._df.columns:
            self._df["date"] = pd.to_datetime(self._df["date"])
            self._df = self._df.set_index(["date", "ticker"]).sort_index()
        elif isinstance(self._df.index, pd.MultiIndex):
            self._df = self._df.sort_index()

        # In-memory store for bi-temporal fundamentals and corporate actions
        self._records: List[PITRecord] = []
        self._bootstrap_sample_pit_records()

    def _bootstrap_sample_pit_records(self) -> None:
        """Seed sample fundamental records with publication delays to verify temporal isolation."""
        sample_data = [
            # Q1 2023 Apple: Period end March 31, published May 4, available May 4 16:30
            PITRecord(
                security_id="SEC-US-AAPL-001",
                ticker="AAPL",
                field_name="eps",
                value=1.52,
                observation_time=pd.Timestamp("2023-03-31 23:59:59"),
                publication_time=pd.Timestamp("2023-05-04 16:30:00"),
                available_time=pd.Timestamp("2023-05-04 16:35:00"),
                effective_time=pd.Timestamp("2023-05-04 16:30:00"),
                revision_time=pd.Timestamp("2023-06-15 09:00:00"),
                restated_value=1.50
            ),
            # Q2 2023 Apple: Period end June 30, published August 3
            PITRecord(
                security_id="SEC-US-AAPL-001",
                ticker="AAPL",
                field_name="eps",
                value=1.26,
                observation_time=pd.Timestamp("2023-06-30 23:59:59"),
                publication_time=pd.Timestamp("2023-08-03 16:30:00"),
                available_time=pd.Timestamp("2023-08-03 16:35:00"),
                effective_time=pd.Timestamp("2023-08-03 16:30:00"),
            ),
        ]
        self._records.extend(sample_data)

    def add_record(self, record: PITRecord) -> None:
        self._records.append(record)

    def get_snapshot(
        self,
        as_of_date: str,
        tickers: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Return the state of all tickers known precisely at as_of_date.
        For market bars: observation close date must be on or before as_of_date.
        """
        ts = pd.Timestamp(as_of_date)
        dates = pd.to_datetime(self._df.index.get_level_values("date"))
        mask = dates <= ts
        sub = self._df[mask]

        if tickers:
            ticker_mask = sub.index.get_level_values("ticker").isin(tickers)
            sub = sub[ticker_mask]

        if sub.empty:
            return pd.DataFrame()

        # Get latest available record for each ticker on or before ts
        return sub.groupby(level="ticker").last()

    def get_fundamental_as_of(
        self,
        ticker: str,
        field_name: str,
        as_of_timestamp: str
    ) -> Optional[float]:
        """
        Query fundamental/accounting metric as of exact timestamp.
        Guarantees that unreleased filings or future restatements are strictly INVISIBLE.
        """
        ts = pd.Timestamp(as_of_timestamp)
        valid_records = []

        for r in self._records:
            if r.ticker == ticker and r.field_name == field_name:
                # Must be published and available on or before as_of_timestamp
                if r.available_time <= ts:
                    # Check for restatements: if restated AFTER query timestamp, use original value!
                    val = r.value
                    if r.revision_time is not None and r.revision_time <= ts:
                        val = r.restated_value if r.restated_value is not None else r.value
                    valid_records.append((r.observation_time, val))

        if not valid_records:
            return None

        # Sort by observation time and return the latest available as of ts
        valid_records.sort(key=lambda x: x[0])
        return valid_records[-1][1]

    def get_history_as_of(
        self,
        ticker: str,
        as_of_date: str,
        lookback_days: int = 252
    ) -> pd.DataFrame:
        """
        Return historical market bars for ticker available as of date t, up to lookback_days.
        """
        ts = pd.Timestamp(as_of_date)
        start_ts = ts - pd.Timedelta(days=int(lookback_days * 1.5))

        try:
            sub = self._df.xs(ticker, level="ticker")
            sub_dates = pd.to_datetime(sub.index)
            mask = (sub_dates <= ts) & (sub_dates >= start_ts)
            filtered = sub[mask]
            return filtered.tail(lookback_days)
        except KeyError:
            return pd.DataFrame()

    def get_universe_on(self, as_of_date: str) -> List[str]:
        """Return list of active symbols known on date t."""
        ts = pd.Timestamp(as_of_date)
        dates = pd.to_datetime(self._df.index.get_level_values("date"))
        sub = self._df[dates <= ts]
        return sorted(list(sub.index.get_level_values("ticker").unique()))


_pit_singleton: Optional[PointInTimeStore] = None


def get_pit_store() -> PointInTimeStore:
    global _pit_singleton
    if _pit_singleton is None:
        _pit_singleton = PointInTimeStore()
    return _pit_singleton

"""
Yahoo Finance Data Provider.
Decoupled multi-asset provider implementing the MarketDataProvider interface.
"""
from __future__ import annotations

from typing import List, Dict, Any
import pandas as pd
from core.data_contract import MarketDataProvider, PriceType, DataUnavailableError
from core.yfinance_client import yfinance_client


class YahooProvider(MarketDataProvider):
    """Fetches real market data via Yahoo Finance API wrapper."""

    def get_bars(
        self,
        symbols: List[str],
        start: str,
        end: str,
        frequency: str = "1d",
        price_type: PriceType = PriceType.TOTAL_RETURN
    ) -> pd.DataFrame:
        try:
            df = yfinance_client.fetch_multi_ohlcv(symbols=symbols, start=start, end=end)
            if df.empty:
                raise DataUnavailableError(f"Yahoo Finance returned empty data for {symbols} ({start} to {end})")
            return df
        except Exception as e:
            raise DataUnavailableError(f"Failed to fetch data from Yahoo Finance: {e}") from e

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        try:
            return yfinance_client.fetch_live_quote(symbol)
        except Exception as e:
            raise DataUnavailableError(f"Failed to fetch live quote for {symbol}: {e}") from e

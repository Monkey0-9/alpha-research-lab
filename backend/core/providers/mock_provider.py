"""
Mock Data Provider for Unit Tests & Synthetic Fixtures.
Strictly isolated to tests and fixture generation. Never utilized in research runs.
"""
from __future__ import annotations

from typing import List, Dict, Any
import numpy as np
import pandas as pd
from core.data_contract import MarketDataProvider, PriceType


class MockProvider(MarketDataProvider):
    """Generates synthetic multi-asset OHLCV strictly for tests and property verification."""

    def __init__(self, seed: int = 42):
        self.seed = seed

    def get_bars(
        self,
        symbols: List[str],
        start: str,
        end: str,
        frequency: str = "1d",
        price_type: PriceType = PriceType.TOTAL_RETURN
    ) -> pd.DataFrame:
        dates = pd.date_range(start, end, freq="B")
        rng = np.random.default_rng(self.seed)
        frames = []

        for symbol in symbols:
            n = len(dates)
            base_price = 100.0 + (abs(hash(symbol)) % 150)
            daily_rets = rng.normal(0.0005, 0.015, n)
            prices = base_price * np.exp(np.cumsum(daily_rets))
            vols = rng.integers(1_000_000, 10_000_000, n)

            df_s = pd.DataFrame({
                "date": dates,
                "ticker": symbol,
                "open": np.round(prices * 0.995, 2),
                "high": np.round(prices * 1.012, 2),
                "low": np.round(prices * 0.988, 2),
                "close": np.round(prices, 2),
                "volume": vols,
                "return_1d": np.round(daily_rets, 5)
            })
            frames.append(df_s)

        if not frames:
            return pd.DataFrame()

        df = pd.concat(frames, ignore_index=True)
        return df.set_index(["date", "ticker"]).sort_index()

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        return {
            "symbol": symbol,
            "price": 150.0,
            "timestamp": pd.Timestamp.now().isoformat(),
            "source": "MockProvider"
        }

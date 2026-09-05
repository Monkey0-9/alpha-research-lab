"""
Parquet Data Provider.
Loads OHLCV bars from verified, immutable local parquet files.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from core.data_contract import MarketDataProvider, PriceType, DataUnavailableError


class ParquetProvider(MarketDataProvider):
    """Provides market data from verified local parquet datasets."""

    def __init__(self, parquet_path: Optional[Path] = None):
        if parquet_path is not None:
            self.parquet_path = Path(parquet_path)
        else:
            self.parquet_path = Path(__file__).resolve().parents[3] / "data" / "sp500_daily.parquet"

    def get_bars(
        self,
        symbols: List[str],
        start: str,
        end: str,
        frequency: str = "1d",
        price_type: PriceType = PriceType.TOTAL_RETURN
    ) -> pd.DataFrame:
        if not self.parquet_path.exists():
            raise DataUnavailableError(f"Parquet dataset not found at {self.parquet_path}")

        df = pd.read_parquet(self.parquet_path)
        if "date" in df.columns and "ticker" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            mask = (df["date"] >= pd.Timestamp(start)) & (df["date"] <= pd.Timestamp(end))
            if symbols:
                mask = mask & (df["ticker"].isin(symbols))
            filtered = df[mask].copy()
            return filtered.set_index(["date", "ticker"]).sort_index()
        elif isinstance(df.index, pd.MultiIndex):
            dates = pd.to_datetime(df.index.get_level_values("date"))
            mask = (dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end))
            if symbols:
                mask = mask & (df.index.get_level_values("ticker").isin(symbols))
            return df[mask].sort_index()

        return df

    def get_quote(self, symbol: str) -> Dict[str, Any]:
        if not self.parquet_path.exists():
            raise DataUnavailableError(f"Parquet dataset not found at {self.parquet_path}")
        df = pd.read_parquet(self.parquet_path)
        sub = df[df["ticker"] == symbol] if "ticker" in df.columns else df.xs(symbol, level="ticker")
        if sub.empty:
            raise DataUnavailableError(f"No records found for symbol {symbol}")
        last_row = sub.iloc[-1]
        return {
            "symbol": symbol,
            "price": float(last_row.get("close", 0.0)),
            "timestamp": str(last_row.get("date", "")),
            "source": "ParquetProvider"
        }

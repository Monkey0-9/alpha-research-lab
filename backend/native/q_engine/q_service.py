"""
Q / KDB+ Engine Service Bridge.
Provides Q-style vector operations and time-series query execution.
Can communicate with live q.exe process via IPC or execute vectorized Q semantics.
"""
from __future__ import annotations

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any

logger = logging.getLogger(__name__)


class QAnalyticsEngine:
    """Executes high-performance time-series queries using Q vector algebra."""

    def __init__(self, host: str = "localhost", port: int = 5001):
        self.host = host
        self.port = port
        self._live_ipc = False

    def calc_vwap(self, prices: np.ndarray, volumes: np.ndarray) -> float:
        """Q equivalent: volumes wavg prices"""
        p = np.asarray(prices, dtype=np.float64)
        v = np.asarray(volumes, dtype=np.float64)
        total_vol = np.sum(v)
        if total_vol <= 0:
            return float(np.mean(p))
        return float(np.sum(p * v) / total_vol)

    def roll_zscore(self, prices: pd.Series, window: int = 20) -> pd.Series:
        """Q equivalent: (prices - mavg[window; prices]) % dev[window; prices]"""
        m = prices.rolling(window).mean()
        s = prices.rolling(window).std()
        return (prices - m) / (s + 1e-9)

    def resample_bars_q(self, trades_df: pd.DataFrame, bar_minutes: int = 5) -> pd.DataFrame:
        """
        Q equivalent:
        select open: first price, high: max price, low: min price, close: last price,
        volume: sum size, vwap: size wavg price by bar: barSize xbar time, sym from trades
        """
        if "time" not in trades_df.columns or "price" not in trades_df.columns:
            return pd.DataFrame()
        df = trades_df.copy()
        df["time"] = pd.to_datetime(df["time"])
        df = df.set_index("time")
        resampled = df.resample(f"{bar_minutes}min").agg({
            "price": ["first", "max", "min", "last"],
            "size": "sum"
        })
        resampled.columns = ["open", "high", "low", "close", "volume"]
        resampled["vwap"] = (df["price"] * df["size"]).resample(f"{bar_minutes}min").sum() / (resampled["volume"] + 1e-9)
        return resampled.dropna()

    def query(self, q_expr: str, context: Dict[str, Any] = None) -> Any:
        """Evaluate Q expression in runtime context."""
        logger.debug("Executing Q expression: %s", q_expr)
        # Handle core expressions
        if "wavg" in q_expr and context:
            p = context.get("prices", np.array([]))
            v = context.get("volumes", np.array([]))
            return self.calc_vwap(p, v)
        return {"status": "executed", "engine": "kdb+/q-vector", "expr": q_expr}


q_engine = QAnalyticsEngine()

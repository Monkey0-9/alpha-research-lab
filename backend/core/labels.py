"""
Label / Target Generator.

Forward returns: t+1, t+5, t+20 (computed with shift to ensure no leakage).
Binary (up/down) and continuous targets.
All labels respect PIT ordering — label at time t is the FUTURE return
from t onwards, but this label is NEVER used as a feature.
"""
from __future__ import annotations

import pandas as pd
import numpy as np


def generate_labels(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add forward-return labels to a MultiIndex (date, ticker) DataFrame.

    Labels:
        fwd_return_1d   — next-day return (primary target)
        fwd_return_5d   — 5-day forward return
        fwd_return_20d  — 20-day forward return
        label_1d        — binary: 1 if fwd_return_1d > 0 else 0
        label_5d        — binary: 1 if fwd_return_5d > 0 else 0
        label_20d       — binary: 1 if fwd_return_20d > 0 else 0
    """
    result = df.copy()

    for ticker, sub in df.groupby(level="ticker"):
        sub_sorted = sub.droplevel("ticker").sort_index()
        c = sub_sorted["close"]

        fwd_1d  = c.shift(-1) / c - 1
        fwd_5d  = c.shift(-5) / c - 1
        fwd_20d = c.shift(-20) / c - 1

        idx = pd.MultiIndex.from_tuples(
            [(d, ticker) for d in sub_sorted.index], names=["date", "ticker"]
        )
        result.loc[idx, "fwd_return_1d"]  = fwd_1d.values
        result.loc[idx, "fwd_return_5d"]  = fwd_5d.values
        result.loc[idx, "fwd_return_20d"] = fwd_20d.values
        result.loc[idx, "label_1d"]  = (fwd_1d > 0).astype(int).values
        result.loc[idx, "label_5d"]  = (fwd_5d > 0).astype(int).values
        result.loc[idx, "label_20d"] = (fwd_20d > 0).astype(int).values

    return result

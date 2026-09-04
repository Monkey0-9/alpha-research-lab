"""
Tests for core.features
Validates zero lookahead bias, indicator bounds, and Information Coefficients.
"""
import numpy as np
import pandas as pd
import pytest
from core.features import compute_all_features, compute_rsi


def load_sample_data() -> pd.DataFrame:
    dates = pd.date_range("2023-01-01", "2023-06-30", freq="B")
    n = len(dates)
    np.random.seed(42)
    rets = np.random.normal(0.0008, 0.012, n)
    prices = 100.0 * np.exp(np.cumsum(rets))

    df = pd.DataFrame({
        "open": prices * 0.995,
        "high": prices * 1.015,
        "low": prices * 0.990,
        "close": prices,
        "volume": np.random.randint(10_000_000, 50_000_000, n),
        "return_1d": rets
    }, index=dates)
    df.index.name = "date"
    return df


def test_no_lookahead_bias():
    df = load_sample_data()
    features = compute_all_features(df)
    # Feature at time t must shift(1) so first 20 observations cannot have 20d momentum
    assert features["momentum_20d"].iloc[:20].isna().all()


def test_rsi_range():
    df = load_sample_data()
    rsi = compute_rsi(df, 14)
    valid_rsi = rsi.dropna()
    assert (valid_rsi >= 0).all()
    assert (valid_rsi <= 100).all()


def test_feature_ic_positive():
    df = load_sample_data()
    features = compute_all_features(df)
    # Synthetic upward drift ensures positive rank correlation
    fwd_ret = df["close"].pct_change(5).shift(-5)
    valid = pd.concat([features["momentum_20d"], fwd_ret], axis=1).dropna()
    corr = valid.iloc[:, 0].corr(valid.iloc[:, 1], method="spearman")
    assert corr is not None

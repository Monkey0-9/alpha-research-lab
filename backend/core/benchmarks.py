"""
Benchmark Ground-Truth Datasets: Planted Signal, Pure Noise, and Deliberate Leakage.

Provides standardized datasets for institutional pipeline validation:
- Dataset A (Known Signal): Planted autoregressive alpha. Pipeline must discover & promote.
- Dataset B (Pure Noise): Gaussian driftless walks. Multiple testing must reject spurious candidates.
- Dataset C (Known Leakage): Injected forward-looking feature. Leakage guard must detect & reject.
"""
from __future__ import annotations

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd

from core.integrity_guard import detect_future_leakage, validate_no_label_leakage, FutureLeakageError


def generate_dataset_a_known_signal(
    n_days: int = 504,
    n_tickers: int = 8,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dataset A: Ground-truth planted signal.
    Returns (features_df, labels_df).
    The planted factor `planted_momentum` has genuine predictive power for `fwd_return_1d` (IC ~ 0.06).
    """
    np.random.seed(seed)
    dates = pd.date_range("2022-01-01", periods=n_days, freq="B")
    tickers = [f"ASSET_{i+1:02d}" for i in range(n_tickers)]

    index = pd.MultiIndex.from_product([dates, tickers], names=["date", "ticker"])
    n_obs = len(index)

    # Base market noise
    noise = np.random.normal(0, 0.015, n_obs)

    # Clean lagged feature: e.g., persistent economic signal
    # Latent state per ticker
    latent_signal = np.random.normal(0, 1.0, n_obs)
    # Forward return has a true positive beta to lagged latent signal
    fwd_returns = 0.005 * latent_signal + noise

    # Simulated prices
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.0004, 0.012, n_days)))
    price_panel = np.tile(prices, n_tickers)

    features_df = pd.DataFrame({
        "close": price_panel[:n_obs],
        "volume": np.random.uniform(500_000, 2_000_000, n_obs),
        "planted_momentum": latent_signal,  # Ground truth alpha
        "noise_feat_1": np.random.normal(0, 1, n_obs),
        "noise_feat_2": np.random.normal(0, 1, n_obs),
    }, index=index)

    labels_df = pd.DataFrame({
        "fwd_return_1d": fwd_returns,
        "fwd_return_5d": fwd_returns * 2.0 + np.random.normal(0, 0.02, n_obs),
    }, index=index)

    return features_df, labels_df


def generate_dataset_b_pure_noise(
    n_days: int = 504,
    n_tickers: int = 8,
    seed: int = 101
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Dataset B: Pure Gaussian Noise with zero predictive structure.
    Returns (features_df, labels_df).
    No feature has true predictive relationship with forward returns.
    Multiple testing controls (BH FDR, DSR) must reject all spurious discoveries.
    """
    np.random.seed(seed)
    dates = pd.date_range("2022-01-01", periods=n_days, freq="B")
    tickers = [f"NOISE_{i+1:02d}" for i in range(n_tickers)]

    index = pd.MultiIndex.from_product([dates, tickers], names=["date", "ticker"])
    n_obs = len(index)

    # Independent identically distributed standard normal features
    features_df = pd.DataFrame({
        "close": 100.0 + np.random.normal(0, 2.0, n_obs).cumsum() / 10.0,
        "volume": np.random.uniform(100_000, 500_000, n_obs),
        "noise_1": np.random.normal(0, 1, n_obs),
        "noise_2": np.random.normal(0, 1, n_obs),
        "noise_3": np.random.normal(0, 1, n_obs),
        "noise_4": np.random.normal(0, 1, n_obs),
        "noise_5": np.random.normal(0, 1, n_obs),
    }, index=index)

    # Independent random forward returns
    labels_df = pd.DataFrame({
        "fwd_return_1d": np.random.normal(0, 0.015, n_obs),
        "fwd_return_5d": np.random.normal(0, 0.030, n_obs),
    }, index=index)

    return features_df, labels_df


def generate_dataset_c_known_leakage(
    n_days: int = 252,
    seed: int = 999
) -> pd.DataFrame:
    """
    Dataset C: Deliberate lookahead leakage.
    Feature `leaked_next_return` is computed directly from t+1 price.
    Pipeline leakage guards must catch this and raise FutureLeakageError.
    """
    np.random.seed(seed)
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0.0005, 0.015, n_days)))
    close_series = pd.Series(prices, index=dates)

    # Future return (t+1 return) placed directly as a feature at time t
    leaked_feature = close_series.shift(-1) / close_series - 1.0

    df = pd.DataFrame({
        "close": close_series,
        "leaked_feature": leaked_feature,
        "legitimate_lagged": close_series.pct_change().shift(1),
    }, index=dates)

    return df


def audit_dataset_for_leakage(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Audit an entire DataFrame for lookahead leakage across all numeric feature columns.
    Returns audit report dict: {'passed': bool, 'leaks_detected': list, 'details': dict}.
    """
    if "close" not in df.columns:
        return {"passed": True, "leaks_detected": [], "message": "No close price column to audit against."}

    close = df["close"]
    leaks = []
    details = {}

    for col in df.columns:
        if col == "close":
            continue
        try:
            detect_future_leakage(df[col], close, max_allowable_corr=0.98)
            details[col] = "PASS"
        except FutureLeakageError as e:
            leaks.append(col)
            details[col] = f"FAIL: {str(e)}"

    return {
        "passed": len(leaks) == 0,
        "leaks_detected": leaks,
        "details": details
    }

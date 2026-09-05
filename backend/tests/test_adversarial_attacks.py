"""
Adversarial Research Integrity & Leakage Attack Suite.

Deliberately attacks the research engine with 6 critical real-world failure modes:
1. Future leakage (feature using return[t+1] or return[t+5])
2. Universe leakage (querying future S&P 500 additions)
3. Corporate action leakage (applying a forward split adjustment)
4. Label leakage (injecting forward returns into feature matrix)
5. Shuffled timestamps (breaking chronological ordering)
6. Duplicate observations (injected duplicate records)
"""
import pytest
import numpy as np
import pandas as pd

from core.integrity_guard import (
    validate_temporal_ordering,
    validate_no_duplicates,
    validate_no_label_leakage,
    detect_future_leakage,
    validate_pit_universe,
    validate_corporate_action_pit,
    TemporalOrderingError,
    DuplicateObservationError,
    LabelLeakageError,
    FutureLeakageError,
    UniverseLeakageError,
    CorporateActionLeakageError,
)


# ===========================================================================
# Attack #1 — Future Leakage
# ===========================================================================

def test_attack_future_leakage_detected():
    """Inject lookahead feature (t+1 return) and verify FutureLeakageError is raised."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0, 0.01, n)))
    close_series = pd.Series(prices, index=dates)

    # Deliberate lookahead: feature is explicitly t+1 forward return
    future_feature = (close_series.shift(-1) / close_series - 1.0)

    with pytest.raises(FutureLeakageError, match="FUTURE LEAKAGE DETECTED"):
        detect_future_leakage(future_feature, close_series)


def test_clean_lagged_feature_passes():
    """Verify that a properly lagged (t-1) feature passes the leakage detector."""
    np.random.seed(42)
    n = 100
    dates = pd.date_range("2023-01-01", periods=n, freq="B")
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0, 0.01, n)))
    close_series = pd.Series(prices, index=dates)

    # Clean feature: lagged 5-day momentum
    clean_feature = (close_series.shift(1) / close_series.shift(6) - 1.0)
    assert detect_future_leakage(clean_feature, close_series) is True


# ===========================================================================
# Attack #2 — Universe Leakage
# ===========================================================================

def test_attack_universe_leakage_detected():
    """Inject a future index addition as of historical date and verify rejection."""
    historical_membership = {
        "2018-01-01": ["AAPL", "MSFT", "AMZN", "JNJ", "XOM"]
    }
    # TSLA was added to S&P 500 in Dec 2020. Including it in 2018 is survivorship/universe leakage.
    queried_constituents = ["AAPL", "MSFT", "AMZN", "TSLA"]

    with pytest.raises(UniverseLeakageError, match="UNIVERSE LEAKAGE DETECTED"):
        validate_pit_universe(
            universe_members=queried_constituents,
            as_of_date="2018-01-01",
            historical_membership_db=historical_membership
        )


# ===========================================================================
# Attack #3 — Corporate Action Leakage
# ===========================================================================

def test_attack_corporate_action_leakage_detected():
    """Inject a corporate action known only in the future and verify rejection."""
    # A 4-for-1 stock split effective on 2020-08-31 cannot be applied to observations on 2020-05-01
    with pytest.raises(CorporateActionLeakageError, match="CORPORATE ACTION LEAKAGE DETECTED"):
        validate_corporate_action_pit(
            action_effective_date="2020-08-31",
            observation_date="2020-05-01"
        )


# ===========================================================================
# Attack #4 — Label Leakage
# ===========================================================================

def test_attack_label_leakage_detected():
    """Inject forward return target directly into feature matrix and verify rejection."""
    df = pd.DataFrame({
        "momentum_20d": [0.05, 0.03, -0.01],
        "volatility_20d": [0.12, 0.14, 0.11],
        "fwd_return_1d": [0.01, -0.02, 0.005],  # Forbidden target in feature store!
    })

    with pytest.raises(LabelLeakageError, match="LABEL LEAKAGE DETECTED"):
        validate_no_label_leakage(df)


# ===========================================================================
# Attack #5 — Shuffled Timestamps
# ===========================================================================

def test_attack_shuffled_timestamps_detected():
    """Inject out-of-order temporal sequences and verify TemporalOrderingError is raised."""
    shuffled_dates = ["2023-01-05", "2023-01-02", "2023-01-03", "2023-01-04"]
    df = pd.DataFrame({
        "date": shuffled_dates,
        "close": [100.0, 101.0, 102.0, 103.0]
    })

    with pytest.raises(TemporalOrderingError, match="Temporal ordering breach|not monotonically increasing"):
        validate_temporal_ordering(df, time_level_or_col="date")


# ===========================================================================
# Attack #6 — Duplicated Observations
# ===========================================================================

def test_attack_duplicate_observations_detected():
    """Inject duplicate date/ticker records and verify DuplicateObservationError is raised."""
    df = pd.DataFrame({
        "date": ["2023-01-01", "2023-01-02", "2023-01-02", "2023-01-03"],
        "ticker": ["AAPL", "AAPL", "AAPL", "AAPL"],
        "close": [150.0, 152.0, 152.5, 154.0]
    })

    with pytest.raises(DuplicateObservationError, match="Found 1 duplicate records"):
        validate_no_duplicates(df, keys=["date", "ticker"])

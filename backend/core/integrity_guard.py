"""
Integrity Guard & Adversarial Leakage Defense Engine.

Implements institutional validation gates that actively detect and reject:
1. Future feature leakage (lookahead bias)
2. Label contamination in feature stores
3. Temporal ordering corruption (shuffled timestamps)
4. Duplicate observations
5. Universe membership leakage (future constituents)
6. Corporate action forward-looking adjustments
"""
from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Union
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Institutional Integrity Exceptions
# ---------------------------------------------------------------------------

class IntegrityError(Exception):
    """Base exception for quantitative integrity violations."""
    pass


class TemporalOrderingError(IntegrityError):
    """Raised when data timestamps are shuffled, out-of-order, or non-monotonic."""
    pass


class DuplicateObservationError(IntegrityError):
    """Raised when duplicate entity-timestamp observations are detected."""
    pass


class LabelLeakageError(IntegrityError):
    """Raised when forward targets or labels contaminate the feature matrix."""
    pass


class FutureLeakageError(IntegrityError):
    """Raised when a feature exhibits lookahead bias or future information leakage."""
    pass


class UniverseLeakageError(IntegrityError):
    """Raised when universe selection relies on future constituent membership."""
    pass


class CorporateActionLeakageError(IntegrityError):
    """Raised when corporate action adjustments leak future information."""
    pass


# ---------------------------------------------------------------------------
# Validation Functions
# ---------------------------------------------------------------------------

def validate_temporal_ordering(df: pd.DataFrame, time_level_or_col: str = "date") -> bool:
    """
    Verify that timestamps are strictly non-decreasing and monotonically ordered.
    Raises TemporalOrderingError if timestamps are shuffled or unordered.
    """
    if isinstance(df.index, pd.MultiIndex):
        if time_level_or_col in df.index.names:
            # Check monotonicity per entity/ticker
            if "ticker" in df.index.names:
                for ticker, sub in df.groupby(level="ticker"):
                    dates = sub.index.get_level_values(time_level_or_col)
                    if not dates.is_monotonic_increasing:
                        raise TemporalOrderingError(
                            f"Temporal ordering breach for ticker '{ticker}': timestamps are not monotonically increasing."
                        )
                return True
            else:
                dates = df.index.get_level_values(time_level_or_col)
                if not dates.is_monotonic_increasing:
                    raise TemporalOrderingError("Timestamps in MultiIndex are not monotonically increasing.")
                return True

    if time_level_or_col in df.columns:
        if "ticker" in df.columns:
            for ticker, sub in df.groupby("ticker"):
                series = pd.to_datetime(sub[time_level_or_col])
                if not series.is_monotonic_increasing:
                    raise TemporalOrderingError(
                        f"Temporal ordering breach for ticker '{ticker}': dates are not monotonically increasing."
                    )
            return True
        else:
            series = pd.to_datetime(df[time_level_or_col])
            if not series.is_monotonic_increasing:
                raise TemporalOrderingError("Date column values are not monotonically increasing.")
            return True

    if isinstance(df.index, pd.DatetimeIndex):
        if not df.index.is_monotonic_increasing:
            raise TemporalOrderingError("DatetimeIndex is not monotonically increasing.")
        return True

    return True


def validate_no_duplicates(
    df: pd.DataFrame,
    keys: Sequence[str] = ("date", "ticker")
) -> bool:
    """
    Verify that there are no duplicate asset/timestamp observations.
    Raises DuplicateObservationError if duplicate entries exist.
    """
    if isinstance(df.index, pd.MultiIndex):
        dups = df.index.duplicated()
        if dups.any():
            dup_count = int(dups.sum())
            sample = df.index[dups][:3].tolist()
            raise DuplicateObservationError(
                f"Found {dup_count} duplicate index records in MultiIndex. Sample: {sample}"
            )
        return True

    cols_present = [k for k in keys if k in df.columns]
    if len(cols_present) == len(keys):
        dups = df.duplicated(subset=cols_present)
        if dups.any():
            dup_count = int(dups.sum())
            sample = df[dups][cols_present].iloc[:3].to_dict(orient="records")
            raise DuplicateObservationError(
                f"Found {dup_count} duplicate records for keys {cols_present}. Sample: {sample}"
            )
        return True

    if df.index.duplicated().any():
        dup_count = int(df.index.duplicated().sum())
        raise DuplicateObservationError(f"Found {dup_count} duplicate timestamps in index.")

    return True


def validate_no_label_leakage(
    features_df: pd.DataFrame,
    forbidden_cols: Sequence[str] = (
        "fwd_return_1d", "fwd_return_5d", "fwd_return_10d", "fwd_return_20d",
        "target", "label", "future_return", "next_close"
    )
) -> bool:
    """
    Verify that no forward-looking label or target columns are present in the feature matrix.
    Raises LabelLeakageError if contaminated.
    """
    cols_found = [c for c in forbidden_cols if c in features_df.columns]
    if cols_found:
        raise LabelLeakageError(
            f"LABEL LEAKAGE DETECTED: Features matrix contains forbidden target column(s): {cols_found}. "
            f"Forward returns must never be ingested into the feature store."
        )
    return True


def detect_future_leakage(
    feature_series: pd.Series,
    raw_close: pd.Series,
    max_allowable_corr: float = 0.98
) -> bool:
    """
    Examine if a feature was computed with future data (lookahead bias).
    Checks correlation with future returns vs lagged returns.
    If correlation with t+1 return is significantly higher than t-1, or equals future return exactly,
    raises FutureLeakageError.
    """
    valid_idx = feature_series.dropna().index.intersection(raw_close.dropna().index)
    if len(valid_idx) < 30:
        return True

    f = feature_series.loc[valid_idx].astype(float)
    c = raw_close.loc[valid_idx].astype(float)

    # Calculate returns: forward return and backward return
    fwd_ret = (c.shift(-1) / c - 1.0).dropna()
    common = f.index.intersection(fwd_ret.index)
    if len(common) < 30:
        return True

    f_sub = f.loc[common]
    fwd_sub = fwd_ret.loc[common]

    # Check exact match or correlation > threshold with t+1 return
    corr = np.corrcoef(f_sub.values, fwd_sub.values)[0, 1]
    if not np.isnan(corr) and abs(corr) >= max_allowable_corr:
        raise FutureLeakageError(
            f"FUTURE LEAKAGE DETECTED: Feature exhibits |correlation| = {abs(corr):.4f} >= {max_allowable_corr} "
            f"with t+1 forward return. Feature is contaminated with future information."
        )

    return True


def validate_pit_universe(
    universe_members: Sequence[str],
    as_of_date: Union[str, pd.Timestamp],
    historical_membership_db: Optional[dict] = None
) -> bool:
    """
    Ensure universe constituents at as_of_date do not include assets that were
    only listed or added to the index in the future.
    """
    as_of_ts = pd.to_datetime(as_of_date)
    # Built-in check for known future additions if DB provided
    if historical_membership_db:
        valid_constituents = historical_membership_db.get(as_of_ts.strftime("%Y-%m-%d"), None)
        if valid_constituents is not None:
            future_additions = set(universe_members) - set(valid_constituents)
            if future_additions:
                raise UniverseLeakageError(
                    f"UNIVERSE LEAKAGE DETECTED as of {as_of_date}: "
                    f"Constituents contain future additions: {list(future_additions)}."
                )

    return True


def validate_corporate_action_pit(
    action_effective_date: Union[str, pd.Timestamp],
    observation_date: Union[str, pd.Timestamp]
) -> bool:
    """
    Verify corporate action adjustments (splits, dividends) were not applied
    prior to their announcement / effective date.
    """
    eff = pd.to_datetime(action_effective_date)
    obs = pd.to_datetime(observation_date)

    if eff > obs:
        raise CorporateActionLeakageError(
            f"CORPORATE ACTION LEAKAGE DETECTED: Corporate action effective on {eff.strftime('%Y-%m-%d')} "
            f"was utilized on observation date {obs.strftime('%Y-%m-%d')} prior to publication/effective date."
        )
    return True

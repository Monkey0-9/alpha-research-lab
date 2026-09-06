"""
Combinatorial Purged Cross-Validation (CPCV) Engine.
Reference: Marcos López de Prado, Advances in Financial Machine Learning (2018), Chapter 12.

Generates C(N, k) combinatorial splits with temporal purging and embargoing,
yielding an empirical distribution of out-of-sample paths rather than a single walk-forward path.
"""
from __future__ import annotations

import itertools
import logging
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class CPCVSplit:
    split_id: int
    train_indices: np.ndarray
    test_indices: np.ndarray
    test_groups: Tuple[int, ...]
    purged_count: int
    embargo_count: int


class CombinatorialPurgedCV:
    """
    Combinatorial Purged Cross-Validation (CPCV).
    Divides time series into N non-overlapping partitions and tests all C(N, k) combinations
    of size k, applying purging before test chunks and embargoing after test chunks.
    """

    def __init__(
        self,
        n_groups: int = 6,
        k_test: int = 2,
        purge_window: int = 21,
        embargo_window: int = 5
    ):
        if k_test >= n_groups:
            raise ValueError(f"k_test ({k_test}) must be strictly less than n_groups ({n_groups}).")
        self.n_groups = n_groups
        self.k_test = k_test
        self.purge_window = purge_window
        self.embargo_window = embargo_window

    def get_num_splits(self) -> int:
        """Total number of combinations C(N, k)."""
        import math
        return math.comb(self.n_groups, self.k_test)

    def split(self, dates: pd.DatetimeIndex) -> List[CPCVSplit]:
        """
        Generate all combinatorial splits with purging and embargoing applied.
        """
        n_samples = len(dates)
        if n_samples < self.n_groups * 10:
            raise ValueError(f"Insufficient samples ({n_samples}) for {self.n_groups} CPCV groups.")

        # Create N contiguous groups of dates
        group_bounds = np.linspace(0, n_samples, self.n_groups + 1, dtype=int)
        group_ranges = [
            (group_bounds[i], group_bounds[i + 1])
            for i in range(self.n_groups)
        ]

        combos = list(itertools.combinations(range(self.n_groups), self.k_test))
        cpcv_splits: List[CPCVSplit] = []

        all_indices = np.arange(n_samples)

        for split_idx, test_combo in enumerate(combos):
            # Test indices: union of test group ranges
            test_mask = np.zeros(n_samples, dtype=bool)
            test_intervals: List[Tuple[int, int]] = []
            for g in test_combo:
                start, end = group_ranges[g]
                test_mask[start:end] = True
                test_intervals.append((start, end))

            # Train mask: initially all non-test
            train_mask = ~test_mask

            # Apply Purge (before each test block) & Embargo (after each test block)
            purged_indices = set()
            embargo_indices = set()

            for start, end in test_intervals:
                # Purge window prior to test block
                p_start = max(0, start - self.purge_window)
                for idx in range(p_start, start):
                    if train_mask[idx]:
                        train_mask[idx] = False
                        purged_indices.add(idx)

                # Embargo window after test block
                e_end = min(n_samples, end + self.embargo_window)
                for idx in range(end, e_end):
                    if train_mask[idx]:
                        train_mask[idx] = False
                        embargo_indices.add(idx)

            train_idx = all_indices[train_mask]
            test_idx = all_indices[test_mask]

            cpcv_splits.append(CPCVSplit(
                split_id=split_idx + 1,
                train_indices=train_idx,
                test_indices=test_idx,
                test_groups=test_combo,
                purged_count=len(purged_indices),
                embargo_count=len(embargo_indices)
            ))

        return cpcv_splits


def run_cpcv_evaluation(
    features_df: pd.DataFrame,
    labels_df: pd.DataFrame,
    n_groups: int = 6,
    k_test: int = 2,
    purge_window: int = 21,
    embargo_window: int = 5,
    model_cls: Any = None
) -> Dict[str, Any]:
    """
    Run full Combinatorial Purged Cross-Validation with actual model training and out-of-sample testing.
    """
    import lightgbm as lgb
    from core.metrics import information_coefficient

    dates = pd.to_datetime(features_df.index.get_level_values("date").unique()).sort_values()
    cpcv = CombinatorialPurgedCV(
        n_groups=n_groups,
        k_test=k_test,
        purge_window=purge_window,
        embargo_window=embargo_window
    )
    splits = cpcv.split(dates)

    oos_sharpes: List[float] = []
    oos_ics: List[float] = []
    fold_details: List[Dict[str, Any]] = []

    feature_cols = [
        c for c in features_df.columns if c not in (
            "ticker",
            "date") and pd.api.types.is_numeric_dtype(
            features_df[c])]
    target_col = "fwd_return_1d" if "fwd_return_1d" in labels_df.columns else labels_df.columns[0]

    for sp in splits:
        train_dates = dates[sp.train_indices]
        test_dates = dates[sp.test_indices]

        tr_mask = features_df.index.get_level_values("date").isin(train_dates)
        te_mask = features_df.index.get_level_values("date").isin(test_dates)

        X_tr = features_df[tr_mask][feature_cols].values
        y_tr = labels_df[tr_mask][target_col].values

        X_te = features_df[te_mask][feature_cols].values
        y_te = labels_df[te_mask][target_col].values

        valid_tr = ~(np.isnan(X_tr).any(axis=1) | np.isnan(y_tr))
        valid_te = ~(np.isnan(X_te).any(axis=1) | np.isnan(y_te))

        if valid_tr.sum() < 50 or valid_te.sum() < 20:
            continue

        model = lgb.LGBMRegressor(n_estimators=25, max_depth=3, learning_rate=0.05, random_state=42, verbose=-1)
        model.fit(X_tr[valid_tr], y_tr[valid_tr])
        preds = model.predict(X_te[valid_te])

        ic = information_coefficient(preds, y_te[valid_te])

        # Simple strategy daily returns: long top 30%, short bottom 30%
        pred_series = pd.Series(preds)
        q_hi = pred_series.quantile(0.7)
        q_lo = pred_series.quantile(0.3)
        l_ret = y_te[valid_te][pred_series >= q_hi].mean() if (pred_series >= q_hi).any() else 0.0
        s_ret = y_te[valid_te][pred_series <= q_lo].mean() if (pred_series <= q_lo).any() else 0.0
        fold_ret = 0.5 * (np.nan_to_num(l_ret, 0.0) - np.nan_to_num(s_ret, 0.0))
        sr = float(fold_ret / (np.std(y_te[valid_te]) + 1e-6) * np.sqrt(252))

        oos_sharpes.append(sr)
        oos_ics.append(ic)

        fold_details.append({
            "split_id": sp.split_id,
            "test_groups": list(sp.test_groups),
            "oos_sharpe": round(sr, 2),
            "oos_ic": round(ic, 4),
            "train_samples": int(valid_tr.sum()),
            "test_samples": int(valid_te.sum())
        })

    return {
        "n_splits": len(splits),
        "evaluated_splits": len(oos_sharpes),
        "mean_oos_sharpe": round(float(np.mean(oos_sharpes)), 2) if oos_sharpes else 0.0,
        "std_oos_sharpe": round(float(np.std(oos_sharpes, ddof=1)), 2) if len(oos_sharpes) > 1 else 0.0,
        "mean_oos_ic": round(float(np.mean(oos_ics)), 4) if oos_ics else 0.0,
        "positive_oos_ratio": round(float(np.mean(np.array(oos_sharpes) > 0)), 2) if oos_sharpes else 0.0,
        "splits": fold_details
    }

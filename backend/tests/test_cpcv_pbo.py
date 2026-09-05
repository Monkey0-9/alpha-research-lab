"""
Unit and Integration Tests for CPCV (Combinatorial Purged CV) and PBO (Probability of Backtest Overfitting).
"""
import numpy as np
import pandas as pd

from core.cpcv import CombinatorialPurgedCV
from core.pbo import compute_pbo


def test_cpcv_combinatorial_splits():
    """Verify C(6, 2) = 15 splits with strictly disjoint train/test and active purge/embargo."""
    n_days = 300
    dates = pd.date_range("2022-01-01", periods=n_days, freq="B")

    cpcv = CombinatorialPurgedCV(n_groups=6, k_test=2, purge_window=10, embargo_window=5)
    assert cpcv.get_num_splits() == 15

    splits = cpcv.split(dates)
    assert len(splits) == 15

    for sp in splits:
        train_set = set(sp.train_indices)
        test_set = set(sp.test_indices)
        # 1. No overlap between train and test
        assert len(train_set.intersection(test_set)) == 0
        # 2. Both train and test are non-empty
        assert len(train_set) > 0
        assert len(test_set) > 0
        # 3. Purged and embargoed samples exist
        assert sp.purged_count > 0 or sp.embargo_count > 0


def test_pbo_low_overfitting_on_persistent_signal():
    """When a real signal exists, IS winners reliably outperform OOS, leading to low PBO."""
    np.random.seed(42)
    n_splits = 20
    n_candidates = 15

    # Strategy 0 is a truly superior strategy across all splits
    base_oos = np.random.normal(0.0, 0.2, (n_splits, n_candidates))
    base_is = np.random.normal(0.0, 0.2, (n_splits, n_candidates))

    # Plant strong alpha in candidate 0
    base_is[:, 0] += 2.0
    base_oos[:, 0] += 1.8

    res = compute_pbo(base_is, base_oos, n_trials=n_candidates)
    assert res["pbo"] <= 0.10
    assert res["is_overfit"] is False
    assert "LOW_OVERFITTING" in res["interpretation"]


def test_pbo_high_overfitting_on_pure_noise():
    """When candidates are pure random noise, IS winner selection suffers severe overfitting."""
    np.random.seed(123)
    n_splits = 50
    n_candidates = 30

    # Completely independent noise between IS and OOS
    noise_is = np.random.normal(0.5, 0.5, (n_splits, n_candidates))
    noise_oos = np.random.normal(0.0, 0.5, (n_splits, n_candidates))

    res = compute_pbo(noise_is, noise_oos, n_trials=n_candidates)
    # With pure noise, in-sample winner should underperform median OOS roughly half the time or more
    assert res["pbo"] >= 0.40
    assert res["is_overfit"] is True

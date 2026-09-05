"""
Tests for core.validation
Validates temporal ordering in walk-forward and purge/embargo isolation in Purged K-Fold.
"""
import pandas as pd
import pytest
from core.validation import walk_forward_cv, purged_kfold_cv


def test_walk_forward_temporal_order():
    folds = walk_forward_cv(n_folds=12)
    assert len(folds) > 0
    for i, fold in enumerate(folds):
        assert fold.train_end < fold.test_start
        if i > 0:
            assert fold.train_start <= folds[i - 1].train_start or fold.train_end > folds[i - 1].train_end


def test_purged_cv_has_gaps():
    folds = purged_kfold_cv(n_splits=5)
    if len(folds) == 0:
        # Insufficient data — purged_kfold_cv returns empty instead of synthetic results
        pytest.skip("Insufficient data for purged K-fold CV")
    for fold in folds:
        assert fold.purge_start < fold.test_start
        assert fold.embargo_end > fold.test_end

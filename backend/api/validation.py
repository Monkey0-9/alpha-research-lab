"""
Validation API Router.
Endpoints:
- GET /api/validation/walk-forward: 12-fold walk-forward cross-validation with embargo
- GET /api/validation/purged-kfold: Purged K-Fold validation
- GET /api/validation/regime-tests: Performance breakdown by market regime
"""
from __future__ import annotations

from fastapi import APIRouter, Query
from core.validation import validator
from core.regime import regime_engine

router = APIRouter()


@router.get("/walk-forward")
def get_walk_forward(model_type: str = Query("lightgbm", description="Model architecture")):
    """
    12-fold walk-forward cross-validation.
    Expanding train window, fixed test window, 1-month embargo.
    """
    res = validator.run_walk_forward(num_folds=12, model_type=model_type)
    return res


@router.get("/purged-kfold")
def get_purged_kfold():
    """
    Purged K-Fold CV removing overlapping return periods.
    """
    return validator.run_purged_kfold(n_splits=5, purge_window=21, embargo=5)


@router.get("/regime-tests")
def get_regime_tests():
    """
    Strategy performance partitioned across Low-Vol, High-Vol, and Crisis regimes.
    """
    results = regime_engine.test_robustness()
    return {
        "regimes_tested": len(results),
        "results": results
    }

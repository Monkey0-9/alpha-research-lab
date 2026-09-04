"""
Tests for core.models and ensemble
Validates ML model training, out-of-sample evaluation, and ensemble weighting.
"""
import numpy as np
import pytest
from core.models import ModelTrainer
from core.ensemble import ensemble_engine


def test_model_trainer_pipeline():
    trainer = ModelTrainer()
    X = np.random.normal(0, 1, (200, 10))
    y = X[:, 0] * 0.4 + X[:, 1] * 0.2 + np.random.normal(0, 0.1, 200)

    ridge = trainer.train_ridge(X[:150], y[:150])
    assert ridge is not None

    preds = ridge.predict(X[150:])
    assert len(preds) == 50

    lgb_model = trainer.train_lightgbm(X[:150], y[:150])
    assert lgb_model is not None


def test_ensemble_comparison_leaderboard():
    comp = ensemble_engine.run_comparison()
    assert "models" in comp
    assert len(comp["models"]) >= 4
    for m in comp["models"]:
        assert "sharpe" in m
        assert "ic" in m

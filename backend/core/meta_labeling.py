"""
Meta-Labeling System (López de Prado Architecture).

Two-Stage Decision Pipeline:
- Primary Model: Predicts market direction (Sign of return: +1 or -1).
- Secondary Meta-Model: Predicts probability that the primary model is CORRECT.
- Execution Rule: Only execute trades when secondary model confidence > 0.60.
Maximizes precision, eliminates low-conviction churn, and reduces turnover.
"""
from __future__ import annotations

from typing import Dict, Any, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import lightgbm as lgb


class MetaLabelingSystem:
    def __init__(self, confidence_threshold: float = 0.60):
        self.threshold = confidence_threshold
        self.primary_model = lgb.LGBMRegressor(n_estimators=40, max_depth=3, learning_rate=0.03, random_state=42, verbose=-1)
        self.meta_classifier = RandomForestClassifier(n_estimators=40, max_depth=3, random_state=42)

    def fit(self, X: np.ndarray, returns: np.ndarray):
        """
        Fit primary model on returns, then construct meta-labels:
        meta_label = 1 if sign(primary_pred) == sign(actual_return) else 0.
        """
        self.primary_model.fit(X, returns)
        primary_preds = self.primary_model.predict(X)
        primary_direction = np.sign(primary_preds)

        actual_direction = np.sign(returns)
        # Binary target for secondary model: was the primary prediction correct?
        meta_y = (primary_direction == actual_direction).astype(int)

        # Train secondary model on features to predict success probability
        self.meta_classifier.fit(X, meta_y)

    def generate_signals(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Generate filtered high-conviction signals.
        """
        primary_preds = self.primary_model.predict(X)
        primary_direction = np.sign(primary_preds)

        # Meta-probabilities that primary is correct
        prob_correct = self.meta_classifier.predict_proba(X)[:, 1]

        # Execute only if confidence > threshold
        filtered_signals = np.where(prob_correct >= self.threshold, primary_direction, 0.0)
        filtered_sizes = np.where(prob_correct >= self.threshold, prob_correct, 0.0)

        trade_fraction = float(np.mean(filtered_signals != 0.0))
        mean_confidence = float(np.mean(prob_correct))

        return {
            "primary_direction": primary_direction.tolist(),
            "confidence_probabilities": prob_correct.tolist(),
            "filtered_signals": filtered_signals.tolist(),
            "trade_execution_rate": round(trade_fraction, 3),
            "average_confidence": round(mean_confidence, 3),
            "confidence_threshold": self.threshold
        }

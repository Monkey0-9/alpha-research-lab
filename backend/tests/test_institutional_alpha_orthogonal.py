"""
Institutional Alpha DSL, Evaluator, Orthogonalization & Multi-Testing Test Suite (Sprint 3).
Validates:
1. Alpha DSL extended operator AST parsing and type checking.
2. Vectorized AlphaEvaluator on panel data matrices across multiple assets and dates.
3. Alpha orthogonalization and Gram-Schmidt projection against active alpha books.
4. AlphaBookManager collinear candidate rejection (|rho| > 0.40) and residual admission.
5. Hansen's Superior Predictive Ability (SPA) and White's Reality Check multiple testing.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from core.alpha_dsl import AlphaParser, AlphaEvaluator, OpType, DslType
from core.alpha_orthogonalization import (
    orthogonalize_alpha,
    gram_schmidt_orthogonalize_book,
    AlphaBookManager,
)
from core.statistics import hansens_spa_test


@pytest.fixture
def sample_market_panel():
    """Generates clean panel data fixture with 5 tickers and 50 trading days."""
    dates = pd.date_range("2023-01-01", periods=50, freq="B")
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA"]

    rng = np.random.default_rng(42)
    close_data = 100.0 + np.cumsum(rng.normal(0.05, 1.0, size=(50, 5)), axis=0)
    open_data = close_data - rng.normal(0, 0.5, size=(50, 5))
    high_data = np.maximum(close_data, open_data) + rng.uniform(0.1, 1.0, size=(50, 5))
    low_data = np.minimum(close_data, open_data) - rng.uniform(0.1, 1.0, size=(50, 5))
    volume_data = rng.uniform(500000, 2000000, size=(50, 5))

    return {
        "open": pd.DataFrame(open_data, index=dates, columns=tickers),
        "high": pd.DataFrame(high_data, index=dates, columns=tickers),
        "low": pd.DataFrame(low_data, index=dates, columns=tickers),
        "close": pd.DataFrame(close_data, index=dates, columns=tickers),
        "volume": pd.DataFrame(volume_data, index=dates, columns=tickers),
    }


def test_extended_alpha_dsl_parsing():
    expr = "CS_RANK(TS_DECAY_LINEAR(close, 10))"
    ast = AlphaParser.parse(expr)
    assert ast.op == OpType.CS_RANK
    assert ast.node_type == DslType.PANEL
    assert ast.canonical_str() == "CS_RANK(TS_DECAY_LINEAR(close,10))"

    expr2 = "SIGNED_POWER(TS_ZSCORE(volume, 20), 0.5)"
    ast2 = AlphaParser.parse(expr2)
    assert ast2.op == OpType.SIGNED_POWER
    assert ast2.node_type == DslType.PANEL


def test_alpha_evaluator_panel_computation(sample_market_panel):
    expr = "CS_RANK(TS_DELTA(close, 5))"
    res = AlphaEvaluator.evaluate(expr, sample_market_panel)

    assert isinstance(res, pd.DataFrame)
    assert res.shape == (50, 5)
    # Cross-sectional ranks centered at 0 must lie within [-0.5, 0.5]
    valid_rows = res.dropna()
    assert len(valid_rows) > 0
    assert np.all(valid_rows.values >= -0.5001)
    assert np.all(valid_rows.values <= 0.5001)


def test_alpha_orthogonalization_linear_projection():
    np.random.seed(42)
    n = 200
    base_alpha1 = np.random.normal(0, 1, n)
    base_alpha2 = np.random.normal(0, 1, n)
    existing = np.column_stack([base_alpha1, base_alpha2])

    # Candidate 1: Highly collinear with base_alpha1 (rho ~ 0.85)
    collinear_candidate = 0.85 * base_alpha1 + 0.15 * np.random.normal(0, 1, n)
    diag1 = orthogonalize_alpha(collinear_candidate, existing, max_correlation_threshold=0.40)

    assert not diag1["is_orthogonal"], "Collinear candidate must be flagged as non-orthogonal"
    assert diag1["max_correlation"] > 0.70
    assert diag1["r_squared"] > 0.50
    assert "residual_signal" in diag1

    # Candidate 2: Truly independent orthogonal alpha
    independent_candidate = np.random.normal(0, 1, n)
    diag2 = orthogonalize_alpha(independent_candidate, existing, max_correlation_threshold=0.40)

    assert diag2["is_orthogonal"], "Independent candidate must pass orthogonality"
    assert diag2["max_correlation"] < 0.40


def test_alpha_book_manager_workflow():
    np.random.seed(42)
    n = 300
    fwd_returns = np.random.normal(0.001, 0.02, n)

    # Signal 1 has real predictive power
    alpha1 = fwd_returns + np.random.normal(0, 0.02, n)

    manager = AlphaBookManager(max_correlation_threshold=0.40, min_residual_t_stat=1.8)

    # 1. First alpha is admitted
    res1 = manager.add_alpha("Alpha_Momentum", alpha1, forward_returns=fwd_returns)
    assert res1["decision"] == "ACCEPTED_RAW"
    assert manager.num_alphas == 1

    # 2. Add an almost identical duplicate (rho ~ 0.95) with no extra information
    duplicate_alpha = alpha1 + np.random.normal(0, 0.002, n)
    res2 = manager.add_alpha("Alpha_Dup", duplicate_alpha, forward_returns=fwd_returns)
    assert res2["decision"] in {"REJECTED_NO_INCREMENTAL_VALUE", "REJECTED_COLLINEAR"}
    assert manager.num_alphas == 1

    # 3. Add orthogonal alpha with genuine independent signal
    independent_noise = np.random.normal(0, 0.02, n)
    independent_alpha = fwd_returns + independent_noise - \
        (np.corrcoef(fwd_returns + independent_noise, alpha1)[0, 1] * alpha1)
    res3 = manager.add_alpha("Alpha_Reversal", independent_alpha, forward_returns=fwd_returns)
    assert res3["decision"] in {"ACCEPTED_RAW", "ACCEPTED_RESIDUAL"}
    assert manager.num_alphas == 2


def test_gram_schmidt_orthogonalize_book():
    np.random.seed(42)
    n = 100
    x1 = np.random.normal(0, 1, n)
    x2 = 0.5 * x1 + 0.5 * np.random.normal(0, 1, n)
    x3 = 0.3 * x1 + 0.4 * x2 + 0.5 * np.random.normal(0, 1, n)

    signals = np.column_stack([x1, x2, x3])
    names = ["Alpha1", "Alpha2", "Alpha3"]

    ortho_matrix, surviving = gram_schmidt_orthogonalize_book(signals, names)

    assert ortho_matrix.shape == (n, 3)
    assert len(surviving) == 3

    # Verify that the resulting columns are mutually orthogonal: dot products ~ 0
    c01 = np.dot(ortho_matrix[:, 0], ortho_matrix[:, 1])
    c02 = np.dot(ortho_matrix[:, 0], ortho_matrix[:, 2])
    c12 = np.dot(ortho_matrix[:, 1], ortho_matrix[:, 2])
    assert abs(c01) < 1e-6
    assert abs(c02) < 1e-6
    assert abs(c12) < 1e-6


def test_hansens_spa_test():
    np.random.seed(42)
    n_days = 250
    n_models = 20

    # 19 pure noise trading models + 1 truly profitable model
    excess_returns = np.random.normal(0.0, 0.01, size=(n_days, n_models))
    excess_returns[:, 5] += 0.003  # Model 5 has true positive edge

    res = hansens_spa_test(
        candidate_excess_returns=excess_returns,
        mean_block_size=5,
        n_bootstraps=300,
        seed=42,
    )

    assert res["status"] == "SUCCESS"
    assert res["best_model_index"] == 5, "Hansen SPA must identify model 5 as the best performing rule"
    assert res["t_stat"] > 1.5
    assert "p_value_spa" in res
    assert "p_value_white" in res
    assert res["p_value_spa"] <= res["p_value_white"] + 1e-6, "Consistent SPA p-value is less conservative than White"

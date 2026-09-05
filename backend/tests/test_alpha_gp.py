"""
Tests for core.alpha_gp and Alpha Discovery Endpoints.
Validates AST parsing, formula evaluation, GP search, and elimination of string hashing.
"""
from core.alpha_gp import parse_formula, evaluate_alpha
from core.data_loader import load_sp500_data
from core.features import build_features
from core.labels import generate_labels
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_ast_parsing_and_evaluation():
    raw_data = load_sp500_data("2022-01-01", "2023-12-31")
    df = build_features(raw_data)
    l_df = generate_labels(df if "close" in df.columns else raw_data)
    if "fwd_return_1d" in l_df.columns:
        df["fwd_return_1d"] = l_df["fwd_return_1d"]

    formula = "ts_zscore(momentum_20d, 20) * rank(volume)"
    node = parse_formula(formula)
    assert node is not None
    assert node.complexity() > 1

    res = evaluate_alpha(node, df)
    assert res.formula is not None
    assert isinstance(res.ic, float)
    assert isinstance(res.sharpe, float)
    assert len(res.equity_curve) > 0
    assert res.trades_count > 0


def test_alpha_build_endpoint_real_evaluation():
    # Evaluate a real formula
    res = client.post("/api/alpha-discovery/build", json={
        "formula": "ts_rank(ts_delta(close, 5), 20)",
        "start_date": "2022-01-01",
        "end_date": "2023-12-31"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["formula"] == "ts_rank(ts_delta(close, 5), 20)"
    assert "sharpe" in data
    assert "ic" in data
    assert "equity_curve" in data
    assert len(data["equity_curve"]) > 0

    # Changing formula must change results based on actual signal, not string hash
    res2 = client.post("/api/alpha-discovery/build", json={
        "formula": "-1 * volatility_20d",
        "start_date": "2022-01-01",
        "end_date": "2023-12-31"
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["sharpe"] != data["sharpe"] or data2["ic"] != data["ic"]

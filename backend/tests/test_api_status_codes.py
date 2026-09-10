"""
Universal API HTTP Status-Code & Fail-Closed Integrity Suite.

Institutionally enforces that computational endpoints never hide failure
inside an HTTP 200 success code:
- Valid computation + data available -> HTTP 2xx
- Invalid schema / validation error   -> HTTP 422 Unprocessable Entity
- Missing / nonexistent data         -> HTTP 4xx (422 / 404)
- Solver failure / unhandled error   -> HTTP 5xx
- NEVER: HTTP 200 {"status": "NO_DATA"} or {"status": "ERROR"}
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def assert_never_hides_failure_in_200(response):
    """Universal institutional assertion: 200 MUST NOT contain error/no_data payloads."""
    if response.status_code == 200:
        data = response.json()
        if isinstance(data, dict):
            status = str(data.get("status", "")).upper()
            assert status not in ("NO_DATA", "ERROR", "INSUFFICIENT_DATA", "FAILED"), (
                f"Violation: Endpoint hidden failure in HTTP 200! Body: {data}"
            )


# ==============================================================================
# 1. Portfolio Convex Optimization (/api/portfolio/convex-optimize)
# ==============================================================================

def test_convex_optimize_valid_input_returns_200():
    """Valid inputs with available tickers must return HTTP 200 with status OPTIMAL."""
    payload = {
        "tickers": ["AAPL", "MSFT", "GOOGL", "AMZN"],
        "target_net_leverage": 0.0,
        "gross_leverage_limit": 1.5,
        "max_position_weight": 0.35,
        "turnover_budget": 0.25,
        "risk_aversion": 1.0,
    }
    res = client.post("/api/portfolio/convex-optimize", json=payload)
    assert res.status_code == 200
    assert_never_hides_failure_in_200(res)
    body = res.json()
    assert body["status"] == "OPTIMAL"
    assert "allocations" in body


def test_convex_optimize_nonexistent_tickers_returns_422():
    """Missing or nonexistent tickers must return HTTP 422, NEVER HTTP 200 {"status": "NO_DATA"}."""
    payload = {
        "tickers": ["NONEXISTENT_XYZ_1", "NONEXISTENT_XYZ_2"],
        "target_net_leverage": 0.0,
    }
    res = client.post("/api/portfolio/convex-optimize", json=payload)
    # Must reject with 422 Unprocessable Entity
    assert res.status_code == 422, f"Expected 422 on nonexistent data, got {res.status_code}: {res.text}"
    detail = res.json().get("detail", {})
    assert detail.get("code") == "UNIVERSE_DATA_UNAVAILABLE" or "UNIVERSE_DATA_UNAVAILABLE" in str(detail)


def test_convex_optimize_invalid_schema_returns_422():
    """Malformed payload fields must return HTTP 422 validation error."""
    payload = {
        "gross_leverage_limit": "INVALID_STRING_NOT_FLOAT",
    }
    res = client.post("/api/portfolio/convex-optimize", json=payload)
    assert res.status_code == 422


# ==============================================================================
# 2. Portfolio Standard Optimization (/api/portfolio/optimize)
# ==============================================================================

def test_portfolio_optimize_valid_tickers_returns_200():
    """Standard optimizer with real tickers returns HTTP 200 with non-zero allocations."""
    payload = {
        "method": "hrp",
        "tickers": ["AAPL", "MSFT", "GOOGL"],
    }
    res = client.post("/api/portfolio/optimize", json=payload)
    assert res.status_code == 200
    assert_never_hides_failure_in_200(res)
    body = res.json()
    assert len(body["allocations"]) == 3


def test_portfolio_optimize_nonexistent_tickers_returns_422():
    """Optimizer with missing tickers must return HTTP 422 instead of silent zero allocations."""
    payload = {
        "method": "mv",
        "tickers": ["FAKE_TICKER_1", "FAKE_TICKER_2"],
    }
    res = client.post("/api/portfolio/optimize", json=payload)
    assert res.status_code == 422
    detail = res.json().get("detail", {})
    assert detail.get("code") == "UNIVERSE_DATA_UNAVAILABLE" or "UNIVERSE_DATA_UNAVAILABLE" in str(detail)


# ==============================================================================
# 3. Alpha Discovery AST Build (/api/alpha-discovery/build)
# ==============================================================================

def test_alpha_build_valid_formula_returns_200():
    """Valid formula returns 200 with computed backtest metrics."""
    payload = {
        "formula": "ts_rank(momentum_20d, 60)",
    }
    res = client.post("/api/alpha-discovery/build", json=payload)
    assert res.status_code == 200
    assert_never_hides_failure_in_200(res)
    body = res.json()
    assert "sharpe" in body
    assert isinstance(body["sharpe"], (int, float))


def test_alpha_build_syntax_error_returns_422():
    """Malformed formula syntax must return HTTP 422, not 200 or unhandled 500."""
    payload = {
        "formula": "ts_rank(((((broken_syntax",
    }
    res = client.post("/api/alpha-discovery/build", json=payload)
    assert res.status_code == 422
    assert "Formula parsing or evaluation failed" in res.json().get("detail", "")


# ==============================================================================
# 4. Statistical Engine Deflated Sharpe Ratio (/api/statistical-engine/dsr)
# ==============================================================================

def test_dsr_valid_input_returns_200():
    """Valid DSR request returns HTTP 200."""
    payload = {
        "sharpe": 2.1,
        "n_trials": 100,
    }
    res = client.post("/api/statistical-engine/dsr", json=payload)
    assert res.status_code == 200
    assert_never_hides_failure_in_200(res)


def test_dsr_invalid_schema_returns_422():
    """Invalid data type for trials returns HTTP 422."""
    payload = {
        "sharpe": "NOT_A_NUMBER",
        "n_trials": "INVALID",
    }
    res = client.post("/api/statistical-engine/dsr", json=payload)
    assert res.status_code == 422


# ==============================================================================
# 5. Risk Compliance Check (/api/risk/compliance-check)
# ==============================================================================

def test_compliance_check_valid_returns_200():
    """Valid compliance check request returns HTTP 200."""
    payload = {
        "gross_leverage": 1.6,
        "max_single_weight": 0.12,
        "short_enabled": True,
    }
    res = client.post("/api/risk/compliance-check", json=payload)
    assert res.status_code == 200
    assert_never_hides_failure_in_200(res)


def test_compliance_check_invalid_schema_returns_422():
    """Malformed compliance check request returns HTTP 422."""
    payload = {
        "gross_leverage": "EXCESSIVE_STRING",
    }
    res = client.post("/api/risk/compliance-check", json=payload)
    assert res.status_code == 422


# ==============================================================================
# 6. Universal Fail-Closed Verification across Core Endpoints
# ==============================================================================

@pytest.mark.parametrize("endpoint", [
    "/api/portfolio/frontier",
    "/api/portfolio/shrinkage-compare",
    "/api/portfolio/holdings",
    "/api/features/list",
    "/api/validation/splits",
    "/api/dashboard/summary",
    "/api/risk/var",
    "/api/monitoring/telemetry",
    "/api/data/sources",
    "/api/data/quality",
    "/api/alpha-discovery/hypotheses",
    "/api/model-lab/comparison",
])
def test_endpoints_never_return_hidden_failure_status(endpoint):
    """None of the production core endpoints may return HTTP 200 with error payloads."""
    res = client.get(endpoint)
    if res.status_code == 200:
        assert_never_hides_failure_in_200(res)


# ==============================================================================
# 7. Parameterized Computational Post Endpoints Matrix
# ==============================================================================

COMPUTATIONAL_POST_MATRIX = [
    # (endpoint, valid_payload, malformed_payload)
    (
        "/api/portfolio/convex-optimize",
        {"tickers": ["AAPL", "MSFT", "GOOGL"], "gross_leverage_limit": 1.5},
        {"gross_leverage_limit": "INVALID_STRING"}
    ),
    (
        "/api/portfolio/optimize",
        {"method": "hrp", "tickers": ["AAPL", "MSFT", "GOOGL"]},
        {"method": 12345, "tickers": "NOT_A_LIST"}
    ),
    (
        "/api/alpha-discovery/build",
        {"formula": "ts_rank(momentum_20d, 20)"},
        {"formula": "broken((((syntax"}
    ),
    (
        "/api/statistical-engine/dsr",
        {"sharpe": 1.85, "n_trials": 50},
        {"sharpe": "INVALID"}
    ),
    (
        "/api/risk/compliance-check",
        {"gross_leverage": 1.5, "max_single_weight": 0.15},
        {"gross_leverage": "MALFORMED"}
    ),
    (
        "/api/data/pit",
        {"ticker": "AAPL", "as_of_date": "2024-01-01"},
        {"as_of_date": 12345}
    ),
    (
        "/api/statistical/cpcv",
        {"n_splits": 6, "n_test_splits": 2},
        {"n_splits": "NOT_AN_INT"}
    ),
    (
        "/api/statistical/pbo",
        {"n_candidates": 16, "n_partitions": 8},
        {"n_candidates": "INVALID"}
    ),
    (
        "/api/statistical/spa",
        {"n_benchmarks": 10, "n_samples": 252},
        {"n_benchmarks": "NOT_AN_INT"}
    ),
    (
        "/api/statistical/evidence-card",
        {"alpha_id": "ALPHA-001", "name": "Momentum Alpha", "formula": "ts_rank(momentum_20d, 20)"},
        {"formula": {"invalid_nested": "dict_not_str"}}
    ),
    (
        "/api/execution/cpp-backtest",
        {"n_bars": 100, "initial_cash": 500000.0},
        {"n_bars": "INVALID_INT"}
    ),
    (
        "/api/native/c/kalman",
        {"observations": [100.0, 101.0, 100.5], "q_process_noise": 0.01},
        {"observations": "NOT_A_LIST"}
    ),
    (
        "/api/native/c/hurst",
        {"prices": [100.0, 101.0, 102.0, 101.5, 103.0, 102.5] * 10, "window": 30},
        {"prices": "NOT_A_LIST"}
    ),
    (
        "/api/native/c/microprice",
        {"bid_prices": [100.0, 99.9], "bid_sizes": [500, 300], "ask_prices": [100.1, 100.2], "ask_sizes": [400, 200]},
        {"bid_prices": "INVALID"}
    ),
]


@pytest.mark.parametrize("endpoint,valid_payload,malformed_payload", COMPUTATIONAL_POST_MATRIX)
def test_computational_endpoint_matrix_status_codes(endpoint, valid_payload, malformed_payload):
    """
    Every computational endpoint must fulfill:
    1. Valid input -> HTTP 2xx, response never hides failure inside 200
    2. Malformed input -> HTTP 422 Unprocessable Entity
    """
    # 1. Test valid payload
    res_valid = client.post(endpoint, json=valid_payload)
    assert res_valid.status_code in (200, 201), (
        f"{endpoint} failed on valid payload: {res_valid.status_code} - {res_valid.text}"
    )
    assert_never_hides_failure_in_200(res_valid)

    # 2. Test malformed payload
    res_malformed = client.post(endpoint, json=malformed_payload)
    assert res_malformed.status_code == 422, (
        f"{endpoint} accepted malformed payload with HTTP {res_malformed.status_code} instead of 422!"
    )

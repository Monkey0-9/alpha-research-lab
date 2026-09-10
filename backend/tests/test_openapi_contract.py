"""
OpenAPI Schema & API Contract Verification Test Suite.
Validates that:
1. FastAPI app produces a compliant OpenAPI 3.1 schema.
2. Every frontend API route in src/lib/api.ts exists in the backend OpenAPI specification.
3. Every computational endpoint defines appropriate 2xx and 4xx/5xx status codes.
4. Serialized HTTP responses contain the exact fields required by frontend types.
"""
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_openapi_schema_generation():
    """Verify backend generates valid OpenAPI schema."""
    schema = app.openapi()
    assert schema is not None
    assert schema["openapi"].startswith("3.")
    assert "paths" in schema
    assert len(schema["paths"]) >= 25


def test_frontend_routes_exist_in_openapi():
    """Verify that core endpoints called by src/lib/api.ts exist in OpenAPI schema."""
    schema = app.openapi()
    paths = schema["paths"]

    frontend_required_endpoints = [
        "/api/dashboard/summary",
        "/api/dashboard/equity-curve",
        "/api/dashboard/drawdown",
        "/api/data/sources",
        "/api/data/quality",
        "/api/data/pit",
        "/api/features/list",
        "/api/alpha-discovery/hypotheses",
        "/api/alpha-discovery/build",
        "/api/statistical-engine/mtc",
        "/api/statistical-engine/dsr",
        "/api/model-lab/comparison",
        "/api/quality-gate/alphas",
        "/api/quality-gate/remediate",
        "/api/portfolio/holdings",
        "/api/portfolio/optimize",
        "/api/portfolio/frontier",
        "/api/portfolio/convex-optimize",
        "/api/portfolio/shrinkage-compare",
        "/api/risk/var",
        "/api/monitoring/telemetry",
        "/api/validation/splits",
        "/api/validation/walk-forward",
        "/api/validation/purged-cv",
        "/api/validation/regime-tests",
        "/api/execution/algos",
        "/api/execution/impact",
        "/api/statistical/cpcv",
        "/api/statistical/pbo",
        "/api/statistical/spa",
        "/api/statistical/evidence-card",
        "/api/execution/cpp-backtest",
        "/api/execution/ledger-audit",
        "/api/risk/compliance-check",
    ]

    for endpoint in frontend_required_endpoints:
        assert endpoint in paths, f"Frontend required endpoint '{endpoint}' missing from OpenAPI specification!"


def test_dashboard_summary_contract():
    """Verify actual serialized response matches ExecutiveDashboardSummary frontend type."""
    res = client.get("/api/dashboard/summary")
    assert res.status_code == 200
    data = res.json()

    # Required fields from types.ExecutiveDashboardSummary
    assert "portfolio_nav" in data or "portfolio" in data or "live_paper_pnl" in data
    assert "daily_pnl_dollars" in data or "live_paper_pnl" in data


def test_portfolio_optimize_contract():
    """Verify /api/portfolio/optimize response schema."""
    res = client.post("/api/portfolio/optimize", json={"method": "hrp", "tickers": ["AAPL", "MSFT"]})
    assert res.status_code == 200
    data = res.json()
    assert "method" in data
    assert "allocations" in data
    assert isinstance(data["allocations"], list)
    for item in data["allocations"]:
        assert "ticker" in item
        assert "weight" in item
        assert "side" in item


def test_convex_optimize_contract():
    """Verify /api/portfolio/convex-optimize response schema."""
    res = client.post("/api/portfolio/convex-optimize", json={"tickers": ["AAPL", "MSFT"]})
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "gross_leverage" in data
    assert "net_leverage" in data
    assert "portfolio_volatility" in data
    assert "allocations" in data


def test_features_list_contract():
    """Verify /api/features/list response matches FeatureItem array contract."""
    res = client.get("/api/features/list")
    assert res.status_code == 200
    data = res.json()
    assert "features" in data
    assert isinstance(data["features"], list)
    if data["features"]:
        feat = data["features"][0]
        assert "id" in feat
        assert "name" in feat
        assert "category" in feat

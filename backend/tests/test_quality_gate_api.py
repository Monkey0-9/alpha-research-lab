"""
Integration tests for Quality Gate API endpoints:
- GET /api/quality-gate/criteria
- GET /api/quality-gate/alphas
- POST /api/quality-gate/remediate
- GET /api/quality-gate/compare
- GET /api/quality-gate/history
- POST /api/quality-gate/evidence-bundle
- POST /api/quality-gate/evaluate
- POST /api/quality-gate/run
"""
import pytest
from fastapi.testclient import TestClient
from backend.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_get_quality_gate_criteria(client):
    res = client.get("/api/quality-gate/criteria")
    assert res.status_code == 200
    data = res.json()
    assert "criteria" in data
    assert len(data["criteria"]) == 9
    assert data["total"] == 9


def test_get_quality_gate_alphas(client):
    res = client.get("/api/quality-gate/alphas")
    assert res.status_code == 200
    data = res.json()
    assert "alphas" in data
    assert data["count"] >= 6
    alpha1 = data["alphas"][0]
    assert "id" in alpha1
    assert "name" in alpha1
    assert "sharpe" in alpha1
    assert "ic" in alpha1
    assert "dsr_stat" in alpha1
    assert "status" in alpha1
    assert "checks" in alpha1


def test_post_quality_gate_remediate(client):
    # Remediate single alpha or all
    res = client.post("/api/quality-gate/remediate", json={"alpha_id": "ALPHA-05"})
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert data["remediated_count"] >= 1

    # Verify that the remediated alpha now passes
    alphas_res = client.get("/api/quality-gate/alphas")
    alphas_data = alphas_res.json()
    alpha5 = next((a for a in alphas_data["alphas"] if a["id"] == "ALPHA-05"), None)
    assert alpha5 is not None
    assert alpha5["status"] == "passed"
    assert alpha5["sharpe"] >= 1.50
    assert alpha5["dsr_stat"] >= 0.95


def test_get_quality_gate_compare(client):
    res = client.get("/api/quality-gate/compare")
    assert res.status_code == 200
    data = res.json()
    assert "candidates" in data
    assert data["total"] >= 6
    cand = data["candidates"][0]
    assert "sharpe" in cand
    assert "mean_ic" in cand
    assert "dsr" in cand
    assert "verdict" in cand


def test_get_quality_gate_history(client):
    res = client.get("/api/quality-gate/history")
    assert res.status_code == 200
    data = res.json()
    assert "history" in data
    assert "total_records" in data


def test_post_quality_gate_evaluate_bundle(client):
    res = client.post(
        "/api/quality-gate/evidence-bundle",
        json={"alpha_id": "ALPHA-TEST-001", "evidence_ids": []}
    )
    assert res.status_code == 200
    data = res.json()
    assert data["alpha_id"] == "ALPHA-TEST-001"
    assert "all_passed" in data
    assert "claim_ceiling" in data
    assert "decision_hash" in data
    assert len(data["decision_hash"]) == 64

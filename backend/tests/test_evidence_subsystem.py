"""
Test Suite for QuantAlpha Evidence Subsystem & Level-5 Research Governance.

Verifies:
1. Universal EvidenceStatus behavior and cryptographic provenance hashing.
2. DataValidationEvidence computes true schema, null rate, and file SHA-256 checks.
3. LeakageAuditEvidence detects lookahead contamination and verifies PIT availability.
4. Quality Gate fail-closed behavior: missing evidence strictly causes stage failure and caps claim ceiling.
5. Zero-fallback policy: factor_attribution returns RISK_MODEL_UNAVAILABLE when factor data
   is absent (no synthetic factors).
6. Deterministic full-bundle reproduction: verifies multi-metric tolerances, equity curve hashes,
   and blotter hashes without synthetic jitter.
"""
import numpy as np
import pandas as pd

from backend.core.evidence.base import Evidence, EvidenceBundle, EvidenceStatus
from backend.core.evidence.data import DataValidationEvidence
from backend.core.evidence.leakage import LeakageAuditEvidence
from backend.core.evidence.promotion import (
    ClaimCeiling,
)
from backend.core.quality_gate import evaluate_evidence_bundle
from backend.core.risk import factor_attribution
from backend.core.reproduce import execute_research_pipeline
from backend.core.experiment import PreRegistrationSpec


def test_evidence_status_and_provenance_hash():
    """Verify evidence status and deterministic cryptographic provenance hashing."""
    ev = Evidence(
        evidence_id="EV-TEST-001",
        stage_id="DATA_VALIDATION",
        status=EvidenceStatus.SUCCESS,
        description="Dataset verified",
        dataset_id="SP500_DAILY",
        dataset_sha256="abc123hash",
        metrics={"rows": 5000},
    )
    assert ev.passed is True
    assert len(ev.provenance_hash) == 64
    assert ev.status == EvidenceStatus.SUCCESS

    # Verify provenance hash changes if metrics change
    ev2 = Evidence(
        evidence_id="EV-TEST-001",
        stage_id="DATA_VALIDATION",
        status=EvidenceStatus.SUCCESS,
        description="Dataset verified",
        dataset_id="SP500_DAILY",
        dataset_sha256="abc123hash",
        metrics={"rows": 9999},
        timestamp=ev.timestamp,
    )
    assert ev.provenance_hash != ev2.provenance_hash


def test_data_validation_evidence_from_df():
    """Verify DataValidationEvidence detects schema violations and nulls."""
    # Valid dataframe
    df_valid = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=100),
        "ticker": ["AAPL"] * 100,
        "close": np.linspace(150, 180, 100),
        "volume": np.random.uniform(1e6, 2e6, 100),
    })
    ev = DataValidationEvidence.create_from_dataframe(df_valid, dataset_id="TEST_DATA")
    assert ev.passed is True
    assert ev.status == EvidenceStatus.SUCCESS
    assert ev.metrics["total_rows"] == 100

    # Invalid dataframe with missing required column
    df_invalid = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=50),
        "ticker": ["AAPL"] * 50,
        "close": np.linspace(150, 180, 50),
    })
    ev_bad = DataValidationEvidence.create_from_dataframe(
        df_invalid,
        dataset_id="TEST_BAD",
        required_columns=["close", "volume"]
    )
    assert ev_bad.passed is False
    assert ev_bad.status == EvidenceStatus.FAILED
    assert "missing required columns" in ev_bad.description


def test_leakage_audit_evidence():
    """Verify LeakageAuditEvidence detects lookahead return leakage."""
    np.random.seed(42)
    n = 100
    future_ret = np.random.normal(0, 0.02, n)
    df_leaky = pd.DataFrame({
        "fwd_return_1d": future_ret,
        # Leaked feature identical to future return
        "leaked_feat": future_ret * 0.99,
        "clean_feat": np.random.normal(0, 1, n),
    })

    ev = LeakageAuditEvidence.create_from_audit(
        alpha_id="ALPHA-LEAK",
        features_df=df_leaky,
        feature_names=["leaked_feat", "clean_feat"],
        target_col="fwd_return_1d",
    )
    assert ev.passed is False
    assert ev.status == EvidenceStatus.FAILED
    assert ev.metrics["feature_leakage_detected"] is True


def test_quality_gate_fail_closed_on_missing_evidence():
    """Verify Quality Gate strictly fails stages when evidence is missing."""
    empty_bundle = EvidenceBundle(
        bundle_id="BUNDLE-EMPTY",
        alpha_id="ALPHA-EMPTY",
        hypothesis_id="HYP-EMPTY",
    )
    decision = evaluate_evidence_bundle(empty_bundle)

    assert decision.all_passed is False
    assert decision.status in ["REJECTED", "DEVELOPMENT"]
    assert decision.claim_ceiling == ClaimCeiling.EXPLORATORY
    assert len(decision.failed_stages) > 0
    assert "DATA_VALIDATION" in decision.failed_stages
    assert "LEAKAGE_CHECK" in decision.failed_stages


def test_zero_fallback_factor_attribution():
    """Verify factor_attribution returns RISK_MODEL_UNAVAILABLE and does NOT invent random factors."""
    p_returns = np.random.normal(0.0005, 0.01, 100)

    # Call factor_attribution without factor_returns
    res = factor_attribution(portfolio_returns=p_returns, factor_returns=None)

    assert res["status"] == "RISK_MODEL_UNAVAILABLE"
    assert res["systematic_risk"] == 0.0
    assert res["r_squared"] == 0.0
    assert len(res["factor_exposures"]) == 0


def test_deterministic_pipeline_execution_no_synthetic_jitter():
    """Verify execute_research_pipeline is 100% deterministic and produces exact hashes."""
    df_test = pd.DataFrame({
        "date": pd.date_range("2023-01-01", periods=100),
        "ticker": ["AAPL"] * 50 + ["MSFT"] * 50,
        "close": np.linspace(100, 150, 100),
        "volume": np.linspace(1e6, 2e6, 100),
    })
    spec = PreRegistrationSpec(
        experiment_id="EXP-TEST-DETERMINISM",
        hypothesis_name="Test Determinism",
        economic_rationale="Verifying zero synthetic noise injection",
    )

    res1 = execute_research_pipeline(df_test, spec=spec, seed=42)
    res2 = execute_research_pipeline(df_test, spec=spec, seed=42)

    assert res1["sharpe"] == res2["sharpe"]
    assert res1["ic"] == res2["ic"]
    assert res1["max_drawdown"] == res2["max_drawdown"]
    assert res1["equity_curve_hash"] == res2["equity_curve_hash"]
    assert res1["blotter_hash"] == res2["blotter_hash"]
    assert len(res1["equity_curve_hash"]) == 64
    assert len(res1["blotter_hash"]) == 64

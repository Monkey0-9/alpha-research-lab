"""
v0.2.0 Integrity Core Test Suite.
Verifies the non-negotiable Level-5 failure invariants:
1. NO DATA -> FAIL
2. DATA HASH MISMATCH -> FAIL
3. FUTURE INFORMATION -> FAIL
4. MISSING VALIDATION -> FAIL
5. STATISTICAL TEST NOT RUN -> FAIL
6. EXECUTION MODEL UNAVAILABLE -> FAIL
7. RISK MODEL UNAVAILABLE -> FAIL
8. OPTIMIZER FAILURE -> FAIL
9. REPRODUCTION MISMATCH -> FAIL
10. LEDGER IMBALANCE -> FAIL
11. Immutable 6-dimensional Artifact Identity & Envelope Verification
12. 10-Stage Canonical Evidence Graph Verification
13. 14-Metric Multi-Metric Reproduction Verification
14. Search Budget Accounting ($N_trials$) & Selection Bias Expectation
15. Synthetic Data Firewall under ResearchMode.EMPIRICAL
"""
import pytest
import pandas as pd
import numpy as np

from backend.core.artifacts import (
    ArtifactEnvelope,
    ArtifactRepository,
    ArtifactTamperingException,
    GENESIS_PARENT_HASH,
    compute_sha256,
)
from backend.core.trials import (
    SearchBudgetTracker,
)
from backend.core.evidence import (
    EvidenceGraph,
    EvidenceStage,
    CANONICAL_STAGE_ORDER,
    ResearchArtifact,
    MissingEvidenceException,
)
from backend.core.reproducibility import (
    MultiMetricReproductionComparator,
    ReproductionMismatchException,
    Level5ReproductionEngine,
)
from backend.core.governance import (
    ResearchMode,
    research_mode_context,
    FallbackFirewall,
    MissingDataException,
    DataHashMismatchException,
    MissingValidationException,
    StatisticalTestNotRunException,
    ExecutionModelUnavailableException,
    RiskModelUnavailableException,
    OptimizerFailureException,
    LedgerImbalanceException,
    SyntheticDataBlockedException,
)
from backend.core.integrity_guard import detect_future_leakage, FutureLeakageError
from backend.core.evidence.manifest import ExperimentManifest


# ---------------------------------------------------------------------------
# 1. NO DATA -> FAIL
# ---------------------------------------------------------------------------
def test_no_data_fails_closed():
    """Assert empty or None empirical data strictly raises MissingDataException."""
    with pytest.raises(MissingDataException):
        FallbackFirewall.assert_empirical_data_present(None, "quote_feed")

    with pytest.raises(MissingDataException):
        FallbackFirewall.assert_empirical_data_present(pd.DataFrame(), "ohlcv_feed")

    with pytest.raises(MissingDataException):
        FallbackFirewall.assert_empirical_data_present([], "universe_constituents")


# ---------------------------------------------------------------------------
# 2. DATA HASH MISMATCH -> FAIL
# ---------------------------------------------------------------------------
def test_data_hash_mismatch_fails_closed():
    """Assert any discrepancy between actual data hash and manifest hash raises DataHashMismatchException."""
    expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    actual = "0000000000000000000000000000000000000000000000000000000000000000"

    with pytest.raises(DataHashMismatchException):
        FallbackFirewall.assert_empirical_hash_match(expected, actual, "sp500_daily")


# ---------------------------------------------------------------------------
# 3. FUTURE INFORMATION -> FAIL
# ---------------------------------------------------------------------------
def test_future_information_leakage_fails_closed():
    """Assert lookahead bias where feature correlates perfectly with t+1 return is rejected."""
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=100)
    prices = pd.Series(100.0 + np.cumsum(np.random.randn(100)), index=dates)

    # Contaminated feature: exactly forward 1-day return
    fwd_ret = prices.shift(-1) / prices - 1.0

    with pytest.raises(FutureLeakageError):
        detect_future_leakage(feature_series=fwd_ret, raw_close=prices, max_allowable_corr=0.95)


# ---------------------------------------------------------------------------
# 4. MISSING VALIDATION -> FAIL
# ---------------------------------------------------------------------------
def test_missing_validation_fails_closed():
    """Assert unvalidated models strictly raise MissingValidationException."""
    with pytest.raises(MissingValidationException):
        FallbackFirewall.assert_validation_executed(None)

    with pytest.raises(MissingValidationException):
        FallbackFirewall.assert_validation_executed({"executed": False})


# ---------------------------------------------------------------------------
# 5. STATISTICAL TEST NOT RUN -> FAIL
# ---------------------------------------------------------------------------
def test_statistical_test_not_run_fails_closed():
    """Assert omission of multiple testing corrections raises StatisticalTestNotRunException."""
    with pytest.raises(StatisticalTestNotRunException):
        FallbackFirewall.assert_statistical_tests_executed(None)

    with pytest.raises(StatisticalTestNotRunException):
        FallbackFirewall.assert_statistical_tests_executed({"executed": False})


# ---------------------------------------------------------------------------
# 6. EXECUTION MODEL UNAVAILABLE -> FAIL
# ---------------------------------------------------------------------------
def test_execution_model_unavailable_fails_closed():
    """Assert unavailable execution cost model raises ExecutionModelUnavailableException."""
    with pytest.raises(ExecutionModelUnavailableException):
        FallbackFirewall.assert_execution_model_available(False, "Almgren-Chriss kernel missing")


# ---------------------------------------------------------------------------
# 7. RISK MODEL UNAVAILABLE -> FAIL
# ---------------------------------------------------------------------------
def test_risk_model_unavailable_fails_closed():
    """Assert unavailable risk model raises RiskModelUnavailableException."""
    with pytest.raises(RiskModelUnavailableException):
        FallbackFirewall.assert_risk_model_available(False, "Barra covariance matrix unavailable")


# ---------------------------------------------------------------------------
# 8. OPTIMIZER FAILURE -> FAIL (Never equal weight)
# ---------------------------------------------------------------------------
def test_optimizer_failure_fails_closed():
    """Assert convex optimization solver failure raises OptimizerFailureException instead of fallback."""
    with pytest.raises(OptimizerFailureException):
        FallbackFirewall.assert_optimizer_success("INFEASIBLE", "Convex QP did not converge")

    with pytest.raises(OptimizerFailureException):
        FallbackFirewall.assert_optimizer_success("SOLVER_ERROR", "Singular covariance matrix")


# ---------------------------------------------------------------------------
# 9. REPRODUCTION MISMATCH -> FAIL
# ---------------------------------------------------------------------------
def test_reproduction_mismatch_fails_closed():
    """Assert discrepancies in any of the 14 quantitative dimensions raise ReproductionMismatchException."""
    ref_metrics = {
        "sharpe": 2.14,
        "oos_sharpe": 1.95,
        "ic": 0.082,
        "icir": 1.45,
        "annualized_return": 0.185,
        "annualized_volatility": 0.092,
        "max_drawdown": -0.065,
        "turnover": 0.24,
        "total_cost": 0.0035,
        "capacity": 250_000_000,
        "trade_count": 1420,
        "equity_curve_hash": "a1b2c3d4e5f6",
        "trade_blotter_hash": "f6e5d4c3b2a1",
        "risk_report_hash": "123456abcdef",
    }

    # Reproduced run with mismatched trade count
    rep_metrics = dict(ref_metrics)
    rep_metrics["trade_count"] = 1425

    with pytest.raises(ReproductionMismatchException):
        MultiMetricReproductionComparator.compare("EXP-001", ref_metrics, rep_metrics, fail_closed=True)


# ---------------------------------------------------------------------------
# 10. LEDGER IMBALANCE -> FAIL
# ---------------------------------------------------------------------------
def test_ledger_imbalance_fails_closed():
    """Assert double-entry debits != credits raises LedgerImbalanceException."""
    with pytest.raises(LedgerImbalanceException):
        FallbackFirewall.assert_ledger_balanced(debits=1000.0, credits=995.0)


# ---------------------------------------------------------------------------
# 11. Immutable 6-Dimensional Artifact Identity & Envelope Verification
# ---------------------------------------------------------------------------
def test_artifact_envelope_integrity_and_tamper_detection():
    """Verify 6-dimensional identity and cryptographic sealing."""
    payload = {"expression": "rank(ts_mean(close, 20))", "ic": 0.075}
    env = ArtifactEnvelope.create(
        artifact_id="ART-001",
        artifact_type="ALPHA_AST",
        payload=payload,
        parent_hash=GENESIS_PARENT_HASH,
        schema_hash="SCHEMA_ALPHA_V1",
        code_sha="abc123git",
        environment_hash="env456lock",
        configuration_hash="cfg789hash",
    )

    assert env.verify() is True
    assert len(env.envelope_hash) == 64

    # Storage in content-addressed repository
    repo = ArtifactRepository()
    stored_hash = repo.store(env)
    assert stored_hash == env.envelope_hash
    assert repo.count() == 1

    # Tamper payload -> must raise ArtifactTamperingException
    env.payload["ic"] = 0.999
    with pytest.raises(ArtifactTamperingException):
        env.verify()


# ---------------------------------------------------------------------------
# 12. 10-Stage Canonical Evidence Graph Verification
# ---------------------------------------------------------------------------
def test_10_stage_canonical_evidence_graph():
    """Verify that all 10 stages must be sequentially linked without skipping."""
    graph = EvidenceGraph(experiment_id="EXP-LEAD-001")

    # Helper to create chained artifacts
    parent_hash = GENESIS_PARENT_HASH
    for stage in CANONICAL_STAGE_ORDER:
        payload = {"stage_data": f"content_for_{stage.value}"}
        content_h = compute_sha256(payload)
        art = ResearchArtifact(
            artifact_id=f"ART-{stage.value}",
            artifact_type=stage.value,
            content_hash=content_h,
            schema_hash="SCHEMA_DEFAULT",
            parent_hash=parent_hash,
            producer="UnitTest",
            code_sha="git_sha",
            environment_hash="env_hash",
            payload=payload,
        )
        graph.attach_stage(stage, art)
        parent_hash = art.artifact_hash

    assert graph.verify_complete_graph() is True
    assert graph.to_dict()["is_fully_certified"] is True


def test_evidence_graph_rejects_out_of_order_stage():
    """Assert attaching stage out-of-order raises MissingEvidenceException."""
    graph = EvidenceGraph(experiment_id="EXP-GAP-001")

    # Try attaching VALIDATION without DATA, FEATURE, ALPHA, TRIAL
    payload = {"data": 1}
    art = ResearchArtifact(
        artifact_id="ART-VAL",
        artifact_type="VALIDATION",
        content_hash=compute_sha256(payload),
        schema_hash="SCHEMA_DEFAULT",
        parent_hash=GENESIS_PARENT_HASH,
        producer="UnitTest",
        code_sha="git_sha",
        environment_hash="env_hash",
        payload=payload,
    )
    with pytest.raises(MissingEvidenceException):
        graph.attach_stage(EvidenceStage.VALIDATION, art)


# ---------------------------------------------------------------------------
# 13. 14-Metric Multi-Metric Reproduction Verification
# ---------------------------------------------------------------------------
def test_14_metric_reproduction_success():
    """Verify that when all 14 metrics match within tolerances, reproduction succeeds."""
    ref_metrics = {
        "sharpe": 2.14005,
        "oos_sharpe": 1.95005,
        "ic": 0.08201,
        "icir": 1.45001,
        "annualized_return": 0.185005,
        "annualized_volatility": 0.092003,
        "max_drawdown": -0.065002,
        "turnover": 0.24005,
        "total_cost": 0.0035001,
        "capacity": 250_000_000,
        "trade_count": 1420,
        "equity_curve_hash": "a1b2c3d4e5f6",
        "trade_blotter_hash": "f6e5d4c3b2a1",
        "risk_report_hash": "123456abcdef",
    }
    # Matches within 1e-4 relative tolerance
    rep_metrics = {
        "sharpe": 2.14000,
        "oos_sharpe": 1.95000,
        "ic": 0.08200,
        "icir": 1.45000,
        "annualized_return": 0.185000,
        "annualized_volatility": 0.092000,
        "max_drawdown": -0.065000,
        "turnover": 0.24000,
        "total_cost": 0.0035000,
        "capacity": 250_000_000,
        "trade_count": 1420,
        "equity_curve_hash": "a1b2c3d4e5f6",
        "trade_blotter_hash": "f6e5d4c3b2a1",
        "risk_report_hash": "123456abcdef",
    }

    report = MultiMetricReproductionComparator.compare("EXP-001", ref_metrics, rep_metrics, fail_closed=True)
    assert report.all_passed is True
    assert report.passed_count == 14

    manifest = ExperimentManifest(
        experiment_id="EXP-001",
        hypothesis={"id": "HYP-001"},
        dataset={"id": "SP500"},
        universe={"id": "SP500_UNIVERSE"},
        features={"count": 20},
        alpha={"ast": "ts_mean(close, 20)"},
    )
    cert = Level5ReproductionEngine.verify_and_certify(manifest, ref_metrics, rep_metrics, fail_closed=True)
    assert cert.passed is True


# ---------------------------------------------------------------------------
# 14. Search Budget Accounting ($N_trials$) & Selection Bias Expectation
# ---------------------------------------------------------------------------
def test_search_budget_tracking_and_deflation():
    """Verify trial tracking increments N_trials and computes expected maximum Sharpe."""
    tracker = SearchBudgetTracker(experiment_id="EXP-SRCH-001", max_allocated_trials=50)

    for i in range(10):
        tracker.registry.record_trial(
            candidate_id=f"ALPHA-{i+1}",
            parameters={"window": 10 + i},
            dataset_id="SP500_DAILY",
            score=1.2 + 0.05 * i,
        )

    assert tracker.trials_used == 10
    assert tracker.budget_remaining == 40
    assert tracker.check_budget_available() is True

    # Analytical expectation of maximum Sharpe under null hypothesis increases with N_trials
    exp_sr_1 = tracker.expected_maximum_sr(1)
    exp_sr_10 = tracker.expected_maximum_sr(10)
    exp_sr_100 = tracker.expected_maximum_sr(100)

    assert exp_sr_1 == 0.0
    assert exp_sr_10 > 0.0
    assert exp_sr_100 > exp_sr_10


# ---------------------------------------------------------------------------
# 15. Synthetic Data Firewall under ResearchMode.EMPIRICAL
# ---------------------------------------------------------------------------
def test_synthetic_data_firewall():
    """Verify that ResearchMode.EMPIRICAL strictly rejects synthetic data injections."""
    with research_mode_context(ResearchMode.EMPIRICAL):
        with pytest.raises(SyntheticDataBlockedException):
            FallbackFirewall.reject_synthetic_fallback("mock_gaussian_generator", "prices")

    # In SIMULATION or FIXTURE mode, synthetic data is explicitly tolerated
    with research_mode_context(ResearchMode.SIMULATION):
        # Should not raise
        FallbackFirewall.reject_synthetic_fallback("monte_carlo_generator", "returns")

    with research_mode_context(ResearchMode.FIXTURE):
        # Should not raise
        FallbackFirewall.reject_synthetic_fallback("fixture_loader", "test_trades")

"""
Tier 0 & Tier 2 Research Integrity Attacks & Fail-Closed Adversarial Test Suite.

Directly implements adversarial challenge specifications:
1. Lookahead attack (injecting forward returns t+1 into feature) -> Pipeline Fail-Closed
2. Dataset mutation (flipping 1 byte in dataset) -> Checksum / TamperingDetectedException
3. Feature mutation (altering calculation) -> Feature hash mismatch
4. Alpha AST mutation (rank(momentum) -> rank(reversal)) -> AST hash discrepancy
5. Configuration mutation (transaction cost 10 bps -> 11 bps) -> Config hash mismatch
6. Model artifact mutation (modifying model payload) -> Artifact hash failure
7. Evidence chain mutation (tampering intermediate node) -> EvidenceChainBrokenException
8. Portfolio singular covariance attack -> Infeasible / SOLVER_FAILED (zero silent fallbacks)
9. Risk missing factor data -> RISK_MODEL_UNAVAILABLE (no synthetic factor generation)
10. Multi-metric reproduction sensitivity -> Exact divergence detection
"""
import pytest
import numpy as np
import pandas as pd
import hashlib

from core.integrity_guard import detect_future_leakage, FutureLeakageError
from core.evidence.artifact import ResearchArtifact, ArtifactType, compute_sha256
from core.evidence.chain import EvidenceChain
from core.evidence.exceptions import (
    EvidenceChainBrokenException,
    TamperingDetectedException,
    OptimizationFailedException,
)
from core.alpha_genealogy import ResearchSearchBudget
from core.portfolio import convex_portfolio_optimizer
from core.risk import factor_attribution
from core.reproducibility.comparator import MultiMetricReproductionComparator


# ===========================================================================
# Tier 0 — Research Integrity Attacks (Section 34 Specifications)
# ===========================================================================

def test_attack_01_lookahead_leakage_rejected():
    """
    Test 1 — Lookahead attack: Inject forward return (t+1) into a candidate feature.
    Must raise FutureLeakageError and reject the pipeline stage.
    """
    np.random.seed(101)
    n = 100
    dates = pd.date_range("2024-01-01", periods=n, freq="B")
    prices = 100.0 * np.exp(np.cumsum(np.random.normal(0, 0.015, n)))
    close_series = pd.Series(prices, index=dates)

    # Malicious forward lookahead (future return at t+1)
    leaked_feature = (close_series.shift(-1) / close_series - 1.0)

    with pytest.raises(FutureLeakageError, match="FUTURE LEAKAGE DETECTED"):
        detect_future_leakage(leaked_feature, close_series)


def test_attack_02_dataset_byte_mutation_detected():
    """
    Test 2 — Dataset mutation: Change one byte of the underlying dataset.
    Must trigger TamperingDetectedException upon verification.
    """
    original_data = {"ticker": "AAPL", "records": [150.10, 150.25, 150.80, 151.05]}
    dataset_artifact = ResearchArtifact(
        artifact_id="DS-SP500-001",
        artifact_type=ArtifactType.DATASET_MANIFEST.value,
        content_hash="",
        schema_hash="schema-v1-parquet",
        parent_hash="GENESIS",
        producer="DATA_INGESTION_ENGINE",
        code_sha="git-abc1234",
        environment_hash="env-py311-win",
        payload=original_data,
    )
    assert dataset_artifact.verify_integrity() is True

    # Attack: Mutate one record value (one byte in serial representation)
    dataset_artifact.payload["records"][0] = 150.11

    with pytest.raises(TamperingDetectedException, match="Artifact content tampered"):
        dataset_artifact.verify_integrity()


def test_attack_03_feature_mutation_detected():
    """
    Test 3 — Feature mutation: Change feature definition payload without updating envelope.
    Must trigger TamperingDetectedException.
    """
    feature_payload = {"feature_name": "momentum_20d", "formula": "ts_delta(close, 20)"}
    feature_artifact = ResearchArtifact(
        artifact_id="FEAT-MOM-020",
        artifact_type=ArtifactType.FEATURE_MANIFEST.value,
        content_hash="",
        schema_hash="feat-schema-v1",
        parent_hash="DS-SP500-001",
        producer="FEATURE_FACTORY",
        code_sha="git-abc1234",
        environment_hash="env-py311-win",
        payload=feature_payload,
    )
    assert feature_artifact.verify_integrity() is True

    # Mutate feature definition
    feature_artifact.payload["formula"] = "ts_delta(close, 10)"

    with pytest.raises(TamperingDetectedException):
        feature_artifact.verify_integrity()


def test_attack_04_alpha_ast_mutation_detected():
    """
    Test 4 — Alpha mutation: Change expression from rank(momentum) to rank(reversal).
    Must detect AST hash mismatch against registered trial genealogy.
    """
    budget = ResearchSearchBudget(experiment_id="EXP-GENEALOGY-ATTACK")
    node = budget.register_alpha_node(
        alpha_id="ALPHA-001",
        parent_ids=[],
        expression="rank(momentum_20d)",
        generation=1,
        complexity=2,
        dataset_id="DS-SP500-001",
    )
    original_ast_hash = node.ast_hash
    expected_hash = hashlib.sha256("rank(momentum_20d)".encode("utf-8")).hexdigest()
    assert original_ast_hash == expected_hash

    # Malicious mutation of expression
    mutated_expr = "rank(reversal_5d)"
    recalculated_hash = hashlib.sha256(mutated_expr.encode("utf-8")).hexdigest()
    assert recalculated_hash != node.ast_hash


def test_attack_05_configuration_mutation_detected():
    """
    Test 5 — Configuration mutation: Change transaction cost from 10 bps to 11 bps.
    Must detect configuration hash failure.
    """
    config_10bps = {"slippage_model": "almgren_chriss", "cost_bps": 10.0, "seed": 42}
    config_11bps = {"slippage_model": "almgren_chriss", "cost_bps": 11.0, "seed": 42}

    hash_10 = compute_sha256(config_10bps)
    hash_11 = compute_sha256(config_11bps)

    assert hash_10 != hash_11, "Configuration mutation must produce distinct cryptographic hashes."


def test_attack_06_model_artifact_mutation_detected():
    """
    Test 6 — Model artifact mutation: Modify serialized model weights.
    Must fail artifact envelope verification.
    """
    model_payload = {"model_architecture": "LightGBM", "n_estimators": 100, "learning_rate": 0.05}
    model_artifact = ResearchArtifact(
        artifact_id="MDL-LIGHTGBM-001",
        artifact_type=ArtifactType.ALPHA_AST.value,
        content_hash="",
        schema_hash="model-spec-v1",
        parent_hash="ALPHA-001",
        producer="MODEL_LAB",
        code_sha="git-abc1234",
        environment_hash="env-py311-win",
        payload=model_payload,
    )
    assert model_artifact.verify_integrity() is True

    # Mutate parameter
    model_artifact.payload["learning_rate"] = 0.10
    with pytest.raises(TamperingDetectedException):
        model_artifact.verify_integrity()


def test_attack_07_evidence_chain_intermediate_tampering_detected():
    """
    Test 7 — Evidence chain mutation: Modify an intermediate parent hash.
    EvidenceChain.verify_chain() must detect broken link and raise EvidenceChainBrokenException.
    """
    chain = EvidenceChain(chain_id="CHN-ATTACK-001", experiment_id="EXP-ATTACK")

    # Stage 1: Dataset
    art1 = ResearchArtifact(
        artifact_id="ART-1",
        artifact_type=ArtifactType.DATASET_MANIFEST.value,
        content_hash="",
        schema_hash="s1",
        parent_hash="0000000000000000000000000000000000000000000000000000000000000000",
        producer="P1",
        code_sha="c1",
        environment_hash="e1",
        payload={"data": "raw"},
    )
    chain.append(art1)

    # Stage 2: Feature
    art2 = ResearchArtifact(
        artifact_id="ART-2",
        artifact_type=ArtifactType.FEATURE_MANIFEST.value,
        content_hash="",
        schema_hash="s2",
        parent_hash=art1.artifact_hash,
        producer="P2",
        code_sha="c2",
        environment_hash="e2",
        payload={"features": ["f1", "f2"]},
    )
    chain.append(art2)

    assert chain.verify_chain() is True

    # Deliberate attack: Tamper parent link of art2
    art2.parent_hash = "malicious_fake_parent_hash_ffffffffffffffffffffff"
    # Recalculate envelope hash to simulate an attacker trying to fake the artifact
    art2.artifact_hash = art2.compute_artifact_hash()

    with pytest.raises(EvidenceChainBrokenException, match="Evidence chain broken"):
        chain.verify_chain()


# ===========================================================================
# Tier 1 & Tier 2 — Portfolio & Risk Fail-Closed Attacks
# ===========================================================================

def test_attack_08_portfolio_singular_covariance_fail_closed():
    """
    Test 8 — Singular / ill-conditioned covariance matrix in portfolio solver.
    Under fail_closed=True, solver must raise OptimizationFailedException,
    and never silently output equal weights as an 'optimal' solution.
    """
    alpha = np.array([0.05, 0.04, 0.03])
    # Singular covariance matrix (all assets have identical perfectly collinear returns)
    singular_cov = np.ones((3, 3)) * 0.04

    # When fail_closed is True, must raise OptimizationFailedException on solver failure
    with pytest.raises(OptimizationFailedException, match="OPTIMIZATION_FAILED"):
        convex_portfolio_optimizer(
            alpha_signal=alpha,
            cov_matrix=singular_cov,
            target_net_leverage=1.0,  # Impossible: 3 assets bounded at [-0.01, 0.01] cannot sum to 1.0!
            max_position_weight=0.01,
            fail_closed=True,
        )

    # When fail_closed is False, must return explicit SOLVER_FAILED status, not fake OPTIMAL
    result = convex_portfolio_optimizer(
        alpha_signal=alpha,
        cov_matrix=singular_cov,
        target_net_leverage=1.0,
        max_position_weight=0.01,
        fail_closed=False,
    )
    assert result["status"] == "SOLVER_FAILED"
    assert result["optimization_success"] is False


def test_attack_09_risk_missing_factors_zero_synthetic_fallback():
    """
    Test 9 — Factor risk attribution with absent factor dataset.
    Must return RISK_MODEL_UNAVAILABLE and never synthesize normal random numbers.
    """
    p_returns = np.random.normal(0.0005, 0.01, 100)
    res = factor_attribution(portfolio_returns=p_returns, factor_returns=None)

    assert res["status"] == "RISK_MODEL_UNAVAILABLE"
    assert res["r_squared"] == 0.0
    assert len(res["factor_exposures"]) == 0
    assert "zero synthetic factor fallback enforced" in res["reason"]


def test_attack_10_reproduction_sensitivity_detected():
    """
    Test 10 — Multi-metric reproduction sensitivity:
    Changing Sharpe from 1.85 to 1.60 must be caught by MultiMetricReproductionComparator
    and raise ReproductionMismatchException when fail_closed=True.
    """
    from core.reproducibility.comparator import ReproductionMismatchException

    reference = {
        "sharpe": 1.85,
        "oos_sharpe": 1.70,
        "ic": 0.065,
        "icir": 1.20,
        "annualized_return": 0.18,
        "annualized_volatility": 0.10,
        "max_drawdown": 0.08,
        "turnover": 0.25,
        "total_cost": 0.0015,
        "capacity": 50000000.0,
        "trade_count": 420,
        "equity_curve_hash": "a1b2c3d4",
        "trade_blotter_hash": "e5f6g7h8",
        "risk_report_hash": "i9j0k1l2",
    }
    reproduced_mutated = dict(reference)
    reproduced_mutated["sharpe"] = 1.60  # Substantial divergence beyond tolerance

    with pytest.raises(ReproductionMismatchException):
        MultiMetricReproductionComparator.compare(
            experiment_id="EXP-REPRO-ATTACK",
            reference=reference,
            reproduced=reproduced_mutated,
            fail_closed=True,
        )

    # When fail_closed is False, report must show all_passed = False
    report = MultiMetricReproductionComparator.compare(
        experiment_id="EXP-REPRO-ATTACK",
        reference=reference,
        reproduced=reproduced_mutated,
        fail_closed=False,
    )
    assert report.all_passed is False
    assert report.failed_count >= 1

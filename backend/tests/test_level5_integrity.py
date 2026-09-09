"""
Level-5 Integrity Transformation Verification Test Suite.
Tests non-negotiable institutional laws:
- Cryptographic Evidence Chain and Tamper Detection
- Fail-Closed Quality Gate and Linear Promotion State Machine
- Point-In-Time Universe and Survivorship Bias Prevention
- Double-Entry Ledger Invariant Verification (Debits == Credits)
- Empirical Search Budget (N_trials) Tracking
- Canonical Event-Driven Execution Loop
- Multi-Metric Level-5 Reproduction and ASCII Evidence Card
"""
import pytest
import numpy as np

from core.evidence.exceptions import (
    EvidenceChainBrokenException,
    TamperingDetectedException,
    LedgerCorruptionException,
    OptimizationFailedException,
)
from core.evidence.artifact import ResearchArtifact, ArtifactType, compute_sha256
from core.evidence.manifest import ExperimentManifest
from core.evidence.chain import EvidenceChain, GENESIS_PARENT_HASH
from core.evidence.evidence import EvidenceResult, StageEvidenceStatus
from core.evidence.certificate import AlphaEvidenceCard
from core.governance.state_machine import GovernanceStateMachine, PromotionState
from core.governance.quality_gate import EvidenceBasedQualityGate
from core.governance.decisions import DecisionOutcome
from core.security_master.universe import PointInTimeUniverseEngine
from core.ledger.journal import LedgerJournal
from core.ledger.entries import JournalTransaction, JournalLine
from core.ledger.audit import LedgerAuditVerifier
from core.alpha_genealogy import ResearchSearchBudget
from core.event_engine import EventDrivenExecutionPipeline, MarketEvent, SignalEvent
from core.reproduction_runner import ReproductionRunner
from core.portfolio import mean_variance_optimization


def test_research_artifact_and_tamper_detection():
    """Verify research artifact hashing and tamper rejection."""
    payload = {"data": [1, 2, 3], "metric": "test"}
    content_hash = compute_sha256(payload)

    art = ResearchArtifact(
        artifact_id="ART-001",
        artifact_type=ArtifactType.DATASET_MANIFEST.value,
        content_hash=content_hash,
        schema_hash="SCHEMA-V1",
        parent_hash=GENESIS_PARENT_HASH,
        producer="TEST_RUNNER",
        code_sha="GIT_TEST",
        environment_hash="ENV_TEST",
        payload=payload,
    )
    assert art.verify_integrity() is True

    # Tampering with payload must raise TamperingDetectedException
    art.payload["data"] = [9, 9, 9]
    with pytest.raises(TamperingDetectedException):
        art.verify_integrity()


def test_cryptographic_evidence_chain_tamper_detection():
    """Verify that break in cryptographic parent linkage raises EvidenceChainBrokenException."""
    chain = EvidenceChain(chain_id="CHN-001", experiment_id="EXP-001")

    # Node 1: Dataset
    art1 = ResearchArtifact(
        artifact_id="ART-DATA-01",
        artifact_type="DATASET_MANIFEST",
        content_hash=compute_sha256({"rows": 1000}),
        schema_hash="SCHEMA-1",
        parent_hash=GENESIS_PARENT_HASH,
        producer="DATA_STAGE",
        code_sha="GIT_1",
        environment_hash="ENV_1",
        payload={"rows": 1000},
    )
    chain.append(art1)
    assert chain.verify_chain() is True

    # Node 2: Features (correctly linked to art1)
    art2 = ResearchArtifact(
        artifact_id="ART-FEAT-01",
        artifact_type="FEATURE_MANIFEST",
        content_hash=compute_sha256({"features": 50}),
        schema_hash="SCHEMA-1",
        parent_hash=art1.artifact_hash,
        producer="FEAT_STAGE",
        code_sha="GIT_1",
        environment_hash="ENV_1",
        payload={"features": 50},
    )
    chain.append(art2)
    assert chain.verify_chain() is True

    # Node 3: Broken parent link
    art3_broken = ResearchArtifact(
        artifact_id="ART-ALPHA-01",
        artifact_type="ALPHA_AST",
        content_hash=compute_sha256({"expr": "ts_rank(close, 10)"}),
        schema_hash="SCHEMA-1",
        parent_hash="INVALID_PARENT_HASH",
        producer="ALPHA_STAGE",
        code_sha="GIT_1",
        environment_hash="ENV_1",
        payload={"expr": "ts_rank(close, 10)"},
    )

    with pytest.raises(EvidenceChainBrokenException):
        chain.append(art3_broken)


def test_fail_closed_quality_gate_decision():
    """Verify that gate evaluation strictly rejects when required evidence is missing or failed."""
    gate = EvidenceBasedQualityGate()

    # Case 1: Missing all evidence -> must produce REJECTED
    dec_empty = gate.evaluate(alpha_id="ALPHA-001", experiment_id="EXP-001")
    assert dec_empty.outcome == DecisionOutcome.REJECTED
    assert not dec_empty.passed
    assert len(dec_empty.reasons) > 0

    # Build valid chain
    chain = EvidenceChain(chain_id="CHN-001", experiment_id="EXP-001")
    art1 = ResearchArtifact(
        artifact_id="ART-DATA-01",
        artifact_type="DATASET_MANIFEST",
        content_hash=compute_sha256({"data": "clean"}),
        schema_hash="SCH-1",
        parent_hash=GENESIS_PARENT_HASH,
        producer="TEST",
        code_sha="GIT",
        environment_hash="ENV",
        payload={"data": "clean"},
    )
    chain.append(art1)

    # Case 2: One stage FAILS -> must produce REJECTED
    data_ev = EvidenceResult(
        stage="DATA_EVIDENCE",
        status=StageEvidenceStatus.PASS,
        evidence_id="EV-DATA-1",
        artifact_hash=art1.artifact_hash,
        methodology="PIT_VERIFIED",
    )
    val_ev_failed = EvidenceResult(
        stage="VALIDATION_EVIDENCE",
        status=StageEvidenceStatus.FAIL,
        evidence_id="EV-VAL-1",
        artifact_hash="HASH-VAL",
        methodology="CPCV",
    )

    dec_failed = gate.evaluate(
        alpha_id="ALPHA-001",
        experiment_id="EXP-001",
        dataset_evidence=data_ev,
        validation_evidence=val_ev_failed,
        evidence_chain=chain,
    )
    assert dec_failed.outcome == DecisionOutcome.REJECTED
    assert not dec_failed.passed


def test_linear_governance_state_machine_and_promotion():
    """Verify 12-state promotion pipeline and fail-to-rejected behavior."""
    sm = GovernanceStateMachine(PromotionState.IDEA)
    assert sm.current_state == PromotionState.IDEA

    # Advancing without verified evidence routes to REJECTED
    sm.advance(evidence_verified=False, reason="Missing leakage check")
    assert sm.current_state == PromotionState.REJECTED
    assert sm.is_rejected is True
    assert sm.is_terminal is True


def test_point_in_time_universe_prevents_survivorship_bias():
    """Verify that 2026 constituents cannot leak into 2015 backtest universe."""
    universe = PointInTimeUniverseEngine("SP500")

    # AAPL listed in 1980, active
    universe.add_membership("SEC-AAPL", effective_from="1980-12-12", effective_to=None)
    # XRX delisted from S&P in 2021
    universe.add_membership("SEC-XRX", effective_from="1960-01-01", effective_to="2021-03-22")
    # TSLA joined S&P only in Dec 2020
    universe.add_membership("SEC-TSLA", effective_from="2020-12-21", effective_to=None)

    # As of 2015: AAPL and XRX must be in the universe, TSLA MUST NOT
    constituents_2015 = universe.get_constituents_as_of("2015-06-01")
    assert "SEC-AAPL" in constituents_2015
    assert "SEC-XRX" in constituents_2015
    assert "SEC-TSLA" not in constituents_2015  # Survivorship leak blocked!

    # As of 2023: AAPL and TSLA must be in the universe, XRX MUST NOT
    constituents_2023 = universe.get_constituents_as_of("2023-06-01")
    assert "SEC-AAPL" in constituents_2023
    assert "SEC-TSLA" in constituents_2023
    assert "SEC-XRX" not in constituents_2023


def test_double_entry_ledger_invariants():
    """Verify double-entry general ledger invariant: sum(Debits) == sum(Credits)."""
    ledger = LedgerJournal(initial_cash=1_000_000.0)
    assert ledger.balances["CASH"] == 1_000_000.0

    # Trade 1: Buy 100 AAPL @ 150.00, fee 5.00
    tx1 = ledger.record_trade(
        transaction_id="TX-001",
        security_id="SEC-AAPL",
        quantity=100.0,
        price=150.0,
        fees=5.0,
        timestamp="2026-09-01T10:00:00Z",
    )
    assert ledger.positions["SEC-AAPL"] == 100.0
    assert ledger.balances["LONG_ASSETS"] == 15_000.0
    assert ledger.balances["COMMISSION"] == 5.0
    assert ledger.balances["CASH"] == 1_000_000.0 - 15_005.0

    # Verify audit
    audit = LedgerAuditVerifier.audit_journal(ledger)
    assert audit["valid"] is True
    assert audit["transaction_count"] == 2  # INIT + TX-001

    # Attempting to record unbalanced transaction must raise LedgerCorruptionException
    with pytest.raises(LedgerCorruptionException):
        JournalTransaction(
            transaction_id="TX-CORRUPT",
            timestamp="2026-09-01T11:00:00Z",
            description="Corrupt transaction",
            lines=[
                JournalLine(account="CASH", debit=100.0, credit=0.0),
                JournalLine(account="REALIZED_PNL", debit=0.0, credit=50.0),  # Discrepancy!
            ],
            prev_hash=tx1.transaction_hash,
        )


def test_research_search_budget_tracks_total_candidates():
    """Verify that GP search budget accurately counts empirical candidates evaluated."""
    budget = ResearchSearchBudget(experiment_id="EXP-GEN-001")

    # Record 50 trial evaluations
    for i in range(50):
        budget.record_trial(
            candidate_id=f"ALPHA-CAND-{i}",
            generation=i // 10,
            parameters={"decay": 5},
            dataset="SP500_DAILY",
            training_period="2015-2022",
            validation_period="2023-2026",
            score=0.05 + 0.01 * (i % 5),
        )

    assert budget.total_trials_count == 50

    # Register winner
    winner = budget.register_alpha_node(
        alpha_id="ALPHA-WINNER-42",
        parent_ids=["ALPHA-CAND-30"],
        expression="ts_rank(volume, 20)",
        generation=4,
        complexity=3,
        dataset_id="SP500_DAILY",
    )
    assert winner.trial_number == 50
    assert budget.trials_prior_to_discovery("ALPHA-WINNER-42") == 50


def test_event_driven_pipeline_execution():
    """Verify event-driven execution pipeline updating double-entry ledger and NAV."""
    pipeline = EventDrivenExecutionPipeline(initial_cash=500_000.0)

    # Market event
    mkt = MarketEvent(
        timestamp="2026-09-01T09:30:00Z",
        security_id="SEC-MSFT",
        open=300.0,
        high=305.0,
        low=299.0,
        close=302.0,
        volume=1000000.0,
    )
    pipeline.on_market_event(mkt)

    # Signal event
    sig = SignalEvent(
        timestamp="2026-09-01T09:31:00Z",
        alpha_id="ALPHA-MOM-01",
        security_id="SEC-MSFT",
        target_weight=0.05,
        target_shares=100.0,
    )
    order = pipeline.on_signal_event(sig)
    assert order is not None

    risk = pipeline.on_order_risk_check(order)
    assert risk.passed is True

    fill = pipeline.execute_order(order, slippage_bps=2.0)
    assert fill.quantity == 100.0
    assert pipeline.journal.positions["SEC-MSFT"] == 100.0
    assert pipeline.get_current_nav() > 0.0


def test_level5_reproduction_certificate_and_ascii_card():
    """Verify Level-5 reproduction certificate generation and ASCII card rendering."""
    manifest = ExperimentManifest(
        experiment_id="EXP-2026-000042",
        hypothesis={"id": "HYP-01", "statement": "Short-term momentum reversals in large-caps"},
        dataset={"id": "DATA-SP500", "version": "2026.09", "sha256": "abc123hash"},
        universe={"id": "SP500", "version": "2026.09", "membership_hash": "univhash"},
        features={"manifest_hash": "feathash"},
        alpha={"ast_hash": "asthash", "expression": "ts_rank(close, 10)"},
        code_sha="gitsha123",
        environment_lock_hash="envlock123",
        configuration_hash="confighash123",
        seed=42,
    )
    manifest.freeze()
    assert manifest.verify_seal() is True

    # Matching reproduction artifacts
    matching_artifacts = {
        "dataset_id": "DATA-SP500",
        "dataset_sha256": "abc123hash",
        "universe_hash": "univhash",
        "pit_clean": True,
        "features_hash": "feathash",
        "alpha_ast_hash": "asthash",
        "model_hash": "MODEL_NONE",
        "config_hash": "confighash123",
        "code_sha": "gitsha123",
        "env_lock_hash": "envlock123",
        "statistics_hash": "statshash",
        "execution_hash": "exechash",
        "ledger_balanced": True,
        "risk_model_hash": "riskhash",
        "equity_curve_hash": "eqhash",
        "trade_blotter_hash": "blotterhash",
        "evidence_chain_verified": True,
    }

    ref_artifacts = dict(matching_artifacts)
    cert = ReproductionRunner.reproduce_experiment(manifest, matching_artifacts, ref_artifacts)
    assert cert.final_result == "REPRODUCED_EXACTLY"
    assert cert.is_exact is True
    ascii_cert = cert.render_ascii()
    assert "LEVEL-5 REPRODUCTION CERTIFICATE" in ascii_cert
    assert "REPRODUCED_EXACTLY" in ascii_cert

    # Test ASCII Alpha Evidence Card
    card = AlphaEvidenceCard(
        alpha_id="ALPHA-00042",
        hypothesis="Momentum reversal",
        expression="ts_rank(close, 10)",
        ast_hash="asthash",
        dataset_id="SP500_DAILY",
        universe_id="SP500",
        is_period="2015-2022",
        oos_period="2023-2026",
        ic=0.062,
        icir=0.88,
        sharpe=1.82,
        dsr=0.98,
        pbo=0.08,
        fdr=0.02,
        reality_check_pvalue=0.015,
        spa_pvalue=0.012,
        turnover=0.25,
        transaction_cost_bps=8.5,
        capacity_millions=150.0,
        final_decision="APPROVE",
    )
    ascii_card = card.render_ascii()
    assert "ALPHA EVIDENCE CARD" in ascii_card
    assert "FINAL DECISION: APPROVE" in ascii_card


def test_optimizer_fail_closed_mode():
    """Verify that optimizer in fail-closed mode raises OptimizationFailedException rather than equal weights."""
    expected_returns = np.array([0.10, 0.12])
    # Infeasible or broken covariance matrix (singular/NaN)
    broken_cov = np.array([[np.nan, 0.0], [0.0, np.nan]])

    with pytest.raises(OptimizationFailedException):
        mean_variance_optimization(
            expected_returns=expected_returns,
            cov_matrix=broken_cov,
            fail_closed=True,
        )

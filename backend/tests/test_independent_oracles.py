"""
Independent Cross-Validation Test Suite: Production Engines vs Independent Oracles.
Verifies that:
1. No system component verifies itself.
2. Production results are mathematically identical to reference analytical closed-form oracles.
3. Formal safety invariants are verified by decoupled specification validators.
"""
from datetime import datetime, timezone
import pytest

from backend.core.fix_engine import FixSession
from backend.core.governance_gatekeeper import ResearchGovernanceGatekeeper
from backend.core.oms_ems import (
    ExecutionManagementSystem,
    OrderSide,
    TransactionCostAnalysis,
)
from backend.core.pit_fabric import PITDataFabric, TemporalLookaheadError
from backend.core.raft_consensus import RaftCluster

# Independent Oracles (Decoupled Reference)
from backend.oracles.oracle_execution import OracleExecution
from backend.oracles.oracle_fix import OracleFixParser, OracleFixValidationError
from backend.oracles.oracle_pit import OraclePITEvent, OraclePITValidator, OracleTemporalViolation
from backend.oracles.oracle_raft import OracleRaftLogEntry, OracleRaftSafetyValidator
from backend.oracles.oracle_statistics import OracleStatistics


def test_oracle_pit_cross_validation():
    # 1. Setup production fabric and reference history
    fabric = PITDataFabric()
    oracle_history = []

    event_time = datetime(2020, 6, 30, tzinfo=timezone.utc)
    pub_dates = [
        datetime(2020, 7, 15, 9, 0, tzinfo=timezone.utc),
        datetime(2020, 8, 15, 9, 0, tzinfo=timezone.utc)
    ]
    vals = [10.5, 11.2]

    for v, pub in zip(vals, pub_dates, strict=True):
        fabric.record_observation("AAPL", "sales", v, event_time, pub, pub, "SEC")
        oracle_history.append(OraclePITEvent("AAPL", "sales", v, event_time, pub, pub, "SEC"))

    # Test query at 2020-07-20: Both must return v=10.5
    q1 = datetime(2020, 7, 20, tzinfo=timezone.utc)
    prod_rec1 = fabric.query_as_of("AAPL", "sales", event_time, q1)
    oracle_rec1 = OraclePITValidator.reference_as_of_lookup(oracle_history, "AAPL", "sales", event_time, q1)
    assert prod_rec1 is not None and oracle_rec1 is not None
    assert prod_rec1.value == oracle_rec1.value == 10.5

    # Test query at 2020-09-01: Both must return v=11.2
    q2 = datetime(2020, 9, 1, tzinfo=timezone.utc)
    prod_rec2 = fabric.query_as_of("AAPL", "sales", event_time, q2)
    oracle_rec2 = OraclePITValidator.reference_as_of_lookup(oracle_history, "AAPL", "sales", event_time, q2)
    assert prod_rec2.value == oracle_rec2.value == 11.2

    # Test lookahead at 2020-07-01: Both must raise violation
    q_pre = datetime(2020, 7, 1, tzinfo=timezone.utc)
    with pytest.raises(TemporalLookaheadError):
        fabric.query_as_of("AAPL", "sales", event_time, q_pre, fail_closed=True)
    with pytest.raises(OracleTemporalViolation):
        OraclePITValidator.reference_as_of_lookup(oracle_history, "AAPL", "sales", event_time, q_pre)


def test_oracle_execution_almgren_chriss_cross_validation():
    # Slicing 10,000 shares across 5 intervals
    prod_slices = ExecutionManagementSystem.slice_almgren_chriss(
        total_quantity=10_000.0,
        num_intervals=5,
        daily_volatility=0.02,
        daily_volume=1_000_000.0,
        risk_aversion=1e-4
    )

    oracle_slices = OracleExecution.almgren_chriss_optimal_trajectory(
        total_shares=10_000.0,
        num_intervals=5,
        daily_vol=0.02,
        risk_aversion=1e-4
    )

    assert len(prod_slices) == len(oracle_slices) == 5
    for p_val, o_val in zip(prod_slices, oracle_slices, strict=True):
        # Numerical convergence within 0.01 shares
        assert pytest.approx(p_val, abs=1e-2) == o_val


def test_oracle_implementation_shortfall_cross_validation():
    fills = [(300.0, 101.0), (700.0, 101.5)]
    # Buy order: Decision $100.00, Arrival $100.50
    prod_tca = TransactionCostAnalysis.compute(
        side=OrderSide.BUY,
        decision_price=100.0,
        arrival_price=100.5,
        fills=fills
    )

    vwap, delay, trading, total = OracleExecution.implementation_shortfall_breakdown(
        is_buy=True,
        p_decision=100.0,
        p_arrival=100.5,
        fills=fills
    )

    assert prod_tca.execution_vwap == vwap
    assert prod_tca.delay_cost_bps == delay == 50.0
    assert prod_tca.trading_cost_bps == trading == 85.0
    assert prod_tca.total_is_bps == total == 135.0


def test_oracle_fix_protocol_cross_validation():
    # Build production NewOrderSingle
    session = FixSession("BUY_SIDE", "SELL_SIDE")
    msg = session.build_new_order_single(
        cl_ord_id="CL-TEST-999",
        symbol="AAPL",
        side="1",
        quantity=500.0,
        price=155.25,
        ord_type="2"
    )
    wire = msg.to_wire()

    # Pass production wire output through independent Oracle parser
    parsed_tags, msg_type = OracleFixParser.parse_and_validate_wire(wire)
    assert msg_type == "D"
    assert parsed_tags[8] == "FIX.4.2"
    assert parsed_tags[11] == "CL-TEST-999"
    assert parsed_tags[55] == "AAPL"
    assert float(parsed_tags[38]) == 500.0
    assert float(parsed_tags[44]) == 155.25

    # Corrupting Tag 10 checksum must cause Oracle rejection
    corrupted_wire = wire[:-4] + "999" + wire[-1]
    with pytest.raises(OracleFixValidationError, match="Checksum mismatch"):
        OracleFixParser.parse_and_validate_wire(corrupted_wire)


def test_oracle_raft_safety_cross_validation():
    cluster = RaftCluster(node_ids=["node1", "node2", "node3"])
    cluster.elect_leader("node1")

    # Replicate 2 entries via submit_evidence
    cluster.submit_evidence("node1", "EVIDENCE_HASH_ALPHA")
    cluster.submit_evidence("node1", "EVIDENCE_HASH_BETA")

    # Formal Oracle validator inspection
    oracle = OracleRaftSafetyValidator()
    oracle.record_leader_election(1, "node1")

    # Extract logs from nodes and verify Log Matching Invariant
    for nid, node in cluster.nodes.items():
        o_entries = [OracleRaftLogEntry(e.index, e.term, e.data) for e in node.log]
        oracle.record_node_log(nid, o_entries)

    # State Machine Safety check on committed entries
    leader = cluster.nodes["node1"]
    for e in leader.log[:leader.commit_index + 1]:
        oracle.record_committed_entry(OracleRaftLogEntry(e.index, e.term, e.data))


def test_oracle_statistics_dsr_cross_validation():
    gatekeeper = ResearchGovernanceGatekeeper()
    m_hash = gatekeeper.pre_register("HYP-STAT-ORACLE", "Statement", "AST", search_budget=10)

    # Evaluate trial
    rec = gatekeeper.evaluate_alpha(
        manifest_hash=m_hash,
        gross_sharpe=1.80,
        net_sharpe=1.60,
        total_is_bps=10.0,
        sample_length_days=756
    )

    # Independent Oracle DSR calculation
    exp_max_sr, oracle_pvalue = OracleStatistics.deflated_sharpe_ratio_oracle(
        estimated_sr=1.60,
        n_trials=1,
        sample_length=756
    )

    # Production gatekeeper dsr_pvalue matches oracle within 0.005
    assert pytest.approx(rec.dsr_pvalue, abs=0.005) == oracle_pvalue

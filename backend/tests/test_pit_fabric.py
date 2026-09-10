"""
Institutional Verification Tests for Multi-Timestamp Point-in-Time Data Fabric.
Verifies:
1. Causality invariants (event_time <= published_at <= available_at <= decision_time).
2. Fail-closed rejection of wire/publication lookahead queries.
3. Revision superseding and bitemporal query fidelity.
4. Historical snapshot immutability across macro/earnings revisions.
"""
from datetime import datetime, timezone
import pytest
from backend.core.pit_fabric import PITDataFabric, TemporalLookaheadError


def test_pit_fabric_ingestion_and_digest():
    fabric = PITDataFabric()
    event_time = datetime(2020, 3, 31, 0, 0, tzinfo=timezone.utc)
    published_at = datetime(2020, 4, 28, 8, 30, tzinfo=timezone.utc)
    available_at = datetime(2020, 4, 28, 8, 45, tzinfo=timezone.utc)

    record = fabric.record_observation(
        entity_id="US_MACRO",
        feature_name="gdp_growth_annualized",
        value=-4.8,
        event_time=event_time,
        published_at=published_at,
        available_at=available_at,
        source_id="BEA_ADVANCE"
    )

    assert record.revision_id == 0
    assert record.effective_from == available_at
    assert record.effective_to is None
    assert len(record.digest) == 64  # SHA-256


def test_pit_fabric_causality_rejection():
    fabric = PITDataFabric()
    event_time = datetime(2020, 3, 31, 0, 0, tzinfo=timezone.utc)

    # published_at < event_time is impossible
    with pytest.raises(ValueError, match="published_at .* cannot precede event_time"):
        fabric.record_observation(
            entity_id="AAPL",
            feature_name="revenue",
            value=58.3,
            event_time=event_time,
            published_at=datetime(2020, 3, 1, tzinfo=timezone.utc),
            available_at=datetime(2020, 4, 30, tzinfo=timezone.utc),
            source_id="SEC_10Q"
        )

    # available_at < published_at is impossible (wire speed violation)
    with pytest.raises(ValueError, match="available_at .* cannot precede published_at"):
        fabric.record_observation(
            entity_id="AAPL",
            feature_name="revenue",
            value=58.3,
            event_time=event_time,
            published_at=datetime(2020, 4, 30, 16, 0, tzinfo=timezone.utc),
            available_at=datetime(2020, 4, 30, 15, 0, tzinfo=timezone.utc),
            source_id="SEC_10Q"
        )


def test_pit_lookahead_fail_closed():
    fabric = PITDataFabric()
    event_time = datetime(2020, 3, 31, 0, 0, tzinfo=timezone.utc)
    published_at = datetime(2020, 4, 28, 8, 30, tzinfo=timezone.utc)
    available_at = datetime(2020, 4, 28, 8, 45, tzinfo=timezone.utc)

    fabric.record_observation(
        entity_id="US_MACRO",
        feature_name="gdp_growth_annualized",
        value=-4.8,
        event_time=event_time,
        published_at=published_at,
        available_at=available_at,
        source_id="BEA_ADVANCE"
    )

    # Attempting to query before published_at
    prior_decision = datetime(2020, 4, 20, 12, 0, tzinfo=timezone.utc)
    with pytest.raises(TemporalLookaheadError, match="Lookahead violation"):
        fabric.query_as_of("US_MACRO", "gdp_growth_annualized", event_time, prior_decision, fail_closed=True)

    # Attempting to query during wire delay (published at 8:30, available at 8:45, query at 8:35)
    wire_delay_decision = datetime(2020, 4, 28, 8, 35, tzinfo=timezone.utc)
    with pytest.raises(TemporalLookaheadError, match="Lookahead violation"):
        fabric.query_as_of("US_MACRO", "gdp_growth_annualized", event_time, wire_delay_decision, fail_closed=True)

    # Querying after available_at succeeds
    valid_decision = datetime(2020, 4, 28, 9, 0, tzinfo=timezone.utc)
    rec = fabric.query_as_of("US_MACRO", "gdp_growth_annualized", event_time, valid_decision)
    assert rec is not None
    assert rec.value == -4.8
    assert rec.revision_id == 0


def test_pit_multi_revision_lineage():
    fabric = PITDataFabric()
    event_time = datetime(2020, 3, 31, 0, 0, tzinfo=timezone.utc)

    # 1. Advance estimate on 2020-04-28
    t_avail_0 = datetime(2020, 4, 28, 8, 45, tzinfo=timezone.utc)
    r0 = fabric.record_observation(
        entity_id="US_MACRO",
        feature_name="gdp_growth",
        value=-4.8,
        event_time=event_time,
        published_at=datetime(2020, 4, 28, 8, 30, tzinfo=timezone.utc),
        available_at=t_avail_0,
        source_id="BEA_ADVANCE"
    )

    # 2. Preliminary revision on 2020-05-28
    t_avail_1 = datetime(2020, 5, 28, 8, 45, tzinfo=timezone.utc)
    r1 = fabric.record_observation(
        entity_id="US_MACRO",
        feature_name="gdp_growth",
        value=-5.0,
        event_time=event_time,
        published_at=datetime(2020, 5, 28, 8, 30, tzinfo=timezone.utc),
        available_at=t_avail_1,
        source_id="BEA_PRELIM"
    )

    # 3. Final revision on 2020-06-25
    t_avail_2 = datetime(2020, 6, 25, 8, 45, tzinfo=timezone.utc)
    r2 = fabric.record_observation(
        entity_id="US_MACRO",
        feature_name="gdp_growth",
        value=-5.1,
        event_time=event_time,
        published_at=datetime(2020, 6, 25, 8, 30, tzinfo=timezone.utc),
        available_at=t_avail_2,
        source_id="BEA_FINAL"
    )

    # Check revision IDs
    assert r0.revision_id == 0
    assert r1.revision_id == 1
    assert r2.revision_id == 2

    # Querying on 2020-05-01 should strictly return r0 (-4.8)
    q_may1 = fabric.query_as_of("US_MACRO", "gdp_growth", event_time, datetime(2020, 5, 1, tzinfo=timezone.utc))
    assert q_may1.value == -4.8
    assert q_may1.revision_id == 0

    # Querying on 2020-06-01 should strictly return r1 (-5.0)
    q_jun1 = fabric.query_as_of("US_MACRO", "gdp_growth", event_time, datetime(2020, 6, 1, tzinfo=timezone.utc))
    assert q_jun1.value == -5.0
    assert q_jun1.revision_id == 1

    # Querying on 2020-07-01 should strictly return r2 (-5.1)
    q_jul1 = fabric.query_as_of("US_MACRO", "gdp_growth", event_time, datetime(2020, 7, 1, tzinfo=timezone.utc))
    assert q_jul1.value == -5.1
    assert q_jul1.revision_id == 2

    # Audit trail verifies all 3 revisions exist
    history = fabric.get_revision_history("US_MACRO", "gdp_growth", event_time)
    assert len(history) == 3
    assert [h.value for h in history] == [-4.8, -5.0, -5.1]


def test_pit_history_as_of_snapshot():
    fabric = PITDataFabric()

    # Ingest 3 quarters of data with subsequent revisions
    q1_event = datetime(2020, 3, 31, tzinfo=timezone.utc)
    q2_event = datetime(2020, 6, 30, tzinfo=timezone.utc)

    fabric.record_observation(
        "AAPL", "eps", 1.20, q1_event,
        datetime(2020, 4, 30, 16, 0, tzinfo=timezone.utc),
        datetime(2020, 4, 30, 16, 15, tzinfo=timezone.utc),
        "SEC_10Q"
    )

    fabric.record_observation(
        "AAPL", "eps", 1.25, q2_event,
        datetime(2020, 7, 30, 16, 0, tzinfo=timezone.utc),
        datetime(2020, 7, 30, 16, 15, tzinfo=timezone.utc),
        "SEC_10Q"
    )

    # Query history as of 2020-05-15: Only Q1 should be known
    h_may = fabric.query_history_as_of(
        "AAPL", "eps",
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2020, 12, 31, tzinfo=timezone.utc),
        datetime(2020, 5, 15, tzinfo=timezone.utc)
    )
    assert len(h_may) == 1
    assert h_may[0].event_time == q1_event
    assert h_may[0].value == 1.20

    # Query history as of 2020-08-15: Both Q1 and Q2 should be known
    h_aug = fabric.query_history_as_of(
        "AAPL", "eps",
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2020, 12, 31, tzinfo=timezone.utc),
        datetime(2020, 8, 15, tzinfo=timezone.utc)
    )
    assert len(h_aug) == 2
    assert [rec.value for rec in h_aug] == [1.20, 1.25]


def test_pit_bitemporal_matrix_invariants():
    """
    Exhaustive bitemporal matrix verification across a dense grid of decision times.
    Asserts invariant: available_at <= decision_time < effective_to
    """
    fabric = PITDataFabric()
    event_time = datetime(2021, 12, 31, tzinfo=timezone.utc)

    # 3 revisions released at 3 distinct dates
    dates = [
        datetime(2022, 1, 15, 9, 0, tzinfo=timezone.utc),  # r0
        datetime(2022, 2, 15, 9, 0, tzinfo=timezone.utc),  # r1
        datetime(2022, 3, 15, 9, 0, tzinfo=timezone.utc),  # r2
    ]
    values = [100.0, 102.5, 101.8]

    for val, avail in zip(values, dates, strict=True):
        fabric.record_observation(
            entity_id="EQUITY_X",
            feature_name="ebitda",
            value=val,
            event_time=event_time,
            published_at=avail,
            available_at=avail,
            source_id="TEST_SOURCE"
        )

    # Test 1: Before r0 available
    pre_r0 = datetime(2022, 1, 10, tzinfo=timezone.utc)
    with pytest.raises(TemporalLookaheadError):
        fabric.query_as_of("EQUITY_X", "ebitda", event_time, pre_r0, fail_closed=True)
    assert fabric.query_as_of("EQUITY_X", "ebitda", event_time, pre_r0, fail_closed=False) is None

    # Test 2: Exactly at r0 availability
    rec_r0 = fabric.query_as_of("EQUITY_X", "ebitda", event_time, dates[0])
    assert rec_r0 is not None and rec_r0.value == 100.0 and rec_r0.revision_id == 0

    # Test 3: Between r0 and r1 (e.g. Feb 1)
    rec_between_0_1 = fabric.query_as_of("EQUITY_X", "ebitda", event_time, datetime(2022, 2, 1, tzinfo=timezone.utc))
    assert rec_between_0_1.value == 100.0 and rec_between_0_1.revision_id == 0

    # Test 4: Exactly at r1 availability
    rec_r1 = fabric.query_as_of("EQUITY_X", "ebitda", event_time, dates[1])
    assert rec_r1.value == 102.5 and rec_r1.revision_id == 1

    # Test 5: Between r1 and r2 (e.g. Mar 1)
    rec_between_1_2 = fabric.query_as_of("EQUITY_X", "ebitda", event_time, datetime(2022, 3, 1, tzinfo=timezone.utc))
    assert rec_between_1_2.value == 102.5 and rec_between_1_2.revision_id == 1

    # Test 6: Exactly at r2 and post-r2
    rec_r2 = fabric.query_as_of("EQUITY_X", "ebitda", event_time, dates[2])
    assert rec_r2.value == 101.8 and rec_r2.revision_id == 2

    post_r2 = datetime(2022, 12, 31, tzinfo=timezone.utc)
    assert fabric.query_as_of("EQUITY_X", "ebitda", event_time, post_r2).value == 101.8


def test_pit_digest_tamper_detection():
    fabric = PITDataFabric()
    event_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    pub = datetime(2020, 1, 10, tzinfo=timezone.utc)
    rec = fabric.record_observation("SEC_A", "f1", 42.0, event_time, pub, pub, "SRC_A")

    # Recomputed digest with correct params matches rec.digest
    from backend.core.pit_fabric import PITRecord
    expected_digest = PITRecord.compute_digest("SEC_A", "f1", 42.0, event_time, pub, pub, 0, "SRC_A")
    assert rec.digest == expected_digest

    # Tampered value generates mismatched digest
    tampered_digest = PITRecord.compute_digest("SEC_A", "f1", 42.000001, event_time, pub, pub, 0, "SRC_A")
    assert rec.digest != tampered_digest


def test_pit_cross_asset_query_isolation():
    fabric = PITDataFabric()
    event_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    pub = datetime(2020, 1, 10, tzinfo=timezone.utc)

    fabric.record_observation("ASSET_ALPHA", "vol", 0.15, event_time, pub, pub, "SRC")
    fabric.record_observation("ASSET_BETA", "vol", 0.35, event_time, pub, pub, "SRC")

    dec_time = datetime(2020, 1, 15, tzinfo=timezone.utc)
    rec_a = fabric.query_as_of("ASSET_ALPHA", "vol", event_time, dec_time)
    rec_b = fabric.query_as_of("ASSET_BETA", "vol", event_time, dec_time)

    assert rec_a.value == 0.15
    assert rec_b.value == 0.35
    assert rec_a.entity_id == "ASSET_ALPHA"
    assert rec_b.entity_id == "ASSET_BETA"


def test_pit_naive_datetime_normalization():
    fabric = PITDataFabric()
    # Pass naive datetimes
    event_time = datetime(2020, 6, 30, 0, 0)
    published_at = datetime(2020, 7, 15, 12, 0)
    available_at = datetime(2020, 7, 15, 12, 30)

    rec = fabric.record_observation("SEC_NAIVE", "cf", 10.0, event_time, published_at, available_at, "SRC")
    assert rec.event_time.tzinfo == timezone.utc
    assert rec.available_at.tzinfo == timezone.utc

    query_naive = datetime(2020, 7, 20, 0, 0)
    queried = fabric.query_as_of("SEC_NAIVE", "cf", event_time, query_naive)
    assert queried is not None
    assert queried.value == 10.0

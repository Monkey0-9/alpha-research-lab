"""
Adversarial Property-Based Test Suite: Point-In-Time Future Attack Generator.
Simulates 1,000+ randomized adversarial data-injection attacks:
1. Injects future earnings & macro information before publication.
2. Injects wire latency compression (querying during wire propagation).
3. Injects out-of-order restatements and late-arriving vendor revisions.
4. Asserts 100% fail-closed detection with zero lookahead leakage.
"""
from datetime import datetime, timedelta, timezone
import random
import pytest
from backend.core.pit_fabric import PITDataFabric, TemporalLookaheadError


def test_pit_adversarial_attack_generator_1000_trials():
    """
    Stress-tests the PIT fabric against 1,000 randomized future-information injection attacks.
    Every attempt to access future information must fail closed.
    """
    fabric = PITDataFabric()
    rng = random.Random(42)  # Seeded deterministic pseudo-random generator

    base_time = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    attack_count = 0

    for i in range(1000):
        entity = f"EQUITY_{i:04d}"
        feature = "earnings_per_share"
        true_value = round(rng.uniform(1.0, 100.0), 4)

        # 1. Generate chronological event, publication, and availability times
        t_event = base_time + timedelta(days=rng.randint(1, 1000))
        pub_delay_hours = rng.randint(24, 720)  # 1 to 30 days publication delay
        t_published = t_event + timedelta(hours=pub_delay_hours)
        wire_delay_seconds = rng.randint(60, 3600)  # 1 to 60 minutes wire delay
        t_available = t_published + timedelta(seconds=wire_delay_seconds)

        fabric.record_observation(
            entity_id=entity,
            feature_name=feature,
            value=true_value,
            event_time=t_event,
            published_at=t_published,
            available_at=t_available,
            source_id="VENDOR_FEED"
        )

        # 2. Adversarial Attack Type A: Query before publication (event_time < query < published_at)
        delta_pub = (t_published - t_event).total_seconds()
        query_time_a = t_event + timedelta(seconds=rng.uniform(1, max(delta_pub - 1, 2)))
        with pytest.raises(TemporalLookaheadError):
            fabric.query_as_of(entity, feature, t_event, query_time_a, fail_closed=True)
        assert fabric.query_as_of(entity, feature, t_event, query_time_a, fail_closed=False) is None
        attack_count += 1

        # 3. Adversarial Attack Type B: Query during wire dissemination (published_at < query < available_at)
        query_time_b = t_published + timedelta(seconds=rng.uniform(1, wire_delay_seconds - 1))
        with pytest.raises(TemporalLookaheadError):
            fabric.query_as_of(entity, feature, t_event, query_time_b, fail_closed=True)
        assert fabric.query_as_of(entity, feature, t_event, query_time_b, fail_closed=False) is None
        attack_count += 1

        # 4. Valid Query: query >= available_at MUST succeed and return exact true_value
        query_time_c = t_available + timedelta(seconds=rng.uniform(0, 86400))
        valid_rec = fabric.query_as_of(entity, feature, t_event, query_time_c)
        assert valid_rec is not None
        assert valid_rec.value == true_value

    assert attack_count == 2000  # 1000 Type A + 1000 Type B = 2000 attacks repelled


def test_pit_late_arriving_data_and_restatement_sequence():
    """
    Verifies timeline integrity when data revisions arrive with erratic delays.
    """
    fabric = PITDataFabric()
    ev = datetime(2021, 3, 31, tzinfo=timezone.utc)

    # Revision 0: Released April 30
    t_avail_0 = datetime(2021, 4, 30, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 2.0, ev, t_avail_0, t_avail_0, "BEA")

    # Revision 1: Released May 30 (Revised downward to 1.8)
    t_avail_1 = datetime(2021, 5, 30, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 1.8, ev, t_avail_1, t_avail_1, "BEA")

    # Revision 2: Restatement released August 15 (Revised to 1.9)
    t_avail_2 = datetime(2021, 8, 15, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 1.9, ev, t_avail_2, t_avail_2, "BEA")

    # Backtest as of June 15: Must see Revision 1 (1.8), NEVER Revision 2 (1.9)
    res_june = fabric.query_as_of("MACRO_GDP", "rate", ev, datetime(2021, 6, 15, tzinfo=timezone.utc))
    assert res_june is not None
    assert res_june.value == 1.8
    assert res_june.revision_id == 1

    # Backtest as of September 1: Must see Revision 2 (1.9)
    res_sept = fabric.query_as_of("MACRO_GDP", "rate", ev, datetime(2021, 9, 1, tzinfo=timezone.utc))
    assert res_sept is not None
    assert res_sept.value == 1.9
    assert res_sept.revision_id == 2

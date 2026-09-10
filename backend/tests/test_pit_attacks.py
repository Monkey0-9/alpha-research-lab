"""
Adversarial Point-in-Time (PIT) Attack & Lookahead Falsification Matrix.
Simulates 2,000 structured adversarial lookahead attacks across 4 distinct attack classes:
1. future_tick (500 cases): Querying future timestamps before event occurrence.
2. revision_forgery (500 cases): Querying unannounced fundamental revisions prior to publication.
3. restatement_leakage (500 cases): Querying post-period restatements during wire transit.
4. negative_time (500 cases): Retrograde query injection (query_time < event_time).

Guarantees:
- Seed: 918273 (deterministic reproducibility)
- 100% fail-closed rejection rate (0 false negatives, 0 false positives).
"""
from datetime import datetime, timedelta, timezone
import random
from backend.core.pit_fabric import PITDataFabric, TemporalLookaheadError


def test_pit_adversarial_attack_matrix_2000_cases():
    """
    Execute 2,000 structured adversarial attacks across 4 attack categories with seed 918273.
    """
    fabric = PITDataFabric()
    seed = 918273
    rng = random.Random(seed)

    base_time = datetime(2020, 1, 1, 0, 0, tzinfo=timezone.utc)
    categories = {
        "future_tick": {"generated": 0, "rejected": 0, "accepted": 0},
        "revision_forgery": {"generated": 0, "rejected": 0, "accepted": 0},
        "restatement_leakage": {"generated": 0, "rejected": 0, "accepted": 0},
        "negative_time": {"generated": 0, "rejected": 0, "accepted": 0},
    }
    false_negatives = 0
    false_positives = 0
    valid_successes = 0

    for i in range(500):
        entity = f"SEC_{i:04d}"
        feature = "operating_cashflow"
        true_value = round(rng.uniform(10.0, 500.0), 2)

        t_event = base_time + timedelta(days=i + 1)
        pub_delay_sec = rng.randint(86400, 86400 * 30)  # 1 to 30 days
        t_published = t_event + timedelta(seconds=pub_delay_sec)
        wire_delay_sec = rng.randint(60, 3600)  # 1 to 60 mins
        t_available = t_published + timedelta(seconds=wire_delay_sec)

        fabric.record_observation(
            entity_id=entity,
            feature_name=feature,
            value=true_value,
            event_time=t_event,
            published_at=t_published,
            available_at=t_available,
            source_id="EDGAR_SEC"
        )

        # 1. Attack Class: future_tick (Query before event_time)
        categories["future_tick"]["generated"] += 1
        query_time_ft = t_event - timedelta(seconds=rng.uniform(1, 86400))
        try:
            fabric.query_as_of(entity, feature, t_event, query_time_ft, fail_closed=True)
            categories["future_tick"]["accepted"] += 1
            false_negatives += 1
        except TemporalLookaheadError:
            categories["future_tick"]["rejected"] += 1

        # 2. Attack Class: revision_forgery (event_time < query < published_at)
        categories["revision_forgery"]["generated"] += 1
        query_time_rf = t_event + timedelta(seconds=rng.uniform(1, max(pub_delay_sec - 10, 2)))
        try:
            fabric.query_as_of(entity, feature, t_event, query_time_rf, fail_closed=True)
            categories["revision_forgery"]["accepted"] += 1
            false_negatives += 1
        except TemporalLookaheadError:
            categories["revision_forgery"]["rejected"] += 1

        # 3. Attack Class: restatement_leakage (published_at < query < available_at)
        categories["restatement_leakage"]["generated"] += 1
        query_time_rl = t_published + timedelta(seconds=rng.uniform(1, max(wire_delay_sec - 5, 2)))
        try:
            fabric.query_as_of(entity, feature, t_event, query_time_rl, fail_closed=True)
            categories["restatement_leakage"]["accepted"] += 1
            false_negatives += 1
        except TemporalLookaheadError:
            categories["restatement_leakage"]["rejected"] += 1

        # 4. Attack Class: negative_time (Arbitrary retrograde timestamp query)
        categories["negative_time"]["generated"] += 1
        query_time_nt = base_time - timedelta(days=rng.randint(1, 100))
        try:
            fabric.query_as_of(entity, feature, t_event, query_time_nt, fail_closed=True)
            categories["negative_time"]["accepted"] += 1
            false_negatives += 1
        except TemporalLookaheadError:
            categories["negative_time"]["rejected"] += 1

        # Valid Query Check: query >= available_at MUST succeed
        query_valid = t_available + timedelta(seconds=rng.uniform(10, 86400))
        try:
            val = fabric.query_as_of(entity, feature, t_event, query_valid, fail_closed=True)
            if val is not None and val.value == true_value:
                valid_successes += 1
            else:
                false_positives += 1
        except Exception:
            false_positives += 1

    # Assertions across all categories
    for cat_name, stats in categories.items():
        assert stats["generated"] == 500, f"{cat_name} generated mismatch"
        assert stats["rejected"] == 500, f"{cat_name} rejected mismatch"
        assert stats["accepted"] == 0, f"{cat_name} accepted mismatch (lookahead leaked!)"

    assert false_negatives == 0, "Lookahead leakage detected (false negatives > 0)"
    assert false_positives == 0, "Valid queries incorrectly rejected (false positives > 0)"
    assert valid_successes == 500, "Valid query successes mismatch"


def test_pit_restatement_chronology_isolation():
    """
    Verifies multi-version revision chronology isolation.
    """
    fabric = PITDataFabric()
    ev = datetime(2021, 3, 31, tzinfo=timezone.utc)

    # Revision 0: Released April 30 (2.0)
    t_avail_0 = datetime(2021, 4, 30, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 2.0, ev, t_avail_0, t_avail_0, "BEA")

    # Revision 1: Released May 30 (1.8)
    t_avail_1 = datetime(2021, 5, 30, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 1.8, ev, t_avail_1, t_avail_1, "BEA")

    # Revision 2: Restatement released August 15 (1.9)
    t_avail_2 = datetime(2021, 8, 15, 9, 0, tzinfo=timezone.utc)
    fabric.record_observation("MACRO_GDP", "rate", 1.9, ev, t_avail_2, t_avail_2, "BEA")

    # Historical point-in-time queries
    res_june = fabric.query_as_of("MACRO_GDP", "rate", ev, datetime(2021, 6, 15, tzinfo=timezone.utc))
    assert res_june is not None and res_june.value == 1.8 and res_june.revision_id == 1

    res_sept = fabric.query_as_of("MACRO_GDP", "rate", ev, datetime(2021, 9, 1, tzinfo=timezone.utc))
    assert res_sept is not None and res_sept.value == 1.9 and res_sept.revision_id == 2

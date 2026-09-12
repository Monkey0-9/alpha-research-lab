"""
Test suite validating the Adversarial Backtesting Attack Engine (Phase 3).
Verifies that all look-ahead leakages, survivorship bias anomalies, corporate action adjustments,
and timestamp attacks are detected and handled fail-closed.
"""
import pytest
from backend.backtesting.adversarial_engine import (
    AdversarialBacktestEngine,
    AttackType,
    BacktestIntegrityViolation,
    BarEvent,
    FundamentalFiling,
)


@pytest.fixture
def engine():
    return AdversarialBacktestEngine(execution_delay_seconds=1)


def test_adversarial_detects_negative_delta_timestamp(engine):
    res = engine.run_adversarial_suite(AttackType.TIMESTAMP_NEGATIVE_DELTA)
    assert res["detected_and_handled"] is True
    assert "out of order" in res["message"].lower()


def test_adversarial_detects_lookahead_fundamentals(engine):
    res = engine.run_adversarial_suite(AttackType.LOOKAHEAD_FUNDAMENTALS)
    assert res["detected_and_handled"] is True
    assert "lookahead fundamentals" in res["message"].lower()


def test_adversarial_detects_lookahead_price_peeking(engine):
    res = engine.run_adversarial_suite(AttackType.LOOKAHEAD_PRICE)
    assert res["detected_and_handled"] is True
    assert "lookahead price" in res["message"].lower()


def test_adversarial_handles_survivorship_delisting(engine):
    res = engine.run_adversarial_suite(AttackType.SURVIVORSHIP_DELISTED)
    assert res["detected_and_handled"] is True
    assert "delisting" in res["message"].lower()


def test_adversarial_handles_corporate_action_splits(engine):
    res = engine.run_adversarial_suite(AttackType.CORPORATE_ACTION_SPLIT)
    assert res["detected_and_handled"] is True
    assert "split" in res["message"].lower()


def test_adversarial_validates_monotonic_valid_stream(engine):
    valid_events = [
        BarEvent(timestamp_utc=1000, ticker="AAPL", open=150, high=155, low=149, close=153, volume=1000),
        BarEvent(timestamp_utc=1060, ticker="AAPL", open=153, high=154, low=151, close=152, volume=800),
        BarEvent(timestamp_utc=1120, ticker="AAPL", open=152, high=156, low=152, close=155, volume=1200),
    ]
    # Should not raise exception
    engine.validate_event_stream_integrity(valid_events)

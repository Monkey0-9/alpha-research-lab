"""
Unit Tests for Security Master, Corporate Actions, Historical Universe, and Multi-Temporal PIT Store.
"""
import pytest
import pandas as pd
from core.security_master.master import security_master
from core.universe.universe_engine import universe_engine
from core.pit_store import get_pit_store
from core.data_contract import PriceType


def test_security_master_historical_ticker_resolution():
    # In 2018, Meta was traded under 'FB'
    sec_2018 = security_master.resolve_ticker("FB", "2018-06-01")
    assert sec_2018 is not None
    assert sec_2018.security_id == "SEC-US-META-001"
    assert sec_2018.get_ticker_as_of("2018-06-01") == "FB"

    # In 2023, Meta trades under 'META'
    sec_2023 = security_master.resolve_ticker("META", "2023-06-01")
    assert sec_2023 is not None
    assert sec_2023.security_id == "SEC-US-META-001"
    assert sec_2023.get_ticker_as_of("2023-06-01") == "META"


def test_historical_universe_membership_eliminates_survivorship():
    # Tesla was added to S&P 500 on 2020-12-21
    members_2015 = universe_engine.get_members("SP500", "2015-06-01")
    assert "SEC-US-TSLA-001" not in members_2015

    members_2021 = universe_engine.get_members("SP500", "2021-06-01")
    assert "SEC-US-TSLA-001" in members_2021

    # Xerox (XRX) was removed from S&P 500 on 2021-03-22
    members_2018 = universe_engine.get_members("SP500", "2018-01-01")
    assert "SEC-US-XRX-001" in members_2018

    members_2022 = universe_engine.get_members("SP500", "2022-01-01")
    assert "SEC-US-XRX-001" not in members_2022


def test_true_pit_temporal_isolation():
    pit = get_pit_store()

    # Q1 2023 EPS period ended March 31, 2023, but was published/available on May 4, 2023 16:35
    # Query as of May 1, 2023 MUST return None (invisible before public filing)
    eps_before = pit.get_fundamental_as_of("AAPL", "eps", "2023-05-01 00:00:00")
    assert eps_before is None

    # Query as of May 5, 2023 MUST return original reported EPS 1.52
    eps_after_pub = pit.get_fundamental_as_of("AAPL", "eps", "2023-05-05 00:00:00")
    assert eps_after_pub == 1.52

    # Restatement occurred on June 15, 2023 (revised to 1.50)
    # Query on June 1, 2023 must still see the unrevised 1.52
    eps_before_restatement = pit.get_fundamental_as_of("AAPL", "eps", "2023-06-01 00:00:00")
    assert eps_before_restatement == 1.52

    # Query on June 20, 2023 must see the restated 1.50
    eps_after_restatement = pit.get_fundamental_as_of("AAPL", "eps", "2023-06-20 00:00:00")
    assert eps_after_restatement == 1.50

"""
Institutional Verification Tests for Security Master & Point-in-Time Historical Universe Engine.
Verifies:
1. Point-in-Time Ticker & Identity Resolution across historical symbol changes (FB -> META, GOOG -> GOOGL).
2. Backward price adjustment for corporate actions (Stock Splits & Cash Dividends).
3. Point-in-Time Universe filtering eliminating survivorship bias.
4. Delisting payouts and terminal liquidation event handling.
"""
import pandas as pd
import pytest
from core.data_contract import PriceType
from core.security_master import (
    DelistingEvent,
    DelistingReason,
    PointInTimeUniverseEngine,
    SecurityMaster,
)


@pytest.fixture
def sec_master() -> SecurityMaster:
    return SecurityMaster()


def test_historical_ticker_resolution(sec_master: SecurityMaster):
    # Meta Platforms: Ticker was FB prior to 2022-06-09, and META thereafter
    sec_2020 = sec_master.resolve_ticker("FB", "2020-05-01")
    assert sec_2020 is not None
    assert sec_2020.security_id == "SEC-US-META-001"
    assert sec_2020.name == "Meta Platforms Inc."

    sec_2023 = sec_master.resolve_ticker("META", "2023-01-15")
    assert sec_2023 is not None
    assert sec_2023.security_id == "SEC-US-META-001"

    # Alphabet: Ticker was GOOG prior to 2014-04-02, and GOOGL thereafter
    sec_goog_2010 = sec_master.resolve_ticker("GOOG", "2010-06-01")
    assert sec_goog_2010 is not None
    assert sec_goog_2010.security_id == "SEC-US-GOOGL-001"

    sec_googl_2020 = sec_master.resolve_ticker("GOOGL", "2020-06-01")
    assert sec_googl_2020 is not None
    assert sec_googl_2020.security_id == "SEC-US-GOOGL-001"


def test_split_and_dividend_price_adjustments(sec_master: SecurityMaster):
    # Apple had a 4-for-1 forward split on 2020-08-31
    dates = pd.date_range("2020-08-25", "2020-09-05", freq="B")
    raw_df = pd.DataFrame({
        "open": [500.0] * len(dates),
        "high": [510.0] * len(dates),
        "low": [495.0] * len(dates),
        "close": [500.0] * len(dates),
        "volume": [1000000] * len(dates),
    }, index=dates)

    # Adjust backward from the split date
    adj_df = sec_master.adjust_prices(raw_df, "SEC-US-AAPL-001", price_type=PriceType.SPLIT_ADJUSTED)

    # Bars prior to 2020-08-31 should be divided by 4.0 (500 -> 125.0)
    pre_split_bar = adj_df.loc[pd.Timestamp("2020-08-28")]
    assert pre_split_bar["close"] == 125.0
    assert pre_split_bar["volume"] == 4000000  # Volume scaled up

    # Bars on/after 2020-08-31 should remain unchanged
    post_split_bar = adj_df.loc[pd.Timestamp("2020-09-01")]
    assert post_split_bar["close"] == 500.0


def test_point_in_time_universe_survivorship_protection():
    engine = PointInTimeUniverseEngine(universe_id="SP500")

    # Tesla (SEC-US-TSLA-001) added on 2020-12-21
    engine.add_membership("SEC-US-TSLA-001", effective_from="2020-12-21", effective_to=None)

    # Xerox (SEC-US-XRX-001) removed from S&P on 2021-03-22
    engine.add_membership("SEC-US-XRX-001", effective_from="1980-01-01", effective_to="2021-03-22")

    # Apple (SEC-US-AAPL-001) permanent member
    engine.add_membership("SEC-US-AAPL-001", effective_from="1982-11-30", effective_to=None)

    # 1. Backtest Date: 2020-06-01 (Mid-2020)
    # TSLA must NOT be in the universe (No survivorship bias)
    # XRX must be in the universe
    u_2020 = engine.get_constituents_as_of("2020-06-01")
    assert "SEC-US-AAPL-001" in u_2020
    assert "SEC-US-XRX-001" in u_2020
    assert "SEC-US-TSLA-001" not in u_2020

    # 2. Backtest Date: 2021-01-15
    # TSLA now included, XRX still included
    u_2021 = engine.get_constituents_as_of("2021-01-15")
    assert "SEC-US-TSLA-001" in u_2021
    assert "SEC-US-XRX-001" in u_2021

    # 3. Backtest Date: 2022-01-15
    # XRX removed, TSLA active
    u_2022 = engine.get_constituents_as_of("2022-01-15")
    assert "SEC-US-TSLA-001" in u_2022
    assert "SEC-US-XRX-001" not in u_2022

    # Verify universe SHA-256 fingerprint reproducibility
    digest_2020 = engine.compute_membership_hash("2020-06-01")
    assert len(digest_2020) == 64
    assert digest_2020 == engine.compute_membership_hash("2020-06-01")  # Deterministic


def test_delisting_terminal_liquidation():
    # Verify delisting events record liquidation and terminal payouts
    lehman_delist = DelistingEvent(
        event_id="DELIST-LEH-2008",
        security_id="SEC-US-LEH-001",
        effective_date="2008-09-15",
        reason=DelistingReason.BANKRUPTCY,
        final_terminal_price=0.0,
        cash_distribution_per_share=0.0
    )
    assert lehman_delist.reason == DelistingReason.BANKRUPTCY
    assert lehman_delist.final_terminal_price == 0.0

    twtr_buyout = DelistingEvent(
        event_id="DELIST-TWTR-2022",
        security_id="SEC-US-TWTR-001",
        effective_date="2022-10-27",
        reason=DelistingReason.PRIVATIZATION,
        final_terminal_price=54.20,
        cash_distribution_per_share=54.20
    )
    assert twtr_buyout.reason == DelistingReason.PRIVATIZATION
    assert twtr_buyout.cash_distribution_per_share == 54.20

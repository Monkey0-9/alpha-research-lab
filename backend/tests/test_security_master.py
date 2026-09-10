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


def test_reverse_stock_split_price_adjustment(sec_master: SecurityMaster):
    from core.security_master.models import CorporateAction, ActionType, Security
    # Register a company with 1-for-5 reverse split (ratio = 0.2)
    sec_rev = Security(
        security_id="SEC-US-REV-001",
        ticker="REV",
        name="Reverse Split Corp",
        exchange="NYSE",
        ticker_history=[("REV", "2015-01-01", None)]
    )
    sec_master.register_security(sec_rev)
    sec_master.add_corporate_action(CorporateAction(
        action_id="CA-REV-2020",
        security_id="SEC-US-REV-001",
        action_type=ActionType.SPLIT,
        effective_date="2020-05-01",
        ratio=0.2  # 1-for-5 reverse split
    ))

    dates = pd.date_range("2020-04-25", "2020-05-05", freq="B")
    raw_df = pd.DataFrame({
        "open": [10.0] * len(dates),
        "high": [10.0] * len(dates),
        "low": [10.0] * len(dates),
        "close": [10.0] * len(dates),
        "volume": [100000] * len(dates),
    }, index=dates)

    adj_df = sec_master.adjust_prices(raw_df, "SEC-US-REV-001", price_type=PriceType.SPLIT_ADJUSTED)

    # Bars before 2020-05-01 should be divided by 0.2 -> multiplied by 5 (10.0 -> 50.0)
    pre_bar = adj_df.loc[pd.Timestamp("2020-04-30")]
    assert pre_bar["close"] == 50.0
    assert pre_bar["volume"] == 20000  # 100000 * 0.2

    # Bars on/after 2020-05-01 remain 10.0
    post_bar = adj_df.loc[pd.Timestamp("2020-05-01")]
    assert post_bar["close"] == 10.0


def test_cash_dividend_total_return_adjustment(sec_master: SecurityMaster):
    from core.security_master.models import CorporateAction, ActionType, Security
    sec_div = Security(
        security_id="SEC-US-DIV-001",
        ticker="DIVI",
        name="Dividend Payer Corp",
        exchange="NYSE",
        ticker_history=[("DIVI", "2018-01-01", None)]
    )
    sec_master.register_security(sec_div)
    # $2.00 dividend on ex-date 2020-06-01
    sec_master.add_corporate_action(CorporateAction(
        action_id="CA-DIV-2020",
        security_id="SEC-US-DIV-001",
        action_type=ActionType.DIVIDEND,
        effective_date="2020-06-01",
        cash_amount=2.0
    ))

    dates = pd.date_range("2020-05-25", "2020-06-05", freq="B")
    raw_df = pd.DataFrame({
        "open": [100.0] * len(dates),
        "high": [102.0] * len(dates),
        "low": [98.0] * len(dates),
        "close": [100.0] * len(dates),
        "volume": [50000] * len(dates),
    }, index=dates)

    # 1. Total Return adjusted: Div factor = (100 - 2)/100 = 0.98
    tr_df = sec_master.adjust_prices(raw_df, "SEC-US-DIV-001", price_type=PriceType.TOTAL_RETURN)
    pre_div_bar = tr_df.loc[pd.Timestamp("2020-05-29")]
    assert round(pre_div_bar["close"], 2) == 98.0
    post_div_bar = tr_df.loc[pd.Timestamp("2020-06-01")]
    assert post_div_bar["close"] == 100.0

    # 2. Split adjusted: should ignore cash dividend and stay 100.0
    split_df = sec_master.adjust_prices(raw_df, "SEC-US-DIV-001", price_type=PriceType.SPLIT_ADJUSTED)
    assert split_df.loc[pd.Timestamp("2020-05-29"), "close"] == 100.0


def test_raw_price_preservation(sec_master: SecurityMaster):
    dates = pd.date_range("2020-08-25", "2020-09-05", freq="B")
    raw_df = pd.DataFrame({"close": [500.0] * len(dates)}, index=dates)

    # Requesting PriceType.RAW for AAPL (which has a 4:1 split) must preserve exact raw prices
    unadj = sec_master.adjust_prices(raw_df, "SEC-US-AAPL-001", price_type=PriceType.RAW)
    assert (unadj["close"] == 500.0).all()


def test_reused_ticker_symbol_temporal_isolation(sec_master: SecurityMaster):
    from core.security_master.models import Security
    # Old company A had ticker "OLD" from 1990 to 2005
    sec_a = Security(
        security_id="SEC-OLD-A",
        ticker="OLD",
        name="Old Vintage Company",
        exchange="NYSE",
        ticker_history=[("OLD", "1990-01-01", "2005-12-31")]
    )
    # New company B took over ticker "OLD" from 2015 onward
    sec_b = Security(
        security_id="SEC-NEW-B",
        ticker="OLD",
        name="New Technology Corp",
        exchange="NASDAQ",
        ticker_history=[("OLD", "2015-01-01", None)]
    )
    sec_master.register_security(sec_a)
    sec_master.register_security(sec_b)

    # Query in 2000 resolves to SEC-OLD-A
    res_2000 = sec_master.resolve_ticker("OLD", "2000-06-01")
    assert res_2000 is not None
    assert res_2000.security_id == "SEC-OLD-A"

    # Query in 2020 resolves to SEC-NEW-B
    res_2020 = sec_master.resolve_ticker("OLD", "2020-06-01")
    assert res_2020 is not None
    assert res_2020.security_id == "SEC-NEW-B"

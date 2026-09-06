"""
Comprehensive Tests for Institutional Data Foundation (Task 2 / Milestone M1).
Verifies:
1. Permanent Security Master identity resolution across historical ticker changes.
2. Corporate actions unmutated store producing 4 distinct price series.
3. Historical universe constituent engine eliminating survivorship bias.
4. Bi-temporal 5-timestamp point-in-time isolation.
5. Dataset Registry cryptographic content and schema hashing.
"""
import pandas as pd
import numpy as np

from core.security_master.models import (
    CorporateAction,
    ActionType,
    PriceSeriesType,
)
from core.security_master.master import SecurityMaster
from core.security_master.corporate_actions import CorporateActionEngine
from core.universe.universe_engine import UniverseEngine
from core.pit_store import PointInTimeStore
from core.dataset_registry import DatasetRegistry


def test_permanent_security_master_symbology_and_history():
    """Verify permanent security identity across ticker renames (FB -> META)."""
    sm = SecurityMaster()

    # Meta resolution
    meta_sec = sm.resolve_ticker("FB", as_of_date="2018-05-15")
    assert meta_sec is not None
    assert meta_sec.security_id == "SEC-US-META-001"
    assert meta_sec.get_ticker_as_of("2018-05-15") == "FB"
    assert meta_sec.get_ticker_as_of("2024-01-01") == "META"

    # Alphabet resolution (GOOG -> GOOGL)
    goog_sec = sm.resolve_ticker("GOOG", as_of_date="2010-06-01")
    assert goog_sec is not None
    assert goog_sec.security_id == "SEC-US-GOOGL-001"
    assert goog_sec.get_ticker_as_of("2010-06-01") == "GOOG"
    assert goog_sec.get_ticker_as_of("2024-01-01") == "GOOGL"


def test_corporate_action_engine_four_price_series():
    """Verify that corporate actions produce 4 distinct series without mutating raw bars."""
    ca_engine = CorporateActionEngine()
    sec_id = "SEC-TEST-SPLIT-DIV"

    # Raw prices spanning 4 days
    dates = pd.date_range("2020-01-01", "2020-01-04", freq="D")
    raw_df = pd.DataFrame(
        {
            "open": [100.0, 102.0, 52.0, 54.0],
            "high": [105.0, 104.0, 55.0, 56.0],
            "low": [98.0, 100.0, 50.0, 52.0],
            "close": [100.0, 100.0, 50.0, 52.0],
            "volume": [1000.0, 1200.0, 2400.0, 2200.0],
        },
        index=dates,
    )
    raw_copy = raw_df.copy()

    # 2-for-1 split effective on 2020-01-03
    ca_engine.register_action(
        CorporateAction(
            action_id="CA-001",
            security_id=sec_id,
            action_type=ActionType.SPLIT,
            effective_date="2020-01-03",
            ratio=2.0,
        )
    )

    # Cash dividend of $1.00 effective on 2020-01-04
    ca_engine.register_action(
        CorporateAction(
            action_id="CA-002",
            security_id=sec_id,
            action_type=ActionType.DIVIDEND,
            effective_date="2020-01-04",
            cash_amount=1.00,
        )
    )

    # 1. RAW_PRICE (must be identical to raw_df)
    raw_res = ca_engine.generate_price_series(raw_df, sec_id, PriceSeriesType.RAW_PRICE)
    pd.testing.assert_frame_equal(raw_res, raw_copy)

    # 2. SPLIT_ADJUSTED (pre-split prices divided by 2.0; volumes multiplied by 2.0)
    split_res = ca_engine.generate_price_series(raw_df, sec_id, PriceSeriesType.SPLIT_ADJUSTED)
    assert np.isclose(split_res.loc["2020-01-01", "close"], 50.0)  # 100 / 2
    assert np.isclose(split_res.loc["2020-01-02", "close"], 50.0)  # 100 / 2
    assert np.isclose(split_res.loc["2020-01-03", "close"], 50.0)  # Post-split unchanged
    assert np.isclose(split_res.loc["2020-01-01", "volume"], 2000.0)  # 1000 * 2

    # 3. TOTAL_RETURN (splits + dividend factor reinvestment)
    tr_res = ca_engine.generate_price_series(raw_df, sec_id, PriceSeriesType.TOTAL_RETURN)
    assert tr_res.loc["2020-01-01", "close"] < split_res.loc["2020-01-01", "close"]

    # 4. TRADEABLE_PRICE (must equal raw executable price)
    trade_res = ca_engine.generate_price_series(raw_df, sec_id, PriceSeriesType.TRADEABLE_PRICE)
    pd.testing.assert_frame_equal(trade_res, raw_copy)

    # Critical invariant: raw_df MUST NOT be mutated!
    pd.testing.assert_frame_equal(raw_df, raw_copy)


def test_historical_universe_eliminates_survivorship():
    """Verify point-in-time universe additions and removals."""
    ue = UniverseEngine()

    # Tesla added in Dec 2020: absent in 2018, present in 2022
    members_2018 = ue.get_active_tickers("SP500", as_of_date="2018-06-01")
    members_2022 = ue.get_active_tickers("SP500", as_of_date="2022-06-01")

    assert "TSLA" not in members_2018
    assert "TSLA" in members_2022

    # Xerox removed March 2021: present in 2018, absent in 2022
    assert "XRX" in members_2018
    assert "XRX" not in members_2022


def test_bitemporal_pit_store_isolation():
    """Verify fundamental 5-timestamp temporal isolation and restatements."""
    dates = pd.date_range("2023-01-01", "2023-06-01", freq="D")
    sample_market = pd.DataFrame(
        {
            "close": [150.0] * len(dates),
            "volume": [1_000_000.0] * len(dates),
            "ticker": ["AAPL"] * len(dates),
            "date": dates,
        }
    )
    store = PointInTimeStore(data_df=sample_market)

    # Q1 earnings: period ended 2023-03-31, published 2023-05-04 at 16:30
    # Query on May 1 (before publication): must return None
    pre_pub = store.get_fundamental_as_of("AAPL", "eps", as_of_timestamp="2023-05-01 12:00:00")
    assert pre_pub is None

    # Query on May 5 (after publication, before restatement): returns 1.52
    post_pub = store.get_fundamental_as_of("AAPL", "eps", as_of_timestamp="2023-05-05 10:00:00")
    assert post_pub == 1.52

    # Query on June 20 (after restatement on June 15): returns restated 1.50
    post_restatement = store.get_fundamental_as_of("AAPL", "eps", as_of_timestamp="2023-06-20 10:00:00")
    assert post_restatement == 1.50


def test_dataset_registry_content_and_schema_hashing(tmp_path):
    """Verify immutable dataset registration and cryptographic checksums."""
    reg = DatasetRegistry(registry_dir=tmp_path)

    df = pd.DataFrame(
        {
            "date": pd.date_range("2023-01-01", periods=10),
            "ticker": ["AAPL"] * 10,
            "close": [150.0 + i for i in range(10)],
            "volume": [1000.0] * 10,
        }
    )
    p = tmp_path / "ds_sample.parquet"
    df.to_parquet(p)

    manifest = reg.register_dataset(
        dataset_id="DS-000001",
        df=df,
        provider="POLYGON",
        file_path=p,
        quality_status="PASS",
    )

    assert manifest.dataset_id == "DS-000001"
    assert manifest.version == 1
    assert len(manifest.content_hash) == 64
    assert len(manifest.schema_hash) == 64
    assert manifest.record_count == 10
    assert manifest.quality_status == "PASS"

    # Register next version
    manifest_v2 = reg.register_dataset(
        dataset_id="DS-000001",
        df=df,
        provider="POLYGON",
        file_path=p,
        quality_status="PASS",
    )
    assert manifest_v2.version == 2

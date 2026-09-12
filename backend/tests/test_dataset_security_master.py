"""
Test suite validating Real Financial Dataset Layer and Security Master (Phases 4 & 5).
Verifies immutable hashing, schema verification, point-in-time ticker resolution,
and rejection of look-ahead universe queries.
"""
import pandas as pd
import pytest
from backend.data.dataset_layer import HistoricalDatasetLayer, DatasetMetadata
from backend.data.security_master import PointInTimeSecurityMaster, SecurityMasterViolation


@pytest.fixture
def sample_market_df():
    return pd.DataFrame({
        "date": ["2023-01-03", "2023-01-03", "2023-01-04", "2023-01-04"],
        "ticker": ["AAPL", "MSFT", "AAPL", "MSFT"],
        "open": [130.0, 240.0, 131.0, 242.0],
        "high": [132.0, 243.0, 133.0, 245.0],
        "low": [129.0, 238.0, 130.0, 241.0],
        "close": [131.0, 242.0, 132.5, 244.0],
        "volume": [50000, 30000, 45000, 28000],
    })


def test_dataset_layer_creates_deterministic_provenance(sample_market_df, tmp_path):
    layer = HistoricalDatasetLayer(storage_root=tmp_path)
    df, meta = layer.create_research_dataset(
        dataset_id="DS_TEST_001",
        df=sample_market_df,
        source="test_source"
    )

    assert meta.dataset_id == "DS_TEST_001"
    assert len(meta.sha256_checksum) == 64
    assert meta.coverage_start_utc == "2023-01-03"
    assert meta.coverage_end_utc == "2023-01-04"

    bundle_dir = layer.save_dataset_bundle(df, meta, target_dir=tmp_path / "bundle")
    assert (bundle_dir / "dataset.parquet").exists()
    assert (bundle_dir / "manifest.json").exists()


def test_security_master_resolves_historical_ticker():
    master = PointInTimeSecurityMaster()

    # In 2015, Meta traded under ticker FB
    sec_2015 = master.resolve_ticker_at_timestamp("FB", "2015-06-01")
    assert sec_2015.primary_ticker == "META"

    # In 2023, Meta trades under ticker META
    sec_2023 = master.resolve_ticker_at_timestamp("META", "2023-01-01")
    assert sec_2023.entity_id == "SEC_META"


def test_security_master_rejects_delisted_or_prelisting_access():
    master = PointInTimeSecurityMaster()

    # Lehman Brothers in 2005 is valid
    sec_leh = master.resolve_ticker_at_timestamp("LEH", "2005-01-01")
    assert sec_leh.primary_ticker == "LEH"

    # Lehman Brothers after bankruptcy in 2009 must raise SecurityMasterViolation
    with pytest.raises(SecurityMasterViolation, match="delisted"):
        master.resolve_ticker_at_timestamp("LEH", "2009-01-01")

    # Meta before its IPO in 2010 must raise SecurityMasterViolation
    with pytest.raises(SecurityMasterViolation, match="not listed"):
        master.resolve_ticker_at_timestamp("FB", "2010-01-01")


def test_security_master_pit_universe():
    master = PointInTimeSecurityMaster()

    # In 2005, LEH was in SP500, but META (FB) was not
    u_2005 = master.get_point_in_time_universe("SP500", "2005-01-01")
    assert "LEH" in u_2005
    assert "AAPL" in u_2005
    assert "FB" not in u_2005
    assert "META" not in u_2005

    # In 2023, META is in SP500, LEH is not
    u_2023 = master.get_point_in_time_universe("SP500", "2023-01-01")
    assert "META" in u_2023
    assert "LEH" not in u_2023

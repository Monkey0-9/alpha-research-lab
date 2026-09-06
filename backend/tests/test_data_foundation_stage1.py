"""
Stage 1 Data Foundation Unit Tests.
Tests DuckDB analytical engine, Arrow zero-copy query, True PIT extraction,
Dataset Registry cryptographic hashing, and Data Quality Engine fail-closed behavior.
"""
from datetime import datetime, timezone, timedelta
import pandas as pd
import pyarrow as pa
import polars as pl
import pytest

from backend.core.storage.duckdb_engine import DuckDBEngine
from backend.core.dataset_registry import DatasetRegistry
from backend.core.data_quality import DataQualityEngine, QualityStatus


@pytest.fixture
def sample_parquet_file(tmp_path):
    """Generate a clean sample parquet file with multi-temporal timestamps."""
    dates = pd.date_range("2023-01-01", periods=10, freq="D")
    records = []
    for d in dates:
        # Publication and availability is next morning at 09:00 UTC
        avail = d + timedelta(hours=33)
        records.append({
            "security_id": "SEC-US-AAPL-001",
            "observation_time": str(d),
            "available_time": str(avail),
            "open": 150.0,
            "high": 155.0,
            "low": 149.0,
            "close": 152.0,
            "volume": 1000000,
        })
    df = pd.DataFrame(records)
    file_path = tmp_path / "sample_stage1.parquet"
    df.to_parquet(file_path, index=False)
    return file_path, df


def test_duckdb_parquet_arrow_and_polars(sample_parquet_file):
    file_path, df = sample_parquet_file
    engine = DuckDBEngine()

    # Query via Arrow
    p_str = str(file_path.resolve()).replace("\\", "/")
    arrow_tbl = engine.query_arrow(f"SELECT * FROM read_parquet('{p_str}')")
    assert isinstance(arrow_tbl, pa.Table)
    assert arrow_tbl.num_rows == 10
    assert "close" in arrow_tbl.column_names

    # Query via Polars
    pl_df = engine.query_polars(f"SELECT security_id, close, volume FROM read_parquet('{p_str}')")
    assert isinstance(pl_df, pl.DataFrame)
    assert len(pl_df) == 10
    assert pl_df["close"].sum() == 1520.0

    # Test forward returns window calculation
    fwd_df = engine.compute_forward_returns(file_path, horizons=[1, 2])
    assert "fwd_ret_1d" in fwd_df.columns
    assert "fwd_ret_2d" in fwd_df.columns
    assert len(fwd_df) == 10


def test_duckdb_point_in_time_isolation(tmp_path):
    """
    Test that an observation observed on Jan 1 but only available on Jan 2 09:00
    is NOT accessible when querying as_of Jan 1 23:59.
    """
    data = [
        {
            "security_id": "SEC-001",
            "observation_time": "2023-01-01 16:00:00",
            "available_time": "2023-01-02 09:00:00",  # Lagged filing
            "close": 100.0,
        },
        {
            "security_id": "SEC-001",
            "observation_time": "2023-01-02 16:00:00",
            "available_time": "2023-01-03 09:00:00",
            "close": 102.0,
        },
    ]
    file_path = tmp_path / "pit_test.parquet"
    pd.DataFrame(data).to_parquet(file_path, index=False)

    engine = DuckDBEngine()

    # As of Jan 1 at 23:59, nothing is available yet
    tbl_t0 = engine.point_in_time_query(file_path, as_of_time="2023-01-01 23:59:59")
    assert tbl_t0.num_rows == 0

    # As of Jan 2 at 12:00, only the first record is available
    tbl_t1 = engine.point_in_time_query(file_path, as_of_time="2023-01-02 12:00:00")
    assert tbl_t1.num_rows == 1
    assert tbl_t1.column("close")[0].as_py() == 100.0

    # As of Jan 3 at 12:00, both records are available
    tbl_t2 = engine.point_in_time_query(file_path, as_of_time="2023-01-03 12:00:00")
    assert tbl_t2.num_rows == 2


def test_dataset_registry_model_and_hashing(tmp_path, sample_parquet_file):
    file_path, df = sample_parquet_file
    reg = DatasetRegistry(registry_dir=tmp_path / "registry")

    # Register version 1
    m1 = reg.register_dataset(
        dataset_id="DS-EQUITY-DAILY-TEST",
        df=df,
        provider="TEST_VENDOR",
        file_path=file_path,
        quality_status="PASS",
    )
    assert m1.version == 1
    assert len(m1.content_hash) == 64
    assert len(m1.schema_hash) == 64
    assert m1.quality_status == "PASS"

    # Verify integrity passes
    assert reg.verify_integrity("DS-EQUITY-DAILY-TEST", 1) is True

    # Tamper with file
    with open(file_path, "ab") as f:
        f.write(b"CORRUPTED_BYTES")

    # Integrity verification must now detect tampering and return False
    assert reg.verify_integrity("DS-EQUITY-DAILY-TEST", 1) is False


def test_data_quality_engine_clean_data(sample_parquet_file):
    _, df = sample_parquet_file
    engine = DataQualityEngine()
    report = engine.validate_dataset(df)
    assert report.overall_status == QualityStatus.PASS
    assert len(report.errors) == 0


def test_data_quality_engine_fails_closed_on_violations():
    engine = DataQualityEngine()

    # 1. High < Low violation
    bad_hl_df = pd.DataFrame({
        "security_id": ["SEC-001"],
        "observation_time": ["2023-01-01"],
        "open": [100.0],
        "high": [90.0],  # High < Low!
        "low": [95.0],
        "close": [92.0],
        "volume": [1000],
    })
    r1 = engine.validate_dataset(bad_hl_df)
    assert r1.overall_status == QualityStatus.FAIL
    assert any("High < Low" in err for err in r1.errors)

    # 2. Negative volume violation
    bad_vol_df = pd.DataFrame({
        "security_id": ["SEC-001"],
        "observation_time": ["2023-01-01"],
        "close": [100.0],
        "volume": [-500],  # Negative volume!
    })
    r2 = engine.validate_dataset(bad_vol_df)
    assert r2.overall_status == QualityStatus.FAIL
    assert any("negative volume" in err.lower() for err in r2.errors)

    # 3. Duplicate primary keys violation
    bad_dupe_df = pd.DataFrame({
        "security_id": ["SEC-001", "SEC-001"],
        "observation_time": ["2023-01-01", "2023-01-01"],  # Duplicate!
        "close": [100.0, 101.0],
        "volume": [1000, 2000],
    })
    r3 = engine.validate_dataset(bad_dupe_df)
    assert r3.overall_status == QualityStatus.FAIL
    assert any("duplicate" in err.lower() for err in r3.errors)

    # 4. Future timestamp violation
    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
    bad_time_df = pd.DataFrame({
        "security_id": ["SEC-001"],
        "observation_time": [future_date],
        "close": [100.0],
        "volume": [1000],
    })
    r4 = engine.validate_dataset(bad_time_df)
    assert r4.overall_status == QualityStatus.FAIL
    assert any("future" in err.lower() for err in r4.errors)

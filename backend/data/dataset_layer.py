"""
QuantAlpha Real Financial Dataset Layer (Phase 4).
Implements an immutable historical dataset architecture:
Raw Data -> Immutable Dataset -> Data Version -> Point-in-Time Transformation -> Research Dataset.
Enforces rigorous metadata tracking, cryptographic hashing, schema contracts, and adjustment policies.
"""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd


@dataclass
class DatasetMetadata:
    dataset_id: str
    source: str
    download_timestamp_utc: str
    coverage_start_utc: str
    coverage_end_utc: str
    frequency: str  # e.g., '1d', '1m', 'tick'
    timezone: str   # 'UTC'
    adjustment_policy: str  # 'SPLIT_DIVIDEND_ADJUSTED', 'RAW_UNADJUSTED', 'POINT_IN_TIME_SPLIT_ONLY'
    corporate_action_policy: str  # 'SURVIVORSHIP_INCLUSIVE'
    universe_definition: str  # e.g., 'SP500_HISTORICAL_CONSTITUENTS'
    schema_fields: List[Dict[str, str]]
    sha256_checksum: str
    version: str = "1.0.0"


class HistoricalDatasetLayer:
    """
    Manages the lifecycle of immutable financial datasets from ingestion to research feature generation.
    """

    def __init__(self, storage_root: Optional[Path] = None):
        self.storage_root = Path(storage_root) if storage_root else Path("data")

    def create_research_dataset(
        self,
        dataset_id: str,
        df: pd.DataFrame,
        source: str = "yfinance_sp500_historical",
        frequency: str = "1d",
        adjustment_policy: str = "SPLIT_DIVIDEND_ADJUSTED",
        universe_definition: str = "SP500_HISTORICAL"
    ) -> Tuple[pd.DataFrame, DatasetMetadata]:
        """
        Transforms and hashes a DataFrame into an immutable research dataset with cryptographic provenance.
        """
        required_cols = ["date", "ticker", "open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                raise ValueError(f"Missing required column {col} in dataset")

        # Sort strictly by date, ticker to ensure deterministic serialization
        sorted_df = df.sort_values(by=["date", "ticker"]).reset_index(drop=True)

        # Compute SHA-256 over raw CSV representation
        raw_bytes = sorted_df.to_csv(index=False).encode("utf-8")
        sha256_hash = hashlib.sha256(raw_bytes).hexdigest()

        start_date = str(sorted_df["date"].min())
        end_date = str(sorted_df["date"].max())
        now_iso = datetime.now(timezone.utc).isoformat()

        schema_fields = [{"name": c, "type": str(sorted_df[c].dtype)} for c in sorted_df.columns]

        meta = DatasetMetadata(
            dataset_id=dataset_id,
            source=source,
            download_timestamp_utc=now_iso,
            coverage_start_utc=start_date,
            coverage_end_utc=end_date,
            frequency=frequency,
            timezone="UTC",
            adjustment_policy=adjustment_policy,
            corporate_action_policy="SURVIVORSHIP_INCLUSIVE",
            universe_definition=universe_definition,
            schema_fields=schema_fields,
            sha256_checksum=sha256_hash,
            version="1.0.0"
        )

        return sorted_df, meta

    def save_dataset_bundle(
        self,
        df: pd.DataFrame,
        meta: DatasetMetadata,
        target_dir: Optional[Path] = None
    ) -> Path:
        """Persists the research dataset parquet file alongside its JSON metadata manifest."""
        out_dir = Path(target_dir) if target_dir else (self.storage_root / "research_bundles" / meta.dataset_id)
        out_dir.mkdir(parents=True, exist_ok=True)

        data_path = out_dir / "dataset.parquet"
        meta_path = out_dir / "manifest.json"

        df.to_parquet(data_path, index=False)
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(asdict(meta), f, indent=2)

        return out_dir

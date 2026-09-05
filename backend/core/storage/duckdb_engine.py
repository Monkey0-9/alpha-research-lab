"""
DuckDB High-Performance Analytical Storage Engine.
Executes zero-copy analytical queries over versioned Parquet datasets
yielding Arrow tables, Polars dataframes, and Pandas series.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import duckdb
import pyarrow as pa
import polars as pl
import pandas as pd

logger = logging.getLogger(__name__)


class DuckDBEngine:
    """Analytical query engine backed by DuckDB for zero-copy Parquet and Arrow processing."""

    def __init__(self, db_path: str = ":memory:"):
        self.conn = duckdb.connect(database=db_path)
        # Configure optimizations
        try:
            self.conn.execute("SET preserve_insertion_order=false;")
            self.conn.execute("SET threads TO 4;")
        except Exception as e:
            logger.debug(f"DuckDB configuration adjustment: {e}")

    def register_parquet(self, view_name: str, parquet_path: Union[str, Path]) -> None:
        """Register a parquet file or directory as a virtual SQL table/view."""
        p_str = str(Path(parquet_path).resolve()).replace("\\", "/")
        query = f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{p_str}');"
        self.conn.execute(query)
        logger.info(f"Registered view '{view_name}' from {p_str}")

    def query_arrow(self, sql: str, params: Optional[List[Any]] = None) -> pa.Table:
        """Execute query and return Apache Arrow Table (zero-copy)."""
        rel = self.conn.execute(sql, params or [])
        res = rel.arrow()
        if hasattr(res, "read_all"):
            return res.read_all()
        return res

    def query_polars(self, sql: str, params: Optional[List[Any]] = None) -> pl.DataFrame:
        """Execute query and return Polars DataFrame."""
        arrow_table = self.query_arrow(sql, params)
        return pl.from_arrow(arrow_table)

    def query_pandas(self, sql: str, params: Optional[List[Any]] = None) -> pd.DataFrame:
        """Execute query and return Pandas DataFrame."""
        rel = self.conn.execute(sql, params or [])
        return rel.df()

    def point_in_time_query(
        self,
        parquet_path: Union[str, Path],
        as_of_time: str,
        security_ids: Optional[List[str]] = None,
        columns: Optional[List[str]] = None,
    ) -> pa.Table:
        """
        Strict multi-temporal Point-in-Time extraction.
        Guarantees that NO record published or revised after as_of_time enters the sample.
        Predicate: available_time <= as_of_time
        """
        p_str = str(Path(parquet_path).resolve()).replace("\\", "/")
        cols_str = ", ".join(columns) if columns else "*"

        if security_ids:
            sec_list_str = ", ".join(f"'{s}'" for s in security_ids)
            sec_filter = f"AND security_id IN ({sec_list_str})"
        else:
            sec_filter = ""

        sql = f"""
            SELECT {cols_str}
            FROM read_parquet('{p_str}')
            WHERE available_time <= ?
              {sec_filter}
            ORDER BY observation_time ASC, security_id ASC
        """
        return self.query_arrow(sql, [as_of_time])

    def compute_forward_returns(
        self,
        parquet_path: Union[str, Path],
        horizons: List[int] = [1, 5, 20],
        price_col: str = "close",
    ) -> pl.DataFrame:
        """
        Compute forward returns vectorized inside DuckDB using window functions.
        Avoids loading entire universe prices into Python RAM.
        """
        p_str = str(Path(parquet_path).resolve()).replace("\\", "/")
        fwd_clauses = [
            f"(LEAD({price_col}, {h}) OVER (PARTITION BY security_id ORDER BY observation_time) / NULLIF({price_col}, 0.0) - 1.0) AS fwd_ret_{h}d"
            for h in horizons
        ]
        clauses_str = ", ".join(fwd_clauses)

        sql = f"""
            SELECT
                security_id,
                observation_time,
                available_time,
                {price_col},
                {clauses_str}
            FROM read_parquet('{p_str}')
            ORDER BY security_id, observation_time
        """
        return self.query_polars(sql)

    def calculate_universe_summary(self, parquet_path: Union[str, Path]) -> Dict[str, Any]:
        """Compute quick summary statistics of a dataset via DuckDB."""
        p_str = str(Path(parquet_path).resolve()).replace("\\", "/")
        sql = f"""
            SELECT
                COUNT(DISTINCT security_id) AS num_securities,
                COUNT(*) AS total_rows,
                MIN(observation_time) AS start_date,
                MAX(observation_time) AS end_date,
                MIN(available_time) AS min_available_time,
                MAX(available_time) AS max_available_time
            FROM read_parquet('{p_str}')
        """
        df = self.conn.execute(sql).df()
        if df.empty:
            return {}
        row = df.iloc[0].to_dict()
        return {k: str(v) if not isinstance(v, (int, float)) else v for k, v in row.items()}


_DUCKDB_ENGINE: Optional[DuckDBEngine] = None


def get_duckdb_engine() -> DuckDBEngine:
    """Singleton getter for the DuckDB query engine."""
    global _DUCKDB_ENGINE
    if _DUCKDB_ENGINE is None:
        _DUCKDB_ENGINE = DuckDBEngine()
    return _DUCKDB_ENGINE

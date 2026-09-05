"""
Storage package for analytical data engines (DuckDB, Arrow, Parquet).
"""
from backend.core.storage.duckdb_engine import DuckDBEngine, get_duckdb_engine

__all__ = ["DuckDBEngine", "get_duckdb_engine"]

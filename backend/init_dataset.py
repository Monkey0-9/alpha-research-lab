"""
QuantAlpha — Market Dataset Initializer
Initializes or refreshes baseline S&P 500 Parquet dataset using real
market data from Yahoo Finance / Robinhood, with deterministic offline
resilience.
"""
import argparse
import sys
from pathlib import Path

# Add backend directory to sys.path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from core.data_pipeline import (  # noqa: E402
    data_pipeline,
    DEFAULT_TICKERS,
    PARQUET_PATH,
)


def init_dataset(
    provider: str = "yfinance",
    offline: bool = False,
    start: str = "2020-01-01",
    end: str = "2024-12-31",
):
    print("=== QuantAlpha Dataset Initialization ===")
    print(f"Target file: {PARQUET_PATH}")
    print(
        f"Universe: {len(DEFAULT_TICKERS)} tickers | "
        f"Provider: {provider} | Offline mode: {offline}"
    )

    if not offline:
        try:
            print(f"Fetching real market data from {provider}...")
            result = data_pipeline.run_pipeline(
                provider=provider,
                start=start,
                end=end,
                persist=True
            )
            print(
                f"Ingestion successful! "
                f"Records: {result['records_count']} | "
                f"Clean %: {result['clean_pct']}% | "
                f"Time: {result['elapsed_seconds']}s"
            )
            return
        except Exception as e:
            print(
                f"Live market fetch encountered error: {e}. "
                "Generating offline dataset fallback..."
            )

    # Offline / fallback generation
    import numpy as np
    import pandas as pd

    dates = pd.date_range(start, end, freq="B")
    n_dates = len(dates)
    frames = []
    np.random.seed(42)

    for ticker in DEFAULT_TICKERS:
        drift = np.random.uniform(0.0003, 0.0008)
        vol = np.random.uniform(0.012, 0.024)
        daily_returns = np.random.normal(drift, vol, n_dates)

        # COVID shock
        covid_mask = (dates >= "2020-02-20") & (dates <= "2020-03-23")
        daily_returns[covid_mask] -= np.random.uniform(0.015, 0.035, np.sum(covid_mask))

        price = 100.0 * np.cumprod(1.0 + daily_returns)
        volume = np.random.lognormal(
            mean=16.5, sigma=0.5, size=n_dates
        )

        df_t = pd.DataFrame({
            "date": dates,
            "ticker": ticker,
            "open": price * np.random.uniform(0.995, 1.002, n_dates),
            "high": price * np.random.uniform(1.005, 1.025, n_dates),
            "low": price * np.random.uniform(0.975, 0.995, n_dates),
            "close": price,
            "volume": volume.astype(int),
            "return_1d": daily_returns
        })
        frames.append(df_t)

    full_df = pd.concat(frames, ignore_index=True)
    full_df = full_df.set_index(["date", "ticker"]).sort_index()
    full_df.to_parquet(PARQUET_PATH)
    print(
        f"Successfully generated {len(full_df)} records across "
        f"{len(DEFAULT_TICKERS)} tickers in {PARQUET_PATH}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize QuantAlpha S&P 500 Market Dataset"
    )
    parser.add_argument(
        "--provider",
        choices=["yfinance", "robinhood", "hybrid"],
        default="yfinance",
        help="Market data provider",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Force generate offline deterministic dataset",
    )
    parser.add_argument(
        "--start",
        default="2020-01-01",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        default="2024-12-31",
        help="End date (YYYY-MM-DD)",
    )
    args = parser.parse_args()

    init_dataset(
        provider=args.provider,
        offline=args.offline,
        start=args.start,
        end=args.end,
    )

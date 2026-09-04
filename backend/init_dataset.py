"""
Generate or download baseline 2019-2024 S&P 500 Parquet dataset.
"""
import numpy as np
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
PARQUET_PATH = DATA_DIR / "sp500_daily.parquet"

TICKERS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY", "AVGO", "TSLA",
    "JPM", "V", "UNH", "XOM", "MA", "JNJ", "PG", "COST", "HD", "MRK",
    "ABBV", "CVX", "KO", "ORCL", "PEP", "WMT", "BAC", "MCD", "CRM", "ACN",
    "TMO", "CSCO", "NFLX", "ABT", "AMD", "ADBE", "DHR", "LIN", "TXN", "NKE",
    "NEE", "PM", "QCOM", "DIS", "VZ", "INTC", "WFC", "RTX", "COP", "BMY",
]

dates = pd.date_range("2019-01-02", "2024-12-31", freq="B")
n_dates = len(dates)

frames = []
np.random.seed(42)

for ticker in TICKERS:
    # Drift and vol tailored to ticker
    drift = np.random.uniform(0.0003, 0.0008)
    vol = np.random.uniform(0.012, 0.024)
    daily_returns = np.random.normal(drift, vol, n_dates)
    
    # 2020 COVID shock
    covid_mask = (dates >= "2020-02-20") & (dates <= "2020-03-23")
    daily_returns[covid_mask] -= np.random.uniform(0.015, 0.035, np.sum(covid_mask))
    
    # 2020-2021 Tech recovery
    recovery_mask = (dates >= "2020-04-01") & (dates <= "2021-11-01")
    daily_returns[recovery_mask] += np.random.uniform(0.0005, 0.0015, np.sum(recovery_mask))

    price = 100.0 * np.cumprod(1.0 + daily_returns)
    volume = np.random.lognormal(mean=16.5, sigma=0.5, size=n_dates)

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
print(f"Successfully generated {len(full_df)} records across {len(TICKERS)} tickers in {PARQUET_PATH}")

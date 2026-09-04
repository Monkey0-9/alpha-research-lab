"""
QuantAlpha Research Lab - Configuration & Settings
Institutional Quant Configuration Engine
"""
from pathlib import Path
import os
from typing import List

# Base Paths
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(PROJECT_ROOT / "data")))
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(BASE_DIR / "models")))

DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# API Keys
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
FRED_API_KEY = os.getenv("FRED_API_KEY", "")

# Backtest Defaults
DEFAULT_UNIVERSE = os.getenv("DEFAULT_UNIVERSE", "sp500")
DEFAULT_REBALANCE_FREQ = os.getenv("DEFAULT_REBALANCE_FREQ", "M")
DEFAULT_TRANSACTION_COST = float(os.getenv("DEFAULT_TRANSACTION_COST", "0.001"))

# Risk & Quality Gate Defaults
DEFAULT_VAR_CONFIDENCE = float(os.getenv("DEFAULT_VAR_CONFIDENCE", "0.95"))
TARGET_VOLATILITY = float(os.getenv("TARGET_VOLATILITY", "0.10"))
QUALITY_GATE_MIN_SHARPE = float(os.getenv("QUALITY_GATE_MIN_SHARPE", "1.0"))
QUALITY_GATE_MAX_DRAWDOWN = float(os.getenv("QUALITY_GATE_MAX_DRAWDOWN", "0.15"))
QUALITY_GATE_MIN_IC = float(os.getenv("QUALITY_GATE_MIN_IC", "0.03"))

# Tickers universe (Liquid S&P 500 constituents)
CORE_UNIVERSE: List[str] = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "BRK-B", "LLY", "AVGO", "TSLA",
    "JPM", "V", "UNH", "XOM", "MA", "JNJ", "PG", "COST", "HD", "MRK",
    "ABBV", "CVX", "KO", "ORCL", "PEP", "WMT", "BAC", "MCD", "CRM", "ACN",
    "TMO", "CSCO", "NFLX", "ABT", "AMD", "ADBE", "DHR", "LIN", "TXN", "NKE",
    "NEE", "PM", "QCOM", "DIS", "VZ", "INTC", "WFC", "RTX", "COP", "BMY"
]

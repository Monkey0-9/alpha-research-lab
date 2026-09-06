# QuantAlpha — Institution-Inspired Quantitative Research & Alpha Discovery Platform

Institution-inspired quantitative research and alpha discovery platform with PIT-aware data handling, adversarial validation, statistical multiple-testing controls, native C/C++/Rust acceleration, portfolio/risk research and reproducible experiment lineage. QuantAlpha integrates a high-performance Python FastAPI quantitative research backend with real-market data provider abstractions (**Yahoo Finance `yfinance`** and **Robinhood `robin_stocks`**), native C/C++/Rust accelerators, and a Next.js 16 / React 19 quantitative research portal.

---

## 🌟 Architecture & Modules Overview

The platform is organized into 13 synchronized modules covering the quantitative investment lifecycle from raw tick/OHLCV data ingestion to live execution and telemetry:

| # | Module | Route | Backend API | Key Quantitative Capabilities |
|---|---|---|---|---|
| **00** | **Executive Dashboard** | [`/`](src/app/page.tsx) | [`/api/dashboard/summary`](backend/api/dashboard.py) | Live portfolio metrics, active P&L dynamics, multi-engine telemetry, alert streams |
| **01** | **Data Infrastructure** | [`/data`](src/app/data/page.tsx) | [`/api/data/*`](backend/api/data.py) | **Real-market pipeline (Yahoo Finance & Robinhood)**, Point-In-Time (PIT) join engine, streaming quotes |
| **02** | **Feature / Signal Factory** | [`/features`](src/app/features/page.tsx) | [`/api/features/*`](backend/api/features.py) | 50+ time-series features (price, fundamental, microstructure) with strict lag shifts & rolling IC analysis |
| **03** | **Alpha Discovery Lab** | [`/alpha-discovery`](src/app/alpha-discovery/page.tsx) | [`/api/backtest/*`](backend/api/backtest.py) | Genetic programming expression search, ML feature importance ranking, hypothesis pipeline, IC vs Sharpe |
| **04** | **Statistical Engine** | [`/statistical-engine`](src/app/statistical-engine/page.tsx) | [`/api/validation/statistics`](backend/api/validation.py) | Multiple testing correction (Bonferroni, Benjamini-Hochberg FDR), Deflated Sharpe Ratio (DSR), decay half-life |
| **05** | **Model Research Lab** | [`/model-lab`](src/app/model-lab/page.tsx) | [`/api/model-lab/*`](backend/api/model_lab.py) | Multi-model benchmarking (LightGBM, XGBoost, Random Forest, Ridge), meta-labeling, stacking & blending ensembles |
| **06** | **Time-Series Validation** | [`/validation`](src/app/validation/page.tsx) | [`/api/validation/*`](backend/api/validation.py) | Walk-forward cross-validation (12 folds), purged K-fold with embargo windows, 3-state HMM regime audits |
| **07** | **Alpha Quality Gate** | [`/quality-gate`](src/app/quality-gate/page.tsx) | [`/api/quality-gate/*`](backend/api/quality_gate.py) | Strict 9-criteria pass/fail gate (IC, OOS, FDR, decay, turnover, correlation, drawdown, regime, capacity) |
| **08** | **Portfolio Engine** | [`/portfolio`](src/app/portfolio/page.tsx) | [`/api/portfolio/*`](backend/api/portfolio.py) | Markowitz Mean-Variance (MVO), Hierarchical Risk Parity (HRP), CVaR minimization, Efficient Frontier |
| **09** | **Execution Research** | [`/execution`](src/app/execution/page.tsx) | [`/api/execution/*`](backend/api/execution.py) | Almgren-Chriss market impact solver, TWAP/VWAP simulator, venue fill quality, slippage models |
| **10** | **Risk Engine** | [`/risk`](src/app/risk/page.tsx) | [`/api/risk/*`](backend/api/risk.py) | Historical & Parametric VaR / CVaR (95% & 99%), Barra factor risk decomposition, CPPI drawdown control |
| **11** | **Live Research** | [`/live-research`](src/app/live-research/page.tsx) | [`/api/live-research/*`](backend/api/live_research.py) | Paper trading simulator, paper-to-production promotion criteria, live production alpha health |
| **12** | **Production Monitor** | [`/monitoring`](src/app/monitoring/page.tsx) | [`/api/monitoring/*`](backend/api/monitoring.py) | Real-time system telemetry, alpha decay alerts, feature drift (Population Stability Index - PSI) |

---

## 📡 Real-Market Research Data Pipeline (Yahoo Finance & Robinhood)

QuantAlpha includes an automated real-market research data pipeline and provider abstraction in `backend/core/` and `backend/api/data.py`:

```
                    ┌─────────────────────────┐
                    │   Yahoo Finance (YF)    │ (OHLCV, Splits, Dividends, Multi-thread)
                    └────────────┬────────────┘
                                 │
┌─────────────────────────┐      │      ┌─────────────────────────┐
│  Robinhood API (RH)     ├──────┼─────►│  MarketDataPipeline     │
│  (Quotes, Depth, Crypto)│      │      │  (Hampel Filter, Clean, │
└─────────────────────────┘      │      │   Survivorship Adjust)  │
                                 │      └────────────┬────────────┘
                                 │                   │
                                 ▼                   ▼
                    ┌─────────────────────────────────────────────┐
                    │       Immutable PIT Parquet Datastore       │
                    │        data/sp500_daily.parquet             │
                    └──────────────────────┬──────────────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │      FastAPI Endpoints & Next.js UI         │
                    │  (/api/data/pipeline/sync, /live-quote)     │
                    └─────────────────────────────────────────────┘
```

### Key Capabilities:
- **Yahoo Finance Client (`backend/core/yfinance_client.py`)**:
  - Multi-threaded batch historical downloads with automatic adjustment for stock splits and cash dividends.
  - Real-time quote streaming with bid/ask, trailing PE, market cap, and 52-week statistics.
  - Macro index benchmark feeds (`SPY`, `QQQ`, `DIA`, `^VIX`, `^TNX`).
- **Robinhood Client (`backend/core/robinhood_client.py`)**:
  - Real-time NBBO quotes, bid/ask depth spread, and volume tracking.
  - Crypto quote streaming (`BTC-USD`, `ETH-USD`).
  - Market operating schedule and extended-hours trading detector.
  - Optional authenticated institutional login with session persistence and MFA/TOTP.
- **Unified Pipeline (`backend/core/data_pipeline.py`)**:
  - Automated cleaning: forward-fills small gaps, eliminates duplicates, and scrubs bad ticks using a rolling 20-day Hampel filter ($Z > 4.5$).
  - Point-in-Time (PIT) partition alignment and local Parquet persistence (`data/sp500_daily.parquet`).
  - Zero-breakage offline fallback ensuring offline unit tests execute with deterministic sub-second speed.

### Real Market CLI Commands:
```bash
# Ingest live market data from Yahoo Finance
.venv\Scripts\python backend/core/data_pipeline.py --provider yfinance --start 2020-01-01 --update

# Ingest live market data from Robinhood
.venv\Scripts\python backend/core/data_pipeline.py --provider robinhood --start 2020-01-01 --update

# Hybrid dual-feed ingestion
.venv\Scripts\python backend/core/data_pipeline.py --provider hybrid --start 2020-01-01 --update

# Initialize dataset script with real market provider
.venv\Scripts\python backend/init_dataset.py --provider yfinance
```

---

## ⚡ High-Performance Native Accelerators

The backend includes a polyglot acceleration bridge (`backend/native/native_bridge.py`) with zero-overhead fallback:
- **Rust FFI (`rust_engine`)**: Sub-microsecond calculation of annualized Sharpe ratio, Maximum Drawdown, historical CVaR tail risk, and vector portfolio P&L.
- **C++ Solver (`cpp_engine`)**: Almgren-Chriss optimal liquidation trajectory solver and order fill simulator.
- **C SIMD (`c_engine`)**: Vectorized rolling mean, standard deviation, exponential moving average, and RSI.
- **Q / KDB+ (`q_service.py`)**: Vector tick-to-bar aggregation and Volume-Weighted Average Price (VWAP) queries.
- **R Econometrics (`attribution.R`)**: Multi-factor Barra econometric regression and residual risk decomposition.
- **OCaml Rules (`quality_rules.ml`)**: Type-safe formal verification of the 9 Alpha Quality Gate thresholds.

---

## 🧪 Testing & Verification Suite

The repository contains automated unit and integration tests across both the Python computational core and TypeScript frontend:

### 1. Python Backend Pytest Suite (76 Tests)
```bash
# Run all backend unit and API integration tests
.venv\Scripts\python -m pytest backend/tests/ -v
```
- **`test_real_market_pipeline.py`** (8 tests): Real-market Yahoo Finance client, Robinhood client, market hours, crypto quotes, pipeline cleaning, and API sync endpoints.
- **`test_api.py`** (16 tests): Core router endpoints for health, data, features, validation, portfolio, risk, execution, quality gate, and live research.
- **`test_api_comprehensive.py`** (12 tests): In-depth API integration across all parameter options and data schemas.
- **`test_core.py`** (7 tests): Native accelerator bridges, FDR multiple testing, Deflated Sharpe Ratio, and quality gate logic.
- **`test_core_advanced.py`** (16 tests): Advanced quant algorithms (PIT store, multi-horizon labels, vol targeting, VaR/CVaR, CPPI, MVO, HRP, 3-state HMM, Almgren-Chriss, PSI drift, meta-labeling).
- **`test_data_loader.py`** (3 tests): Data ingestion, survivorship-bias elimination, and PIT point-in-time temporal isolation.
- **`test_features.py`** (3 tests): 50+ features with `.shift(1)` lookahead protection.
- **`test_models.py`** (2 tests): Model training pipeline and ensemble comparison leaderboard.
- **`test_portfolio.py`** (2 tests): HRP and Markowitz optimization constraints.
- **`test_risk.py`** (2 tests): VaR, CVaR, and Barra factor decomposition.
- **`test_validation.py`** (2 tests): Walk-forward cross-validation and purged K-fold CV.
- **`test_backtester.py`** (3 tests): Temporal backtesting, leakage prevention, and transaction cost modeling.

### 2. Frontend Node Test Runner (11 Tests)
```bash
# Run frontend quant generator and metric tests
npm test
```
All 11 tests pass with 0 failures in ~135ms.

### 3. Frontend Typecheck & Lint
```bash
# Verify TypeScript strict type-safety
npm run typecheck

# Check React 19 compiler hygiene & ESLint rules
npm run lint
```

### 4. Production Build Verification
```bash
# Build optimized Next.js production bundle with Turbopack
npm run build
```
All 14 application routes prerender cleanly as static content.

---

## 🚀 Getting Started

### Local Development

#### 1. Backend Server
```bash
# Ensure Python virtual environment is activated
.venv\Scripts\activate

# (Optional) Set environment variables for Robinhood in .env:
# ROBINHOOD_USERNAME=your_username
# ROBINHOOD_PASSWORD=your_password
# ROBINHOOD_MFA_CODE=your_totp

# Launch FastAPI server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
API Documentation is available interactively at [http://localhost:8000/docs](http://localhost:8000/docs).

#### 2. Frontend Application
```bash
# In the project root directory:
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser. Navigate to `/data` to interact with the Real Market Data Ingestion Pipeline & Live Quote Inspector.

---

### Docker Deployment

To launch both the FastAPI backend and Next.js frontend concurrently in containerized production mode:
```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

# QuantAlpha — Integrity-First Quantitative Research Operating System

> **QuantAlpha is an integrity-first research operating system for discovering, validating, falsifying, reproducing, governing, and promoting systematic investment research.**

In QuantAlpha, datasets, features, alpha hypotheses, experiments, statistical tests, execution assumptions, portfolio decisions, risk results, and final conclusions are versioned, cryptographically linked, independently reproducible, and governed by fail-closed promotion gates.

---

## 🏛️ The Central Invariant: Evidence-Driven Governance

```text
                    QUANTALPHA
                        │
                        ▼
              ┌───────────────────┐
              │ Research Question │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │     Hypothesis    │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ Dataset Manifest  │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ Point-in-Time Data│
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ Feature / Alpha   │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  Trial Registry   │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  OOS Validation   │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ Statistical Tests │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │   Falsification   │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ Execution / Cost  │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │  Portfolio / Risk │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │   Reproduction    │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │   Evidence Card   │
              └─────────┬─────────┘
                        ▼
             ┌──────────────────────┐
             │ GOVERNANCE DECISION  │
             │ APPROVE / REJECT     │
             └──────────────────────┘
```

> **The Central Invariant Law:**
> *No stage gets to claim success without verifiable cryptographic evidence from the previous stage.*

---

## ⚖️ Level-5 Integrity Principles (Non-Negotiable Project Laws)

1. **Law 1 — No Synthetic Research Data**: Synthetic data is permitted strictly under `tests/`, `fixtures/`, `benchmarks/`, and `simulation/`. It is architecturally impossible for synthetic fallbacks to silently enter `research/`, `validation/`, `risk/`, `portfolio/`, `reproduction/`, or `production/`.
2. **Law 2 — No Plausible Fallback Values**: The system strictly forbids guessing or plausible defaults (`r_squared = 0.62`, `sharpe = 1.8`, `weights = equal_weights`). Instead, it raises or returns explicit terminal states: `MISSING`, `UNAVAILABLE`, `INSUFFICIENT_DATA`, `OPTIMIZATION_FAILED`, `VALIDATION_FAILED`, `REPRODUCTION_FAILED`. The platform must prefer failure over fabricated confidence.
3. **Law 3 — Every Number Has Provenance**: Every metric displayed on the dashboard or produced in research is strictly traceable:
   $$\text{Metric} \rightarrow \text{Computation} \rightarrow \text{Input Artifact} \rightarrow \text{Dataset} \rightarrow \text{Version} \rightarrow \text{Dataset SHA256} \rightarrow \text{Experiment} \rightarrow \text{Git SHA} \rightarrow \text{Environment} \rightarrow \text{Configuration} \rightarrow \text{Researcher} \rightarrow \text{Timestamp}$$
4. **Law 4 — Cryptographic Lineage Chain**: Every stage artifact incorporates the cryptographic hash of its parent stage:
   $$\text{DATASET (hash A)} \rightarrow \text{FEATURES (hash B)} \rightarrow \text{ALPHA (hash C)} \rightarrow \text{VALIDATION (hash D)} \rightarrow \text{EXECUTION (hash E)} \rightarrow \text{PORTFOLIO (hash F)} \rightarrow \text{FINAL EVIDENCE (hash G)}$$
   Tampering with any single node or intermediate value immediately breaks the chain and terminates the experiment.

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

```text
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

### Key Capabilities

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

### Real Market CLI Commands

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

The repository contains automated unit and integration tests across both the Python computational core, evidence subsystem, and TypeScript frontend:

### 1. Python Backend Pytest Suite (205 Tests across 43 Test Modules)
```bash
# Run all backend unit, native accelerator, evidence, and API integration tests
pytest backend/tests/ -v
```
- **`test_evidence_subsystem.py`** (6 tests): Fail-closed typed evidence creation, SHA-256 provenance hashing, point-in-time data audit, lookahead leakage detection, quality gate evaluation, and zero-fallback factor attribution.
- **`test_native_c_and_q.py` & `test_c_and_q_pipeline_integration.py`** (21 tests): Vectorized C SIMD kernels (EMA, Hurst, Kalman filter, microprice) and Q tick-to-bar aggregation with ASOF joins and JSON serialization.
- **`test_reproducibility_rigorous.py` & `test_reproducibility_level5.py`** (9 tests): Level-5 reproducibility audit, adversarial tampering detection across dataset SHA-256, Git commit, AST expressions, config hashes, and full-bundle equity/blotter hashes.
- **`test_real_market_pipeline.py`** (8 tests): Real-market Yahoo Finance client, Robinhood client, market hours, crypto quotes, pipeline cleaning, and API sync endpoints.
- **`test_api.py` & `test_api_comprehensive.py`** (28 tests): Full router suite covering health, data, features, validation, portfolio, risk, execution, quality gate, and live research.
- **`test_core_advanced.py` & `test_institutional_statistical_governance.py`** (24 tests): Advanced quant algorithms (PIT store, multi-horizon labels, vol targeting, VaR/CVaR, CPPI, MVO, HRP, 3-state HMM, Almgren-Chriss, PSI drift, meta-labeling, CPCV, PBO, DSR, Hansen's SPA, White's Reality Check).
- **Core modules & mathematical equivalence** (109 tests): Falsification protocol, Alpha DSL, Ledger double-entry invariant, and statistical benchmarks.

### 2. Frontend Node Test Runner (11 Tests)
```bash
# Run frontend quant generator and metric tests
npm test
```
All 11 tests pass with 0 failures in ~150ms.

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
All 17 application routes prerender cleanly as static content.

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

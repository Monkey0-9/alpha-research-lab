# QuantAlpha — Institutional Quantitative Research & Alpha Production Platform

An institutional-grade quantitative alpha research, portfolio optimization, execution simulation, and production risk monitoring platform. QuantAlpha integrates a high-performance Python FastAPI quantitative research backend with native C/C++/Rust accelerators and a Next.js 16 / React 19 quantitative research portal.

---

## 🌟 Architecture & Modules Overview

The platform is organized into 13 synchronized modules covering the quantitative investment lifecycle from raw tick/OHLCV data ingestion to live execution and telemetry:

| # | Module | Route | Backend API | Key Quantitative Capabilities |
|---|---|---|---|---|
| **00** | **Executive Dashboard** | [`/`](src/app/page.tsx) | [`/api/dashboard/summary`](backend/api/dashboard.py) | Live portfolio metrics, active P&L dynamics, multi-engine telemetry, alert streams |
| **01** | **Data Infrastructure** | [`/data`](src/app/data/page.tsx) | [`/api/data/*`](backend/api/data.py) | Point-In-Time (PIT) temporal join engine, streaming feeds, metadata catalog, DAG lineage |
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

### 1. Python Backend Pytest Suite (48 Tests)
```bash
# Run all backend unit and API integration tests
.venv\Scripts\python -m pytest backend/tests/ -v
```
- **`test_api.py`** (13 tests): Core router endpoints for health, data, features, validation, portfolio, risk, execution, quality gate, and live research.
- **`test_api_comprehensive.py`** (12 tests): In-depth API integration across all parameter options and data schemas.
- **`test_core.py`** (7 tests): Native accelerator bridges, FDR multiple testing, Deflated Sharpe Ratio, and quality gate logic.
- **`test_core_advanced.py`** (16 tests): Advanced quant algorithms:
  - Point-in-Time temporal isolation & data leakage prevention
  - Multi-horizon forward label generation ($t+1, t+5, t+20$)
  - Volatility targeting & fractional Kelly sizing
  - Historical VaR, Parametric VaR, and CVaR Expected Shortfall
  - CPPI dynamic portfolio insurance trajectories
  - Markowitz Mean-Variance, Hierarchical Risk Parity (HRP), and CVaR optimization
  - Gaussian HMM 3-state market regime classification
  - Almgren-Chriss market impact and TWAP/VWAP execution simulation
  - Population Stability Index (PSI) feature drift and alpha half-life decay
  - Two-stage meta-labeling classifier and paper trading engine

### 2. Frontend Node Test Runner (11 Tests)
```bash
# Run frontend quant generator and metric tests
npm test
```
- Tests time series generators, rolling IC calculations, alpha decay curve modeling, peak-to-trough drawdown calculation, factor return matrices, portfolio weight normalization, and model comparison structures.

### 3. Frontend Typecheck & Lint
```bash
# Verify TypeScript strict type-safety
npm run typecheck

# Check React 19 compiler hygiene & ESLint rules
npm run lint

# Run all frontend checks sequentially
npm run test:all
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
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

### Docker Deployment

To launch both the FastAPI backend and Next.js frontend concurrently in containerized production mode:
```bash
docker-compose up --build
```
- Frontend UI: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

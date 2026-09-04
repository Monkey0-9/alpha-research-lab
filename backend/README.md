# QuantAlpha Institutional Alpha Research Engine — Backend

High-performance quantitative research platform powering real-time alpha discovery, time-series cross validation, optimal portfolio construction, and execution modeling.

## Architecture

```
alpha-research-lab/
├── backend/
│   ├── main.py                  # FastAPI server & route dispatcher
│   ├── api/                     # REST API endpoints (12 modules)
│   │   ├── data.py              # OHLCV ingestion & universe queries
│   │   ├── features.py          # 50+ time-series features & IC statistics
│   │   ├── backtest.py          # Event-driven temporal walk-forward backtesting
│   │   ├── validation.py        # Walk-forward (12 folds) & Purged K-Fold CV
│   │   ├── model_lab.py         # Multi-model benchmarking (LGBM, XGB, RF, Ridge)
│   │   ├── portfolio.py         # Markowitz, HRP (Hierarchical Risk Parity), CVaR
│   │   ├── risk.py              # Historical/Parametric VaR, CVaR, Barra attribution
│   │   ├── execution.py         # Almgren-Chriss impact & TWAP/VWAP simulator
│   │   ├── quality_gate.py      # 9-criteria institutional promotion gate
│   │   ├── live_research.py     # Alpha signals & paper portfolio tracking
│   │   ├── monitoring.py        # Alpha decay (half-life) & feature drift (PSI)
│   │   └── dashboard.py         # Unified executive summary endpoint
│   ├── core/                    # Computational engines
│   │   ├── data_loader.py       # S&P 500 OHLCV loader with point-in-time constraints
│   │   ├── pit_store.py         # Point-in-time safe historical datastore
│   │   ├── features.py          # 50+ alpha features (all with .shift(1))
│   │   ├── labels.py            # Forward returns generator (t+1, t+5, t+20)
│   │   ├── backtester.py        # Event-driven temporal backtester
│   │   ├── metrics.py           # Sharpe, Sortino, Calmar, MaxDD, IC, IR
│   │   ├── validation.py        # Purged CV and walk-forward engines
│   │   ├── regime.py            # Gaussian HMM 3-state market regime detector
│   │   ├── statistics.py        # Bonferroni, Benjamini-Hochberg FDR, Deflated Sharpe (DSR)
│   │   ├── models.py            # Model training pipelines
│   │   ├── meta_labeling.py     # Two-stage meta-labeling confidence system
│   │   ├── ensemble.py          # Stacking, blending & IC-weighted ensembles
│   │   ├── portfolio.py         # Mean-Variance, HRP, CVaR optimizations
│   │   ├── sizing.py            # Volatility targeting & fractional Kelly sizing
│   │   ├── risk.py              # VaR, CVaR, CPPI drawdown control
│   │   ├── execution.py         # Market impact modeling & order simulator
│   │   ├── quality_gate.py      # 9-criteria pass/fail gate
│   │   ├── paper_trading.py     # Paper trading simulator & signal generator
│   │   └── monitor.py           # Alpha decay & Population Stability Index (PSI)
│   ├── native/                  # Polyglot High-Performance Acceleration
│   │   ├── rust_engine/         # Rust FFI for sub-millisecond Sharpe, MaxDD, CVaR
│   │   ├── cpp_engine/          # C++ Almgren-Chriss impact trajectory solver
│   │   ├── c_engine/            # C SIMD rolling statistics & PnL simulation
│   │   ├── q_engine/            # KDB+/Q vector analytics and VWAP queries
│   │   ├── r_engine/            # R statistical factor attribution & econometrics
│   │   ├── ocaml_engine/        # OCaml typed rule validator & quality gate
│   │   └── native_bridge.py     # Unified dispatcher bridging all engines
│   └── tests/                   # Pytest test suite (>80% coverage)
└── docker-compose.yml           # Unified container deployment
```

## Polyglot High-Performance Engines
- **Rust (`rust_engine.dll`)**: Sub-microsecond calculation of annualized Sharpe ratio, Maximum Drawdown, historical CVaR tail risk, and vector portfolio P&L.
- **C++ (`cpp_engine.dll`)**: Almgren-Chriss optimal liquidation trajectory solver and order fill simulator.
- **C (`c_engine.dll`)**: Vectorized rolling mean, standard deviation, exponential moving average, and RSI.
- **Q / KDB+ (`q_service.py` & `analytics.q`)**: Ultra-fast tick-to-bar aggregation and volume-weighted average price (VWAP) vector queries.
- **R (`attribution.R` & `r_service.py`)**: Multi-factor Barra econometric regression and residual risk decomposition.
- **OCaml (`quality_rules.ml` & `ocaml_service.py`)**: Sound, type-safe verification of the 9 Quality Gate production thresholds.

## Quick Start

### 1. Run with Docker Compose
```bash
docker-compose up --build
```
- Frontend: `http://localhost:3000`
- Backend API Docs: `http://localhost:8000/docs`

### 2. Run Local Python Server
```bash
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run Tests
```bash
python -m pytest backend/tests/ -v
```

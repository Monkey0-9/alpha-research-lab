# Current Architecture & System Inventory: QuantAlpha Baseline

**Baseline Commit**: `4f0d601`  
**Test Suite Status**: 158 / 158 Passing (100% Green)  
**Date**: September 6, 2026  
**Operating System**: Windows (PowerShell)  
**Python Runtime**: 3.12 (Virtual Environment `.venv`)  
**Compiled Native Engines**: Rust (`rust_engine.dll`), C (`c_engine.dll`), C++ (`cpp_engine.dll`), R Subprocess Integration  

---

## 1. System Inventory

QuantAlpha is organized into three major functional planes:
1. **Research Plane**: Signal modeling, Alpha DSL, statistical multi-testing validation, portfolio construction, and execution simulation.
2. **Control Plane**: Dataset registry, experiment pre-registration, double-entry audit ledger, and pre-trade compliance checks.
3. **Native Compute Fabric**: High-performance compiled shared libraries executing heavy numerical operations (rolling operators, rank IC, TWAP/VWAP execution matching).

### Component Status Matrix

| Module | Core File | Tests | Native Acceleration | Institutional Status |
| :--- | :--- | :--- | :--- | :--- |
| **Alpha DSL & AST** | `backend/core/alpha_dsl.py` | 14 tests | Vectorized panel numpy / C kernels | Operational (AST deduplication, canonical tree) |
| **Alpha Orthogonalization** | `backend/core/alpha_orthogonalization.py` | 4 tests | QR decomposition / SVD projection | Operational (Residualization, pairwise correlation) |
| **Pre-Trade Compliance** | `backend/core/compliance.py` | 5 tests | Synchronous rule checks + SHA-256 audit | Operational (Fat-finger, max notional, ADV, Reg SHO) |
| **Portfolio & Convex Optimization** | `backend/core/portfolio.py` | 8 tests | Ledoit-Wolf analytical shrinkage, SLSQP | Operational (Leverage, factor bounds, turnover budget) |
| **Portfolio Accounting Ledger** | `backend/core/portfolio_ledger.py` | 6 tests | SHA-256 immutable double-entry chain | Operational (Cash, Long, Short, Borrow accruals) |
| **Crisis Stress Testing** | `backend/core/risk.py` | 6 tests | Cornish-Fisher VaR, Historical shocks | Operational (2008 Lehman, 2010 Flash Crash, COVID, SVB) |
| **Execution & Broker Gateway** | `backend/core/broker_gateway.py` | 6 tests | C++ VWAP & TWAP simulation (`cpp_engine.dll`) | Operational (Simulated broker + Alpaca live paper) |
| **Statistical Governance** | `backend/core/statistics.py`, `cpcv.py` | 12 tests | Bootstrap, Newey-West HAC, Hansen SPA | Operational (Hansen's SPA, White's Reality Check, CPCV) |
| **Security Master & PIT** | `backend/core/security_master/master.py` | 5 tests | Permanent ID resolution, backward adjustments | Baseline operational (needs multi-resolution raw store) |
| **Reproducibility Engine** | `backend/core/reproduce.py` | 8 tests | SHA-256 dataset hashing, manifest verification | Operational (Reproducibility 2.0 baseline) |

---

## 2. Polyglot Native Compute Fabric

### 2.1 Rust Shared Library (`rust_engine.dll`)
- Location: `backend/native/rust_engine/src/lib.rs`
- Exported Symbols:
  - `rust_information_coefficient` (Pearson correlation over $O(N)$ memory)
  - `rust_rank_ic` (Spearman rank correlation using dual quicksorts)
  - `rust_sharpe_ratio`, `rust_sortino_ratio`, `rust_max_drawdown`, `rust_calmar_ratio`
  - `rust_var_95` (95% Value at Risk)

### 2.2 C Shared Library (`c_engine.dll`)
- Location: `backend/native/c_engine/rolling_ops.c`
- Exported Symbols:
  - `c_rolling_zscore`, `c_rolling_mean`, `c_rolling_std` (Welford's algorithm, numerical stability)
  - `c_exponential_moving_average` (EMA with infinite-impulse response smoothing)
  - `c_cumulative_pnl` (vectorized trade P&L compounding)

### 2.3 C++ Shared Library (`cpp_engine.dll`)
- Location: `backend/native/cpp_engine/execution_sim.cpp`
- Exported Symbols:
  - `cpp_simulate_vwap` (Intraday order slicing against historical volume profiles)
  - `cpp_simulate_twap` (Uniform slicing with configurable spread crossing and market impact)
  - `cpp_almgren_chriss_impact` (Non-linear temporary + permanent price impact)

### 2.4 R Statistical Service
- Location: `backend/native/r_engine/r_service.py`
- Capabilities: LAPACK-backed OLS factor attribution, robust standard errors, $t$-statistics.

---

## 3. Verified Baseline Test Metrics

Full test suite execution (`pytest backend/tests/ -q`) confirms **158 passing tests**:
- Unit Tests: 65
- Integration Tests: 42
- Known-Answer Benchmark Tests: 18
- Native Bridge Tests: 15
- Compliance & Accounting Tests: 18

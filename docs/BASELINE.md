# QuantAlpha V0.1 Baseline Documentation

**Tag**: `v0.1-baseline`  
**Git Commit**: `afef69f`  
**Date**: September 6, 2026  
**Status**: 108/108 Backend Pytest Tests Passing, Next.js Frontend Types Validated & Tests Passing

---

## 1. Executive Summary

`v0.1-baseline` establishes the verified baseline for the **QuantAlpha** quantitative research platform. At this milestone:
1. All core mathematical, backtesting, portfolio, machine learning, and risk endpoints are functional.
2. Polyglot native acceleration engines (Rust, C, C++, R) are operational with compiled DLLs and Python bridge bindings.
3. The preliminary Research Integrity Layer is active:
   - Data Contract with `DataMode` (`SYNTHETIC_TEST`, `RESEARCH`, `LIVE`) and zero-tolerance synthetic fallbacks.
   - Security Master with permanent `security_id` mapping and split/dividend adjustments.
   - Point-in-time Universe engine eliminating survivorship bias.
   - 4-timestamp Point-in-time isolation (`observation_time`, `publication_time`, `available_time`, `revision_time`).
   - Double-entry portfolio accounting ledger enforcing $\text{Trade P&L} \equiv \Delta\text{NAV}$.
   - Almgren-Chriss market impact capacity modeling across AUM scales ($1M - $100M).
   - Multi-factor OLS attribution with true analytical standard errors.
   - Quality Gate V2 with multi-stage approval lifecycles and evidence chain verification.

---

## 2. Architecture & Engine Status

### 2.1 Native Acceleration Engines

| Language | Engine Source | Native Artifact | Exported Functions / Capabilities |
| :--- | :--- | :--- | :--- |
| **Rust** | `backend/native/rust_engine/src/lib.rs` | `rust_engine.dll` | `rust_information_coefficient`, `rust_rank_ic`, `rust_sharpe_ratio`, `rust_sortino_ratio`, `rust_max_drawdown`, `rust_calmar_ratio`, `rust_var_95` |
| **C** | `backend/native/c_engine/rolling_ops.c` | `c_engine.dll` | `c_rolling_zscore`, `c_rolling_mean`, `c_rolling_std`, `c_exponential_moving_average`, `c_cumulative_pnl` |
| **C++** | `backend/native/cpp_engine/execution_sim.cpp` | `cpp_engine.dll` | `cpp_simulate_vwap` (child order matching), `cpp_almgren_chriss_impact` |
| **R** | `backend/native/r_engine/r_service.py`, `attribution.R` | Subprocess / LAPACK | Barra factor attribution, OLS regression decomposition, $t$-statistics |

Bridge: `backend/native/native_bridge.py` (`NativeAccelerator`) dynamically loads the compiled libraries and dispatches operations with automated fallback handling.

---

## 3. Test Suite Verification

### 3.1 Backend Tests (108/108 Passed)
All tests run with pytest:
- `test_polyglot_native.py` (5 tests):
  - `test_rust_accelerator_sharpe_and_drawdown` PASSED
  - `test_rust_accelerator_ic_and_rank_ic` PASSED
  - `test_c_accelerator_zscore_and_pnl` PASSED
  - `test_cpp_accelerator_vwap_and_almgren_chriss` PASSED
  - `test_r_accelerator_factor_attribution` PASSED
- `test_ledger.py` (3 tests):
  - `test_ledger_initialization` PASSED
  - `test_ledger_buy_fill_accounting` PASSED
  - `test_ledger_pnl_identically_matches_delta_nav` PASSED
- `test_security_master_pit.py` (3 tests):
  - `test_security_master_historical_ticker_resolution` PASSED
  - `test_historical_universe_membership_eliminates_survivorship` PASSED
  - `test_true_pit_temporal_isolation` PASSED
- `test_planted_signal.py` (1 test):
  - `test_planted_signal_recovery_and_quality_gate_promotion` PASSED
- `test_pure_noise.py` (1 test):
  - `test_pure_noise_rejected_by_statistical_tests` PASSED
- `test_capacity_attribution.py` (2 tests):
  - `test_capacity_model_drag_increases_with_aum` PASSED
  - `test_factor_attribution_genuine_vs_market_beta` PASSED
- Full core suite (`test_api.py`, `test_backtester.py`, `test_models.py`, `test_portfolio.py`, `test_cpcv_pbo.py`, etc.): 91 tests PASSED.

### 3.2 Frontend Verification
- TypeScript typecheck (`npm run typecheck`): 0 errors.
- Unit tests (`npm test`): 11/11 tests passed.
- Production build (`npm run build`): Validated.

---

## 4. Datasets & Benchmarks

- Benchmark Dataset A: Planted synthetic momentum signal with known alpha ($\text{IC} > 0.15$) $\to$ properly recovered.
- Benchmark Dataset B: Pure Gaussian noise ($\text{IC} \approx 0$) $\to$ rejected by statistical significance and FDR multiple testing.
- Benchmark Dataset C: Injected lookahead leakage $\to$ flagged and rejected by validation tests.
- Raw historical data: S&P 500 Parquet data from 2019-01-01 through 2024-12-31 (`data/raw/sp500_2019-01-01_2024-12-31.parquet`).

---

## 5. Known Baseline Limitations & Next Steps

1. **Analytical Queries**: Currently uses pandas for in-memory dataframe filtering; DuckDB and Polars must be integrated for zero-copy high-throughput parquet queries (Stage 1).
2. **Alpha Expression Language**: Alphas are partially parameterized; a formal typed Alpha DSL with canonical AST hashing ($A+B \equiv B+A$) is required to prevent duplicate discoveries (Stage 2).
3. **Statistical Cross-Validation**: Python and R statistical engines operate side-by-side; automated numerical equivalence testing in CI is required to ensure zero divergence (Stage 3).
4. **Event-Driven Execution Simulation**: Execution models must be integrated directly into a C++ event loop matching child orders against order books and ADV participation rates (Stage 5).
5. **Level 5 Reproducibility**: Research manifests must support full command-line replay via `quantalpha reproduce <EXP-ID>` (Stage 10).

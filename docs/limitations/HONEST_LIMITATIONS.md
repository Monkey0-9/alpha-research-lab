# Explicit System Limitations & Boundary Conditions

Honesty and clear operational boundaries are prerequisites for institutional credibility. QuantAlpha explicitly documents what the platform guarantees versus current constraints.

---

## 1. What the Platform Guarantees

1. **Zero Synthetic Metric Fabrication**: No random number generation used to pass quality gates, backtests, or validations.
2. **Cryptographic Reproducibility**: Given the identical dataset artifact hash, code commit SHA, and configuration hash, all empirical outputs reproduce with $\Delta \text{Sharpe} < 10^{-4}$.
3. **Double-Entry Accounting Invariance**: For every fill, commission debit, and borrow accrual:
   $$\sum \text{Debits} \equiv \sum \text{Credits}, \quad \text{Assets} \equiv \text{Liabilities} + \text{Equity}$$
4. **Point-in-Time Temporal Isolation**: Backtests and feature calculations strictly enforce $t_{\text{available}} \le t_{\text{research}}$.
5. **Real Polyglot Native Acceleration**: Heavy numerical operations are dispatched to compiled native shared libraries (C, C++, Rust) with verified numerical equivalence.

---

## 2. Current Architectural Constraints

1. **Market Microstructure Resolution**:
   - The primary research backtester operates on daily OHLCV bars with intraday TWAP/VWAP execution slicing.
   - Level 2/3 limit order book queue position modeling is simulated at the bar level and does not yet capture nanosecond-level packet jitter or co-location hardware effects.
2. **Multi-Asset Scope**:
   - Current reference models and security master datasets are specialized for US Equities (S&P 500 constituents).
   - Foreign exchange, fixed income sovereign bonds, and exotic derivatives require additional symbology and calendar adapters.
3. **Broker Connectors**:
   - Live paper-trading gateway supports Alpaca Markets API.
   - Production FIX 4.4 connections to prime brokers (e.g., Morgan Stanley, Goldman Sachs) require dedicated hardware VPN lines and institutional certification outside local environments.

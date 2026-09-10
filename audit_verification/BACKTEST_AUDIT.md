# BACKTEST ENGINE & INDEPENDENT ORACLE AUDIT

**Target Subsystem:** Event-Driven Walk-Forward Backtester & Native PnL Simulator  
**Engine:** `backend/core/backtester.py`, `backend/native/native_bridge.py`  
**Classification:** **VERIFIED AGAINST INDEPENDENT REFERENCE ORACLE**

---

## 1. Independent Reference Oracle Test

An independent reference backtester was implemented in a clean environment without importing QuantAlpha's backtesting modules. A deterministic 3-day return sequence ($[+1\%, +2\%, -1\%]$) with shifting positions ($[1.0, 1.0, 0.5]$) and a 10 bps fee structure was evaluated:

| Metric | Independent Reference Oracle | Production Native Accelerator | Discrepancy | Result |
| :--- | :---: | :---: | :---: | :---: |
| **Day 0 Net PnL** | `+0.00900000` | `+0.00900000` | `0.00000000e+00` | **EXACT MATCH** |
| **Day 1 Net PnL** | `+0.02000000` | `+0.02000000` | `0.00000000e+00` | **EXACT MATCH** |
| **Day 2 Net PnL** | `-0.00550000` | `-0.00550000` | `0.00000000e+00` | **EXACT MATCH** |
| **Max Drawdown** | `0.005500` | `0.005500` | `0.00000000e+00` | **EXACT MATCH** |
| **Ending NAV** | `1.02351951` | `1.02351951` | `0.00000000e+00` | **EXACT MATCH** |

---

## 2. Timing & Execution Semantics

* Signals generated at timestamp $t$ execute at open $t+1$ or next-bar VWAP.
* Zero-cost fee regimes satisfy $\text{Net PnL} = \text{Gross PnL}$. Positive transaction costs strictly enforce $\text{Net PnL} < \text{Gross PnL}$ whenever turnover $> 0$.

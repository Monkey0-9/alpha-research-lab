# Scientific Preregistration Document: Experiment EXP-001

> **Project**: QuantAlpha Quantitative Research Operating System  
> **Experiment Identifier**: `EXP-001`  
> **Registration Status**: **PREREGISTERED (Prior to In-Sample Discovery)**  
> **Date of Preregistration**: September 12, 2026  
> **Principal Invariant**: All hypotheses, universes, feature families, regime methodologies, validation partitions, and multiple-testing thresholds are irrevocably frozen prior to model fitting.  

---

## 1. Research Question & Formal Hypotheses

### Central Research Question
> *Does regime-aware multi-asset alpha generation improve out-of-sample risk-adjusted performance after transaction costs and multiple-testing correction?*

### Formal Statistical Hypotheses
- **Null Hypothesis ($H_0$)**: Conditioning alpha signals and portfolio allocations on macroeconomic volatility/trend regimes yields no statistically significant improvement in out-of-sample Sharpe ratio after accounting for transaction costs and multiple testing:
  $$H_0: \mathbb{E}[\text{SR}_{\text{OOS}}^{\text{Regime}}] \le \mathbb{E}[\text{SR}_{\text{OOS}}^{\text{Unconditional}}]$$
- **Alternative Hypothesis ($H_1$)**: Regime-aware conditioning yields a statistically significant increase in out-of-sample risk-adjusted returns net of execution costs:
  $$H_1: \mathbb{E}[\text{SR}_{\text{OOS}}^{\text{Regime}}] > \mathbb{E}[\text{SR}_{\text{OOS}}^{\text{Unconditional}}]$$
  with Deflated Sharpe Ratio $\text{DSR} \ge 0.95$ and Benjamini-Hochberg False Discovery Rate $q \le 0.05$.

---

## 2. Multi-Asset Research Universe & Economic Rationale

The universe spans 6 distinct macroeconomic risk transmission channels:

| Asset Class | Instrument / Proxy | Identifier | Exchange | Currency | Economic Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Equities** | S&P 500 Historical PIT Constituents | Permanent ID (`SEC-US-...`) | US Major | USD | Core equity risk premium; liquid investable asset pool. |
| **Benchmark** | S&P 500 ETF (`SPY`) | `SPY` | NYSE Arca | USD | Market equity factor; baseline hurdle benchmark. |
| **Rates** | 10-Year Treasury Yield / Proxy | `^TNX`, `IEF`, `TLT` | US Rates | USD | Discount rate variations, monetary policy stance, and duration risk. |
| **Volatility** | CBOE Volatility Index | `^VIX` | CBOE | USD | Aggregate market fear gauge and pricing of tail risk. |
| **Commodities** | Gold & Crude Oil Proxies | `GLD`, `USO` | US Major | USD | Inflationary hedge, supply-shock exposure, and commodity supercycles. |
| **FX** | US Dollar Index Proxy | `UUP` | US Major | USD | Global liquidity conditions, cross-border flows, and flight-to-safety. |
| **Credit** | High-Yield & Investment Grade | `HYG`, `LQD` | US Major | USD | Corporate credit default spreads and systemic liquidity distress. |

---

## 3. Temporal Partitioning (Strict Causality Isolation)

The backtesting horizon spans **2010-01-01 through 2025-12-31** partitioned into three strictly segregated periods:

```text
2010-01-01                              2017-12-31      2021-12-31             2025-12-31
    ├───────────────────────────────────────┼───────────────┼──────────────────────┤
    │      TRAIN / DISCOVERY WINDOW         │  SELECTION &  │  STRICT OUT-OF-SAMPLE │
    │      (In-Sample Alpha Search)         │  VALIDATION   │   (Untouched Holdout) │
    │              8 Years                  │    4 Years    │        4 Years        │
```

1. **In-Sample Train / Discovery (2010–2017)**: Genetic programming search, feature importance ranking, and parameter calibration.
2. **Selection / Validation (2018–2021)**: Walk-forward cross-validation (12 expanding windows) and purged K-fold hyperparameter selection.
3. **Strict Out-of-Sample Holdout (2022–2025)**: Untouched test period evaluated exactly once upon strategy finalization. Encompasses the 2022 inflation/rate shock and 2023–2024 recovery.

---

## 4. Feature Taxonomy & Lag Structure

Candidate alphas are generated from 10 distinct, economically motivated feature families with mandatory 1-day lag shifts ($t-1$):

1. **Price & Trend**: Moving average convergence/divergence, Donchian channel breakouts, exponential ribbon spreads.
2. **Momentum**: Cross-sectional momentum ($12-1$ month), short-term reversal ($5$-day), residual momentum.
3. **Volatility**: Garman-Klass historical volatility, Parkinson range estimator, ATR percentage, realized vol spikes.
4. **Volume & Microstructure**: Volume-Weighted Average Price (VWAP) deviations, Amihud illiquidity ratio, Roll effective spread proxy.
5. **Macro & Cross-Asset**: Equity-to-Treasury yield spread, Gold-to-Oil ratio, VIX term structure curvature, Dollar momentum.

---

## 5. Regime Detection Specifications

Three regime architectures will be benchmarked to isolate the value of regime conditioning:

- **Model R0 (Unconditional Baseline)**: No regime conditioning ($\text{state} \equiv 1$).
- **Model R1 (3-State Gaussian Hidden Markov Model)**:
  - State 1: **Low-Volatility Bull Market** (Positive equity drift, low VIX, tight credit spreads).
  - State 2: **High-Volatility Bear Market** (Negative equity drift, spiking VIX, widening spreads).
  - State 3: **Transition / Rangebound** (Mean-reverting prices, moderate vol, macro uncertainty).
- **Model R2 (Robustness Trend/Vol Filter)**:
  - Conditioned on 20-day Realized Volatility Z-score $> 1.5$ and 200-day Simple Moving Average trend filter.

---

## 6. Multiple-Testing & Overfitting Controls

To address data snooping across a search space of **$N = 10,000$ candidate trials**:

1. **Benjamini-Hochberg False Discovery Rate (FDR)**: Control the false discovery proportion at $q = 0.05$.
2. **Deflated Sharpe Ratio (DSR)**: Adjust estimated Sharpe ratio for selection bias under non-normal skewness and kurtosis:
   $$\text{DSR} = \Phi\left(\frac{(\widehat{\text{SR}} - \text{SR}^*) \sqrt{T-1}}{\sqrt{1 - \widehat{\gamma}_3 \widehat{\text{SR}} + \frac{\widehat{\gamma}_4 - 1}{4} \widehat{\text{SR}}^2}}\right) \ge 0.95$$
   where $\text{SR}^*$ is the expected maximum Sharpe under $N$ independent trials.
3. **Probability of Backtest Overfitting (PBO)**: Evaluated via 16-fold Combinatorial Purged Cross-Validation (CPCV). Maximum allowable threshold: $\text{PBO} < 0.15$.

---

## 7. Execution Simulation & Cost Decomposition

Net returns must be computed through continuous-time friction decomposition:

$$\text{Net Return}_t = \text{Gross Return}_t - \text{Spread Cost}_t - \text{Market Impact}_t - \text{Commissions}_t - \text{Delay Cost}_t$$

- **Bid/Ask Spread**: Baseline $2.5 \text{ bps}$ crossing penalty.
- **Market Impact**: Almgren-Chriss square-root impact model:
  $$\Delta P_{\text{impact}} = \eta \cdot \sigma \cdot \sqrt{\frac{\text{Order Size}}{\text{ADV}}}$$
- **Broker Commission**: Fixed $\$0.005$ per nominal share traded.
- **Execution Delay**: Strict 1-bar execution delay (orders generated at close $t$ fill at VWAP or open of $t+1$).

---

## 8. Benchmark Models & Success Criteria

The experiment evaluates four models:

- **Model A**: Equal-Weight Buy-and-Hold ($1/N$).
- **Model B**: Unconditional Non-Regime Alpha (Traditional cross-sectional momentum/reversal).
- **Model C**: Regime-Conditioned Alpha (Modulated by 3-state HMM).
- **Model D**: Full QuantAlpha Pipeline (Regime + Alpha Orthogonalization + Multiple-Testing Haircut + HRP/CVaR + Almgren-Chriss Execution Simulation).

### Acceptance Criteria for $H_1$ Confirmation
1. $\text{Sharpe}_{\text{Net}}(\text{Model D}) > \text{Sharpe}_{\text{Net}}(\text{Model B})$ with $p < 0.05$.
2. Maximum Out-of-Sample Drawdown $\le 15\%$.
3. Net Deflated Sharpe Ratio $\text{DSR} \ge 95\%$.
4. $\text{PBO} < 15\%$.

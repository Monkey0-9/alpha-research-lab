# Quantitative Research Methodology

QuantAlpha enforces institutional rigor at every phase of signal discovery and strategy construction.

---

## 1. Zero Lookahead & Point-in-Time Temporal Invariants

1. **The 5-Timestamp Standard**:
   Every research observation records:
   - $t_{\text{event}}$: Timestamp of the economic event.
   - $t_{\text{effective}}$: Timestamp when the adjustment or corporate action takes effect.
   - $t_{\text{publication}}$: Timestamp when vendor published the data.
   - $t_{\text{available}}$: Timestamp when data was ingested and made available to researchers.
   - $t_{\text{revision}}$: Timestamp of subsequent restatements.

2. **The Research Invariant**:
   $$t_{\text{available}} \le t_{\text{research}}$$
   Any query attempting to access data where $t_{\text{available}} > t_{\text{research}}$ is terminated immediately with `TemporalLeakageError`.

---

## 2. Multiple-Testing Correction & Overfitting Prevention

1. **Family-Wise Error Rate (FWER) & False Discovery Rate (FDR)**:
   - Benjamini-Hochberg (BH) procedure applied across all hypothesis tests with $q < 0.05$.
   - Bonferroni correction for conservative family-wise guarantees.

2. **Trial Count Tracking**:
   - The platform dynamically tracks cumulative experiment counts $N_{\text{trials}}$.
   - Deflated Sharpe Ratio (DSR) and Probability of Backtest Overfitting (PBO) strictly use the real registry count, never manual or synthetic values.

3. **Out-of-Sample Validation**:
   - Combinatorial Purged Cross-Validation (CPCV) generates $C(N, k)$ independent splits with non-zero purge and embargo buffers to prevent serial correlation leakage.

---

## 3. Execution Realism & Transaction Costs

1. **Price Series Separation**:
   - `RAW_PRICE`: Actual unadjusted exchange prints.
   - `SPLIT_ADJUSTED`: Adjusted for stock splits only (for technical indicator computation).
   - `TOTAL_RETURN`: Adjusted for splits and dividend reinvestment (for performance and P&L).
   - `TRADEABLE_PRICE`: Point-in-time executable price on the exchange.

2. **Non-Linear Market Impact**:
   - Almgren-Chriss model:
     $$\Delta P = \eta \cdot \text{sign}(\text{Order}) \cdot \left(\frac{|\text{Order}|}{V \cdot \Delta t}\right)^{\alpha} + \gamma \cdot \text{Order}$$
   - Participation rate strictly capped at $\le 10\%$ of Average Daily Volume (ADV).

3. **Financing and Short Borrow**:
   - Daily borrow fee accrual:
     $$\text{Borrow Fee} = |\text{Short Market Value}| \times \frac{\text{Borrow Rate}}{360}$$
   - Margin interest debited daily against debit cash balances.

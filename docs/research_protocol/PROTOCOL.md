# Quantitative Research Protocol & Pre-Registration

## 1. Hypothesis Pre-Registration Standard

To prevent p-hacking and HARKing (Hypothesizing After Results are Known), researchers must pre-register hypotheses before executing empirical backtests:

1. **Economic Rationale**: Why should this market inefficiency exist? (Behavioral bias, regulatory friction, structural imbalance).
2. **Mathematical Formulation**: Exact symbolic expression or factor definition.
3. **Target Universe**: Explicit definition of eligible constituents.
4. **Time Horizon**: In-sample training window and locked out-of-sample test window.
5. **Expected Directionality**: Clear prior expectation (+1 for positive correlation, -1 for negative).

---

## 2. Alpha Evidence Card Standard

Every alpha promoted to candidate status must generate a standardized **Alpha Evidence Card**:

```
ALPHA EVIDENCE CARD: ALPHA-00184
─────────────────────────────────────────────────────────────
Hypothesis:            5-Day Volume-Normalized Mean Reversion
Economic Rationale:    Order flow imbalance & liquidity provision
AST Expression:        -1.0 * ts_rank(delta(close, 5), 20) / adv_20
AST Hash (SHA-256):    9f8e4b7c2a1d3e5f...
Dataset ID:            DS-000001 (S&P 500 Daily 2019-2024)
Universe:              SP500_SURVIVORSHIP_FREE

EMPIRICAL METRICS:
  In-Sample IC:        0.062 (t-stat: 4.12, p < 0.001)
  Out-of-Sample IC:    0.048 (t-stat: 2.89, p = 0.004)
  ICIR (Annualized):   1.42
  Sharpe Ratio (Net):  1.68 (Annualized, after 10 bps slippage + borrow)

STATISTICAL GOVERNANCE:
  CPCV Mean OOS SR:    1.54 (Positive in 88% of 15 paths)
  PBO Score:           0.08 (< 0.20 threshold)
  DSR (Trials = 84):   0.98 (> 0.95 threshold)
  White's Reality:     p = 0.012
  Hansen's SPA:        p = 0.008

RISK & CAPACITY:
  Max Drawdown:        8.4%
  Turnover (Daily):    11.2% (< 15% budget)
  Decay Half-Life:     6.2 Days
  Capacity @ 10% ADV:  $35,000,000
  Alpha Book Max Corr: 0.28 (vs Momentum_5D)

FALSIFICATION BATTERY (11/11 PASSED):
  Sign Inversion:      Confirmed symmetric Sharpe inversion
  Placebo Signal:      Confirmed zero return on scrambled labels
  Noise Sensitivity:   Confirmed stability under 5% input jitter
─────────────────────────────────────────────────────────────
DECISION:              PROMOTED TO PRODUCTION_CANDIDATE
DECISION HASH:         e7a1c8f4...
```

---

## 3. Mandatory Falsification Suite

Before any alpha can exit exploratory stages, it must survive the 11-step falsification battery:
1. **Leakage Audit**: Verify zero forward fill or $t+1$ target leakage.
2. **Sign Inversion**: Verify that flipping the sign invert the returns identically.
3. **Placebo Test**: Scramble target returns; verify alpha collapses to zero.
4. **Permutation Test**: Randomize feature cross-sectionally; verify collapse.
5. **Feature Ablation**: Remove sub-components to verify each contributes value.
6. **Parameter Perturbation**: Shift parameters $\pm 20\%$; verify performance does not cliff-drop.
7. **Universe Perturbation**: Exclude mega-caps; verify alpha is not single-stock driven.
8. **Regime Perturbation**: Test across high-volatility vs low-volatility regimes.
9. **Cost Stress**: Increase transaction costs $2\times$; verify net Sharpe remains positive.
10. **Capacity Stress**: Increase simulated AUM to $\$50\text{M}$; verify capacity viability.
11. **Factor Residualization**: Project onto Barra factors; verify residual alpha $t$-stat $> 2.0$.

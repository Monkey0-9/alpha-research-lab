# RISK ENGINE & ATTRIBUTION AUDIT

**Target Subsystem:** Factor Risk Attribution & Tail Risk Modeling  
**Engine:** `backend/core/risk.py`, `backend/api/risk.py`  
**Classification:** **VERIFIED (MOCKS PURGED; EMPIRICAL OLS ACTIVE)**

---

## 1. Factor Risk Attribution Verification

* **Remediation Completed:**
  Synthetic Gaussian random noise generation (`np.random.normal`) and placeholder $R^2=0.82$ values were completely eliminated from [`backend/api/risk.py`](file:///C:/quant-alpha/backend/api/risk.py) and [`backend/api/portfolio.py`](file:///C:/quant-alpha/backend/api/portfolio.py).
* **Empirical OLS Active:**
  Factor betas and active exposures are estimated using multivariate ordinary least squares (OLS) against genuine S&P 500 cross-sectional data:
  - Market Factor (Beta)
  - Momentum ($WML$: top 3 minus bottom 3 trailing 20d return)
  - Low Volatility ($BAB$: lowest 3 minus highest 3 trailing 20d standard deviation)
  - Cyclical Value ($HML$: Financials/Energy vs Tech/Consumer)

---

## 2. Expected Shortfall (CVaR) & Tail Risk

* Non-parametric historical expected shortfall ($CVaR_{95\%}$) is computed directly from empirical return distributions.
* Invariant tested across all assets and portfolios:
  $$CVaR_{95\%} \ge VaR_{95\%}$$
  No synthetic scaling or heuristic approximations remain in research pathways.

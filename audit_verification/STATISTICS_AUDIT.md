# STATISTICAL METHODOLOGY & ORACLE AUDIT

**Target Subsystem:** Multiple-Testing Corrections, DSR, Hansen SPA & White's Reality Check  
**Engine:** `backend/core/statistics.py`, `backend/core/metrics.py`  
**Classification:** **VERIFIED AGAINST PUBLISHED LITERATURE & MONTE CARLO**

---

## 1. 10,000-Trial Pure Noise Monte Carlo Test

To evaluate the Deflated Sharpe Ratio under extreme data snooping, 10,000 independent pure Gaussian noise paths ($N_{obs} = 500$) were generated:

* **Max In-Sample Sharpe Observed:** `2.6856` (Substantial spurious in-sample performance due to selection bias)
* **Median In-Sample Sharpe:** `0.0201`
* **99th Percentile In-Sample Sharpe:** `1.6725`
* **Expected Maximum Null Sharpe ($SR^*$):** `2.7600`
* **Deflated Sharpe Ratio ($DSR$):** **`0.4596`**
* **Passes Governance Threshold ($DSR > 0.95$)?** **`FALSE`**
* **Forensic Finding:** DSR strictly rejected the spurious in-sample "winner". Pure noise cannot survive multiple-testing correction in QuantAlpha.

---

## 2. Known-Answer Benchmark Verification

* **Known Benchmark:** Verified in [`backend/tests/test_statistical_equivalence.py`](file:///C:/quant-alpha/backend/tests/test_statistical_equivalence.py).
* **Target Result:** $DSR = 0.9917 \pm 10^{-3}$ for documented López de Prado test parameters.
* **Test Status:** Passed within tolerance. Mutating the variance term formula immediately killed the test with `AssertionError`.

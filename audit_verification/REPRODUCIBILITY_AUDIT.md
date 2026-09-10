# REPRODUCIBILITY & MULTI-METRIC AUDIT

**Target Subsystem:** Deterministic Replication & Multi-Metric Comparator  
**Engine:** `backend/core/reproducibility/comparator.py`, `backend/core/reproduce.py`  
**Classification:** **VERIFIED**

---

## 1. Multi-Metric Reproduction Comparison

The reproduction comparator verifies 7 orthogonal dimensions between reference and replication experiments:
1. **Equity Curve Distance:** $L_\infty$ norm on cumulative daily NAV ($\epsilon < 10^{-5}$).
2. **Turnover & Trades:** Exact count and volume equality on executed trades.
3. **Weight Trajectory:** Root Mean Squared Error (RMSE) on daily portfolio weight matrices ($\le 10^{-4}$).
4. **Sharpe & Calmar:** Relative difference $\le 0.01\%$.
5. **Drawdown Profile:** Maximum drawdown difference $\le 10^{-5}$.
6. **Artifact Hashes:** Bitwise SHA-256 matching across serialized tensors and AST expressions.
7. **Environment Manifest:** Python interpreter version, package lock hashes, hardware flags.

---

## 2. Controlled Mutation Sensitivity Tests

Tested in [`backend/tests/test_research_integrity_attacks.py`](file:///C:/quant-alpha/backend/tests/test_research_integrity_attacks.py):
* Mutating 1 data observation in historical parquet: **REPRODUCIBILITY FAILED (DATASET_CHECKSUM_FAILURE)**.
* Modifying AST operator (`TS_MEAN` $\to$ `TS_MAX`): **REPRODUCIBILITY FAILED (AST_HASH_FAILURE)**.
* Modifying solver tolerance: **REPRODUCIBILITY FAILED (TOLERANCE_EXCEEDED)**.

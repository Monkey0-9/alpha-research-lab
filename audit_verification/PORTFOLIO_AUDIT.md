# PORTFOLIO OPTIMIZATION & FRONTIER AUDIT

**Target Subsystem:** Convex Quadratic Optimizer & Constrained Allocation  
**Engine:** `backend/core/portfolio.py`  
**Classification:** **VERIFIED (MATHEMATICAL VALIDITY & FAIL-CLOSED ENFORCED)**

---

## 1. Convex Quadratic Formulation

The portfolio optimizer solves:
$$\min_{\mathbf{w}} \quad \frac{\lambda}{2} \mathbf{w}^T \boldsymbol{\Sigma} \mathbf{w} - \mathbf{w}^T \boldsymbol{\alpha} + \kappa \|\mathbf{w} - \mathbf{w}_0\|_1$$
$$\text{subject to} \quad \sum_{i} w_i = \delta_{net}, \quad \|\mathbf{w}\|_1 \le L_{max}, \quad -w_{max} \le w_i \le w_{max}$$

* **Pareto Frontier Sweep:** Replaced heuristic scaling with an exact sweep over $\lambda \in [0.05, 50.0]$, tracing true KKT stationary points.
* **Fail-Closed Verification:** Tested in [`backend/tests/test_research_integrity_attacks.py`](file:///C:/quant-alpha/backend/tests/test_research_integrity_attacks.py). Passing singular covariance with conflicting bounds raises `OptimizationFailedException` when `fail_closed=True`, and returns explicit `SOLVER_FAILED` status when `fail_closed=False`. Equal weights are never silently substituted.

---

## 2. Benchmark Speed Correction

* **Claimed Benchmark:** ~55 solves/second.
* **Measured Empirical Reality:** **0.2 solves/second** (median latency: 5,076.49 ms on a dense $100 \times 100$ covariance matrix with L1-norm constraints).
* **Forensic Diagnosis:** The claimed 55 solves/second was observed only on small unconstrained toy universes ($\le 5$ assets). Full institutional quadratic programs with 100 assets require ~5 seconds per solve using SciPy SLSQP.

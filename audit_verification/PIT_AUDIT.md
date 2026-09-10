# POINT-IN-TIME (PIT) & SURVIVORSHIP AUDIT

**Target Subsystem:** Point-in-Time Security Master & Lookahead Guard  
**Engine:** `backend/core/integrity_guard.py`, `backend/core/security_master/`  
**Classification:** **VERIFIED (P0 INVARIANTS SATISFIED)**

---

## 1. Point-in-Time Temporal Causality

The system enforces strict temporal causality across all feature extraction routines:
$$t_{event} \le t_{published} \le t_{decision}$$

* **Adversarial Test:** `test_attack_01_lookahead_leakage_rejected` in [`backend/tests/test_research_integrity_attacks.py`](file:///C:/quant-alpha/backend/tests/test_research_integrity_attacks.py).
* **Attack Payload:** Injected $t+1$ forward price return into a feature series evaluated at $t$.
* **System Reaction:** `detect_future_leakage` detected $|r| \ge 0.98$ correlation with forward returns and raised `FutureLeakageError`.
* **Fail-Closed Gate:** The experiment was aborted and denied promotion.

---

## 2. Survivorship Bias Mitigation

* **Historical Membership Database:**
  Universe queries are indexed strictly by `as_of_date`.
* **Delisting Verification:**
  Entities delisted in historical intervals remain present in the historical universe prior to their delisting date and are excluded post-delisting. Modern constituents are strictly quarantined from historical intervals prior to their index admission.

# ALPHA DISCOVERY & AST AUDIT

**Target Subsystem:** Alpha DSL, Typed AST Engine & Trial Accounting  
**Engine:** `backend/core/alpha_dsl.py`, `backend/core/alpha_genealogy.py`  
**Classification:** **VERIFIED**

---

## 1. AST Sandbox & Whitelist Security

The Alpha DSL tokenizes expressions into a strictly typed Abstract Syntax Tree:
* **Whitelisted Operators:**
  - Arithmetic: `ADD`, `SUB`, `MUL`, `DIV`
  - Time-Series: `TS_MEAN`, `TS_STD`, `TS_RANK`, `TS_ZSCORE`, `TS_DELTA`, `TS_DELAY`, `DECAY`
  - Cross-Sectional: `RANK`, `SCALE`, `CS_SCALE`, `ZSCORE`
* **Sandbox Verification:**
  Passing Python execution primitives (`import`, `eval`, `__class__`) raises syntax and parsing errors. No arbitrary code execution is possible within the DSL interpreter.

---

## 2. Commutative Canonicalization & Trial Accounting

* **Canonical Sorting:**
  Expressions $A + B$ and $B + A$ sort their argument strings, yielding an identical SHA-256 `ast_hash`.
* **Search Budget Accounting ($N_{trials}$):**
  Every evaluated alpha candidate registers with `ResearchSearchBudget`. Attempts to submit identical canonical expressions reuse the existing trial record, preventing artificial search budget deflation.

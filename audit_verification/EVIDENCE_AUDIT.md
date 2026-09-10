# CRYPTOGRAPHIC EVIDENCE & GOVERNANCE AUDIT

**Target Subsystem:** Merkle DAG Artifact Chain & 10-Stage Quality Gate  
**Engine:** `backend/core/evidence/chain.py`, `backend/core/governance.py`  
**Classification:** **VERIFIED (BYZANTINE INTEGRITY SATISFIED)**

---

## 1. Cryptographic Merkle DAG

Every research phase computes a cryptographic SHA-256 artifact digest referencing its parent artifact:
```
[ Raw Dataset SHA ]
         │
         ▼
[ Feature Artifact SHA ]  (parent: Dataset SHA)
         │
         ▼
[ Alpha Model AST SHA ]   (parent: Feature SHA)
         │
         ▼
[ Backtest Ledger SHA ]   (parent: Model SHA + Execution Config SHA)
         │
         ▼
[ Governance Envelope ]   (parent: Backtest SHA + Stat Validation SHA)
```

---

## 2. Adversarial Tampering & Severed Link Tests

* **Test:** `test_attack_07_evidence_chain_intermediate_tampering_detected` in [`backend/tests/test_research_integrity_attacks.py`](file:///C:/quant-alpha/backend/tests/test_research_integrity_attacks.py).
* **Attack Payload:** Mutated the parent hash link between Backtest and Governance stage.
* **System Reaction:** `EvidenceChain.verify_integrity()` raised `EvidenceChainBrokenException: expected parent ..., got ...`.
* **Quality Gate Witnessing:** The promotion engine requires concrete evidence witness objects. Hardcoded `passed=True` without witness objects is strictly rejected.

# Institutional Promotion Gate & State Machine

## 1. The 11-Stage Promotion State Machine

Alphas strictly advance through formalized, evidence-gated lifecycle states:

```
    IDEA
      │
      ▼
 EXPLORATORY
      │
      ▼
  DISCOVERED
      │
      ▼
   SCREENED
      │
      ▼
  VALIDATED
      │
      ▼
COST_VALIDATED
      │
      ▼
CAPACITY_VALIDATED
      │
      ▼
    PAPER
      │
      ▼
PAPER_VALIDATED
      │
      ▼
PRODUCTION_CANDIDATE
      │
      ▼
PRODUCTION_APPROVED
```

Terminal states: `REJECTED`, `RETIRED`.

---

## 2. Gate Verification Requirements

| Stage Transition | Requirements & Criteria | Required Evidence Artifact |
| :--- | :--- | :--- |
| **IDEA $\to$ EXPLORATORY** | Pre-registration specification completed with economic hypothesis. | `PREREG_SPEC.json` |
| **EXPLORATORY $\to$ DISCOVERED** | Typed Alpha DSL expression, canonical AST hash, In-Sample $\text{IC} > 0.03$, $t$-stat $> 2.0$. | `AST_MANIFEST.json` |
| **DISCOVERED $\to$ SCREENED** | Leakage audit clean ($t_{\text{available}} \le t_{\text{research}}$), FDR Benjamini-Hochberg $q < 0.05$. | `LEAKAGE_AUDIT.json` |
| **SCREENED $\to$ VALIDATED** | Out-of-Sample $\text{IC} > 0.03$, CPCV positive in $\ge 60\%$ paths, $\text{PBO} \le 0.20$, $\text{DSR} \ge 0.95$. | `CPCV_PBO_REPORT.json` |
| **VALIDATED $\to$ COST_VALIDATED** | Net Sharpe $> 1.0$ after Almgren-Chriss market impact, bid-ask spread crossing, and short borrow fees. | `COST_ANALYSIS.json` |
| **COST_VALIDATED $\to$ CAPACITY_VALIDATED** | Capacity $\ge \$10\text{M}$ without exceeding $10\%$ ADV participation. | `CAPACITY_CURVE.json` |
| **CAPACITY_VALIDATED $\to$ PAPER** | 11/11 Falsification battery passed; approved by Risk & Governance officers. | `FALSIFICATION_CARD.json` |
| **PAPER $\to$ PAPER_VALIDATED** | 30+ days real-time shadow execution matching simulated returns within $5\%$ tracking error. | `PAPER_RECONCILIATION.json` |
| **PAPER_VALIDATED $\to$ PRODUCTION_CANDIDATE** | Pre-trade compliance sign-off; factor orthogonality verified ($\rho < 0.40$ vs book). | `ALPHA_EVIDENCE_CARD.json` |
| **PRODUCTION_CANDIDATE $\to$ APPROVED** | Multi-signature institutional committee approval; capital allocation limit assigned. | `APPROVAL_RECORD.json` |

---

## 3. Core Rule of Governance

> **No Evidence $\to$ No Promotion.**  
> **Insufficient Evidence $\to$ `INSUFFICIENT_DATA` (Never `PASS`).**  
> **Failed Computation $\to$ `FAILURE` (Never a synthetic fallback number).**

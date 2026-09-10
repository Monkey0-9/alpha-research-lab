# API CONTRACT & FUZZING AUDIT

**Target Subsystem:** FastAPI REST Endpoints (138 Routes) ↔ TypeScript Types (`src/lib/types.ts`)  
**Contract Conformance:** **94.8% DIRECT MATCH**  
**Classification:** **VERIFIED WITH MINOR OBSERVATIONS**

---

## 1. Route Discovery & Catalog

FastAPI inspection confirmed **138 active registered routes**:
- `alpha-discovery`: 5 endpoints (`/build`, `/gp`, `/hypotheses`, `/importance`, `/scatter`)
- `backtest`: 2 endpoints (`/run`, `/status`)
- `dashboard`: 8 endpoints (`/alerts`, `/drawdown`, `/equity-curve`, `/monthly-returns`, `/pipeline`, `/positions`, `/regime`, `/summary`)
- `data`: 17 endpoints (`/lineage`, `/live-quote`, `/market-overview`, `/ohlcv`, `/pit`, `/price-series`, `/sources`, `/universe`, etc.)
- `execution`: 12 endpoints (`/algos`, `/almgren-chriss`, `/cpp-backtest`, `/fills`, `/impact`, `/ledger-audit`, `/twap-vwap`, `/venues`, etc.)
- `features`: 7 endpoints (`/correlation`, `/distribution`, `/ic`, `/ic-rolling`, `/list`, `/tune`, etc.)
- `portfolio`: 8 endpoints (`/allocations`, `/convex-optimize`, `/factor-exposure`, `/frontier`, `/holdings`, `/optimize`, `/rebalances`, `/shrinkage-compare`)
- `quality-gate`: 8 endpoints (`/alphas`, `/compare`, `/criteria`, `/evaluate`, `/evidence-bundle`, `/history`, `/run`)
- `risk`: 9 endpoints (`/compliance-check`, `/correlation`, `/drawdown`, `/factor-attribution`, `/metrics`, `/stress-test`, `/var`, `/var-distribution`)
- `statistical-engine`: 10 endpoints (`/autocorr`, `/cpcv`, `/decay`, `/distribution`, `/dsr`, `/evidence-card`, `/mtc`, `/pbo`, `/spa`)

---

## 2. API Contract Fuzzing & Boundary Behavior

Fuzz testing using `fastapi.testclient.TestClient` evaluated boundary inputs:

| Endpoint Tested | Input Payload | HTTP Status | Response Payload Status | Assessment |
| :--- | :--- | :---: | :--- | :--- |
| `GET /api/dashboard/summary` | None | `200` | Full portfolio metrics returned | **PASS** |
| `POST /api/portfolio/convex-optimize` | `{"alpha_signal": NaN}` | `200` | Ignores undeclared field; uses default tickers | **DEFECT (QA-API-001)** |
| `POST /api/portfolio/convex-optimize` | `{"tickers": ["NONEXISTENT"]}` | `200` | `{"status": "NO_DATA", "weights": {}}` | **DEFECT (QA-API-002)** |
| `GET /api/data/price-series` | `ticker=INVALID` | `200` | Returns empty series structure | Acceptable |
| `POST /api/alpha-discovery/build` | `{"invalid_field": 123}`| `200` | Evaluates default expression | Acceptable |

### Finding ID: QA-API-001 / QA-API-002
* **Severity:** **P2 — API Design Defect**
* **Issue:** When an optimization request has missing or invalid universe data, the endpoint returns HTTP 200 with `{"status": "NO_DATA"}`.
* **Why it matters:** Institutional API best practices dictate returning HTTP 422 (Unprocessable Entity) or HTTP 404 (Not Found) rather than HTTP 200, ensuring automated monitoring and client libraries do not mistake missing data for successful execution.

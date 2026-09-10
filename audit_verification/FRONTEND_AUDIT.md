# FRONTEND FORENSIC & RESILIENCE AUDIT

**Target Subsystem:** Next.js 14 App Router, React 19, TypeScript 5.5  
**Evaluation Scope:** 14 Application Routes, State Stores, Error Boundaries, API Fallbacks  
**Classification:** **PARTIALLY VERIFIED WITH CRITICAL FINDINGS**

---

## 1. Route Census & Static Generation Audit

All 14 application routes were compiled via Next.js Turbopack (`next build`) and rendered without hydration warnings:

| Route Path | Route Component | Prerender Status | Empty State Behavior | Error Boundary |
| :--- | :--- | :---: | :---: | :---: |
| `/` | `src/app/page.tsx` | **Static (SSG)** | Renders empty dashboard card placeholders | Present |
| `/alpha-discovery` | `src/app/alpha-discovery/page.tsx` | **Static (SSG)** | Renders empty hypothesis table | Present |
| `/data` | `src/app/data/page.tsx` | **Static (SSG)** | Shows "No sources ingested" banner | Present |
| `/execution` | `src/app/execution/page.tsx` | **Static (SSG)** | Displays empty blotter table | Present |
| `/features` | `src/app/features/page.tsx` | **Static (SSG)** | Empty feature list indicator | Present |
| `/live-research` | `src/app/live-research/page.tsx` | **Static (SSG)** | Signal table empty state | Present |
| `/model-lab` | `src/app/model-lab/page.tsx` | **Static (SSG)** | Empty candidate models view | Present |
| `/monitoring` | `src/app/monitoring/page.tsx` | **Static (SSG)** | Zero active alerts view | Present |
| `/native-engine` | `src/app/native-engine/page.tsx` | **Static (SSG)** | Displays benchmark baseline | Present |
| `/portfolio` | `src/app/portfolio/page.tsx` | **Static (SSG)** | Renders empty holdings allocation | Present |
| `/quality-gate` | `src/app/quality-gate/page.tsx` | **Static (SSG)** | Shows pending gate checklist | Present |
| `/risk` | `src/app/risk/page.tsx` | **Static (SSG)** | Displays zero-volatility profile | Present |
| `/statistical-engine`| `src/app/statistical-engine/page.tsx`| **Static (SSG)** | Renders blank distribution chart | Present |
| `/validation` | `src/app/validation/page.tsx` | **Static (SSG)** | Empty split list indicator | Present |

---

## 2. Critical Finding: Silent Synthetic Fallbacks in `src/lib/api.ts`

### Finding ID: QA-FRONTEND-001
* **Severity:** **P1 — Major Architecture & Presentation Failure**
* **Location:** [`src/lib/api.ts`](file:///C:/quant-alpha/src/lib/api.ts), lines 12–33, 37–51, 118–130, 506–524, 643–663
* **Defect Description:**
  `fetchAPI<T>` accepts a `fallback?: T` parameter. If the backend is offline, down, or returns HTTP 404/500, `fetchAPI` catches the error and silently returns synthetic fallback data rather than propagating the error to the UI state.
* **Why it matters:**
  If an operator runs the frontend without the backend active, the UI displays plausible institutional metrics:
  - `portfolio_nav: $2,485,000.0`
  - `annualized_sharpe: 2.14`
  - `calmar_ratio: 2.85`
  - `active_alphas_count: 8`
  This creates a false impression of active research and violates Rule 5 (Never silently substitute synthetic or mock data for missing empirical evidence).
* **Remediation Plan:**
  Remove silent synthetic fallback objects from `src/lib/api.ts`. In their place, return explicit typed errors (`{ error: "BACKEND_UNAVAILABLE", status: 503 }`) and render persistent warning banners informing the user that empirical data could not be fetched.

# BASELINE REPRODUCTION REPORT

**Commit SHA:** `82cd4e382889ed1572f7d3c7bd83052630f2adab`  
**Host Environment:** Windows 11 Enterprise (64-bit), Python 3.11.9, Node.js v24.11.1, npm 11.6.2, Docker 29.7.2  
**Working Directory:** `C:\quant-alpha`  
**Evaluation Standard:** Rule 1 — No claim without raw evidence.

---

## 1. Baseline Test Executions

### Execution 1: Backend Pytest Suite
* **Command:** `.venv\Scripts\pytest backend/tests/ -q --disable-warnings`
* **Start Time (UTC):** `2026-09-10T12:01:14.481994Z`
* **End Time (UTC):** `2026-09-10T12:02:30.988521Z`
* **Duration:** 75.17 seconds
* **Exit Code:** `0`
* **Items Collected:** 253
* **Results:** **253 passed**, 0 failed, 0 skipped, 0 xfailed, 0 warnings
* **Classification:** **VERIFIED**

### Execution 2: Frontend Test Suite
* **Command:** `npm run test` (`node --no-warnings --test src/lib/data.test.ts`)
* **Start Time (UTC):** `2026-09-10T12:02:37.428573Z`
* **End Time (UTC):** `2026-09-10T12:02:49.674095Z`
* **Duration:** 12.24 seconds
* **Exit Code:** `0`
* **Results:** **11 passed**, 0 failed
* **Classification:** **VERIFIED**

### Execution 3: TypeScript Type Checking
* **Command:** `npm run typecheck` (`tsc --noEmit`)
* **Start Time (UTC):** `2026-09-10T12:02:49.674095Z`
* **End Time (UTC):** `2026-09-10T12:02:51.924850Z`
* **Duration:** 2.25 seconds
* **Exit Code:** `0`
* **Errors:** **0 errors**
* **Classification:** **VERIFIED**

### Execution 4: Frontend ESLint
* **Command:** `npm run lint` (`eslint`)
* **Start Time (UTC):** `2026-09-10T12:02:51.924850Z`
* **End Time (UTC):** `2026-09-10T12:02:58.644824Z`
* **Duration:** 6.72 seconds
* **Exit Code:** `0`
* **Errors/Warnings:** **0 warnings, 0 errors**
* **Classification:** **VERIFIED**

### Execution 5: Backend Flake8 Audit
* **Command:** `.venv\Scripts\flake8 backend/`
* **Start Time (UTC):** `2026-09-10T12:02:58.644824Z`
* **End Time (UTC):** `2026-09-10T12:03:00.912561Z`
* **Exit Code:** `1` (Initial audit discovered 4 line-length violations)
  - `backend/core/reproduce.py:434:121`
  - `backend/tests/test_evidence_subsystem.py:9:121`
  - `backend/tests/test_evidence_subsystem.py:10:121`
  - `backend/tests/test_evidence_subsystem.py:76:121`
* **Remediation:** Lines wrapped; re-executed with **Exit Code: `0`**.
* **Classification:** **VERIFIED AFTER REPAIR**

### Execution 6: Next.js Production Build
* **Command:** `npm run build` (`next build`)
* **Start Time (UTC):** `2026-09-10T12:03:38.900376Z`
* **End Time (UTC):** `2026-09-10T12:04:20.506541Z`
* **Duration:** 41.60 seconds (Compile: 12.8s, Types: 2.4s, Static Generation: 1.5s)
* **Exit Code:** `0`
* **Prerendered Routes (17/17):**
  - `/`
  - `/_not-found`
  - `/alpha-discovery`
  - `/data`
  - `/execution`
  - `/features`
  - `/live-research`
  - `/model-lab`
  - `/monitoring`
  - `/native-engine`
  - `/portfolio`
  - `/quality-gate`
  - `/risk`
  - `/statistical-engine`
  - `/validation`
* **Classification:** **VERIFIED**

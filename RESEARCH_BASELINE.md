# QuantAlpha — Formal Research Baseline (Phase 0 Freeze)

```text
Platform:               QuantAlpha Institutional Research Operating System
Integrity Level:        Level 5 Candidate (Independent Verification in Progress)
Publication Commit:     49506a7e1eba600b730a86db950335bc45a6f737 (49506a7)
Measurement Commit:     e075456b288efa4e850d0f6e04128ca33a58ab4f (e075456)
Working Tree Cleanliness: clean (git_dirty_at_measurement: false, git_dirty_at_publication: false)
Baseline Frozen At:     2026-09-12
```

---

## 1. Baseline Specification & Provenance

| Parameter | Baseline Value |
| :--- | :--- |
| **Project Name** | QuantAlpha |
| **Architecture Tag** | `Level 5 Candidate — Research-Grade Quantitative OS` |
| **Publication Commit** | `49506a7e1eba600b730a86db950335bc45a6f737` (`49506a7`) |
| **Measurement Commit** | `e075456b288efa4e850d0f6e04128ca33a58ab4f` (`e075456`) |
| **Git Dirty State at Measurement** | `false` (Pristine working tree) |
| **Python Version** | `3.11.9` |
| **Node.js Version** | `v24.11.1` (Next.js 16.1.6 App Router) |
| **Operating System** | Windows 11 / WSL2 / Linux Ubuntu 22.04+ (Cross-Platform) |
| **Primary Datasets** | S&P 500 Daily OHLCV Parquet snapshot (`data/sp500_daily.parquet`), metadata registry (`data/pipeline_status.json`) |

---

## 2. Test & Route Inventory

```text
Verified Test Total:    407
  ├── Backend Tests:    381 (across 60 test suites in backend/tests/)
  └── Frontend Tests:   26 (unit, API contract, and adversarial failure suites)

Prerendered Routes:    17 Next.js static/dynamic application routes
Backend Test Status:    ALL_PASSED
Frontend Status:        ALL_PASSED
Lint & Static Analysis: 0 TypeScript errors, 0 ESLint errors, 0 Flake8 errors
```

### Full Route Surface (17 Prerendered Routes)

1. `/` (Mission Control Dashboard)
2. `/_global-error` (Global Exception Boundary)
3. `/_not-found` (Custom 404 Route)
4. `/alpha-discovery` (Alpha DSL & Genetic Programming Lab)
5. `/data` (Point-in-Time Data Ingestion & Quality Inspector)
6. `/execution` (Execution Broker & Microstructure Simulator)
7. `/favicon.ico`
8. `/features` (Orthogonal Feature Engineering & Cross-Sectional Ranking)
9. `/live-research` (Real-Time Market Data Streamer & Order Book)
10. `/model-lab` (ML & Statistical Modeling Lab)
11. `/monitoring` (Consensus Health & Node Diagnostics)
12. `/native-engine` (C++/Q Native Performance Engine)
13. `/portfolio` (Portfolio Optimization & Frontier Solver)
14. `/quality-gate` (Institutional Level 5 Quality Gatekeeper)
15. `/risk` (Parametric/Historical VaR, CVaR & Stress Matrix)
16. `/statistical-engine` (CPCV, PBO, Deflated Sharpe & Falsification Engine)
17. `/validation` (Adversarial Robustness & Attack Simulation Matrix)

---

## 3. Known Limitations

1. **Level 5 Candidate Status**: The 407-test suite and Gate 0–7 integrity framework are self-consistent and pass all internal regression suites, but require external clean-room multi-platform independent verification (Phase 1).
2. **Universe Scale**: The default local market snapshot contains 14–50 S&P 500 equities. Large-scale multi-thousand ticker universes require the planned Real Financial Dataset Layer and Security Master (Phases 4 & 5).
3. **Multi-Asset Coverage**: Primary empirical tests currently focus on equities and synthetic macro feeds. Full cross-asset integration (Rates, FX, Commodities, Volatility) is targeted for Phase 9.
4. **Trial Search Transparency**: The Alpha DSL/GP discovery engine currently generates and evaluates expressions in-memory; an explicit, persistent Alpha Trial Registry (`TRIAL-000001` ... `TRIAL-010000`) with registered negative results is required (Phases 7 & 8).

---

## 4. Known Synthetic & Simulator Components

To maintain complete scientific honesty and avoid unwarranted institutional claims:

| Component | Nature | Description & Boundary |
| :--- | :--- | :--- |
| **FIX Protocol** | *Research Conformance Subset* | Conforms strictly to FIX 4.2 framing, tag-value parsing, sequence ordering, and logon/execution report state machines for research simulation. *Not a certified external broker gateway.* |
| **Raft Consensus** | *In-Memory Deterministic Matrix* | Randomized crash, omission, partition, and Byzantine fault simulation engine. *Not a physically distributed multi-datacenter consensus deployment.* |
| **Exchange & OMS/EMS** | *Microstructure Research Simulator* | Realistic order queue, synthetic limit order book, TWAP/VWAP/POV execution algorithms, and slippage/spread modeling. *Not a physical exchange matching engine.* |
| **Data Generation** | *Deterministic Synthetic Generators* | Geometric Brownian motion, regime-switching jump-diffusion, and synthetic tick generators for stress and boundary condition testing. |

---

## 5. Clean-Room Reproduction Procedure

To verify this baseline from a clean-room independent environment without cached artifacts:

### Step 1: Clone & Checkout Baseline

```bash
git clone https://github.com/Monkey0-9/alpha-research-lab.git quant-alpha
cd quant-alpha
git checkout 49506a7
```

### Step 2: Fresh Python Environment

```bash
# Windows
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Fresh Node.js Dependencies

```bash
npm ci
```

### Step 4: Run Gate 0 Integrity & Self-Consistency Verification

```bash
python scripts/verify_integrity.py --check --strict-git --strict-clean
```

*Expected Output*: `[Gate 0] PASS: STATUS.json is self-consistent.` and `[Gate 0] PASS: RUN_MANIFEST.json is self-consistent.`

### Step 5: Execute Independent Test Runners

```bash
# 1. Backend Pytest Suite (381 tests across 60 suites)
pytest

# 2. Frontend Test Suite (26 tests)
npm test

# 3. Next.js Static & Dynamic Build (17 prerendered routes)
npm run build

# 4. Code Style & Flake8 Linting
flake8 backend/
```

---

## 6. Next Immediate Roadmap Milestones

* **Milestone M1 (Current)**: Freeze Baseline (Phase 0) + Clean-Room Reproducibility (Phase 1).
* **Milestone M2**: Independent Statistical Oracles (Phase 2) + Backtesting Adversarial Attack Framework (Phase 3).
* **Milestone M3**: Real Financial Dataset Layer (Phase 4) + Point-in-Time Security Master (Phase 5).
* **Milestone M4**: Alpha Trial Registry & False Discovery Governance (Phases 7 & 8).
* **Milestone M5**: Multi-Asset Regime-Aware Alpha & Portfolio Optimization (Phases 9, 10, 11).
* **Milestone M6**: Canonical Preregistered Experiment EXP-001 & Final Research Publication (Phases 16, 17, 18, 19).

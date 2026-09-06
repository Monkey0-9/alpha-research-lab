# Target Architecture Specification: QuantAlpha Institutional v1.0

## 1. High-Level Blueprint

```
                                  QUANTALPHA
                                       │
               ┌───────────────────────┴────────────────────────┐
               │                                                │
               ▼                                                ▼
         RESEARCH PLANE                                  CONTROL PLANE
               │                                                │
               ├── Data & Security Master                       ├── Identity & RBAC
               ├── Features & Factor Lab                        ├── Experiments Registry
               ├── Typed Alpha DSL (100+ Ops)                   ├── Dataset Registry (DS-XXXXXX)
               ├── Discovery & Genealogy                        ├── Alpha Book & Orthogonalization
               ├── Statistical Multi-Testing                    ├── Audit Trail (Double-Entry)
               ├── Falsification Battery                        ├── Governance & Promotion Gate
               ├── Backtest & Microstructure                    └── Pre-Trade Risk Compliance
               ├── Portfolio & Covariance
               ├── Real-Time Risk & Stress
               └── Execution Slicers
               │
               ▼
                         NATIVE COMPUTE FABRIC
               ┌──────────────┬──────────────┬──────────────┐
               │              │              │              │
            Python           C++            Rust            C
               │              │              │              │
         orchestration    simulation     data/infra      kernels
               │              │              │              │
               └──────────────┴──────────────┴──────────────┘
                                      │
                                      ▼
                                      R
                             independent statistics
                                      │
                                      ▼
                         Arrow / Parquet / DuckDB
                                      │
                         ┌────────────┴────────────┐
                         ▼                         ▼
                    PostgreSQL                 Object Store
                    (metadata)             (datasets/artifacts)
```

---

## 2. Institutional Quant Lifecycle

The platform strictly enforces the 17-step end-to-end research lifecycle:

```
Research Question
      ↓
Literature
      ↓
Hypothesis
      ↓
Pre-registration
      ↓
Point-in-Time Data
      ↓
Feature / Alpha DSL
      ↓
Alpha Discovery
      ↓
Multiple-Testing Correction
      ↓
CPCV / PBO / DSR / SPA
      ↓
Falsification
      ↓
Factor Neutralization
      ↓
Portfolio Optimization
      ↓
Realistic Execution Simulation
      ↓
Capacity
      ↓
Risk / Stress
      ↓
Paper Trading
      ↓
Reproducible Research Artifact
```

Every stage produces a cryptographically signed, immutable audit artifact.

---

## 3. The 10 Milestones

- **M0: Foundation Freeze**: Preserving baseline (`v0.1-baseline`), test metrics, and architectural specifications.
- **M1: Institutional Data Layer**: Permanent symbology (`FIGI`/`CUSIP`), corporate action unmutated raw store (`RAW_PRICE`, `SPLIT_ADJUSTED`, `TOTAL_RETURN`, `TRADEABLE_PRICE`), historical point-in-time universe, and dataset registry (`DS-XXXXXX`).
- **M2: Research & Alpha Engine**: Typed Alpha DSL (100+ operators), canonical AST deduplication, pairwise correlation orthogonalization, alpha decay half-life, and alpha genealogy.
- **M3: Statistical Governance**: CPCV path distributions, trial-linked PBO and DSR, White's Reality Check, Hansen's SPA, and Alpha Evidence Card generation.
- **M4: C++ Backtest & Execution**: Event loop (`MarketEvent`, `OrderEvent`, `FillEvent`, `BorrowEvent`), order state machine, L2 order book matching, TWAP/VWAP/Almgren-Chriss slicers, and short borrow fee accruals.
- **M5: Portfolio & Risk Engine**: Ledoit-Wolf and OAS shrinkage covariance, convex QP/SOCP optimizer with institutional constraints, historical crisis stress testing, and pre-trade compliance checks.
- **M6: Falsification & Governance**: Mandatory 11-step falsification battery and formal 11-stage promotion state machine.
- **M7: Polyglot Performance**: Zero-copy Apache Arrow boundaries between Python, C++, Rust, and C.
- **M8: Production Infrastructure**: PostgreSQL metadata, MinIO/S3 object storage, DuckDB analytical engine, Redis Celery workers, and WebSocket telemetry.
- **M9: Paper Trading & OMS**: Broker gateway abstraction, real-time order generation, position reconciliation, and trading halts.
- **M10: Institutional Certification**: Comprehensive audit, known-answer regression testing, and production certification.

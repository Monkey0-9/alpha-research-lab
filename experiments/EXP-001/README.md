# Experiment EXP-001: Regime-Aware Multi-Asset Alpha Generation

## Overview

**EXP-001** is the flagship quantitative research experiment of the **QuantAlpha Research Operating System**.

It addresses the fundamental scientific challenge in systematic investing: **backtest overfitting and false discovery survival under realistic market friction**.

---

## Directory Structure

```text
experiments/EXP-001/
├── README.md                   # This overview
├── preregistration.md          # Formal pre-experimental commitment document
├── experiment_manifest.json    # Machine-readable scientific provenance manifest
├── trial_registry/             # Complete log of all 10,000 candidate trials (PASS & FAIL)
├── results/                    # OOS return series, benchmarks, and friction breakdowns
├── figures/                    # Equity curves, regime state charts, and PBO distributions
└── evidence/                   # Cryptographic Merkle DAG evidence packages
```

---

## Central Research Question

> *Does regime-aware multi-asset alpha generation improve out-of-sample risk-adjusted performance after transaction costs and multiple-testing correction?*

---

## Four-Model Benchmark Matrix

| Model Identifier | Architecture Description | Purpose |
| :--- | :--- | :--- |
| **Model A** | Equal-Weight Buy-and-Hold ($1/N$) | Naive market beta baseline |
| **Model B** | Non-Regime Alpha (Momentum + Reversal) | Unconditional quantitative strategy |
| **Model C** | Regime-Conditioned Alpha | Alpha conditioned on 3-state HMM |
| **Model D** | Full QuantAlpha Pipeline | Regime + Alpha Orthogonalization + DSR/FDR + HRP/CVaR + Almgren-Chriss |

---

## Reproduction

Upon completion of the trial search and execution simulations, this experiment can be reproduced via:

```bash
python scripts/reproduce_exp001.py
```

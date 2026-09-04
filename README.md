# QuantAlpha Research Platform

A comprehensive, end-to-end quantitative alpha research and production monitoring platform built with Next.js (App Router), TypeScript, and Recharts.

---

## 🌟 Architecture & Modules Overview

The platform features 12 interconnected modules structured across the complete quantitative research pipeline:

| # | Module | Route | Key Capabilities |
|---|---|---|---|
| **00** | **Executive Dashboard** | [`/`](src/app/page.tsx) | Live portfolio metrics, P&L / drawdown dynamics, alert feeds, and pipeline orchestration |
| **01** | **Data Infrastructure** | [`/data`](src/app/data/page.tsx) | Multi-source streaming feeds, PIT (point-in-time) temporal join store, DAG lineage, quality gate metrics |
| **02** | **Feature / Signal Factory** | [`/features`](src/app/features/page.tsx) | Price, Fundamental, Macro, and Microstructure features, rolling IC/Rank IC analysis, interactive parameter tuning |
| **03** | **Alpha Discovery Lab** | [`/alpha-discovery`](src/app/alpha-discovery/page.tsx) | Genetic programming expression search, ML feature importance ranking, hypothesis pipeline, IC vs. Sharpe scatter |
| **04** | **Statistical Engine** | [`/statistical-engine`](src/app/statistical-engine/page.tsx) | Multiple testing correction (Bonferroni / BH-FDR), DSR, alpha decay half-life, autocorrelation analysis |
| **05** | **Model Research Lab** | [`/model-lab`](src/app/model-lab/page.tsx) | Model tournament (LightGBM, XGBoost, CatBoost, LSTM, Transformers), training loss curves, interactive ensemble weight builder |
| **06** | **Time-Series Validation** | [`/validation`](src/app/validation/page.tsx) | Walk-forward cross-validation, purged k-fold with embargo windows, market regime robustness audits |
| **07** | **Alpha Quality Gate** | [`/quality-gate`](src/app/quality-gate/page.tsx) | Strict 9-criteria pass/fail gate (IC, OOS, FDR, decay, turnover, correlation, drawdown, regime, capacity) with radar comparisons |
| **08** | **Portfolio Engine** | [`/portfolio`](src/app/portfolio/page.tsx) | Mean-Variance, Risk Parity, CVaR Min optimization, Efficient Frontier scatter, factor exposures, hard constraints |
| **09** | **Execution Research** | [`/execution`](src/app/execution/page.tsx) | Almgren-Chriss market impact model ($\sqrt{\text{ADV}}$), venue fill quality, slippage tracking vs limits, algo selector |
| **10** | **Risk Engine** | [`/risk`](src/app/risk/page.tsx) | Historical VaR / CVaR (95% & 99%), Barra-style factor risk attribution, drawdown curves, historical stress scenarios |
| **11** | **Live Research** | [`/live-research`](src/app/live-research/page.tsx) | Paper trading experiment tracking, paper-to-production promotion criteria, live production alpha health |
| **12** | **Production Monitor** | [`/monitoring`](src/app/monitoring/page.tsx) | Real-time system telemetry, alpha decay alerts, feature drift (PSI score), subsystem latency/uptime |

---

## 🛠️ Tech Stack

- **Framework**: [Next.js](https://nextjs.org/) (App Router, Turbopack)
- **Language**: TypeScript (Strict Mode)
- **Styling**: Vanilla CSS Design System with dark mode, glassmorphism, responsive grid layouts
- **Charts & Visualizations**: [Recharts](https://recharts.org/) (Area, Bar, Line, Radar, Scatter)
- **Icons**: [Lucide React](https://lucide.dev/)

---

## 🚀 Getting Started

### 1. Install Dependencies

```bash
npm install
```

### 2. Run Type Check

```bash
npx tsc --noEmit
```

### 3. Build for Production

```bash
npm run build
```

### 4. Start Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser to explore the platform.

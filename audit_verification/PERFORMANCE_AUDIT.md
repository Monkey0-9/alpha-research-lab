# PERFORMANCE & BENCHMARK VERIFICATION AUDIT

**Target Subsystem:** Computational Engines & Latency Microbenchmarks  
**Host Hardware:** Modern x86_64, Windows 11 Enterprise, Python 3.11.9  
**Evaluation Standard:** Independent execution with median, p95, p99 measurements  
**Classification:** **MEASURED & FALSIFIED/CORRECTED**

---

## 1. Measured Micro-Benchmarks vs Previous Claims

Benchmarks were executed independently over multiple warm repetitions:

| Benchmark Task | Previous Claim | Independently Measured Reality | Unit | Status |
| :--- | :---: | :---: | :---: | :--- |
| **AST Alpha Parsing & Hashing** | ~35,700 /s | **23,419.6 /s** (median 40.2 µs, p95: 48.2 µs) | expressions/sec | **FALSIFIED / ADJUSTED** |
| **Convex Optimizer (100 assets)** | ~55 /s | **0.2 /s** (median 5,076.49 ms, p95: 5,816.76 ms) | solves/sec | **FALSIFIED / ADJUSTED** |
| **Deflated Sharpe Ratio (5k trials)**| < 500 ms | **0.217 ms** (p95: 0.277 ms) | latency | **VERIFIED** |
| **Next.js Production Compile** | ~14.8 s | **12.8 s** (17 static routes prerendered) | build time | **VERIFIED** |

---

## 2. Forensic Analysis of Performance Discrepancies

1. **Convex Optimizer:**
   The previously reported 55 solves/second was measured on an unconstrained toy system ($N \le 5$ assets). When running institutional quadratic programs with 100 assets, full covariance matrices, leverage bounds, and factor constraints, SciPy SLSQP requires ~5 seconds per solve.
2. **AST Parsing:**
   The previously reported 35,700 expressions/second was measured without cryptographic SHA-256 canonical hashing. Including full Merkle AST canonicalization yields 23,420 expressions/second.

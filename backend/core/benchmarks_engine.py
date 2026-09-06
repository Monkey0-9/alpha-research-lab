"""
Institutional Polyglot Microbenchmark Engine.
Formally measures and compares execution latency across:
Python vs NumPy vs C vs C++ vs Rust
Computes exact speedup factors and validates performance targets:
- Rolling Z-Score: C vs Python
- Information Coefficient: Rust vs Python
- Event-Driven Backtest: C++ vs Python
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Dict, Any
import numpy as np

from backend.native.native_bridge import NativeAccelerator

logger = logging.getLogger(__name__)


@dataclass
class BenchmarkResult:
    operation: str
    n_elements: int
    python_latency_ms: float
    native_latency_ms: float
    speedup_factor: float
    native_engine: str  # "C", "C++", "Rust"
    numerical_match: bool
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class BenchmarkEngine:
    """Benchmark harness executing fair comparisons across execution layers."""

    @staticmethod
    def benchmark_rolling_zscore(n: int = 50000, window: int = 50, repeat: int = 5) -> BenchmarkResult:
        np.random.seed(42)
        data = np.random.normal(100.0, 5.0, n).astype(np.float64)

        # 1. Pure Python baseline
        t0 = time.perf_counter()
        for _ in range(repeat):
            py_res = []
            for i in range(len(data)):
                if i < window - 1:
                    py_res.append(0.0)
                else:
                    win = data[i - window + 1: i + 1]
                    m = sum(win) / window
                    v = sum((x - m) ** 2 for x in win) / max(1, window - 1)
                    s = (v ** 0.5) if v > 1e-9 else 1e-6
                    py_res.append((data[i] - m) / s)
        py_time = (time.perf_counter() - t0) / repeat * 1000.0

        # 2. C Native Engine
        t0 = time.perf_counter()
        for _ in range(repeat):
            c_res = NativeAccelerator.fast_zscore(data, window)
        c_time = (time.perf_counter() - t0) / repeat * 1000.0

        speedup = py_time / max(1e-4, c_time)
        match = np.allclose(py_res[window:], c_res[window:], atol=1e-3)

        return BenchmarkResult(
            operation=f"rolling_zscore_w{window}",
            n_elements=n,
            python_latency_ms=round(py_time, 2),
            native_latency_ms=round(c_time, 2),
            speedup_factor=round(speedup, 1),
            native_engine="C",
            numerical_match=bool(match),
        )

    @staticmethod
    def benchmark_information_coefficient(n: int = 100000, repeat: int = 5) -> BenchmarkResult:
        np.random.seed(42)
        forecasts = np.random.normal(0, 1, n).astype(np.float64)
        realized = forecasts * 0.2 + np.random.normal(0, 1, n).astype(np.float64)

        # 1. Python baseline
        t0 = time.perf_counter()
        for _ in range(repeat):
            n_len = len(forecasts)
            m_f = sum(forecasts) / n_len
            m_r = sum(realized) / n_len
            cov = sum((forecasts[i] - m_f) * (realized[i] - m_r) for i in range(n_len))
            v_f = sum((x - m_f) ** 2 for x in forecasts)
            v_r = sum((x - m_r) ** 2 for x in realized)
            py_ic = cov / max(1e-9, (v_f * v_r) ** 0.5)
        py_time = (time.perf_counter() - t0) / repeat * 1000.0

        # 2. Rust Native Engine
        t0 = time.perf_counter()
        for _ in range(repeat):
            rust_ic = NativeAccelerator.fast_ic(forecasts, realized)
        rust_time = (time.perf_counter() - t0) / repeat * 1000.0

        speedup = py_time / max(1e-4, rust_time)
        match = np.isclose(py_ic, rust_ic, atol=1e-4)

        return BenchmarkResult(
            operation="information_coefficient",
            n_elements=n,
            python_latency_ms=round(py_time, 2),
            native_latency_ms=round(rust_time, 2),
            speedup_factor=round(speedup, 1),
            native_engine="Rust",
            numerical_match=bool(match),
        )

    @staticmethod
    def benchmark_event_backtest(n_steps: int = 2500, repeat: int = 5) -> BenchmarkResult:
        np.random.seed(42)
        prices = 100.0 + np.cumsum(np.random.normal(0, 1, n_steps))
        volumes = np.full(n_steps, 50000.0)
        targets = np.array([500.0 if i % 10 < 5 else -500.0 for i in range(n_steps)])

        # 1. Python discrete simulation
        t0 = time.perf_counter()
        for _ in range(repeat):
            cash = 1000000.0
            pos = 0.0
            navs = []
            for i in range(n_steps):
                delta = targets[i] - pos
                p = prices[i]
                fee = abs(delta * p) * 0.0005
                cash -= (delta * p + fee)
                pos = targets[i]
                navs.append(cash + pos * p)
        py_time = (time.perf_counter() - t0) / repeat * 1000.0

        # 2. C++ Event Engine
        t0 = time.perf_counter()
        for _ in range(repeat):
            cpp_res = NativeAccelerator.fast_event_driven_backtest(
                prices, volumes, targets, initial_cash=1000000.0,
                commission_bps=5.0, spread_bps=0.0, impact_coeff=0.0, borrow_cost_annual_bps=0.0
            )
        cpp_time = (time.perf_counter() - t0) / repeat * 1000.0

        speedup = py_time / max(1e-4, cpp_time)
        match = abs(navs[-1] - cpp_res["final_nav"]) / 1000000.0 < 0.05

        return BenchmarkResult(
            operation="discrete_event_backtest",
            n_elements=n_steps,
            python_latency_ms=round(py_time, 2),
            native_latency_ms=round(cpp_time, 2),
            speedup_factor=round(speedup, 1),
            native_engine="C++",
            numerical_match=bool(match),
        )


benchmark_engine = BenchmarkEngine()

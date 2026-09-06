"""
Performance microbenchmarks test suite.
Validates that native acceleration (C, C++, Rust) delivers measured speedups
over pure Python reference implementations while preserving exact numerical equivalence.
"""
from backend.core.benchmarks_engine import BenchmarkEngine


def test_benchmark_rolling_zscore_c_acceleration():
    res = BenchmarkEngine.benchmark_rolling_zscore(n=10000, window=30, repeat=2)
    assert res.native_engine == "C"
    assert res.numerical_match is True
    assert res.speedup_factor > 1.0
    assert res.native_latency_ms < res.python_latency_ms


def test_benchmark_ic_rust_acceleration():
    res = BenchmarkEngine.benchmark_information_coefficient(n=20000, repeat=2)
    assert res.native_engine == "Rust"
    assert res.numerical_match is True
    assert res.speedup_factor > 1.0
    assert res.native_latency_ms < res.python_latency_ms


def test_benchmark_backtest_cpp_acceleration():
    res = BenchmarkEngine.benchmark_event_backtest(n_steps=500, repeat=2)
    assert res.native_engine == "C++"
    assert res.numerical_match is True

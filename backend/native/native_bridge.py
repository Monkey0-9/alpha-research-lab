"""
Unified Polyglot Native Dispatcher.
Bridges C, C++, Rust, R, Q, and OCaml native modules into high-speed Python calls.
"""
from __future__ import annotations

import ctypes
import logging
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

from native.q_engine.q_service import q_engine
from native.r_engine.r_service import r_engine
from native.ocaml_engine.ocaml_service import ocaml_engine

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent


def _find_lib(dir_name: str, base_name: str) -> Optional[Path]:
    for ext in (".dll", ".so", ".dylib"):
        p = BASE_DIR / dir_name / f"{base_name}{ext}"
        if p.exists():
            return p
    return None


# Load C Engine
C_LIB_PATH = _find_lib("c_engine", "c_engine")
_c_lib = None
if C_LIB_PATH and C_LIB_PATH.exists():
    try:
        _c_lib = ctypes.CDLL(str(C_LIB_PATH))
        _c_lib.c_rolling_mean.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        _c_lib.c_rolling_std.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        _c_lib.c_rolling_rsi.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_int]
        _c_lib.c_simulate_pnl.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int, ctypes.c_double]
        logger.info("C Native Engine loaded successfully from %s", C_LIB_PATH)
    except Exception as e:
        logger.warning("Could not load C engine: %s", e)

# Load C++ Engine
CPP_LIB_PATH = _find_lib("cpp_engine", "cpp_engine")
_cpp_lib = None
if CPP_LIB_PATH and CPP_LIB_PATH.exists():
    try:
        _cpp_lib = ctypes.CDLL(str(CPP_LIB_PATH))
        _cpp_lib.cpp_almgren_chriss_trajectory.argtypes = [
            ctypes.c_double, ctypes.c_int, ctypes.c_double, ctypes.c_double,
            ctypes.c_double, ctypes.c_double, ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double)
        ]
        _cpp_lib.cpp_simulate_twap.argtypes = [
            ctypes.c_double, ctypes.c_int, ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.c_double, ctypes.c_double,
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double)
        ]
        logger.info("C++ Native Engine loaded successfully from %s", CPP_LIB_PATH)
    except Exception as e:
        logger.warning("Could not load C++ engine: %s", e)

# Load Rust Engine
RUST_LIB_PATH = _find_lib("rust_engine", "rust_engine")
_rust_lib = None
if RUST_LIB_PATH and RUST_LIB_PATH.exists():
    try:
        _rust_lib = ctypes.CDLL(str(RUST_LIB_PATH))
        _rust_lib.rust_sharpe_ratio.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_double]
        _rust_lib.rust_sharpe_ratio.restype = ctypes.c_double

        _rust_lib.rust_max_drawdown.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t]
        _rust_lib.rust_max_drawdown.restype = ctypes.c_double

        _rust_lib.rust_cvar_historical.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_double]
        _rust_lib.rust_cvar_historical.restype = ctypes.c_double

        _rust_lib.rust_fast_backtest_pnl.argtypes = [
            ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double),
            ctypes.POINTER(ctypes.c_double), ctypes.c_size_t, ctypes.c_double
        ]
        _rust_lib.rust_fast_backtest_pnl.restype = ctypes.c_double
        logger.info("Rust Native Engine loaded successfully.")
    except Exception as e:
        logger.warning("Could not load Rust engine: %s", e)


class NativeAccelerator:
    """Central accelerator managing C, C++, Rust, R, Q, and OCaml implementations."""

    @staticmethod
    def fast_sharpe(returns: np.ndarray, periods: float = 252.0) -> float:
        if _rust_lib is not None and len(returns) > 1:
            arr = np.ascontiguousarray(returns, dtype=np.float64)
            ptr = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            return float(_rust_lib.rust_sharpe_ratio(ptr, len(arr), periods))
        # Fallback
        vol = np.std(returns, ddof=1)
        return float((np.mean(returns) / vol) * np.sqrt(periods)) if vol > 1e-9 else 0.0

    @staticmethod
    def fast_max_drawdown(equity: np.ndarray) -> float:
        if _rust_lib is not None and len(equity) > 1:
            arr = np.ascontiguousarray(equity, dtype=np.float64)
            ptr = arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double))
            return float(_rust_lib.rust_max_drawdown(ptr, len(arr)))
        peak = np.maximum.accumulate(equity)
        return float(np.max((peak - equity) / np.maximum(peak, 1e-9)))

    @staticmethod
    def fast_pnl_simulation(daily_returns: np.ndarray, positions: np.ndarray, fee_bps: float = 5.0) -> np.ndarray:
        n = min(len(daily_returns), len(positions))
        if n == 0:
            return np.array([])
        out = np.zeros(n, dtype=np.float64)

        if _rust_lib is not None:
            r_arr = np.ascontiguousarray(daily_returns[:n], dtype=np.float64)
            p_arr = np.ascontiguousarray(positions[:n], dtype=np.float64)
            _rust_lib.rust_fast_backtest_pnl(
                r_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                p_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                n,
                fee_bps
            )
            return out
        elif _c_lib is not None:
            r_arr = np.ascontiguousarray(daily_returns[:n], dtype=np.float64)
            p_arr = np.ascontiguousarray(positions[:n], dtype=np.float64)
            _c_lib.c_simulate_pnl(
                r_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                p_arr.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                out.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                n,
                fee_bps
            )
            return out
        else:
            fee_rate = fee_bps / 10000.0
            prev_pos = 0.0
            for i in range(n):
                pos = positions[i]
                turnover = abs(pos - prev_pos)
                out[i] = pos * daily_returns[i] - turnover * fee_rate
                prev_pos = pos
            return out

    @staticmethod
    def fast_almgren_chriss(
        total_shares: float,
        intervals: int,
        risk_aversion: float = 1e-6,
        volatility: float = 0.02,
        temp_impact: float = 2.5e-6,
        perm_impact: float = 2.5e-7
    ) -> Dict[str, Any]:
        if _cpp_lib is not None and intervals > 0:
            holdings = np.zeros(intervals + 1, dtype=np.float64)
            trades = np.zeros(intervals, dtype=np.float64)
            cost = ctypes.c_double(0.0)

            _cpp_lib.cpp_almgren_chriss_trajectory(
                total_shares, intervals, risk_aversion, volatility,
                temp_impact, perm_impact,
                holdings.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                trades.ctypes.data_as(ctypes.POINTER(ctypes.c_double)),
                ctypes.byref(cost)
            )
            return {
                "engine": "C++-Almgren-Chriss",
                "holdings": holdings.tolist(),
                "trade_schedule": trades.tolist(),
                "expected_impact_cost": float(cost.value)
            }
        # Fallback linear schedule
        trade_size = total_shares / max(1, intervals)
        return {
            "engine": "Python-Linear-Fallback",
            "holdings": [total_shares - i * trade_size for i in range(intervals + 1)],
            "trade_schedule": [trade_size] * intervals,
            "expected_impact_cost": total_shares * volatility * 0.0005
        }

    @staticmethod
    def q_vwap(prices: np.ndarray, volumes: np.ndarray) -> float:
        return q_engine.calc_vwap(prices, volumes)

    @staticmethod
    def r_factor_attribution(portfolio_returns: np.ndarray, factors: Dict[str, np.ndarray]) -> Dict[str, Any]:
        return r_engine.run_factor_attribution(portfolio_returns, factors)

    @staticmethod
    def ocaml_quality_gate(criteria: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        return ocaml_engine.evaluate(criteria)


accelerator = NativeAccelerator()

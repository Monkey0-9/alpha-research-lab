"""
Level-5 Synthetic Data & Fallback Firewall.
Guards runtime execution modes (EMPIRICAL, SIMULATION, FIXTURE) and strictly rejects:
1. Missing data -> synthetic
2. Missing data -> default
3. Optimizer failure -> equal weight
4. Model failure -> plausible metric
5. Failure -> PASS
"""
from __future__ import annotations

import contextlib
import enum
import logging
import threading
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ResearchMode(str, enum.Enum):
    EMPIRICAL = "EMPIRICAL"
    SIMULATION = "SIMULATION"
    FIXTURE = "FIXTURE"


# Thread-local storage for active research mode
_state = threading.local()


def get_current_research_mode() -> ResearchMode:
    return getattr(_state, "mode", ResearchMode.EMPIRICAL)


def set_current_research_mode(mode: ResearchMode) -> None:
    _state.mode = mode


@contextlib.contextmanager
def research_mode_context(mode: ResearchMode):
    old_mode = get_current_research_mode()
    _state.mode = mode
    try:
        yield
    finally:
        _state.mode = old_mode


# ---------------------------------------------------------------------------
# Strict Level-5 Firewall Failure Exceptions
# ---------------------------------------------------------------------------

class EmpiricalIntegrityViolationException(Exception):
    """Base exception for Level-5 empirical firewall violations."""


class SyntheticDataBlockedException(EmpiricalIntegrityViolationException):
    """Raised when synthetic or simulated data is passed to an empirical research process."""


class FallbackBlockedException(EmpiricalIntegrityViolationException):
    """Raised when an algorithm attempts to substitute missing empirical data with defaults."""


class MissingDataException(EmpiricalIntegrityViolationException):
    """Raised when required market, trade, or quote data is missing (NO DATA -> FAIL)."""


class DataHashMismatchException(EmpiricalIntegrityViolationException):
    """Raised when data hash differs from certified manifest (DATA HASH MISMATCH -> FAIL)."""


class MissingValidationException(EmpiricalIntegrityViolationException):
    """Raised when validation results are absent or bypassed (MISSING VALIDATION -> FAIL)."""


class StatisticalTestNotRunException(EmpiricalIntegrityViolationException):
    """Raised when mandatory statistical correction tests were omitted (STATISTICAL TEST NOT RUN -> FAIL)."""


class ExecutionModelUnavailableException(EmpiricalIntegrityViolationException):
    """Raised when execution cost or slippage solver is unavailable (EXECUTION MODEL UNAVAILABLE -> FAIL)."""


class RiskModelUnavailableException(EmpiricalIntegrityViolationException):
    """Raised when risk model or factor covariance matrix is missing (RISK MODEL UNAVAILABLE -> FAIL)."""


class OptimizerFailureException(EmpiricalIntegrityViolationException):
    """Raised when portfolio convex solver fails to converge (OPTIMIZER FAILURE -> FAIL)."""


class LedgerImbalanceException(EmpiricalIntegrityViolationException):
    """Raised when double-entry accounting invariants are violated (LEDGER IMBALANCE -> FAIL)."""


# ---------------------------------------------------------------------------
# Authoritative Fallback Firewall
# ---------------------------------------------------------------------------

class FallbackFirewall:
    """
    Enforces that research in ResearchMode.EMPIRICAL fails closed and never manufactures data.
    """

    @classmethod
    def assert_empirical_data_present(cls, data: Any, name: str = "dataset") -> None:
        """Enforces: NO DATA -> FAIL."""
        is_empty = (
            data is None
            or (hasattr(data, "empty") and data.empty)
            or (isinstance(data, (list, dict)) and len(data) == 0)
        )
        if is_empty:
            raise MissingDataException(
                f"NO DATA -> FAIL: Required empirical entity '{name}' is completely absent. "
                "Substitution with synthetic or default data is strictly forbidden."
            )

    @classmethod
    def assert_empirical_hash_match(cls, expected_hash: str, actual_hash: str, name: str = "dataset") -> None:
        """Enforces: DATA HASH MISMATCH -> FAIL."""
        if expected_hash != actual_hash:
            raise DataHashMismatchException(
                f"DATA HASH MISMATCH -> FAIL: Dataset '{name}' hash {actual_hash} "
                f"does not match manifest expectation {expected_hash}."
            )

    @classmethod
    def assert_validation_executed(cls, validation_result: Optional[dict]) -> None:
        """Enforces: MISSING VALIDATION -> FAIL."""
        if not validation_result or not validation_result.get("executed", False):
            raise MissingValidationException(
                "MISSING VALIDATION -> FAIL: Empirical model cannot proceed without verified validation."
            )

    @classmethod
    def assert_statistical_tests_executed(cls, stats_result: Optional[dict]) -> None:
        """Enforces: STATISTICAL TEST NOT RUN -> FAIL."""
        if not stats_result or not stats_result.get("executed", False):
            raise StatisticalTestNotRunException(
                "STATISTICAL TEST NOT RUN -> FAIL: Deflated Sharpe / Multiple Testing corrections have not run."
            )

    @classmethod
    def assert_execution_model_available(cls, model_available: bool, detail: str = "") -> None:
        """Enforces: EXECUTION MODEL UNAVAILABLE -> FAIL."""
        if not model_available:
            raise ExecutionModelUnavailableException(
                f"EXECUTION MODEL UNAVAILABLE -> FAIL: Real microstructure/impact engine unavailable. {detail}"
            )

    @classmethod
    def assert_risk_model_available(cls, model_available: bool, detail: str = "") -> None:
        """Enforces: RISK MODEL UNAVAILABLE -> FAIL."""
        if not model_available:
            raise RiskModelUnavailableException(
                f"RISK MODEL UNAVAILABLE -> FAIL: Factor risk model unavailable. {detail}"
            )

    @classmethod
    def assert_optimizer_success(cls, status: str, detail: str = "") -> None:
        """Enforces: OPTIMIZER FAILURE -> FAIL (Never equal weight)."""
        if status.upper() not in ("OPTIMAL", "CONVERGED", "SUCCESS"):
            raise OptimizerFailureException(
                f"OPTIMIZER FAILURE -> FAIL: Solver returned status '{status}'. {detail} "
                "Defaulting to equal-weighting is strictly prohibited."
            )

    @classmethod
    def assert_ledger_balanced(cls, debits: float, credits: float, tolerance: float = 1e-6) -> None:
        """Enforces: LEDGER IMBALANCE -> FAIL."""
        diff = abs(debits - credits)
        if diff > tolerance:
            raise LedgerImbalanceException(
                f"LEDGER IMBALANCE -> FAIL: Total Debits ({debits:.4f}) != Total Credits ({credits:.4f}), "
                f"discrepancy {diff:.6f} exceeds tolerance {tolerance}."
            )

    @classmethod
    def reject_synthetic_fallback(cls, source_name: str, payload_type: str = "data") -> None:
        """Rejects synthetic sources when operating in EMPIRICAL mode."""
        if get_current_research_mode() == ResearchMode.EMPIRICAL:
            raise SyntheticDataBlockedException(
                f"SYNTHETIC DATA BLOCKED: Attempted to inject synthetic {payload_type} from '{source_name}' "
                "into empirical research workflow. Synthetic fallbacks are illegal in ResearchMode.EMPIRICAL."
            )

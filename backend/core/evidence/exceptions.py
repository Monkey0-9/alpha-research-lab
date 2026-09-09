"""
Level-5 Evidence Subsystem Fail-Closed Exceptions.
"""
from __future__ import annotations


class EvidenceException(Exception):
    """Base exception for all evidence and integrity failures."""


class EvidenceChainBrokenException(EvidenceException):
    """Raised when an evidence chain's cryptographic linkage is broken."""


class TamperingDetectedException(EvidenceException):
    """Raised when an artifact's content or hash does not match canonical computation."""


class MissingEvidenceException(EvidenceException):
    """Raised when a required evidence stage or artifact is missing or incomplete."""


class LedgerCorruptionException(EvidenceException):
    """Raised when a double-entry ledger invariant (Debits == Credits) is violated."""


class OptimizationFailedException(EvidenceException):
    """Raised when a portfolio optimization solver fails or is infeasible."""


class RiskModelUnavailableException(EvidenceException):
    """Raised when risk model or factor data is unavailable in empirical paths."""


class ReproductionFailedException(EvidenceException):
    """Raised when exact multi-metric reproduction fails verification."""

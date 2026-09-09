"""
Journal Entries and Immutable Debit/Credit Splits.
Every transaction must be zero-sum (sum(debits) == sum(credits)).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import List, Dict, Any

from ..evidence.exceptions import LedgerCorruptionException


@dataclass
class JournalLine:
    account: str
    debit: float = 0.0
    credit: float = 0.0

    def __post_init__(self):
        if self.debit < 0 or self.credit < 0:
            raise LedgerCorruptionException(
                f"Negative balance line forbidden: debit={self.debit}, credit={self.credit}"
            )
        if self.debit > 0 and self.credit > 0:
            raise LedgerCorruptionException(
                f"Single line cannot have both debit and credit: debit={self.debit}, credit={self.credit}"
            )


@dataclass
class JournalTransaction:
    """
    Atomic double-entry transaction.
    Maintains cryptographic link to previous transaction hash.
    """
    transaction_id: str
    timestamp: str
    description: str
    lines: List[JournalLine]
    prev_hash: str = "GENESIS_TX"
    transaction_hash: str = ""

    def __post_init__(self):
        self.verify_balance()
        if not self.transaction_hash:
            self.transaction_hash = self.compute_hash()

    def verify_balance(self, tol: float = 1e-6) -> None:
        total_debits = sum(line.debit for line in self.lines)
        total_credits = sum(line.credit for line in self.lines)
        if abs(total_debits - total_credits) > tol:
            raise LedgerCorruptionException(
                f"LEDGER_CORRUPTION: Debits ({total_debits:.6f}) != Credits ({total_credits:.6f}) "
                f"in transaction {self.transaction_id}"
            )

    def compute_hash(self) -> str:
        lines_str = ";".join(f"{line.account}:{line.debit:.6f}:{line.credit:.6f}" for line in self.lines)
        payload = f"{self.transaction_id}|{self.timestamp}|{lines_str}|{self.prev_hash}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "timestamp": self.timestamp,
            "description": self.description,
            "lines": [{"account": line.account, "debit": line.debit, "credit": line.credit} for line in self.lines],
            "prev_hash": self.prev_hash,
            "transaction_hash": self.transaction_hash,
        }

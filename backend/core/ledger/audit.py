"""
Cryptographic Ledger Audit Verifier.
Validates sequential transaction hash linking and detects ledger corruption or backdated entries.
"""
from __future__ import annotations

from typing import Dict, Any
from .journal import LedgerJournal
from ..evidence.exceptions import LedgerCorruptionException


class LedgerAuditVerifier:
    """Independent auditor for double-entry journals."""

    @classmethod
    def audit_journal(cls, journal: LedgerJournal) -> Dict[str, Any]:
        """
        Verify every transaction's internal debit=credit balance
        and sequential cryptographic hash link.
        """
        if not journal.transactions:
            return {"valid": True, "transaction_count": 0}

        expected_prev = "GENESIS_TX"
        for idx, tx in enumerate(journal.transactions):
            # 1. Zero-sum verification
            tx.verify_balance()

            # 2. Hash link verification
            if tx.prev_hash != expected_prev:
                raise LedgerCorruptionException(
                    f"LEDGER_CORRUPTION: Broken transaction link at #{idx} ({tx.transaction_id}): "
                    f"prev_hash {tx.prev_hash} != expected {expected_prev}"
                )

            # 3. Hash computation verification
            computed = tx.compute_hash()
            if computed != tx.transaction_hash:
                raise LedgerCorruptionException(
                    f"LEDGER_CORRUPTION: Transaction #{idx} ({tx.transaction_id}) tampered: "
                    f"hash {tx.transaction_hash} != computed {computed}"
                )

            expected_prev = tx.transaction_hash

        return {
            "valid": True,
            "transaction_count": len(journal.transactions),
            "tip_hash": expected_prev,
        }

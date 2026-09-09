"""
Trade P&L and Portfolio Delta NAV Reconciliation Engine.
Guarantees: Total Trade Realized + Unrealized P&L == Portfolio Delta NAV.
"""
from __future__ import annotations

from .journal import LedgerJournal
from ..evidence.exceptions import LedgerCorruptionException


class LedgerReconciliationEngine:
    """
    Reconciliation engine verifying that trade accounting matches balance sheet NAV delta.
    """

    @classmethod
    def reconcile_nav_delta(
        cls,
        journal: LedgerJournal,
        start_nav: float,
        end_nav: float,
        capital_flows: float = 0.0,
        tol: float = 1e-4,
    ) -> bool:
        """
        Reconcile NAV change:
        end_nav - start_nav - capital_flows == PnL.
        """
        delta_nav = end_nav - start_nav - capital_flows
        realized_pnl = journal.balances.get("REALIZED_PNL", 0.0)
        unrealized_pnl = journal.balances.get("UNREALIZED_PNL", 0.0)
        commissions = journal.balances.get("COMMISSION", 0.0)
        borrow_fees = journal.balances.get("BORROW", 0.0)

        # Net PnL = Realized + Unrealized - Expenses
        accounted_pnl = realized_pnl + unrealized_pnl - commissions - borrow_fees

        if abs(delta_nav - accounted_pnl) > tol and start_nav > 0:
            raise LedgerCorruptionException(
                f"LEDGER_CORRUPTION: Reconciliation discrepancy: "
                f"Delta NAV={delta_nav:.4f}, Accounted PnL={accounted_pnl:.4f}"
            )
        return True

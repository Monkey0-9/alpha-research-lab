"""
Double-Entry Ledger Journal.
Authoritative accounting book maintaining account balances and cryptographic audit chains.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
from .accounts import StandardAccount, AccountType, ACCOUNT_TYPES
from .entries import JournalLine, JournalTransaction
from ..evidence.exceptions import LedgerCorruptionException

logger = logging.getLogger(__name__)


class LedgerJournal:
    """
    Authoritative double-entry general ledger.
    Every financial event records balancing debits and credits.
    """

    def __init__(self, initial_cash: float = 1_000_000.0, timestamp: str = "1970-01-01T00:00:00Z"):
        self.transactions: List[JournalTransaction] = []
        self.balances: Dict[str, float] = {acc.value: 0.0 for acc in StandardAccount}
        self.positions: Dict[str, float] = {}  # security_id -> shares
        self.avg_cost: Dict[str, float] = {}   # security_id -> avg cost basis

        # Initial capital contribution
        if initial_cash > 0:
            tx = JournalTransaction(
                transaction_id="TX-INIT-000",
                timestamp=timestamp,
                description="Initial Investor Capital",
                lines=[
                    JournalLine(account=StandardAccount.CASH.value, debit=initial_cash, credit=0.0),
                    JournalLine(account=StandardAccount.REALIZED_PNL.value, debit=0.0, credit=initial_cash),
                ],
                prev_hash="GENESIS_TX",
            )
            self._apply_transaction(tx)

    def _apply_transaction(self, tx: JournalTransaction) -> None:
        tx.verify_balance()
        if self.transactions:
            if tx.prev_hash != self.transactions[-1].transaction_hash:
                raise LedgerCorruptionException(
                    f"LEDGER_CORRUPTION: Transaction {tx.transaction_id} prev_hash mismatch: "
                    f"expected {self.transactions[-1].transaction_hash}, got {tx.prev_hash}"
                )

        for line in tx.lines:
            # Asset & Expense increase with debit (+), decrease with credit (-)
            # Liability & Equity increase with credit (+), decrease with debit (-)
            acc_enum = StandardAccount(line.account) if line.account in StandardAccount._value2member_map_ else None
            acc_type = ACCOUNT_TYPES.get(acc_enum, AccountType.ASSET) if acc_enum else AccountType.ASSET

            if acc_type in (AccountType.ASSET, AccountType.EXPENSE):
                self.balances[line.account] += (line.debit - line.credit)
            else:
                self.balances[line.account] += (line.credit - line.debit)

        self.transactions.append(tx)

    def record_trade(
        self,
        transaction_id: str,
        security_id: str,
        quantity: float,
        price: float,
        fees: float,
        timestamp: str,
    ) -> JournalTransaction:
        """Record buy or sell trade fill."""
        prev = self.transactions[-1].transaction_hash if self.transactions else "GENESIS_TX"
        gross_value = abs(quantity) * price

        lines: List[JournalLine] = []

        if quantity > 0:  # BUY
            lines.append(JournalLine(account=StandardAccount.LONG_ASSETS.value, debit=gross_value, credit=0.0))
            if fees > 0:
                lines.append(JournalLine(account=StandardAccount.COMMISSION.value, debit=fees, credit=0.0))
            lines.append(JournalLine(account=StandardAccount.CASH.value, debit=0.0, credit=gross_value + fees))

            # Update position tracking
            cur_qty = self.positions.get(security_id, 0.0)
            cur_basis = self.avg_cost.get(security_id, 0.0)
            new_qty = cur_qty + quantity
            self.avg_cost[security_id] = (cur_qty * cur_basis + gross_value) / new_qty if new_qty > 0 else 0.0
            self.positions[security_id] = new_qty

        else:  # SELL
            sell_qty = abs(quantity)
            cur_qty = self.positions.get(security_id, 0.0)
            cost_basis = self.avg_cost.get(security_id, price)
            cost_total = sell_qty * cost_basis
            realized_pnl = (price - cost_basis) * sell_qty

            lines.append(JournalLine(account=StandardAccount.CASH.value, debit=gross_value - fees, credit=0.0))
            if fees > 0:
                lines.append(JournalLine(account=StandardAccount.COMMISSION.value, debit=fees, credit=0.0))

            lines.append(JournalLine(account=StandardAccount.LONG_ASSETS.value, debit=0.0, credit=cost_total))
            if realized_pnl >= 0:
                lines.append(JournalLine(account=StandardAccount.REALIZED_PNL.value, debit=0.0, credit=realized_pnl))
            else:
                loss_val = abs(realized_pnl)
                lines.append(JournalLine(account=StandardAccount.REALIZED_PNL.value, debit=loss_val, credit=0.0))

            new_qty = cur_qty - sell_qty
            self.positions[security_id] = new_qty
            if new_qty <= 0:
                self.avg_cost[security_id] = 0.0

        tx = JournalTransaction(
            transaction_id=transaction_id,
            timestamp=timestamp,
            description=f"Trade {quantity:+.0f} {security_id} @ {price:.2f}",
            lines=lines,
            prev_hash=prev,
        )
        self._apply_transaction(tx)
        return tx

    def get_nav(self, current_prices: Optional[Dict[str, float]] = None) -> float:
        """Calculate net asset value (Assets - Liabilities)."""
        cash = self.balances.get(StandardAccount.CASH.value, 0.0)
        long_val = 0.0
        if current_prices:
            for sid, qty in self.positions.items():
                if qty > 0:
                    px = current_prices.get(sid, self.avg_cost.get(sid, 0.0))
                    long_val += qty * px
        else:
            long_val = self.balances.get(StandardAccount.LONG_ASSETS.value, 0.0)

        short_liab = self.balances.get(StandardAccount.SHORT_LIABILITIES.value, 0.0)
        return cash + long_val - short_liab

    def verify_invariants(self) -> bool:
        """Verify that sum(Debits) == sum(Credits) holds across all historical transactions."""
        for tx in self.transactions:
            tx.verify_balance()
        return True

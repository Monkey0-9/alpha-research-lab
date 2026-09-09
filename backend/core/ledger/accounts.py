"""
Double-Entry Ledger Account Classification.
Level-5 institutional accounting structure enforcing Assets = Liabilities + Equity.
"""
from __future__ import annotations

import enum


class AccountType(str, enum.Enum):
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"


class StandardAccount(str, enum.Enum):
    CASH = "CASH"
    LONG_ASSETS = "LONG_ASSETS"
    SHORT_LIABILITIES = "SHORT_LIABILITIES"
    COMMISSION = "COMMISSION"
    BORROW = "BORROW"
    FINANCING = "FINANCING"
    REALIZED_PNL = "REALIZED_PNL"
    UNREALIZED_PNL = "UNREALIZED_PNL"
    FX = "FX"


ACCOUNT_TYPES = {
    StandardAccount.CASH: AccountType.ASSET,
    StandardAccount.LONG_ASSETS: AccountType.ASSET,
    StandardAccount.SHORT_LIABILITIES: AccountType.LIABILITY,
    StandardAccount.COMMISSION: AccountType.EXPENSE,
    StandardAccount.BORROW: AccountType.EXPENSE,
    StandardAccount.FINANCING: AccountType.EXPENSE,
    StandardAccount.REALIZED_PNL: AccountType.EQUITY,
    StandardAccount.UNREALIZED_PNL: AccountType.EQUITY,
    StandardAccount.FX: AccountType.EQUITY,
}

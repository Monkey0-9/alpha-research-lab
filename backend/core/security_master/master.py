"""
Security Master Service & Price Adjustment Engine.
Maintains identity resolution across historical ticker changes, delistings, and corporate actions.
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
import pandas as pd
from core.security_master.models import Security, CorporateAction, ActionType, AssetClass
from core.data_contract import PriceType

logger = logging.getLogger(__name__)


class SecurityMaster:
    """Authoritative registry for security metadata, identifiers, and price adjustments."""

    def __init__(self):
        self._securities: Dict[str, Security] = {} # keyed by permanent security_id
        self._ticker_lookup: Dict[str, List[str]] = {} # ticker -> list of security_ids
        self._bootstrap_sp500_master()

    def _bootstrap_sp500_master(self) -> None:
        """Seed security master with baseline constituents and historical changes."""
        seeds = [
            ("SEC-US-AAPL-001", "AAPL", "Apple Inc.", "NASDAQ", [("AAPL", "1980-12-12", None)]),
            ("SEC-US-MSFT-001", "MSFT", "Microsoft Corporation", "NASDAQ", [("MSFT", "1986-03-13", None)]),
            ("SEC-US-GOOGL-001", "GOOGL", "Alphabet Inc. Class A", "NASDAQ", [("GOOG", "2004-08-19", "2014-04-01"), ("GOOGL", "2014-04-02", None)]),
            ("SEC-US-AMZN-001", "AMZN", "Amazon.com Inc.", "NASDAQ", [("AMZN", "1997-05-15", None)]),
            ("SEC-US-NVDA-001", "NVDA", "NVIDIA Corporation", "NASDAQ", [("NVDA", "1999-01-22", None)]),
            ("SEC-US-META-001", "META", "Meta Platforms Inc.", "NASDAQ", [("FB", "2012-05-18", "2022-06-08"), ("META", "2022-06-09", None)]),
            ("SEC-US-BRKB-001", "BRK-B", "Berkshire Hathaway Inc. Class B", "NYSE", [("BRK.B", "1996-05-09", "2010-01-01"), ("BRK-B", "2010-01-02", None)]),
            ("SEC-US-TSLA-001", "TSLA", "Tesla Inc.", "NASDAQ", [("TSLA", "2010-06-29", None)]),
            ("SEC-US-JPM-001", "JPM", "JPMorgan Chase & Co.", "NYSE", [("JPM", "1969-03-05", None)]),
            ("SEC-US-V-001", "V", "Visa Inc.", "NYSE", [("V", "2008-03-19", None)]),
            ("SEC-US-UNH-001", "UNH", "UnitedHealth Group Inc.", "NYSE", [("UNH", "1984-10-18", None)]),
            ("SEC-US-XOM-001", "XOM", "Exxon Mobil Corporation", "NYSE", [("XOM", "1999-11-30", None)]),
            ("SEC-US-XRX-001", "XRX", "Xerox Holdings Corp (Delisted from S&P)", "NASDAQ", [("XRX", "1960-01-01", None)], False, "2021-03-22"),
        ]

        for item in seeds:
            sec_id, sym, name, exch, hist = item[0], item[1], item[2], item[3], item[4]
            is_act = item[5] if len(item) > 5 else True
            delist = item[6] if len(item) > 6 else None
            sec = Security(
                security_id=sec_id,
                ticker=sym,
                name=name,
                exchange=exch,
                ticker_history=hist,
                is_active=is_act,
                delisting_date=delist
            )
            self.register_security(sec)

        # Register sample corporate action (e.g. Apple 4-for-1 split on 2020-08-31)
        self.add_corporate_action(CorporateAction(
            action_id="CA-AAPL-SPLIT-2020",
            security_id="SEC-US-AAPL-001",
            action_type=ActionType.SPLIT,
            effective_date="2020-08-31",
            ratio=4.0
        ))

    def register_security(self, security: Security) -> None:
        self._securities[security.security_id] = security
        for sym, _, _ in security.ticker_history:
            self._ticker_lookup.setdefault(sym, []).append(security.security_id)
        self._ticker_lookup.setdefault(security.ticker, []).append(security.security_id)

    def add_corporate_action(self, action: CorporateAction) -> None:
        if action.security_id in self._securities:
            self._securities[action.security_id].corporate_actions.append(action)

    def resolve_ticker(self, ticker: str, as_of_date: str) -> Optional[Security]:
        """Resolve ticker to permanent Security based on historical effective dates."""
        sec_ids = self._ticker_lookup.get(ticker, [])
        target_dt = pd.Timestamp(as_of_date)
        for sid in sec_ids:
            sec = self._securities[sid]
            for sym, s_str, e_str in sec.ticker_history:
                if sym == ticker:
                    s_dt = pd.Timestamp(s_str) if s_str else pd.Timestamp.min
                    e_dt = pd.Timestamp(e_str) if e_str else pd.Timestamp.max
                    if s_dt <= target_dt <= e_dt:
                        return sec
        # Fallback to current primary ticker
        for sid, sec in self._securities.items():
            if sec.ticker == ticker:
                return sec
        return None

    def get_security(self, security_id: str) -> Optional[Security]:
        return self._securities.get(security_id)

    def adjust_prices(
        self,
        df: pd.DataFrame,
        security_id: str,
        price_type: PriceType = PriceType.TOTAL_RETURN
    ) -> pd.DataFrame:
        """
        Adjust raw price series for splits and dividends backward in time.
        Distinguishes RAW vs SPLIT_ADJUSTED vs TOTAL_RETURN.
        """
        if price_type == PriceType.RAW or df.empty:
            return df.copy()

        sec = self.get_security(security_id)
        if not sec or not sec.corporate_actions:
            return df.copy()

        adj_df = df.copy()
        if "close" not in adj_df.columns:
            return adj_df

        # Sort actions chronologically
        actions = sorted(sec.corporate_actions, key=lambda a: a.effective_date)

        for act in actions:
            act_date = pd.Timestamp(act.effective_date)
            if act.action_type == ActionType.SPLIT and act.ratio > 0:
                # Prior to split date, historical prices are divided by split ratio
                mask = adj_df.index < act_date if not isinstance(adj_df.index, pd.MultiIndex) else adj_df.index.get_level_values("date") < act_date
                for col in ["open", "high", "low", "close"]:
                    if col in adj_df.columns:
                        adj_df.loc[mask, col] = adj_df.loc[mask, col] / act.ratio
                if "volume" in adj_df.columns:
                    adj_df.loc[mask, "volume"] = adj_df.loc[mask, "volume"] * act.ratio

            elif act.action_type == ActionType.DIVIDEND and price_type == PriceType.TOTAL_RETURN and act.cash_amount > 0:
                # Total return adjustment: price factor = (P_ex - Div) / P_ex
                mask = adj_df.index < act_date if not isinstance(adj_df.index, pd.MultiIndex) else adj_df.index.get_level_values("date") < act_date
                ex_bar = adj_df.loc[adj_df.index >= act_date] if not isinstance(adj_df.index, pd.MultiIndex) else adj_df.loc[adj_df.index.get_level_values("date") >= act_date]
                if not ex_bar.empty and "close" in ex_bar.columns:
                    p_ex = float(ex_bar["close"].iloc[0])
                    if p_ex > act.cash_amount:
                        div_factor = (p_ex - act.cash_amount) / p_ex
                        for col in ["open", "high", "low", "close"]:
                            if col in adj_df.columns:
                                adj_df.loc[mask, col] = adj_df.loc[mask, col] * div_factor

        return adj_df


security_master = SecurityMaster()

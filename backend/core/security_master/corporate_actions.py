"""
Institutional Corporate Action & Price Adjustment Engine.
Maintains immutable raw price stores and computes 4 distinct price series:
- RAW_PRICE (unadjusted exchange trade prices)
- SPLIT_ADJUSTED (split-only adjusted prices & volume)
- TOTAL_RETURN (splits + dividend reinvestment adjusted)
- TRADEABLE_PRICE (point-in-time executable price on exchange)
"""
from __future__ import annotations

import logging
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from core.security_master.models import (
    CorporateAction,
    ActionType,
    PriceSeriesType,
)

logger = logging.getLogger(__name__)


class CorporateActionEngine:
    """
    Computes rigorous corporate action adjustment series backwards in time.
    Guarantees that raw bars are NEVER mutated.
    """

    def __init__(self):
        self._actions: Dict[str, List[CorporateAction]] = {}

    def register_action(self, action: CorporateAction) -> None:
        self._actions.setdefault(action.security_id, []).append(action)

    def get_actions(self, security_id: str) -> List[CorporateAction]:
        return sorted(self._actions.get(security_id, []), key=lambda a: a.effective_date)

    def compute_adjustment_factors(
        self,
        raw_df: pd.DataFrame,
        security_id: str,
    ) -> pd.DataFrame:
        """
        Compute backwards adjustment factors for splits and cash dividends without mutating raw prices.
        Returns a DataFrame indexed by date with columns:
        - split_factor (for price adjustment)
        - volume_split_factor (for volume adjustment)
        - dividend_factor (for total return calculation)
        - total_return_factor (split_factor * dividend_factor)
        """
        if raw_df.empty:
            return pd.DataFrame(columns=["split_factor", "volume_split_factor", "dividend_factor", "total_return_factor"])

        dates = raw_df.index if not isinstance(raw_df.index, pd.MultiIndex) else raw_df.index.get_level_values("date")
        dates = pd.to_datetime(dates).sort_values().unique()

        factors_df = pd.DataFrame(
            index=dates,
            data={
                "split_factor": 1.0,
                "volume_split_factor": 1.0,
                "dividend_factor": 1.0,
                "total_return_factor": 1.0,
            }
        )

        actions = self.get_actions(security_id)
        if not actions:
            return factors_df

        # Compute factors backward chronologically
        cum_split = 1.0
        cum_div = 1.0

        for act in sorted(actions, key=lambda x: pd.Timestamp(x.effective_date), reverse=True):
            act_date = pd.Timestamp(act.effective_date)
            mask_before = factors_df.index < act_date

            if act.action_type == ActionType.SPLIT and act.ratio > 0:
                cum_split *= act.ratio
                factors_df.loc[mask_before, "split_factor"] = cum_split
                factors_df.loc[mask_before, "volume_split_factor"] = cum_split

            elif act.action_type == ActionType.DIVIDEND and act.cash_amount > 0:
                # Find ex-dividend price
                post_bars = raw_df.loc[raw_df.index >= act_date] if not isinstance(raw_df.index, pd.MultiIndex) else raw_df.loc[raw_df.index.get_level_values("date") >= act_date]
                if not post_bars.empty and "close" in post_bars.columns:
                    p_ex = float(post_bars["close"].iloc[0])
                    if p_ex > act.cash_amount:
                        div_factor = (p_ex - act.cash_amount) / p_ex
                        cum_div *= div_factor
                        factors_df.loc[mask_before, "dividend_factor"] = cum_div

        factors_df["total_return_factor"] = factors_df["split_factor"] * factors_df["dividend_factor"]
        return factors_df

    def generate_price_series(
        self,
        raw_df: pd.DataFrame,
        security_id: str,
        series_type: PriceSeriesType = PriceSeriesType.TOTAL_RETURN,
    ) -> pd.DataFrame:
        """
        Generate one of the 4 institutional price series from unmutated raw bars.
        """
        if raw_df.empty:
            return raw_df.copy()

        # Immutable copy
        out_df = raw_df.copy()

        if series_type in (PriceSeriesType.RAW_PRICE, PriceSeriesType.TRADEABLE_PRICE):
            return out_df

        factors = self.compute_adjustment_factors(raw_df, security_id)

        # Apply split adjustments
        if series_type in (PriceSeriesType.SPLIT_ADJUSTED, PriceSeriesType.TOTAL_RETURN):
            split_factors = factors["split_factor"].reindex(out_df.index, method="ffill").fillna(1.0)
            vol_factors = factors["volume_split_factor"].reindex(out_df.index, method="ffill").fillna(1.0)

            for col in ["open", "high", "low", "close"]:
                if col in out_df.columns:
                    out_df[col] = out_df[col] / split_factors

            if "volume" in out_df.columns:
                out_df["volume"] = out_df["volume"] * vol_factors

        # Apply dividend adjustments for Total Return series
        if series_type == PriceSeriesType.TOTAL_RETURN:
            div_factors = factors["dividend_factor"].reindex(out_df.index, method="ffill").fillna(1.0)
            for col in ["open", "high", "low", "close"]:
                if col in out_df.columns:
                    out_df[col] = out_df[col] * div_factors

        return out_df


corporate_action_engine = CorporateActionEngine()

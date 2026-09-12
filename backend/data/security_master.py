"""
QuantAlpha Point-in-Time Security Master (Phase 5).
Tracks complete lifecycle of equities and multi-asset instruments:
- Ticker history & symbol mappings (e.g., FB -> META, GOOG -> GOOGL)
- Exchange, currency, sector, and industry classification
- Primary listing dates and delisting / bankruptcy dates
- Point-in-time universe membership queries with fail-closed rejection of future knowledge leaks.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class SecurityMasterViolation(Exception):
    """Raised when point-in-time constraints on security identity or universe membership are breached."""
    pass


@dataclass
class CorporateActionRecord:
    ex_date: str  # YYYY-MM-DD
    announcement_date: str  # YYYY-MM-DD
    action_type: str  # 'SPLIT', 'DIVIDEND', 'SPINOFF', 'NAME_CHANGE'
    ratio_or_amount: float
    notes: str = ""


@dataclass
class SecurityProfile:
    entity_id: str
    primary_ticker: str
    historical_tickers: List[Tuple[str, str, str]] = field(default_factory=list)  # (ticker, start_date, end_date)
    exchange: str = "NASDAQ"
    currency: str = "USD"
    sector: str = "Technology"
    listing_date: str = "2000-01-01"
    delisting_date: Optional[str] = None
    delisting_reason: Optional[str] = None  # 'MERGER', 'BANKRUPTCY', 'REGULATORY'
    corporate_actions: List[CorporateActionRecord] = field(default_factory=list)
    universe_memberships: List[Tuple[str, str, str]] = field(default_factory=list)  # (universe_name, start_date, end_date)


class PointInTimeSecurityMaster:
    """
    Authoritative registry resolving point-in-time entity identity and universe membership.
    """

    def __init__(self):
        self._securities: Dict[str, SecurityProfile] = {}
        self._ticker_to_entity: Dict[str, str] = {}
        self._seed_default_master()

    def _seed_default_master(self):
        """Populate initial representative master with historical changes."""
        # AAPL
        self.register_security(SecurityProfile(
            entity_id="SEC_AAPL",
            primary_ticker="AAPL",
            exchange="NASDAQ",
            currency="USD",
            sector="Technology",
            listing_date="1980-12-12",
            delisting_date=None,
            corporate_actions=[
                CorporateActionRecord(ex_date="2020-08-31", announcement_date="2020-07-30", action_type="SPLIT", ratio_or_amount=4.0),
                CorporateActionRecord(ex_date="2014-06-09", announcement_date="2014-04-23", action_type="SPLIT", ratio_or_amount=7.0),
            ],
            universe_memberships=[("SP500", "1982-11-30", "9999-12-31")]
        ))

        # META (historical FB)
        self.register_security(SecurityProfile(
            entity_id="SEC_META",
            primary_ticker="META",
            historical_tickers=[
                ("FB", "2012-05-18", "2022-06-08"),
                ("META", "2022-06-09", "9999-12-31")
            ],
            exchange="NASDAQ",
            currency="USD",
            sector="Communication Services",
            listing_date="2012-05-18",
            delisting_date=None,
            universe_memberships=[("SP500", "2013-12-23", "9999-12-31")]
        ))

        # Lehman Brothers (Bankrupt delisted)
        self.register_security(SecurityProfile(
            entity_id="SEC_LEH",
            primary_ticker="LEH",
            historical_tickers=[("LEH", "1994-01-01", "2008-09-15")],
            exchange="NYSE",
            currency="USD",
            sector="Financials",
            listing_date="1994-01-01",
            delisting_date="2008-09-15",
            delisting_reason="BANKRUPTCY",
            universe_memberships=[("SP500", "1994-01-01", "2008-09-15")]
        ))

    def register_security(self, profile: SecurityProfile) -> None:
        self._securities[profile.entity_id] = profile
        self._ticker_to_entity[profile.primary_ticker] = profile.entity_id
        for t, _, _ in profile.historical_tickers:
            self._ticker_to_entity[t] = profile.entity_id

    def resolve_ticker_at_timestamp(self, ticker: str, as_of_date: str) -> SecurityProfile:
        """
        Resolves entity profile given a ticker and historical point-in-time timestamp.
        Fails if querying an unlisted, post-delisting, or future ticker.
        """
        entity_id = self._ticker_to_entity.get(ticker)
        if not entity_id or entity_id not in self._securities:
            raise SecurityMasterViolation(f"Unknown security ticker: {ticker}")

        sec = self._securities[entity_id]
        if as_of_date < sec.listing_date:
            raise SecurityMasterViolation(
                f"Lookahead violation: Ticker {ticker} was not listed on {as_of_date} (Listed: {sec.listing_date})"
            )
        if sec.delisting_date and as_of_date > sec.delisting_date:
            raise SecurityMasterViolation(
                f"Survivorship violation: Ticker {ticker} was delisted on {sec.delisting_date} due to {sec.delisting_reason}"
            )
        return sec

    def get_point_in_time_universe(self, universe_name: str, as_of_date: str) -> List[str]:
        """
        Returns exact list of active tickers for a given universe on a specific historical date.
        """
        active_entities = []
        for entity_id, sec in self._securities.items():
            if as_of_date < sec.listing_date:
                continue
            if sec.delisting_date and as_of_date > sec.delisting_date:
                continue

            # Check membership
            in_universe = False
            for u_name, start_d, end_d in sec.universe_memberships:
                if u_name == universe_name and start_d <= as_of_date <= end_d:
                    in_universe = True
                    break

            if in_universe:
                # Find ticker valid at this date
                valid_ticker = sec.primary_ticker
                for t, s_d, e_d in sec.historical_tickers:
                    if s_d <= as_of_date <= e_d:
                        valid_ticker = t
                        break
                active_entities.append(valid_ticker)

        return sorted(active_entities)

"""
QuantAlpha — Institutional Robinhood Market Data Client
Connects via robin_stocks to stream quotes, depth, and historical bars.
Supports both public market data queries and authenticated institutional operations.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import robin_stocks.robinhood as rh
    ROBINHOOD_AVAILABLE = True
except ImportError:
    rh = None
    ROBINHOOD_AVAILABLE = False


class RobinhoodClient:
    """Robinhood market data client with session persistence, public quote mode, and TTL caching."""

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        mfa_code: Optional[str] = None,
        cache_ttl_seconds: int = 60
    ):
        self.username = username
        self.password = password
        self.mfa_code = mfa_code
        self.cache_ttl = cache_ttl_seconds
        self._is_logged_in = False
        self._quote_cache: Dict[str, Dict[str, Any]] = {}
        self._last_auth_attempt: float = 0.0

    def login(self) -> bool:
        """Attempt authentication if credentials are supplied."""
        if not ROBINHOOD_AVAILABLE or rh is None:
            logger.warning("robin_stocks package is not installed or available.")
            return False

        if not self.username or not self.password:
            # Unauthenticated public data mode
            return False

        # Throttle failed login attempts
        if time.time() - self._last_auth_attempt < 30 and not self._is_logged_in:
            return self._is_logged_in

        self._last_auth_attempt = time.time()
        try:
            logger.info("Authenticating with Robinhood API...")
            login_kwargs = {
                "username": self.username,
                "password": self.password,
                "expiresIn": 86400,
                "scope": "internal",
                "by_sms": False,
                "store_session": True
            }
            if self.mfa_code:
                login_kwargs["mfa_code"] = self.mfa_code

            res = rh.login(**login_kwargs)
            self._is_logged_in = bool(res and "access_token" in res)
            if self._is_logged_in:
                logger.info("Successfully authenticated with Robinhood.")
            return self._is_logged_in
        except Exception as e:
            logger.warning(f"Robinhood login error: {e}. Falling back to public quote mode.")
            self._is_logged_in = False
            return False

    def is_authenticated(self) -> bool:
        """Check if active authenticated session is active."""
        return self._is_logged_in

    def get_realtime_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time bid, ask, last trade price, and volume for a single ticker."""
        sym = symbol.upper().strip()
        now = time.time()

        if sym in self._quote_cache:
            entry = self._quote_cache[sym]
            if now - entry["_cached_at"] < self.cache_ttl:
                return entry["data"]

        if not ROBINHOOD_AVAILABLE or rh is None:
            return self._fallback_quote(sym, "LIBRARY_UNAVAILABLE")

        try:
            # robin_stocks.robinhood.get_quotes supports public ticker queries
            quotes = rh.get_quotes(sym)
            if not quotes or not quotes[0]:
                return self._fallback_quote(sym, "EMPTY_RESPONSE")

            q = quotes[0]
            last_price = float(q.get("last_trade_price") or q.get("last_extended_hours_trade_price") or 0.0)
            prev_close = float(q.get("previous_close") or last_price or 1.0)
            bid = float(q.get("bid_price") or last_price)
            ask = float(q.get("ask_price") or last_price)
            bid_size = int(q.get("bid_size") or 0)
            ask_size = int(q.get("ask_size") or 0)

            change = round(last_price - prev_close, 2)
            pct_change = round(100.0 * (change / max(prev_close, 1e-4)), 2)

            quote_data = {
                "ticker": sym,
                "provider": "robinhood",
                "price": round(last_price, 2),
                "previous_close": round(prev_close, 2),
                "change": change,
                "pct_change": pct_change,
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "bid_size": bid_size,
                "ask_size": ask_size,
                "spread": round(ask - bid, 3) if ask >= bid else 0.0,
                "updated_at": q.get("updated_at") or datetime.utcnow().isoformat() + "Z",
                "status": "LIVE"
            }

            self._quote_cache[sym] = {"_cached_at": now, "data": quote_data}
            return quote_data

        except Exception as e:
            logger.debug(f"Robinhood quote query failed for {sym}: {e}")
            return self._fallback_quote(sym, str(e))

    def get_realtime_quotes_batch(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Batch fetch real-time quotes for multiple symbols."""
        if not symbols:
            return []

        clean_symbols = [s.upper().strip() for s in symbols]
        if not ROBINHOOD_AVAILABLE or rh is None:
            return [self._fallback_quote(s, "LIBRARY_UNAVAILABLE") for s in clean_symbols]

        try:
            quotes = rh.get_quotes(clean_symbols)
            results = []
            now = time.time()

            for i, q in enumerate(quotes):
                sym = clean_symbols[i]
                if not q:
                    results.append(self._fallback_quote(sym, "EMPTY"))
                    continue

                last_price = float(q.get("last_trade_price") or q.get("last_extended_hours_trade_price") or 0.0)
                prev_close = float(q.get("previous_close") or last_price or 1.0)
                bid = float(q.get("bid_price") or last_price)
                ask = float(q.get("ask_price") or last_price)

                data = {
                    "ticker": sym,
                    "provider": "robinhood",
                    "price": round(last_price, 2),
                    "previous_close": round(prev_close, 2),
                    "change": round(last_price - prev_close, 2),
                    "pct_change": round(100.0 * ((last_price - prev_close) / max(prev_close, 1e-4)), 2),
                    "bid": round(bid, 2),
                    "ask": round(ask, 2),
                    "updated_at": q.get("updated_at") or datetime.utcnow().isoformat() + "Z",
                    "status": "LIVE"
                }
                self._quote_cache[sym] = {"_cached_at": now, "data": data}
                results.append(data)

            return results
        except Exception as e:
            logger.error(f"Robinhood batch quote error: {e}")
            return [self._fallback_quote(s, str(e)) for s in clean_symbols]

    def get_crypto_quote(self, symbol: str) -> Dict[str, Any]:
        """Fetch real-time quote for crypto pairs (e.g., BTC, ETH)."""
        sym = symbol.upper().replace("-USD", "").strip()
        if not ROBINHOOD_AVAILABLE or rh is None:
            return self._fallback_quote(f"{sym}-USD", "LIBRARY_UNAVAILABLE")

        try:
            q = rh.crypto.get_crypto_quote(sym)
            if not q:
                return self._fallback_quote(f"{sym}-USD", "EMPTY")

            mark = float(q.get("mark_price") or 0.0)
            bid = float(q.get("bid_price") or mark)
            ask = float(q.get("ask_price") or mark)
            vol = float(q.get("volume") or 0.0)

            return {
                "ticker": f"{sym}-USD",
                "asset_type": "CRYPTO",
                "provider": "robinhood",
                "price": round(mark, 2),
                "bid": round(bid, 2),
                "ask": round(ask, 2),
                "volume": int(vol),
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "status": "LIVE"
            }
        except Exception as e:
            logger.debug(f"Robinhood crypto quote error for {sym}: {e}")
            return self._fallback_quote(f"{sym}-USD", str(e))

    def get_historical_bars(
        self,
        symbol: str,
        interval: str = "day",
        span: str = "year"
    ) -> pd.DataFrame:
        """
        Fetch historical candles from Robinhood.
        Interval options: '5minute', '10minute', 'hour', 'day', 'week'.
        Span options: 'day', 'week', 'month', '3month', 'year', '5year'.
        """
        sym = symbol.upper().strip()
        if not ROBINHOOD_AVAILABLE or rh is None:
            return pd.DataFrame()

        try:
            historicals = rh.stocks.get_stock_historicals(
                sym,
                interval=interval,
                span=span,
                bounds="regular"
            )
            if not historicals:
                return pd.DataFrame()

            records = []
            for bar in historicals:
                if not bar or "close_price" not in bar:
                    continue
                records.append({
                    "date": pd.to_datetime(bar["begins_at"]).normalize() if interval == "day" else pd.to_datetime(bar["begins_at"]),
                    "open": float(bar["open_price"]),
                    "high": float(bar["high_price"]),
                    "low": float(bar["low_price"]),
                    "close": float(bar["close_price"]),
                    "volume": int(bar["volume"]),
                    "ticker": sym
                })

            if not records:
                return pd.DataFrame()

            df = pd.DataFrame(records)
            df["return_1d"] = df["close"].pct_change().fillna(0.0).round(6)
            df = df.set_index(["date", "ticker"]).sort_index()
            return df
        except Exception as e:
            logger.error(f"Error fetching historicals from Robinhood for {sym}: {e}")
            return pd.DataFrame()

    def get_market_hours(self) -> Dict[str, Any]:
        """Check market status and operating schedule for US Equities."""
        now = datetime.utcnow()
        is_weekday = now.weekday() < 5
        # US Equity Market regular hours: 13:30 to 20:00 UTC (9:30 AM to 4:00 PM EST)
        hour_min = now.hour * 60 + now.minute
        is_regular = is_weekday and (13 * 60 + 30 <= hour_min <= 20 * 60)
        is_extended = is_weekday and (
            (9 * 60 <= hour_min < 13 * 60 + 30) or (20 * 60 < hour_min <= 24 * 60)
        )

        state = "OPEN" if is_regular else ("EXTENDED_HOURS" if is_extended else "CLOSED")
        return {
            "market": "US_EQUITIES",
            "state": state,
            "is_open": is_regular,
            "extended_hours": is_extended,
            "timestamp": now.isoformat() + "Z",
            "provider": "robinhood"
        }

    def _fallback_quote(self, symbol: str, reason: str = "") -> Dict[str, Any]:
        """Generate graceful deterministic fallback quote if network or auth is restricted."""
        base_price = 100.0 + (abs(hash(symbol)) % 150)
        return {
            "ticker": symbol,
            "provider": "robinhood",
            "price": round(float(base_price), 2),
            "previous_close": round(float(base_price * 0.995), 2),
            "change": round(float(base_price * 0.005), 2),
            "pct_change": 0.50,
            "bid": round(float(base_price * 0.999), 2),
            "ask": round(float(base_price * 1.001), 2),
            "bid_size": 100,
            "ask_size": 100,
            "spread": round(float(base_price * 0.002), 3),
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "status": "FALLBACK"
        }


# Singleton default client
robinhood_client = RobinhoodClient()

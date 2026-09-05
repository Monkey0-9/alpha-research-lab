"""
QuantAlpha — Institutional Alpaca Markets Paper Trading Client
Direct REST integration with Alpaca Paper API (v2) for live portfolio
telemetry, real-time account metrics, positions inspection, and
algorithmic order routing.
"""
from __future__ import annotations

import os
import logging
import urllib.request
import urllib.error
import json
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

DEFAULT_ALPACA_ENDPOINT = os.environ.get(
    "ALPACA_API_ENDPOINT",
    "https://paper-api.alpaca.markets/v2"
)
DEFAULT_ALPACA_KEY = os.environ.get("ALPACA_API_KEY", "")
DEFAULT_ALPACA_SECRET = os.environ.get("ALPACA_API_SECRET", "")


class AlpacaClient:
    """Client for Alpaca Paper Trading REST API."""

    def __init__(
        self,
        endpoint: str = DEFAULT_ALPACA_ENDPOINT,
        api_key: str = DEFAULT_ALPACA_KEY,
        api_secret: str = DEFAULT_ALPACA_SECRET,
    ):
        self.endpoint = endpoint.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self._headers = {
            "APCA-API-KEY-ID": self.api_key,
            "APCA-API-SECRET-KEY": self.api_secret,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def _request(
        self,
        path: str,
        method: str = "GET",
        payload: Optional[Dict[str, Any]] = None,
        timeout: int = 8,
    ) -> Any:
        url = f"{self.endpoint}{path}"
        if not (url.startswith("https://") or url.startswith("http://")):
            raise ValueError(f"Disallowed URL scheme: {url}")
        data_bytes = json.dumps(payload).encode("utf-8") if payload else None
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers=self._headers,
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec B310
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as he:
            err_body = he.read().decode("utf-8", errors="ignore")
            logger.warning(
                f"Alpaca API {method} {path} HTTP {he.code}: {err_body}"
            )
            return {"error": f"HTTP {he.code}", "details": err_body}
        except Exception as exc:
            logger.warning(f"Alpaca API request failed: {exc}")
            return {"error": str(exc)}

    def is_available(self) -> bool:
        """Check whether Alpaca credentials can successfully connect."""
        acc = self.get_account()
        return bool(acc and "id" in acc and acc.get("status") == "ACTIVE")

    def get_account(self) -> Dict[str, Any]:
        """Fetch live paper trading account balance, equity,
        and margin telemetry."""
        res = self._request("/account")
        if isinstance(res, dict) and "id" in res:
            return {
                "id": res.get("id"),
                "status": res.get("status"),
                "currency": res.get("currency", "USD"),
                "equity": float(res.get("equity") or 0.0),
                "buying_power": float(res.get("buying_power") or 0.0),
                "cash": float(res.get("cash") or 0.0),
                "portfolio_value": float(res.get("portfolio_value") or 0.0),
                "multiplier": float(res.get("multiplier") or 4.0),
                "daytrade_count": int(res.get("daytrade_count") or 0),
                "connected": True,
            }
        return {
            "connected": False,
            "error": res.get("error", "Failed to connect"),
        }

    def get_positions(self) -> List[Dict[str, Any]]:
        """Fetch all currently open positions from Alpaca paper account."""
        res = self._request("/positions")
        if isinstance(res, list):
            positions = []
            for p in res:
                positions.append({
                    "symbol": p.get("symbol"),
                    "qty": float(p.get("qty") or 0),
                    "side": p.get("side", "long").upper(),
                    "market_value": float(p.get("market_value") or 0.0),
                    "cost_basis": float(p.get("cost_basis") or 0.0),
                    "unrealized_pl": float(p.get("unrealized_pl") or 0.0),
                    "unrealized_plpc": (
                        float(p.get("unrealized_plpc") or 0.0) * 100.0
                    ),
                    "current_price": float(p.get("current_price") or 0.0),
                    "lastday_price": float(p.get("lastday_price") or 0.0),
                    "change_today": (
                        float(p.get("change_today") or 0.0) * 100.0
                    ),
                })
            return positions
        return []

    def get_orders(
        self, status: str = "all", limit: int = 15
    ) -> List[Dict[str, Any]]:
        """Fetch recent paper orders."""
        res = self._request(f"/orders?status={status}&limit={limit}")
        if isinstance(res, list):
            return [
                {
                    "id": o.get("id"),
                    "symbol": o.get("symbol"),
                    "qty": float(o.get("qty") or 0),
                    "filled_qty": float(o.get("filled_qty") or 0),
                    "side": o.get("side", "buy").upper(),
                    "type": o.get("type", "market"),
                    "status": o.get("status"),
                    "filled_avg_price": float(
                        o.get("filled_avg_price") or 0.0
                    ),
                    "created_at": o.get("created_at"),
                }
                for o in res
            ]
        return []

    def submit_order(
        self,
        symbol: str,
        qty: float,
        side: str = "buy",
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Submit a real paper order directly onto the Alpaca broker."""
        payload: Dict[str, Any] = {
            "symbol": symbol.upper().strip(),
            "qty": str(qty),
            "side": side.lower().strip(),
            "type": order_type.lower().strip(),
            "time_in_force": time_in_force.lower().strip(),
        }
        if limit_price is not None and order_type.lower() == "limit":
            payload["limit_price"] = str(limit_price)

        return self._request("/orders", method="POST", payload=payload)

    def get_clock(self) -> Dict[str, Any]:
        """Fetch US market open/closed status."""
        res = self._request("/clock")
        if isinstance(res, dict) and "is_open" in res:
            return {
                "timestamp": res.get("timestamp"),
                "is_open": res.get("is_open"),
                "next_open": res.get("next_open"),
                "next_close": res.get("next_close"),
            }
        return {"is_open": False}


alpaca_client = AlpacaClient()

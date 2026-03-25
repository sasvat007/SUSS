"""
Setu API Client
───────────────
Thin async wrapper around Setu's Account Aggregator / transaction APIs.
Normalizes raw transaction data into a consistent internal format.
"""

import httpx
import logging
from typing import Any
from app.config import settings

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(20.0, connect=10.0)


class SetuClientError(Exception):
    pass


def _get_auth_headers() -> dict:
    return {
        "x-client-id": settings.SETU_CLIENT_ID or "",
        "x-client-secret": settings.SETU_CLIENT_SECRET or "",
        "Content-Type": "application/json",
    }


async def fetch_transactions(account_id: str) -> list[dict]:
    """
    Fetch raw transactions from Setu for a linked account.
    Returns a normalized list of transaction dicts.
    """
    url = f"{settings.SETU_BASE_URL}/data/{account_id}/transactions"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            r = await client.get(url, headers=_get_auth_headers())
            r.raise_for_status()
            raw = r.json()
            return _normalize_transactions(raw.get("payload", {}).get("fetchResponse", []))
        except httpx.HTTPStatusError as exc:
            logger.error("Setu API error %s: %s", exc.response.status_code, exc.response.text)
            raise SetuClientError(f"Setu API error {exc.response.status_code}") from exc
        except Exception as exc:
            logger.error("Setu client error: %s", exc)
            raise SetuClientError("Setu unreachable") from exc


def _normalize_transactions(raw_list: list[Any]) -> list[dict]:
    """Map Setu's payload structure to our internal schema."""
    normalized = []
    for txn in raw_list:
        normalized.append(
            {
                "transaction_id": txn.get("txnId"),
                "amount": float(txn.get("amount", 0)),
                "type": txn.get("type", "DEBIT").upper(),   # CREDIT | DEBIT
                "date": txn.get("valueDate") or txn.get("transactionTimestamp"),
                "narration": txn.get("narration"),
                "balance": float(txn.get("currentBalance", 0)),
                "mode": txn.get("mode"),
                "reference": txn.get("reference"),
            }
        )
    return normalized

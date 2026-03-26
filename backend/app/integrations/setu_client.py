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


async def create_setu_payment_link(
    amount: float, bill_ref: str, customer_name: str
) -> tuple[str, str]:
    """
    Create a Setu V2 payment link.
    Returns (id, url).
    """
    url = f"{settings.SETU_BASE_URL}/v2/payment-links"
    
    # Setu V2 payload structure
    payload = {
        "amount": {
            "value": int(amount * 100), # value in paise
            "currencyCode": "INR"
        },
        "description": f"Payment for bill {bill_ref}",
        "billReferenceNumber": bill_ref,
        "customer": {
            "name": customer_name
        }
    }
    
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            r = await client.post(url, headers=_get_auth_headers(), json=payload)
            r.raise_for_status()
            data = r.json()
            pl = data.get("data", {}).get("paymentLink", {})
            return (
                pl.get("id", ""),
                pl.get("shortUrl") or pl.get("url", "")
            )
        except httpx.HTTPStatusError as exc:
            logger.error("Setu Payment API error %s: %s", exc.response.status_code, exc.response.text)
            raise SetuClientError(f"Setu Payment error {exc.response.status_code}") from exc
        except Exception as exc:
            logger.error("Setu Payment client error: %s", exc)
            raise SetuClientError("Setu Payment unreachable") from exc


async def get_payment_link_status(link_id: str) -> dict:
    """
    Check status of a Setu V2 payment link.
    """
    url = f"{settings.SETU_BASE_URL}/v2/payment-links/{link_id}"
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            r = await client.get(url, headers=_get_auth_headers())
            r.raise_for_status()
            data = r.json()
            return data.get("data", {})
        except Exception as exc:
            logger.error("Setu Status check error: %s", exc)
            raise SetuClientError("Setu Status check failed") from exc


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

"""
ML Backend Client
─────────────────
Sends financial state to the external ML service and returns
priorities, alerts, risk analysis, and health score.

The ML backend is NOT part of this codebase. This client is the
only integration point. All ML logic lives in the ML service.
"""

import httpx
import logging
from typing import Optional

from app.config import settings
from app.schemas.ml import MLPrioritizeRequest, MLPrioritizeResponse

logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0, connect=10.0)


class MLClientError(Exception):
    """Raised when the ML backend returns an error or is unreachable."""


async def call_ml_prioritize(payload: MLPrioritizeRequest) -> MLPrioritizeResponse:
    """
    POST /ml/prioritize on the ML backend.
    Returns a validated MLPrioritizeResponse.
    Raises MLClientError on any failure.
    """
    url = f"{settings.ML_BACKEND_URL}/ml/prioritize"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": settings.ML_BACKEND_API_KEY,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            response = await client.post(
                url,
                content=payload.model_dump_json(),
                headers=headers,
            )
            response.raise_for_status()
            return MLPrioritizeResponse.model_validate(response.json())
        except httpx.TimeoutException as exc:
            logger.error("ML backend timeout: %s", exc)
            raise MLClientError("ML backend request timed out") from exc
        except httpx.HTTPStatusError as exc:
            logger.error("ML backend HTTP %s: %s", exc.response.status_code, exc.response.text)
            raise MLClientError(f"ML backend error {exc.response.status_code}") from exc
        except Exception as exc:
            logger.error("ML backend unexpected error: %s", exc)
            raise MLClientError("ML backend unreachable") from exc


async def call_ml_simulate(scenario: dict) -> dict:
    """
    POST /ml/simulate — proxy scenario data to ML backend.
    Returns raw JSON response dict.
    """
    url = f"{settings.ML_BACKEND_URL}/ml/simulate"
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": settings.ML_BACKEND_API_KEY,
    }

    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            response = await client.post(url, json=scenario, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException as exc:
            raise MLClientError("ML simulation timed out") from exc
        except httpx.HTTPStatusError as exc:
            raise MLClientError(f"ML simulation error {exc.response.status_code}") from exc
        except Exception as exc:
            raise MLClientError("ML backend unreachable") from exc

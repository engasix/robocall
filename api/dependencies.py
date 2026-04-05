"""Shared FastAPI dependencies for the API service."""

import time
from collections import defaultdict
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
import config
import database
from api.services import api_key as api_key_service

# ── In-memory rate limiter ────────────────────────────────────────────────────
# Tracks (key → list of request timestamps) to enforce a sliding window.
_rate_limit_window = 60        # seconds
_rate_limit_max_requests = 60  # requests per window

_request_log: dict[str, list[float]] = defaultdict(list)


def _check_rate_limit(key: str) -> None:
    now = time.monotonic()
    window_start = now - _rate_limit_window
    timestamps = _request_log[key]

    # Drop timestamps outside the current window
    _request_log[key] = [t for t in timestamps if t > window_start]

    if len(_request_log[key]) >= _rate_limit_max_requests:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Max 60 requests per minute.",
        )

    _request_log[key].append(now)


# ── Internal key auth ─────────────────────────────────────────────────────────

def require_internal_key(x_api_key: str = Header(...)) -> None:
    """Validate the X-Api-Key header against INTERNAL_API_KEY from config.

    Used to protect internal endpoints (e.g. /orders/process) that are only
    called by the demo service — not exposed to store owners directly.
    """
    if not config.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server misconfiguration: INTERNAL_API_KEY not set.",
        )
    if x_api_key != config.INTERNAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    _check_rate_limit(x_api_key)


# ── Per-store API key auth ────────────────────────────────────────────────────

def require_store_api_key(
    x_api_key: str = Header(...),
    db: Session = Depends(database.get_db),
) -> database.Store:
    """Validate X-Api-Key against per-store api_key_hash.

    Returns the authenticated Store. Used to protect public /v1/ endpoints.
    """
    hashed = api_key_service._hash(x_api_key)
    store = db.query(database.Store).filter(database.Store.api_key_hash == hashed).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )
    _check_rate_limit(x_api_key)
    return store

"""FastAPI dependencies for auth and shared logic."""

from __future__ import annotations

import os

from fastapi import Header, HTTPException

_API_KEY = os.getenv("API_KEY", "")


def verify_api_key(x_api_key: str = Header(default="")) -> None:
    """Require ``X-API-Key`` header when ``API_KEY`` env var is set.

    When ``API_KEY`` is empty (the default), auth is bypassed so the demo
    works out of the box without any key management.
    """
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

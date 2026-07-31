"""LLM configuration helpers."""

from __future__ import annotations

import os


def is_enabled() -> bool:
    """Return whether the optional LLM integration is enabled."""

    return bool(os.getenv("BOOKERRROR_API_KEY"))

"""LLM configuration helpers for BookError."""

from __future__ import annotations

import os


def is_enabled() -> bool:
    """Return whether the optional LLM explanation feature is enabled."""
    if os.getenv("BOOKERROR_LLM_DISABLED", "").lower() in ("1", "true", "yes"):
        return False
    return bool(
        os.getenv("ANTHROPIC_API_KEY")
        or os.getenv("OPENAI_API_KEY")
        or os.getenv("GEMINI_API_KEY")
        or os.getenv("BOOKERROR_LLM_ENABLED", "").lower() in ("1", "true", "yes")
    )


def get_llm_provider() -> str:
    """Determine the active LLM provider based on set environment variables."""
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    if os.getenv("GEMINI_API_KEY"):
        return "gemini"
    return "mock"

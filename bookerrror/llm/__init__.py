"""Layer 4: Optional LLM explanation layer for BookError."""

from __future__ import annotations

from bookerrror.llm.client import explain
from bookerrror.llm.config import get_llm_provider, is_enabled
from bookerrror.llm.prompt_builder import build_prompt

__all__ = ["build_prompt", "explain", "get_llm_provider", "is_enabled"]

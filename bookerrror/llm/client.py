"""Optional LLM client integration."""

from __future__ import annotations

from bookerrror.llm.config import is_enabled
from bookerrror.llm.prompt_builder import build_prompt


def explain(causal_path) -> str:
    """Return a plain-language explanation for a causal path."""

    if not is_enabled():
        return "LLM explanation is disabled."
    return build_prompt(causal_path)

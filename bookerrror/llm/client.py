"""Optional LLM client integration for BookError."""

from __future__ import annotations

import logging
import os
from typing import TYPE_CHECKING

from bookerrror.llm.config import get_llm_provider, is_enabled
from bookerrror.llm.prompt_builder import build_prompt

if TYPE_CHECKING:
    from bookerrror.models import CausalPath

logger = logging.getLogger("bookerrror.llm")


def explain(causal_path: CausalPath) -> str:
    """Return a 1-2 sentence plain-language explanation for a causal path."""
    if not is_enabled():
        return _fallback_explanation(causal_path)

    prompt = build_prompt(causal_path)
    provider = get_llm_provider()

    try:
        if provider == "anthropic":
            return _call_anthropic(prompt)
        elif provider == "openai":
            return _call_openai(prompt)
        elif provider == "gemini":
            return _call_gemini(prompt)
        else:
            return _call_mock(causal_path)
    except Exception as err:
        logger.warning(f"BookError LLM explanation failed ({err}). Using fallback.")
        return _fallback_explanation(causal_path)


def _call_anthropic(prompt: str) -> str:
    import anthropic  # type: ignore

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text.strip()


def _call_openai(prompt: str) -> str:
    import openai  # type: ignore

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content.strip()


def _call_gemini(prompt: str) -> str:
    import google.generativeai as genai  # type: ignore

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(prompt)
    return response.text.strip()


def _call_mock(causal_path: CausalPath) -> str:
    """Deterministic mock response for demo / test mode when no API keys are set."""
    if not causal_path or not causal_path.hops:
        return "The error occurred because a required variable or key was not present in the current scope."

    root_hop = causal_path.hops[0]
    last_hop = causal_path.hops[-1]
    return (
        f"Cell '{last_hop.cell_id}' failed because variable '{last_hop.variable}' was modified in "
        f"earlier cell '{root_hop.cell_id}' ({root_hop.summary}). Check the sequence of operations on '{last_hop.variable}'."
    )


def _fallback_explanation(causal_path: CausalPath) -> str:
    """Deterministic fallback using deterministic hop summary strings."""
    if not causal_path or not causal_path.hops:
        return "An exception occurred. Inspect the failing line for invalid accesses or missing variables."

    summaries = [f"{h.cell_id}: {h.summary}" for h in causal_path.hops]
    return f"Causal sequence: {' -> '.join(summaries)}."

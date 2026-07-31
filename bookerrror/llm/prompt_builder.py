"""Prompt construction for optional LLM explanations."""

from __future__ import annotations

from textwrap import dedent


def build_prompt(causal_path) -> str:
    """Build a minimal prompt from a causal path."""

    lines = [
        "A notebook raised an error. Explain the causal path in plain English.",
        f"Error: {causal_path.failure.exc_type}: {causal_path.failure.exc_message}",
        f"Failing line: {causal_path.failure.failing_line}",
        "Causal path:",
    ]
    for hop in causal_path.hops:
        lines.append(f"- Cell {hop.cell_id} ({hop.role}): {hop.summary}")
    return dedent("\n".join(lines)).strip()

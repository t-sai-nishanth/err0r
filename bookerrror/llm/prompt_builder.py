"""Prompt construction for optional LLM explanations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookerrror.models import CausalPath


def build_prompt(causal_path: CausalPath) -> str:
    """Build a minimal, token-efficient prompt from a CausalPath object.

    The prompt contains ONLY the causal path hops and failure info (typically 60-150 tokens),
    deliberately excluding full tracebacks and unrelated notebook cells.
    """
    if not causal_path or not causal_path.hops:
        failure_str = (
            f"{causal_path.failure.exc_type}: {causal_path.failure.exc_message}"
            if causal_path and causal_path.failure
            else "Unknown execution error"
        )
        return (
            f"A Jupyter notebook cell failed with error: {failure_str}.\n"
            "Explain in 1-2 plain language sentences what this error typically means."
        )

    failure = causal_path.failure

    lines = [
        "A Jupyter notebook raised an error. Here is the causal chain that led to it, ",
        "already identified by static analysis — do not re-diagnose, just explain it plainly in 2-3 sentences for a student:\n",
    ]

    for idx, hop in enumerate(causal_path.hops, 1):
        snippet_part = f" (`{hop.source_snippet}`)" if hop.source_snippet else ""
        lines.append(f"{idx}. {hop.cell_id} (exec #{hop.exec_id}): {hop.summary}{snippet_part}")

    lines.append(
        f"\nFinal Cell ({failure.cell_id}) crashed calling `{failure.failing_line}` — {failure.exc_type}: {failure.exc_message}"
    )
    lines.append("\nExplain what went wrong and what the student should inspect, in plain language.")

    return "\n".join(lines)

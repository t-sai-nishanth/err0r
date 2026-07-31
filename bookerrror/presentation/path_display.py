"""Causal path display helpers for BookError."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookerrror.models import CausalPath


def render_path(causal_path: CausalPath) -> str:
    """Render a causal path as a clean HTML hop card list."""
    if not causal_path or not causal_path.hops:
        return "<div>No causal path found.</div>"

    parts = ['<div class="bookerror-path-list" style="margin-top: 10px;">']
    for idx, hop in enumerate(causal_path.hops, 1):
        parts.append(
            f'<div class="bookerror-path-item" style="padding: 6px 10px; margin-bottom: 6px; background: #161b22; border-radius: 4px; border: 1px solid #30363d;">'
            f'<strong style="color: #58a6ff;">Step {idx}: [{html.escape(hop.cell_id)}]</strong> '
            f'<span style="color: #e6edf3;">{html.escape(hop.summary)}</span> '
            f'<em style="color: #8b949e; font-size: 11px;">(var: {html.escape(hop.variable)})</em>'
            f"</div>"
        )
    parts.append("</div>")
    return "".join(parts)


def render_path_text(causal_path: CausalPath) -> str:
    """Render a causal path as plain text representation."""
    if not causal_path or not causal_path.hops:
        return "BookError: No causal path traced."

    lines = [f"BookError Causal Path for {causal_path.failure.exc_type}: {causal_path.failure.exc_message}"]
    for idx, hop in enumerate(causal_path.hops, 1):
        lines.append(f"  {idx}. [{hop.cell_id} | exec_id={hop.exec_id}] {hop.summary} (var: '{hop.variable}')")
        if hop.source_snippet:
            lines.append(f"     Source: {hop.source_snippet}")
    return "\n".join(lines)

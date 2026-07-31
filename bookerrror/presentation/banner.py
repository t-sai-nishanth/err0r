"""Inline error banner rendering."""

from __future__ import annotations

from html import escape


def render_banner(causal_path) -> str:
    """Render the main BookError banner HTML."""

    failure = causal_path.failure
    return (
        '<div style="border:1px solid #2d3f54;padding:12px;margin:12px 0;border-left:4px solid #f85149;background:#1e2a3a;color:#e6edf3;">'
        f'<div><strong>BookError</strong> · {escape(failure.exc_type)}: {escape(failure.exc_message)}</div>'
        f'<div style="margin-top:6px; color:#8b949e;">Cell {escape(failure.cell_id)} · exec #{failure.exec_id}</div>'
        '</div>'
    )

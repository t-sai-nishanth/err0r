"""Causal path display helpers."""

from __future__ import annotations

from html import escape


def render_path(causal_path) -> str:
    """Render a causal path as HTML or plain text."""

    rows = []
    for hop in causal_path.hops:
        rows.append(
            '<div style="margin:8px 0;padding:8px;border:1px solid #2d3f54;background:#1a2332;color:#e6edf3;">'
            f'<div><strong>{escape(hop.role)}</strong> · Cell {escape(hop.cell_id)} · exec #{hop.exec_id}</div>'
            f'<div style="color:#79c0ff;">{escape(hop.summary)}</div>'
            f'<div style="font-family:monospace; color:#8b949e;">{escape(hop.source_snippet)}</div>'
            '</div>'
        )
    return ''.join(rows)

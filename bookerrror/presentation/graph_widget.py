"""Graph visualization widget helpers for BookError (SVG DAG renderer)."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from bookerrror.models import CausalPath


def render_graph(graph: Any = None, causal_path: CausalPath | None = None) -> str:
    """Render the dependency graph as an interactive/styled SVG string.

    Works both with a full DependencyGraph object or directly with a CausalPath.
    """
    nodes = []
    edges = []

    if causal_path and causal_path.hops:
        for idx, hop in enumerate(causal_path.hops):
            nodes.append({
                "id": hop.exec_id,
                "cell_id": hop.cell_id,
                "label": f"{hop.cell_id}\n({hop.variable})",
                "role": hop.role,
                "summary": hop.summary,
            })
            if idx < len(causal_path.hops) - 1:
                next_hop = causal_path.hops[idx + 1]
                edges.append({
                    "from": hop.exec_id,
                    "to": next_hop.exec_id,
                    "var": next_hop.variable or hop.variable or "",
                })

    if not nodes:
        return '<div style="color: #8b949e; font-size: 12px;">No graph nodes available to display.</div>'

    # Compute SVG layout coordinates
    spacing_x = 180
    start_x = 60
    y_pos = 60
    width = max(600, start_x + len(nodes) * spacing_x)
    height = 140

    svg_parts = [
        f'<svg width="100%" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" style="background: #0d1117; border-radius: 6px; border: 1px solid #30363d; margin-top: 10px;">',
        '<defs>',
        '<marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
        '<path d="M 0 0 L 10 5 L 0 10 z" fill="#58a6ff"/>',
        '</marker>',
        '</defs>',
    ]

    coords = {}
    for idx, node in enumerate(nodes):
        cx = start_x + idx * spacing_x
        cy = y_pos
        coords[node["id"]] = (cx, cy)

    # Render edges
    for edge in edges:
        if edge["from"] in coords and edge["to"] in coords:
            x1, y1 = coords[edge["from"]]
            x2, y2 = coords[edge["to"]]
            # Shift x so lines end at node borders
            x1 += 50
            x2 -= 50
            svg_parts.append(
                f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#58a6ff" stroke-width="2" marker-end="url(#arrow)" stroke-dasharray="4,2"/>'
            )
            if edge["var"]:
                mid_x = (x1 + x2) / 2
                svg_parts.append(
                    f'<text x="{mid_x}" y="{y1 - 8}" fill="#79c0ff" font-size="10" font-family="monospace" text-anchor="middle">{html.escape(edge["var"])}</text>'
                )

    # Render node boxes
    for node in nodes:
        cx, cy = coords[node["id"]]
        role = node["role"]
        stroke = "#f59e0b" if role == "root_cause" else ("#ef4444" if role == "failure" else "#3b82f6")
        fill = "#161b22"

        svg_parts.append(
            f'<rect x="{cx - 50}" y="{cy - 25}" width="100" height="50" rx="6" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
        )
        svg_parts.append(
            f'<text x="{cx}" y="{cy - 4}" fill="#f0f6fc" font-size="11" font-weight="bold" font-family="sans-serif" text-anchor="middle">{html.escape(node["cell_id"])}</text>'
        )
        svg_parts.append(
            f'<text x="{cx}" y="{cy + 12}" fill="#8b949e" font-size="9" font-family="monospace" text-anchor="middle">exec #{node["id"]}</text>'
        )

    svg_parts.append("</svg>")
    return "".join(svg_parts)

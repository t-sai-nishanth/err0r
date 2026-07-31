"""Graph visualization widget helpers."""

from __future__ import annotations


def render_graph(graph, causal_path=None) -> str:
    """Render a simple textual graph preview."""

    lines = ["<div style='font-family:monospace; white-space:pre;'>"]
    for edge in graph.edges:
        lines.append(f"#{edge.producer_exec_id} --({edge.variable})--> #{edge.consumer_exec_id}<br/>")
    lines.append("</div>")
    return ''.join(lines)"""Graph visualization widget helpers."""

from __future__ import annotations


def render_graph(graph, causal_path=None) -> str:
    """Render the dependency graph visualization."""

    pass

"""Inline error banner & Scikit-Learn style pipeline rendering for BookError."""

from __future__ import annotations

import html
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bookerrror.models import CausalPath, FailureInfo


def _get_css() -> str:
    return """
<style>
.bookerror-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 16px 20px;
    margin: 12px 0;
    color: #c9d1d9;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    max-width: 100%;
    overflow-x: auto;
}
.bookerror-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 1px solid #21262d;
    padding-bottom: 10px;
    margin-bottom: 16px;
}
.bookerror-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 15px;
    font-weight: 700;
    color: #f0f6fc;
}
.bookerror-badge-error {
    background: rgba(248, 81, 73, 0.15);
    color: #ff7b72;
    border: 1px solid rgba(248, 81, 73, 0.4);
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.bookerror-pipeline {
    display: flex;
    align-items: stretch;
    gap: 12px;
    overflow-x: auto;
    padding-bottom: 8px;
}
.bookerror-node {
    flex: 0 0 auto;
    min-width: 220px;
    max-width: 280px;
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 12px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    transition: transform 0.15s ease, border-color 0.15s ease;
}
.bookerror-node:hover {
    border-color: #58a6ff;
    transform: translateY(-2px);
}
.bookerror-node.root-cause {
    border-left: 4px solid #f59e0b;
}
.bookerror-node.intermediate {
    border-left: 4px solid #3b82f6;
}
.bookerror-node.failure {
    border-left: 4px solid #ef4444;
    background: rgba(239, 68, 68, 0.05);
}
.bookerror-node-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    margin-bottom: 6px;
}
.bookerror-role-pill {
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    padding: 2px 6px;
    border-radius: 4px;
}
.role-root-cause {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
}
.role-intermediate {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
}
.role-failure {
    background: rgba(239, 68, 68, 0.2);
    color: #f87171;
}
.bookerror-cell-tag {
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
    font-size: 11px;
    color: #8b949e;
}
.bookerror-summary {
    font-size: 12px;
    font-weight: 600;
    color: #e6edf3;
    margin: 6px 0;
    line-height: 1.4;
}
.bookerror-code {
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
    font-size: 11px;
    background: #0d1117;
    border: 1px solid #21262d;
    padding: 6px 8px;
    border-radius: 4px;
    color: #79c0ff;
    overflow-x: auto;
    white-space: pre;
    margin-top: 6px;
}
.bookerror-connector {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 0 0 auto;
    color: #58a6ff;
}
.bookerror-var-label {
    font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
    font-size: 10px;
    background: #1f6beb26;
    color: #58a6ff;
    padding: 1px 5px;
    border-radius: 3px;
    border: 1px solid #1f6beb40;
    margin-bottom: 2px;
}
.bookerror-arrow {
    font-size: 18px;
    line-height: 1;
}
.bookerror-nav-btn {
    display: inline-block;
    margin-top: 8px;
    font-size: 11px;
    color: #58a6ff;
    text-decoration: none;
    cursor: pointer;
    font-weight: 600;
}
.bookerror-nav-btn:hover {
    text-decoration: underline;
    color: #79c0ff;
}
.bookerror-llm-section {
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed #30363d;
    font-size: 12px;
}
.bookerror-llm-title {
    font-weight: 600;
    color: #a5d6ff;
    margin-bottom: 4px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.bookerror-llm-body {
    color: #c9d1d9;
    line-height: 1.5;
}
</style>
"""


def _get_js() -> str:
    return """
<script>
function bookerror_scroll_to_cell(cellId) {
    try {
        // Search JupyterLab cell element
        let cellEl = document.querySelector('[data-cell-id="' + cellId + '"]') ||
                     document.getElementById(cellId) ||
                     document.querySelector('.jp-Notebook .jp-Cell[data-id="' + cellId + '"]');

        if (!cellEl) {
            // Fallback search by text match
            const cells = document.querySelectorAll('.jp-Cell, .cell');
            for (let c of cells) {
                if (c.innerText && c.innerText.includes(cellId)) {
                    cellEl = c;
                    break;
                }
            }
        }

        if (cellEl) {
            cellEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
            cellEl.style.transition = 'background-color 0.3s ease';
            const originalBg = cellEl.style.backgroundColor;
            cellEl.style.backgroundColor = 'rgba(245, 158, 11, 0.25)';
            setTimeout(() => {
                cellEl.style.backgroundColor = originalBg;
            }, 1800);
        } else {
            console.log('BookError: Cell ' + cellId + ' not found in current view DOM.');
        }
    } catch (e) {
        console.error('BookError navigation error:', e);
    }
}
</script>
"""


def render_banner(causal_path: CausalPath, llm_explanation: str | None = None) -> str:
    """Render the main Scikit-Learn style pipeline banner for a CausalPath."""
    if not causal_path or not causal_path.hops:
        return render_no_chain_banner(
            causal_path.failure.exc_type if causal_path and causal_path.failure else "Error",
            causal_path.failure.exc_message if causal_path and causal_path.failure else "Execution failure",
        )

    failure = causal_path.failure
    hops = causal_path.hops

    html_parts = [_get_css(), _get_js()]
    html_parts.append('<div class="bookerror-container">')

    # Header
    html_parts.append('<div class="bookerror-header">')
    html_parts.append('<div class="bookerror-title">⚡ BookError Causal Trace</div>')
    html_parts.append(
        f'<div class="bookerror-badge-error">{html.escape(failure.exc_type)}: {html.escape(failure.exc_message)}</div>'
    )
    html_parts.append("</div>")

    # Scikit-Learn style horizontal pipeline flow
    html_parts.append('<div class="bookerror-pipeline">')

    for i, hop in enumerate(hops):
        role_class = hop.role.replace("_", "-") if hop.role else "intermediate"
        role_label = hop.role.replace("_", " ").upper() if hop.role else "HOP"

        html_parts.append(f'<div class="bookerror-node {role_class}">')
        html_parts.append('<div class="bookerror-node-header">')
        html_parts.append(f'<span class="bookerror-role-pill role-{role_class}">{html.escape(role_label)}</span>')
        html_parts.append(f'<span class="bookerror-cell-tag">{html.escape(hop.cell_id)} (run #{hop.exec_id})</span>')
        html_parts.append("</div>")

        html_parts.append(f'<div class="bookerror-summary">{html.escape(hop.summary)}</div>')

        if hop.source_snippet:
            html_parts.append(f'<div class="bookerror-code">{html.escape(hop.source_snippet)}</div>')

        html_parts.append(
            f'<a class="bookerror-nav-btn" onclick="bookerror_scroll_to_cell(\'{html.escape(hop.cell_id)}\')">Go to cell ↗</a>'
        )
        html_parts.append("</div>")

        # Arrow connector between nodes
        if i < len(hops) - 1:
            next_hop = hops[i + 1]
            var_name = next_hop.variable or hop.variable or ""
            html_parts.append('<div class="bookerror-connector">')
            if var_name:
                html_parts.append(f'<span class="bookerror-var-label">{html.escape(var_name)}</span>')
            html_parts.append('<span class="bookerror-arrow">➔</span>')
            html_parts.append("</div>")

    html_parts.append("</div>")  # end pipeline

    # Optional LLM Explanation section
    if llm_explanation:
        html_parts.append('<div class="bookerror-llm-section">')
        html_parts.append('<div class="bookerror-llm-title">🤖 Plain Language Explanation</div>')
        html_parts.append(f'<div class="bookerror-llm-body">{html.escape(llm_explanation)}</div>')
        html_parts.append("</div>")

    html_parts.append("</div>")  # end container
    return "".join(html_parts)


def render_no_chain_banner(exc_type: str, exc_message: str) -> str:
    """Render fallback banner when no causal chain can be traced."""
    html_parts = [_get_css()]
    html_parts.append('<div class="bookerror-container">')
    html_parts.append('<div class="bookerror-header">')
    html_parts.append('<div class="bookerror-title">⚡ BookError</div>')
    html_parts.append(
        f'<div class="bookerror-badge-error">{html.escape(exc_type)}: {html.escape(exc_message)}</div>'
    )
    html_parts.append("</div>")
    html_parts.append(
        '<div style="font-size: 13px; color: #8b949e;">No earlier notebook cell dependencies were found for this error. The error appears isolated to this cell execution.</div>'
    )
    html_parts.append("</div>")
    return "".join(html_parts)

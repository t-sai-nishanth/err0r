"""Layer 3: Presentation helpers and display integration for BookError."""

from __future__ import annotations

from typing import TYPE_CHECKING

from bookerrror.presentation.banner import render_banner, render_no_chain_banner
from bookerrror.presentation.graph_widget import render_graph
from bookerrror.presentation.path_display import render_path, render_path_text

if TYPE_CHECKING:
    from bookerrror.models import CausalPath


def render_causal_path(path: CausalPath, llm_explanation: str | None = None) -> None:
    """Render the causal path as styled HTML in the current cell output block."""
    try:
        from IPython.display import HTML, display  # type: ignore

        html_content = render_banner(path, llm_explanation=llm_explanation)
        display(HTML(html_content))
    except ImportError:
        # Fallback for non-IPython/CLI environments
        print(render_path_text(path))


def render_no_chain(exc_type: str, exc_message: str) -> None:
    """Render the fallback display when no causal chain is found."""
    try:
        from IPython.display import HTML, display  # type: ignore

        html_content = render_no_chain_banner(exc_type, exc_message)
        display(HTML(html_content))
    except ImportError:
        print(f"BookError: No causal path traced for {exc_type}: {exc_message}")


def render_graph_view(path: CausalPath) -> None:
    """Render the SVG DAG dependency graph visualization."""
    try:
        from IPython.display import HTML, display  # type: ignore

        svg_content = render_graph(causal_path=path)
        display(HTML(svg_content))
    except ImportError:
        print("BookError: Graph visualization requires IPython environment.")


__all__ = [
    "render_banner",
    "render_causal_path",
    "render_graph",
    "render_graph_view",
    "render_no_chain",
    "render_no_chain_banner",
    "render_path",
    "render_path_text",
]

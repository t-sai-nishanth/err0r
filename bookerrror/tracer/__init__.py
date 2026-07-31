"""Layer 2: root-cause tracer."""

from __future__ import annotations

from bookerrror.models import CausalPath


def trace_error(graph, exception) -> CausalPath:
    """Trace an exception back through the dependency graph."""

    pass

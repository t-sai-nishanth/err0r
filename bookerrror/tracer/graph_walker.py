"""Backward graph walk utilities."""

from __future__ import annotations


def trace_back(graph, failing_exec_id: int, implicated_vars: set[str]) -> list[object]:
    """Walk the graph backward from a failure to its upstream causes."""

    pass

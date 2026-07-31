"""Backward graph walk utilities."""

from __future__ import annotations

from collections import deque

from bookerrror.tracer.models import FailureInfo, TraceNode


def _record_value(record, attribute: str, fallback: str = "") -> str:
    if record is None:
        return fallback
    return getattr(record, attribute, fallback) or fallback


def trace_back(graph, failing_exec_id: int, implicated_vars: set[str]) -> list[TraceNode]:
    """Walk the graph backward from a failure to its upstream causes."""

    if failing_exec_id is None:
        return []

    record = graph.get_record(failing_exec_id)
    if record is None:
        return []

    start_vars = set(implicated_vars) or set(record.reads) or set(record.writes) or set(record.defines)
    if not start_vars:
        start_vars = {""}

    queue = deque((failing_exec_id, variable) for variable in start_vars)
    visited: set[tuple[int, str]] = set()
    nodes: list[TraceNode] = []

    while queue:
        exec_id, variable = queue.popleft()
        if (exec_id, variable) in visited:
            continue
        visited.add((exec_id, variable))

        current_record = graph.get_record(exec_id)
        if current_record is None:
            continue

        failure = None
        if exec_id == failing_exec_id:
            raised = getattr(current_record, "raised", None)
            if raised is not None:
                failure = FailureInfo(
                    cell_id=current_record.cell_id,
                    exec_id=current_record.exec_id,
                    exc_type=raised.exc_type,
                    exc_message=raised.exc_message,
                    failing_line=raised.failing_line,
                )

        nodes.append(
            TraceNode(
                cell_id=current_record.cell_id,
                exec_id=current_record.exec_id,
                variable=variable,
                source_snippet=current_record.source,
                role="failure" if exec_id == failing_exec_id else "intermediate",
                failure=failure,
            )
        )

        for edge in graph.get_edges_to(exec_id):
            if variable and edge.variable != variable:
                continue
            queue.append((edge.producer_exec_id, edge.variable))

    return nodes

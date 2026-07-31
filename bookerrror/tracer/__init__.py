"""Layer 2: root-cause tracer."""

from __future__ import annotations

from bookerrror.models import CausalPath, FailureInfo
from bookerrror.tracer.collapser import collapse_chain
from bookerrror.tracer.frame_walker import find_failure_frame
from bookerrror.tracer.graph_walker import trace_back
from bookerrror.tracer.summarizer import summarize_hop
from bookerrror.tracer.var_extractor import extract_implicated_vars


def _latest_record(graph):
    if hasattr(graph, "get_latest_record"):
        return graph.get_latest_record()
    records = getattr(graph, "records", [])
    return records[-1] if records else None


def trace_error(graph, exception, exec_id: int | None = None) -> CausalPath:
    """Trace an exception back through the dependency graph."""

    record = graph.get_record(exec_id) if exec_id is not None and hasattr(graph, "get_record") else None
    if record is None:
        record = _latest_record(graph)
        if record is not None and exec_id is None:
            exec_id = getattr(record, "exec_id", None)

    failure_frame = find_failure_frame(exception)
    if failure_frame is None and record is not None:
        raised = getattr(record, "raised", None)
        if raised is not None:
            from bookerrror.tracer.models import FrameInfo

            failure_frame = FrameInfo(
                filename=raised.frame_filename,
                lineno=raised.frame_lineno,
                source_line=raised.failing_line,
                cell_id=getattr(record, "cell_id", ""),
                locals={},
            )

    implicated_vars = extract_implicated_vars(failure_frame, exception)
    if not implicated_vars and record is not None:
        implicated_vars = set(getattr(record, "reads", set())) | set(getattr(record, "writes", set())) | set(getattr(record, "defines", set()))

    raw_chain = trace_back(graph, exec_id, implicated_vars) if exec_id is not None else []
    path = collapse_chain(raw_chain)

    if path.failure.exec_id == -1 or not path.failure.cell_id:
        path.failure = FailureInfo(
            cell_id=getattr(record, "cell_id", "") if record is not None else "",
            exec_id=exec_id if exec_id is not None else -1,
            exc_type=exception.__class__.__name__,
            exc_message=str(exception),
            failing_line=failure_frame.source_line if failure_frame is not None else "",
        )

    for hop in path.hops:
        hop.summary = summarize_hop(graph.get_record(hop.exec_id), hop.variable)

    return path

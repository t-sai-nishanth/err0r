"""IPython hook registration for the tracker."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from IPython import get_ipython

from bookerrror.models import Edge, ExecutionRecord, ExceptionInfo
from bookerrror.llm import explain as llm_explain, is_enabled as llm_is_enabled
from bookerrror.presentation import render_causal_path, render_no_chain
from bookerrror.tracker.ast_analyzer import analyze_cell
from bookerrror.tracker.graph import DependencyGraph
from bookerrror.tracer import trace_error
from bookerrror.utils.ipython_helpers import get_cell_id as helper_get_cell_id


_LOGGER = logging.getLogger("bookerrror")


@dataclass
class ExecutionTracker:
    """Track notebook cell executions and build a dependency graph."""

    graph: DependencyGraph
    _pre_run_snapshot: dict[str, int] | None = None
    _last_exception: BaseException | None = None

    def __init__(self) -> None:
        self.graph = DependencyGraph()
        self._pre_run_snapshot = None
        self._last_exception = None

    def pre_run_cell(self, info: Any) -> None:
        """Capture the current ownership state before the cell runs."""

        try:
            self._pre_run_snapshot = self.graph._version_table.snapshot()
        except Exception:
            _LOGGER.error("BookError pre_run_cell failed", exc_info=True)

    def post_run_cell(self, result: Any) -> None:
        """Record the cell execution and handle errors if the cell failed."""

        try:
            source = getattr(getattr(result, "info", None), "raw_cell", "") or ""
            cell_id = self._get_cell_id(result)
            reads, writes, defines = analyze_cell(source)

            raised = None
            error = getattr(result, "error_in_exec", None)
            self._last_exception = error
            if error is not None:
                raised = self._capture_exception(error, source)

            record = self.graph.record_execution(
                cell_id=cell_id,
                source=source,
                reads=reads,
                writes=writes,
                defines=defines,
                raised=raised,
            )

            if raised is not None:
                self._handle_error(record)
        except Exception:
            _LOGGER.error("BookError post_run_cell failed", exc_info=True)

    def _get_cell_id(self, result: Any) -> str:
        """Extract a stable cell id from notebook metadata when available."""

        cell_id = helper_get_cell_id(result)
        if cell_id:
            return cell_id

        try:
            ipython = get_ipython()
            parent = getattr(getattr(ipython, "kernel", None), "get_parent", lambda: {})()
            cell_id = parent.get("metadata", {}).get("cellId")
            if cell_id:
                return str(cell_id)
        except Exception:
            pass
        return f"cell-exec-{getattr(result, 'execution_count', 'unknown')}"

    def _capture_exception(self, exception: BaseException, source: str) -> ExceptionInfo:
        """Extract exception metadata for the tracer."""

        exc_type = type(exception).__name__
        exc_message = str(exception)
        failing_line = ""
        frame_filename = ""
        frame_lineno = 0

        tb = exception.__traceback__
        while tb is not None:
            filename = tb.tb_frame.f_code.co_filename
            if self._is_notebook_cell(filename):
                frame_filename = filename
                frame_lineno = tb.tb_lineno
                lines = source.splitlines()
                if 0 < tb.tb_lineno <= len(lines):
                    failing_line = lines[tb.tb_lineno - 1].strip()
                break
            tb = tb.tb_next

        return ExceptionInfo(
            exc_type=exc_type,
            exc_message=exc_message,
            failing_line=failing_line,
            frame_filename=frame_filename,
            frame_lineno=frame_lineno,
        )

    def _is_notebook_cell(self, filename: str) -> bool:
        """Return True when a traceback filename looks like notebook code."""

        return (
            "<ipython-input-" in filename
            or "ipykernel_" in filename
            or filename.startswith("/tmp/ipykernel")
            or ("AppData" in filename and "ipykernel" in filename)
        )

    def _handle_error(self, record: ExecutionRecord) -> None:
        """Trace a failing cell and render either the causal chain or fallback."""

        if record.raised is None:
            return

        try:
            exception = self._last_exception or Exception(record.raised.exc_message)
            path = trace_error(self.graph, exception, record.exec_id)

            if path and path.hops:
                llm_explanation = None
                if llm_is_enabled():
                    try:
                        llm_explanation = llm_explain(path)
                    except Exception:
                        _LOGGER.debug(
                            "BookError: LLM explanation failed, using deterministic summaries",
                            exc_info=True,
                        )
                render_causal_path(path, llm_explanation=llm_explanation)
            else:
                render_no_chain(record.raised.exc_type, record.raised.exc_message)
        except Exception:
            _LOGGER.error("BookError _handle_error failed", exc_info=True)


def register_hooks(ipython, tracker: ExecutionTracker) -> None:
    """Register tracker hooks on the active IPython shell."""

    ipython.events.register("pre_run_cell", tracker.pre_run_cell)
    ipython.events.register("post_run_cell", tracker.post_run_cell)


def unregister_hooks(ipython, tracker: ExecutionTracker) -> None:
    """Unregister tracker hooks from the active IPython shell."""

    ipython.events.unregister("pre_run_cell", tracker.pre_run_cell)
    ipython.events.unregister("post_run_cell", tracker.post_run_cell)


def pre_run_cell(info) -> None:
    """Handle the pre-run cell hook."""

    tracker = getattr(get_ipython(), "_bookerrror_tracker", None)
    if tracker is not None:
        tracker.pre_run_cell(info)


def post_run_cell(result) -> None:
    """Handle the post-run cell hook."""

    tracker = getattr(get_ipython(), "_bookerrror_tracker", None)
    if tracker is not None:
        tracker.post_run_cell(result)

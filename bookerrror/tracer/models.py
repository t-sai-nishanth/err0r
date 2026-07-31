"""Local tracer models and re-exports."""

from __future__ import annotations

from dataclasses import dataclass, field

from bookerrror.models import CausalHop, CausalPath, FailureInfo


@dataclass
class FrameInfo:
	"""Information about the traceback frame that failed."""

	filename: str
	lineno: int
	source_line: str
	cell_id: str
	locals: dict[str, object] = field(default_factory=dict)


@dataclass
class TraceNode:
	"""Raw backward-walk node before collapse into a causal path."""

	cell_id: str
	exec_id: int
	variable: str
	source_snippet: str
	role: str
	summary: str = ""
	failure: FailureInfo | None = None


__all__ = [
	"CausalHop",
	"CausalPath",
	"FailureInfo",
	"FrameInfo",
	"TraceNode",
]

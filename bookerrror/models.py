"""Shared data models for BookError."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ExceptionInfo:
    exc_type: str
    exc_message: str
    failing_line: str
    frame_filename: str
    frame_lineno: int


@dataclass
class ExecutionRecord:
    exec_id: int
    cell_id: str
    timestamp: float
    source: str
    reads: set[str] = field(default_factory=set)
    writes: set[str] = field(default_factory=set)
    defines: set[str] = field(default_factory=set)
    raised: ExceptionInfo | None = None


@dataclass
class Edge:
    producer_exec_id: int
    consumer_exec_id: int
    variable: str


@dataclass
class CausalHop:
    cell_id: str
    exec_id: int
    variable: str
    summary: str
    source_snippet: str
    role: str


@dataclass
class FailureInfo:
    cell_id: str
    exec_id: int
    exc_type: str
    exc_message: str
    failing_line: str


@dataclass
class CausalPath:
    failure: FailureInfo
    hops: list[CausalHop] = field(default_factory=list)

"""Dependency graph storage for tracker output."""

from __future__ import annotations

from bookerrror.models import Edge, ExecutionRecord


class DependencyGraph:
    """Store execution records and variable dependency edges."""

    def __init__(self) -> None:
        self.records: dict[int, ExecutionRecord] = {}
        self.edges: list[Edge] = []
        self.current_owner: dict[str, int] = {}

    def record_execution(
        self,
        cell_id: str,
        source: str,
        reads: set[str],
        writes: set[str],
        defines: set[str],
        timestamp: float | None = None,
        raised=None,
    ) -> ExecutionRecord:
        """Create and store an execution record."""

        pass

    def get_record(self, exec_id: int) -> ExecutionRecord | None:
        """Return a stored execution record by exec_id."""

        pass

    def get_edges_to(self, exec_id: int) -> list[Edge]:
        """Return all edges that point to the given execution."""

        pass

    def edge_source(self, exec_id: int, variable: str) -> ExecutionRecord | None:
        """Return the producer record for a variable before a consumer execution."""

        pass

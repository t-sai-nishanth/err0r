"""Dependency graph storage for tracker output."""

from __future__ import annotations

import time

from bookerrror.models import Edge, ExecutionRecord
from bookerrror.tracker.version_table import VersionTable


class DependencyGraph:
    """Store execution records and variable dependency edges."""

    def __init__(self) -> None:
        self.records: list[ExecutionRecord] = []
        self.edges: list[Edge] = []
        self._version_table = VersionTable()
        self._next_exec_id = 0

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

        exec_id = self._next_exec_id
        self._next_exec_id += 1

        for variable in reads:
            owner = self._version_table.get_owner(variable)
            if owner is not None:
                self.edges.append(
                    Edge(
                        producer_exec_id=owner,
                        consumer_exec_id=exec_id,
                        variable=variable,
                    )
                )

        record = ExecutionRecord(
            exec_id=exec_id,
            cell_id=cell_id,
            timestamp=time.time() if timestamp is None else timestamp,
            source=source,
            reads=set(reads),
            writes=set(writes),
            defines=set(defines),
            raised=raised,
        )
        self.records.append(record)
        self._version_table.update(set(writes) | set(defines), exec_id)
        return record

    def get_record(self, exec_id: int) -> ExecutionRecord | None:
        """Return a stored execution record by exec_id."""

        for record in self.records:
            if record.exec_id == exec_id:
                return record
        return None

    def get_edges_to(self, exec_id: int) -> list[Edge]:
        """Return all edges that point to the given execution."""

        return [edge for edge in self.edges if edge.consumer_exec_id == exec_id]

    def edge_source(self, exec_id: int, variable: str) -> ExecutionRecord | None:
        """Return the producer record for a variable before a consumer execution."""

        for edge in reversed(self.edges):
            if edge.consumer_exec_id == exec_id and edge.variable == variable:
                return self.get_record(edge.producer_exec_id)
        return None

    def get_latest_record(self) -> ExecutionRecord | None:
        """Return the most recent execution record."""

        if not self.records:
            return None
        return self.records[-1]

    def get_all_records(self) -> list[ExecutionRecord]:
        """Return a copy of all stored execution records."""

        return list(self.records)

    def get_all_edges(self) -> list[Edge]:
        """Return a copy of all stored dependency edges."""

        return list(self.edges)

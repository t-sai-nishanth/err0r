"""Tests for tracker hook behavior."""

from __future__ import annotations

from types import SimpleNamespace

from bookerrror.tracker.hooks import ExecutionTracker


def test_tracker_records_execution_from_post_run_cell() -> None:
    tracker = ExecutionTracker()
    result = SimpleNamespace(info=SimpleNamespace(raw_cell="x = 1"), error_in_exec=None, execution_count=1)

    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(result)

    assert len(tracker.graph.records) == 1
    assert tracker.graph.records[0].source == "x = 1"
    assert tracker.graph.records[0].writes == {"x"}

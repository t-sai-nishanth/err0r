from __future__ import annotations

import pytest

from bookerrror.models import CausalPath, ExecutionRecord
from bookerrror.tracer import trace_error
from bookerrror.tracer.collapser import collapse_chain
from bookerrror.tracer.frame_walker import find_failure_frame
from bookerrror.tracer.graph_walker import trace_back
from bookerrror.tracer.models import FrameInfo
from bookerrror.tracer.summarizer import summarize_hop
from bookerrror.tracer.var_extractor import extract_implicated_vars
from tests.fixtures.sample_data import MOCK_CAUSAL_PATH, MOCK_EDGES, MOCK_RECORDS


class MockGraph:
    def __init__(self, records, edges):
        self.records = {record.exec_id: record for record in records}
        self.edges = list(edges)

    def get_edges_to(self, exec_id):
        return [edge for edge in self.edges if edge.consumer_exec_id == exec_id]

    def get_record(self, exec_id):
        return self.records.get(exec_id)

    def get_latest_record(self):
        return self.records[max(self.records)]


def test_find_failure_frame_uses_innermost_frame():
    def trigger():
        return {}["age"]

    try:
        trigger()
    except KeyError as exc:
        frame = find_failure_frame(exc)

    assert frame is not None
    assert frame.source_line == 'return {}["age"]'


def test_extract_implicated_vars_for_keyerror():
    frame = FrameInfo(
        filename="<ipython-input-9-abc>",
        lineno=1,
        source_line="result = df[['age', 'income']]",
        cell_id="cell-9",
    )

    vars_ = extract_implicated_vars(frame, KeyError("'age'"))

    assert "df" in vars_


def test_trace_back_follows_mock_graph():
    graph = MockGraph(MOCK_RECORDS, MOCK_EDGES)

    chain = trace_back(graph, failing_exec_id=3, implicated_vars={"df"})

    assert [node.exec_id for node in chain] == [3, 2, 1]


def test_collapse_chain_builds_causal_path():
    graph = MockGraph(MOCK_RECORDS, MOCK_EDGES)
    chain = trace_back(graph, failing_exec_id=3, implicated_vars={"df"})

    path = collapse_chain(chain)

    assert isinstance(path, CausalPath)
    assert [hop.exec_id for hop in path.hops] == [1, 2, 3]
    assert path.failure.exec_id == 3


def test_summarize_hop_matches_fixture_shape():
    record = MOCK_RECORDS[2]

    summary = summarize_hop(record, "df")

    assert "dropped" in summary or "called" in summary or "updated" in summary


def test_trace_error_returns_mock_causal_path_shape():
    graph = MockGraph(MOCK_RECORDS, MOCK_EDGES)

    path = trace_error(graph, KeyError("'age'"), exec_id=3)

    assert isinstance(path, CausalPath)
    assert [hop.exec_id for hop in path.hops] == [1, 2, 3]
    assert path.failure.exec_id == 3
    assert path.hops[-1].summary

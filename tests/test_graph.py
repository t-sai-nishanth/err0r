"""Tests for dependency graph construction."""

from __future__ import annotations

from bookerrror.tracker.graph import DependencyGraph


def test_keyerror_scenario_builds_expected_edges() -> None:
    graph = DependencyGraph()

    graph.record_execution(
        "cell-1",
        "import pandas as pd",
        reads=set(),
        writes=set(),
        defines={"pd"},
    )
    graph.record_execution(
        "cell-2",
        "df = pd.read_csv('data.csv')",
        reads={"pd"},
        writes={"df"},
        defines=set(),
    )
    graph.record_execution(
        "cell-5",
        "df = df.drop(columns=['age'])",
        reads={"df"},
        writes={"df"},
        defines=set(),
    )
    graph.record_execution(
        "cell-9",
        "result = df[['age', 'income']]",
        reads={"df"},
        writes={"result"},
        defines=set(),
    )

    edges_to_cell9 = graph.get_edges_to(3)

    assert len(edges_to_cell9) == 1
    assert edges_to_cell9[0].producer_exec_id == 2
    assert edges_to_cell9[0].consumer_exec_id == 3
    assert edges_to_cell9[0].variable == "df"

    latest = graph.get_latest_record()
    assert latest is not None
    assert latest.exec_id == 3


def test_edge_source_returns_latest_producer_for_variable() -> None:
    graph = DependencyGraph()

    graph.record_execution("cell-1", "x = 1", reads=set(), writes={"x"}, defines=set())
    graph.record_execution("cell-2", "x = 2", reads=set(), writes={"x"}, defines=set())
    graph.record_execution("cell-3", "y = x", reads={"x"}, writes={"y"}, defines=set())

    producer = graph.edge_source(2, "x")

    assert producer is not None
    assert producer.exec_id == 1

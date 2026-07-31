from __future__ import annotations

from types import SimpleNamespace

from bookerrror.models import ExceptionInfo
from bookerrror.tracker.hooks import ExecutionTracker


def _raise_keyerror() -> None:
    {}["age"]


def test_error_hook_renders_causal_path_with_llm(monkeypatch):
    tracker = ExecutionTracker()

    tracker.graph.record_execution(
        cell_id="cell-1",
        source="import pandas as pd",
        reads=set(),
        writes={"pd"},
        defines={"pd"},
    )
    tracker.graph.record_execution(
        cell_id="cell-2",
        source="df = pd.read_csv('data.csv')",
        reads={"pd"},
        writes={"df"},
        defines=set(),
    )
    tracker.graph.record_execution(
        cell_id="cell-5",
        source="df = df.drop(columns=['age'])",
        reads={"df"},
        writes={"df"},
        defines=set(),
    )

    captured = {}

    def fake_render_causal_path(path, llm_explanation=None):
        captured["path"] = path
        captured["llm_explanation"] = llm_explanation

    def fake_render_no_chain(exc_type, exc_message):
        raise AssertionError(f"unexpected no-chain fallback: {exc_type}: {exc_message}")

    monkeypatch.setattr("bookerrror.tracker.hooks.render_causal_path", fake_render_causal_path)
    monkeypatch.setattr("bookerrror.tracker.hooks.render_no_chain", fake_render_no_chain)
    monkeypatch.setattr("bookerrror.tracker.hooks.llm_is_enabled", lambda: True)
    monkeypatch.setattr("bookerrror.tracker.hooks.llm_explain", lambda path: "plain English explanation")

    try:
        _raise_keyerror()
    except KeyError as exc:
        error = exc

    result = SimpleNamespace(
        info=SimpleNamespace(raw_cell="result = df[['age', 'income']]"),
        error_in_exec=error,
        execution_count=4,
    )

    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(result)

    assert len(tracker.graph.records) == 4
    assert tracker.graph.records[-1].raised is not None
    assert tracker.graph.records[-1].raised.exc_type == "KeyError"
    assert captured["llm_explanation"] == "plain English explanation"
    assert captured["path"].failure.exc_type == "KeyError"
    assert [hop.exec_id for hop in captured["path"].hops] == [1, 2, 3]
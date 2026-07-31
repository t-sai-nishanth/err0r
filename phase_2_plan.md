# Phase 2: Integration Plan — Connecting All Three Layers

After a full review of every file across all three workstreams, here is the complete gap analysis and integration plan to wire the project into a working end-to-end pipeline.

---

## Current State Summary

### ✅ Layer 1 — Tracker (Person A) — COMPLETE
| File | Status | Notes |
|---|---|---|
| [ast_analyzer.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/ast_analyzer.py) | ✅ Done | Handles assignments, imports, augmented assigns, for/with, named exprs, mutating methods, comprehensions, tuple unpacking, builtins filtering |
| [version_table.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/version_table.py) | ✅ Done | `get_owner`, `set_owner`, `update`, `snapshot`, `reset` |
| [graph.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/graph.py) | ✅ Done | `record_execution`, `get_record`, `get_edges_to`, `edge_source`, `get_latest_record`, `get_all_records`, `get_all_edges` — matches the interface contract |
| [hooks.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/hooks.py) | ⚠️ Stub wiring | Has `_handle_error` but it only **prints** a stub message. Does NOT call tracer or display. This is the primary integration point. |
| [extension.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/extension.py) | ✅ Done | `load_ipython_extension`, `unload_ipython_extension`, `bookerrror_debug` magic |

### ✅ Layer 2 — Tracer (Person B) — COMPLETE
| File | Status | Notes |
|---|---|---|
| [tracer/\_\_init\_\_.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/__init__.py) | ✅ Done | `trace_error(graph, exception, exec_id)` — the main entry point. Chains frame_walker → var_extractor → graph_walker → collapser → summarizer |
| [frame_walker.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/frame_walker.py) | ✅ Done | Walks `__traceback__`, finds innermost user frame |
| [var_extractor.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/var_extractor.py) | ✅ Done | Extracts implicated vars by exception type (KeyError, AttributeError, NameError, TypeError) |
| [graph_walker.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/graph_walker.py) | ✅ Done | Reverse BFS from failing exec_id, follows edges backward |
| [collapser.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/collapser.py) | ✅ Done | Deduplicates, sorts chronologically, assigns roles (root_cause/intermediate/failure) |
| [summarizer.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracer/summarizer.py) | ✅ Done | AST heuristic summaries for imports, assignments, mutating pandas/sklearn methods |

### ✅ Layer 3 — Presentation (Person C) — COMPLETE
| File | Status | Notes |
|---|---|---|
| [presentation/\_\_init\_\_.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/presentation/__init__.py) | ✅ Done | `render_causal_path(path)`, `render_no_chain(exc_type, exc_message)`, `render_graph_view(path)` |
| [banner.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/presentation/banner.py) | ✅ Done | Scikit-Learn style pipeline HTML with role-colored hop cards, cell navigation JS |
| [path_display.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/presentation/path_display.py) | ✅ Done | HTML hop list and plain text fallback |
| [graph_widget.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/presentation/graph_widget.py) | ✅ Done | SVG DAG renderer |

### ✅ Layer 4 — LLM (Person C) — COMPLETE
| File | Status | Notes |
|---|---|---|
| [llm/config.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/llm/config.py) | ✅ Done | `is_enabled()`, `get_llm_provider()` |
| [llm/prompt_builder.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/llm/prompt_builder.py) | ✅ Done | `build_prompt(causal_path)` |
| [llm/client.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/llm/client.py) | ✅ Done | `explain(causal_path)` with multi-provider support + fallbacks |

---

## Gap Analysis — What's Missing

> [!IMPORTANT]
> Every individual layer works in isolation with mock data. The **only** missing piece is the wiring between them inside the error handler.

### Gap 1: `_handle_error` in hooks.py is a stub
**This is the single most critical gap.** Right now [hooks.py line 117-128](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/hooks.py#L117-L128) just prints a debug message when an error is detected. It does NOT call the tracer or presentation layer.

The `parallel_plan.md` [specified exactly this wiring](file:///c:/Users/hrish/Projects/hackathon/err0r/parallel_plan.md#L407-L430):
```python
if result.error_in_exec:
    exception = result.error_in_exec
    exec_id = self.graph.get_latest_record().exec_id
    path = trace_error(self.graph, exception, exec_id)   # Layer 2
    if path and path.hops:
        render_causal_path(path)                          # Layer 3
    else:
        render_no_chain(type(exception).__name__, str(exception))
```

### Gap 2: LLM explanation is not wired into the display flow
`render_causal_path` accepts an optional `llm_explanation` parameter, but nobody calls `llm.explain()` and passes the result in. The banner has the visual area for it, but the pipeline doesn't populate it.

### Gap 3: `utils/ipython_helpers.py` is a stub
[get_cell_id](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/utils/ipython_helpers.py#L6-L9) is `pass`. This function isn't currently used (hooks.py has its own `_get_cell_id` method), so this is a dead file. Should be cleaned up or removed to avoid confusion.

### Gap 4: Demo notebooks need updating for end-to-end flow
The current [demo_keyerror.ipynb](file:///c:/Users/hrish/Projects/hackathon/err0r/demo/demo_keyerror.ipynb) has a final cell that manually imports mock data and calls `render_causal_path`. Once the pipeline is wired, this shouldn't be needed — the banner should appear automatically when the error cell runs.

### Gap 5: No end-to-end integration test
Individual tests exist for each layer, but there is no test that simulates: create tracker → record 3 cell executions → trigger error → verify a `CausalPath` with correct hops is produced → verify HTML output contains expected content.

### Gap 6: `pyproject.toml` is minimal
Missing `[project.dependencies]` (at minimum `ipython`). Missing `[project.optional-dependencies]` for LLM providers. No `[tool.pytest]` config.

---

## Integration Plan — Exact Changes

### Step 1: Wire `_handle_error` in hooks.py (THE critical change)

#### [MODIFY] [hooks.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/tracker/hooks.py)

1. Add imports at the top:
   ```python
   from bookerrror.tracer import trace_error
   from bookerrror.presentation import render_causal_path, render_no_chain
   from bookerrror.llm import explain as llm_explain, is_enabled as llm_is_enabled
   ```

2. Replace `_handle_error` (lines 117-128) with:
   ```python
   def _handle_error(self, record: ExecutionRecord) -> None:
       """Trace the error back through the dependency graph and render the result."""
       assert record.raised is not None
       try:
           exception = self._last_exception or Exception(record.raised.exc_message)
           path = trace_error(self.graph, exception, record.exec_id)

           if path and path.hops:
               llm_explanation = None
               if llm_is_enabled():
                   try:
                       llm_explanation = llm_explain(path)
                   except Exception:
                       _LOGGER.debug("BookError: LLM explanation failed, using deterministic summaries")
               render_causal_path(path, llm_explanation=llm_explanation)
           else:
               render_no_chain(record.raised.exc_type, record.raised.exc_message)
       except Exception:
           _LOGGER.error("BookError _handle_error failed", exc_info=True)
   ```

3. Capture the live exception object in `post_run_cell` before it's lost:
   - Add `self._last_exception = error` before calling `_handle_error`, so the tracer's `find_failure_frame` can walk the real `__traceback__` chain.

---

### Step 2: Clean up `utils/ipython_helpers.py`

#### [MODIFY] [ipython_helpers.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/utils/ipython_helpers.py)

Either implement `get_cell_id` properly (extracting from kernel parent message, same logic as `hooks.py:_get_cell_id`) or delete this file since `hooks.py` already has its own implementation. Recommendation: **delete it** to avoid dead code confusion, or make `hooks.py._get_cell_id` call this utility.

---

### Step 3: Update demo notebooks for end-to-end flow

#### [MODIFY] [demo_keyerror.ipynb](file:///c:/Users/hrish/Projects/hackathon/err0r/demo/demo_keyerror.ipynb)

Remove the manual `render_causal_path(MOCK_CAUSAL_PATH)` cell. The demo should just be:
1. `%load_ext bookerrror`
2. `df = pd.read_csv('data.csv')`
3. `df = df.drop(columns=['age'])`
4. `result = df[['age', 'income']]` → BookError pipeline banner auto-appears

#### [MODIFY] [demo_attributeerror.ipynb](file:///c:/Users/hrish/Projects/hackathon/err0r/demo/demo_attributeerror.ipynb)

Uncomment the `model.predict(...)` line so it actually triggers the error in the demo flow.

---

### Step 4: Add end-to-end integration test

#### [NEW] [test_integration.py](file:///c:/Users/hrish/Projects/hackathon/err0r/tests/test_integration.py)

A test that simulates the full pipeline without IPython:
```python
def test_full_pipeline_keyerror_scenario():
    """Simulate: tracker records 4 cells → tracer traces error → presentation renders HTML."""
    from bookerrror.tracker.graph import DependencyGraph
    from bookerrror.tracer import trace_error
    from bookerrror.presentation.banner import render_banner

    graph = DependencyGraph()
    graph.record_execution("cell-1", "import pandas as pd", reads=set(), writes=set(), defines={"pd"})
    graph.record_execution("cell-2", "df = pd.read_csv('data.csv')", reads={"pd"}, writes={"df"}, defines=set())
    graph.record_execution("cell-5", "df = df.drop(columns=['age'])", reads={"df"}, writes={"df"}, defines=set())
    graph.record_execution("cell-9", "result = df[['age', 'income']]", reads={"df"}, writes={"result"}, defines=set(),
        raised=ExceptionInfo(...))

    path = trace_error(graph, KeyError("'age'"), exec_id=3)

    assert path is not None
    assert len(path.hops) >= 2
    assert path.hops[0].role == "root_cause"
    assert path.hops[-1].role == "failure"

    html = render_banner(path)
    assert "bookerror-pipeline" in html
    assert "cell-5" in html
    assert "dropped" in html.lower() or "drop" in html.lower()
```

---

### Step 5: Enhance `pyproject.toml`

#### [MODIFY] [pyproject.toml](file:///c:/Users/hrish/Projects/hackathon/err0r/pyproject.toml)

```toml
[project]
name = "bookerrror"
version = "0.1.0"
requires-python = ">=3.10"
description = "Notebook-aware error localizer — deterministic root-cause tracing for Jupyter"
dependencies = [
    "ipython>=8.0",
]

[project.optional-dependencies]
llm = [
    "anthropic>=0.20",
    "openai>=1.0",
    "google-generativeai>=0.5",
]
dev = [
    "pytest>=7.0",
]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends._legacy:_Backend"

[tool.pytest.ini_options]
testpaths = ["tests"]
```

---

### Step 6 (Optional Polish): Add `%bookerrror_explain` magic

#### [MODIFY] [extension.py](file:///c:/Users/hrish/Projects/hackathon/err0r/bookerrror/extension.py)

Register a second magic command `%bookerrror_explain` that re-renders the last error's causal path with the LLM explanation. This allows the "Explain in Plain English" flow from the solution doc without needing a JavaScript button in the HTML:
```python
def bookerrror_explain(line: str = "") -> None:
    """Re-display the last error's causal path with an LLM explanation."""
    # get last CausalPath from tracker, call llm.explain(), render
```

---

## Execution Order

| Step | What | Est. Time | Risk |
|---|---|---|---|
| **1** | Wire `_handle_error` in hooks.py | 15 min | 🔴 Critical path — everything depends on this |
| **2** | Clean up ipython_helpers.py | 5 min | 🟢 Trivial |
| **3** | Update demo notebooks | 10 min | 🟢 Low |
| **4** | Write integration test | 15 min | 🟡 Medium — need to verify real pipeline produces correct hops |
| **5** | Update pyproject.toml | 5 min | 🟢 Trivial |
| **6** | Add `%bookerrror_explain` magic (optional) | 10 min | 🟢 Optional polish |
| **7** | Run full test suite, fix any issues | 15 min | 🟡 Medium |
| **8** | Manual Jupyter test & demo dry-run | 15 min | 🟡 Must verify HTML renders in real JupyterLab |

**Total estimated time: ~1.5 hours**

---

## Verification Plan

### Automated Tests
```bash
python -m pytest tests/ -v
```
All existing tests (test_ast_analyzer, test_graph, test_hooks, test_extension, test_tracer, test_presentation, test_llm) should still pass plus the new `test_integration.py`.

### Manual Jupyter Verification
1. `pip install -e .` in the project root.
2. Open `demo/demo_keyerror.ipynb` in JupyterLab.
3. Run cells 1-4 in order.
4. Verify the Scikit-Learn style pipeline banner auto-appears below cell 4's error output.
5. Click "Go to cell ↗" links and verify smooth scrolling.
6. Run `%bookerrror_debug` to verify graph state.

### What Success Looks Like
When cell 4 (`result = df[['age', 'income']]`) raises a `KeyError`, the output block should automatically show:

```
⚡ BookError Causal Trace                    [KeyError: 'age']

┌──────────────┐     df     ┌──────────────┐     df     ┌──────────────┐
│ 🟠 ROOT CAUSE│ ─────────→ │ 🔵 INTERMEDIATE│ ─────────→ │ 🔴 FAILURE   │
│ cell-2       │            │ cell-5        │            │ cell-9       │
│ defined df   │            │ dropped 'age' │            │ KeyError     │
│ from csv     │            │ from df       │            │              │
└──────────────┘            └──────────────┘            └──────────────┘
```

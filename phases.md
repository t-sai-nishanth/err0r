# BookError — Implementation Phases

## Overview

This plan is designed for an **18-hour hackathon**. Phases 1–5 must be completed within the hackathon window. Phase 6 is post-hackathon.

The order is strictly dependency-driven: each phase builds on the previous one. The demo notebooks (Phase 5) are the final deliverable — if time runs short, features that don't affect the demo are the first to cut.

```
Hour  0          3          6          9          12         15         18
      │──────────│──────────│──────────│──────────│──────────│──────────│
      Phase 1    Phase 2      Phase 3    Phase 4    Phase 5
      Foundation Tracer Core  Present.   Stretch    Demo & Polish
      + Tracker                          (Graph/LLM)
```

---

## Phase 1: Foundation + Execution Tracker (Hours 0–4)

### Objective

Set up the Python package structure, implement the IPython event hooks, build the AST analyzer, and construct the dependency graph — the entire Layer 1.

This is the highest-priority, most novel component. Everything else depends on it being correct.

### Major Tasks

- [ ] Initialize the project structure.
  - Create `bookerrror/` Python package with `__init__.py`.
  - Create `bookerrror/extension.py` with `load_ipython_extension` / `unload_ipython_extension`.
  - Create `pyproject.toml` with project metadata.
  - Create `.gitignore`, initial `README.md`.
  - Verify `%load_ext bookerrror` works in a JupyterLab notebook (prints "BookError active").
- [ ] Implement the AST analyzer (`bookerrror/tracker/ast_analyzer.py`).
  - Parse cell source with `ast.parse()`.
  - Walk AST to extract names in `ast.Load` context (reads).
  - Walk AST to extract names in `ast.Store` context (writes), including:
    - Simple assignments (`x = ...`).
    - Augmented assignments (`x += ...`).
    - `for` targets (`for x in ...`).
    - `with ... as x`.
    - Function definitions (`def foo`).
    - Class definitions (`class Bar`).
    - Import statements (`import x`, `from y import x`).
  - Detect known mutating method calls (`.drop()`, `.fillna()`, etc.) and add the receiver to the write set.
  - Filter out builtins (`print`, `range`, `len`, `True`, `False`, `None`, etc.).
  - Filter out function-local variables (only track module-scope names).
- [ ] Implement the data model (`bookerrror/tracker/models.py`).
  - Define `ExecutionRecord`, `ExceptionInfo`, `Edge` dataclasses.
- [ ] Implement the variable version table (`bookerrror/tracker/version_table.py`).
  - `current_owner: dict[str, int]` — maps variable name to the `exec_id` that last wrote it.
  - `update(writes: set[str], exec_id: int)` method.
  - `get_owner(var: str) -> Optional[int]` method.
- [ ] Implement the dependency graph (`bookerrror/tracker/graph.py`).
  - `DependencyGraph` class with `records`, `edges`, `current_owner`.
  - `record_execution(...)` method that:
    1. Creates an `ExecutionRecord`.
    2. For each read variable, adds an edge from `current_owner[var]` to the current `exec_id`.
    3. Updates `current_owner` with all written variables.
  - `get_edges_to(exec_id)` method for backward traversal.
  - `get_record(exec_id)` method.
- [ ] Implement the IPython hooks (`bookerrror/tracker/hooks.py`).
  - `pre_run_cell` handler: snapshot `current_owner` state (for edge construction).
  - `post_run_cell` handler:
    1. Get cell source from the event.
    2. Run AST analyzer to get reads/writes/defines.
    3. If exception occurred, capture `ExceptionInfo` from `result.error_in_exec`.
    4. Call `graph.record_execution(...)`.
    5. If exception occurred, trigger Layer 2.
  - Extract `cell_id` from Jupyter cell metadata (fallback: use execution count).
- [ ] Write basic tests for the AST analyzer.
  - Test simple assignments, imports, function definitions.
  - Test mutating method detection.
  - Test builtin filtering.
- [ ] Manual verification: open a notebook, load the extension, run a few cells, and inspect the graph state via a debug helper function (`%bookerrror_debug`).

### Dependencies

None. This is the foundation.

### Expected Outcome

- `%load_ext bookerrror` loads without error.
- Running cells builds the dependency graph incrementally.
- `%bookerrror_debug` (or equivalent) prints the current graph state: execution records, edges, and current_owner.
- The graph correctly reflects out-of-order and re-executed cells.
- Overhead is imperceptible (< 5ms per cell).

---

## Phase 2: Root-Cause Tracer (Hours 4–7)

### Objective

Implement Layer 2: when a cell raises an exception, automatically identify the implicated variables, perform a backward graph walk, and produce a `CausalPath` with human-readable hop summaries.

### Major Tasks

- [ ] Implement the traceback frame walker (`bookerrror/tracer/frame_walker.py`).
  - Walk `exc.__traceback__` to find the innermost frame in user notebook code.
  - Detect IPython cell filenames (`<ipython-input-N-hash>` or `/tmp/ipykernel_*/...`).
  - Return `FrameInfo` with filename, line number, and local variables.
  - Handle edge case: no user-code frame found → return `None`.
- [ ] Implement the variable extractor (`bookerrror/tracer/var_extractor.py`).
  - Given the failing line's source code, AST-parse just that line.
  - Extract variable names involved in the exception:
    - `KeyError` → the object being subscripted.
    - `AttributeError` → the object being accessed.
    - `NameError` → the undefined name itself.
    - `TypeError` → the object(s) in the operation.
    - `IndexError` → the object being indexed.
    - Generic fallback: all names in `ast.Load` context on the failing line.
- [ ] Implement the backward graph walker (`bookerrror/tracer/graph_walker.py`).
  - `trace_back(graph, failing_exec_id, implicated_vars) -> list[ChainNode]`.
  - Reverse BFS from the failing node, following producer edges backward.
  - Track visited `(exec_id, var)` pairs to avoid cycles (shouldn't exist but safety net).
  - Return the raw chain in chronological order.
- [ ] Implement the causal path collapser (`bookerrror/tracer/collapser.py`).
  - De-duplicate chain nodes.
  - Sort chronologically by `exec_id`.
  - Produce `CausalPath` with `CausalHop` objects.
- [ ] Implement the hop summarizer (`bookerrror/tracer/summarizer.py`).
  - Analyze each hop's AST to generate a one-line summary.
  - Use a lookup table for common patterns:
    - Assignment: `"defined {var} from {rhs_summary}"`.
    - Method call: `"called .{method}() on {var}"`.
    - Known mutating methods: `"dropped column '{col}' from {var}"`, `"filled NaN values in {var}"`, etc.
    - Reassignment: `"reassigned {var}"`.
    - Import: `"imported {var}"`.
  - Keep summaries under 80 characters.
- [ ] Define the data models (`bookerrror/tracer/models.py`).
  - `CausalHop` dataclass.
  - `CausalPath` dataclass.
  - `FailureInfo` dataclass.
- [ ] Wire Layer 2 into the `post_run_cell` hook.
  - When `result.error_in_exec` is not `None`:
    1. Call frame_walker → get FrameInfo.
    2. Call var_extractor → get implicated variables.
    3. Call graph_walker → get raw chain.
    4. Call collapser → get CausalPath.
    5. Store CausalPath for Layer 3 to render.
- [ ] Test with prepared scenarios:
  - Scenario A: `df = pd.read_csv(...)` → `df.drop(columns=['age'])` → `df[['age', 'income']]` → `KeyError`.
  - Scenario B: `model = SomeModel()` → `model = "not a model"` → `model.predict(X)` → `AttributeError`.
  - Verify the causal chain is correct and summaries are readable.

### Dependencies

- Phase 1 (dependency graph, execution records, AST analyzer).

### Expected Outcome

- When a cell raises an exception, the `CausalPath` is computed automatically.
- The causal chain correctly identifies the root cause cell.
- Hop summaries are human-readable and accurate.
- The full trace completes in < 50ms.
- A debug helper (`%bookerrror_trace`) prints the last causal path.

---

## Phase 3: Presentation Layer (Hours 7–11)

### Objective

Build the inline HTML output that renders the causal chain in the notebook, including the banner, hop cards, variable arrows, and cell navigation. This is what the audience sees in the demo.

### Major Tasks

- [ ] Implement the banner renderer (`bookerrror/presentation/banner.py`).
  - Generate HTML for the full BookError output.
  - Include inline CSS (the output must be self-contained — no external stylesheets in IPython `display(HTML(...))`).
  - Banner header: icon + exception type + root cause cell reference.
  - Causal chain section: numbered hop cards with variable arrows between them.
  - "Explain" button placeholder (wired in Phase 4 if time allows).
- [ ] Implement hop card rendering.
  - Color-coded left border (orange/blue/red by role).
  - Role badge (🟠 ROOT CAUSE / 🔵 / 🔴 FAILED).
  - Cell ID and execution number.
  - Summary text.
  - Code snippet in monospace.
  - "Go →" link.
- [ ] Implement variable arrow rendering.
  - Simple vertical connector with variable name label.
- [ ] Implement the "no causal chain" fallback.
  - Minimal banner for errors that can't be traced.
- [ ] Implement cell navigation.
  - Embed JavaScript in the HTML output to scroll to target cells on "Go →" click.
  - Try multiple cell selector strategies (JupyterLab data attributes, cell index fallback).
  - Add a temporary highlight effect on the target cell (CSS animation injected via JS).
- [ ] Style the entire output.
  - Dark theme colors matching JupyterLab.
  - All CSS inline within the HTML (necessary for IPython display compatibility).
  - Consistent spacing, typography, and visual hierarchy.
  - Subtle animations: banner fade-in, staggered hop card appearance.
- [ ] Wire the presentation layer into the post_run_cell hook.
  - After Layer 2 produces a CausalPath, automatically call the banner renderer.
  - The output appears directly after the standard traceback.
- [ ] Test in JupyterLab.
  - Run the prepared demo scenarios from Phase 2.
  - Verify the banner renders correctly.
  - Verify "Go →" scrolls to the correct cells.
  - Verify the styling looks clean on JupyterLab's dark theme.
  - Test on JupyterLab's light theme too (ensure readability).

### Dependencies

- Phase 2 (CausalPath objects, the trigger mechanism in post_run_cell).

### Expected Outcome

- When a cell errors, a styled causal chain banner appears below the traceback.
- The banner shows the root cause, intermediate hops, and failure with clear visual hierarchy.
- "Go →" links scroll to and briefly highlight the target cells.
- The output looks polished and professional on JupyterLab's dark theme.
- The "no causal chain" fallback renders for untraceable errors.
- End-to-end: load extension → run cells out of order → trigger error → see causal chain → navigate to root cause.

---

## Phase 4: Stretch Features (Hours 11–15)

### Objective

Implement high-demo-value stretch features: the interactive graph visualization, the optional LLM explanation, and stale code detection. Build what time allows, in priority order.

### 4A: Graph Visualization (Hours 11–13) — Highest Demo Value

- [ ] Implement a simple graph renderer (`bookerrror/presentation/graph_widget.py`).
  - Generate an SVG of the dependency DAG.
  - Use a simple top-to-bottom layered layout (one layer per chronological group of exec_ids).
  - Nodes: rounded rectangles with exec_id and primary variable.
  - Edges: arrows labeled with variable names.
  - Causal path: highlighted in orange. Non-causal nodes: dimmed gray.
  - Render as inline SVG via `display(HTML(...))` or `display(SVG(...))`.
- [ ] Add an expandable "Show Graph" section to the banner.
  - Default: collapsed. Expands on click.
  - The graph appears within the banner container.
- [ ] Test with the demo scenarios. Ensure the graph is readable and the causal path is visually obvious.

### 4B: LLM Explanation (Hours 13–14.5)

- [ ] Implement the prompt builder (`bookerrror/llm/prompt_builder.py`).
  - Construct the minimal prompt from the CausalPath (see architecture.md).
  - Log the token count for the demo comparison.
- [ ] Implement the LLM client (`bookerrror/llm/client.py`).
  - Use `httpx` for async HTTP calls (or `requests` for simplicity).
  - Support OpenAI-compatible API endpoints.
  - Configurable via `BOOKERRROR_API_KEY` and `BOOKERRROR_API_URL` environment variables.
  - 10-second timeout.
  - Return the explanation text or a fallback message on failure.
- [ ] Wire the "Explain" button in the banner.
  - Clicking the button calls the LLM client.
  - Replace the button with the explanation text when the response arrives.
  - Show token counts in the explanation footer.
  - This requires JavaScript in the HTML to make the API call client-side, OR a Jupyter kernel callback to call the LLM server-side.
  - **Simpler approach:** Make the LLM call server-side (kernel-side) and render the explanation as a new `display(HTML(...))` output below the banner.
- [ ] Test with a real API key. Verify the explanation is coherent and the token count is ~100.

### 4C: Stale Code Detection (Hours 14.5–15)

- [ ] Track the last-executed source for each cell ID.
  - Compare the cell's current source (from `pre_run_cell`) against the last recorded source.
  - If they differ and the cell hasn't been re-run, mark it as "stale."
- [ ] Add a stale indicator to hop cards.
  - ⚠️ icon with tooltip: "This cell's code has changed since it was last executed."
- [ ] This is a nice-to-have. Skip if time is short.

### Dependencies

- Phases 1–3 (complete working system with visible output).

### Expected Outcome (Best Case)

- The graph visualization shows the dependency DAG with the causal path highlighted.
- The LLM explanation produces a clear, short explanation with a ~100-token prompt.
- Stale code warnings appear on modified-but-not-re-run cells.

### Expected Outcome (Minimum)

- If time is tight, skip 4B and 4C. The graph visualization alone (4A) is the single highest-value stretch feature for the demo.

---

## Phase 5: Demo Preparation & Polish (Hours 15–18)

### Objective

Prepare the hackathon demo notebooks, fix bugs, polish the output, and rehearse the presentation.

### Major Tasks

- [ ] Write demo notebook 1: **KeyError from out-of-order column drop.**
  - Cell 1: `import pandas as pd`.
  - Cell 2: `df = pd.read_csv('data.csv')` — defines df with columns including 'age'.
  - Cell 3: Some unrelated work.
  - Cell 4: `print(df.describe())` — uses df.
  - Cell 5: `df = df.drop(columns=['age'])` — drops the 'age' column.
  - Cell 6: `result = df[['age', 'income']]` — crashes with KeyError.
  - **Demo instruction:** Run cells 1, 2, 3, 4, 6, 5, 6 (out of order). The second run of cell 6 crashes because cell 5 was run in between.
- [ ] Write demo notebook 2: **AttributeError from variable overwrite.**
  - Cell 1: `from sklearn.linear_model import LinearRegression`.
  - Cell 2: `model = LinearRegression()` — defines model.
  - Cell 3: `model.fit(X_train, y_train)` — trains model.
  - Cell 4: `model = "best model ever"` — accidentally overwrites model.
  - Cell 5: `predictions = model.predict(X_test)` — crashes with AttributeError.
  - **Demo instruction:** Run 1, 2, 3, 5 (works), then run 4, then re-run 5 (crashes because model is now a string).
- [ ] Create sample data files for the demo notebooks (small CSVs).
- [ ] Script the exact 3-minute demo flow:
  - 0:00–0:30: "Notebooks are stateful. Running cells out of order causes invisible bugs. Here's an example." Run the demo, show the error.
  - 0:30–1:00: "The traceback tells you *what* broke but not *why*. Copying it into ChatGPT costs 1000+ tokens and takes 10+ seconds."
  - 1:00–2:00: "BookError traces the error backward through the execution history." Load the extension, re-run the demo. Show the causal chain appearing. Click through to the root cause cell.
  - 2:00–2:30: Show the graph view (if available). Show the highlighted causal path.
  - 2:30–3:00: Click "Explain" to show the LLM explanation (if available). Show the side-by-side token comparison.
- [ ] Prepare the comparison slide/output.
  - Show the naive approach: full traceback pasted into ChatGPT. Count tokens (~1000+).
  - Show BookError's prompt: ~100 tokens. Emphasize the 10x reduction.
- [ ] Run the demo at least 5 times end-to-end. Fix any bugs discovered.
- [ ] Polish the HTML output.
  - Fix any visual inconsistencies.
  - Ensure hop summaries are clear and accurate for the demo scenarios.
  - Ensure "Go →" navigation works reliably.
  - Test on both JupyterLab dark and light themes.
- [ ] Write a minimal `README.md` with:
  - What BookError is (one paragraph).
  - Quick start: `%load_ext bookerrror`.
  - What it does (with a screenshot or output example).
- [ ] **Feature freeze at hour 16.** Only bug fixes after that.
- [ ] Rehearse the demo presentation at least 3 times.

### Dependencies

- All previous phases.

### Expected Outcome

- The 3-minute demo runs perfectly from start to finish.
- Two demo notebooks produce compelling causal chains.
- The README allows someone else to try BookError.
- No crashes or visual glitches during the demo path.
- The team has rehearsed and can present confidently.

---

## Phase 6: Post-Hackathon (After Hour 18)

> Everything below is intentionally deferred. Including any of it in the 18-hour window would risk the core MVP.

### 6A: Robustness & Edge Cases

- [ ] Improved AST analysis: list comprehensions, walrus operator (`:=`), augmented assignments, tuple unpacking.
- [ ] Better scope handling: nested functions, class methods, closures.
- [ ] Aliasing detection via shallow value snapshots (hash values before/after cell execution to detect in-place mutations).
- [ ] Handle `%%` magics and shell-outs (record as opaque, warn user).
- [ ] Comprehensive test suite.

### 6B: Full JupyterLab Extension

- [ ] TypeScript/React sidebar panel for the causal chain.
- [ ] Persistent causal path view (survives scrolling).
- [ ] Interactive graph view with D3.js.
- [ ] Cell highlighting via JupyterLab cell API (not JavaScript injection).
- [ ] Proper JupyterLab extension packaging (`jupyter labextension`).

### 6C: Intelligence & Proactive Features

- [ ] Stale variable detection and warnings (proactive, not just on error).
- [ ] Execution order recommendations ("You should re-run cell 5 before cell 9").
- [ ] Variable lifecycle timeline (show when a variable was defined, modified, and used).

### 6D: Distribution

- [ ] `pip install bookerrror` with PyPI release.
- [ ] Google Colab compatibility.
- [ ] VS Code Jupyter extension support.
- [ ] Documentation website.

### 6E: Community

- [ ] Open-source release (license, contributing guide, CI/CD).
- [ ] Example notebooks for common debugging scenarios.
- [ ] Blog post: "How BookError Works Under the Hood."

---

## Time Budget Summary

| Phase | Hours | Cumulative | Focus |
|---|---|---|---|
| 1. Foundation + Tracker | 4 | 4 | Package setup, AST analyzer, graph construction, IPython hooks |
| 2. Root-Cause Tracer | 3 | 7 | Frame walking, variable extraction, backward walk, hop summaries |
| 3. Presentation | 4 | 11 | HTML banner, hop cards, cell navigation, styling |
| 4. Stretch Features | 4 | 15 | Graph visualization, LLM explanation, stale detection |
| 5. Demo & Polish | 3 | 18 | Demo notebooks, bug fixes, rehearsal |

### Buffer Strategy

- **Phase 1 is the riskiest.** The AST analyzer and graph construction must be correct for everything else to work. If Phase 1 takes longer, steal time from Phase 4 (stretch features).
- **Phase 3 takes time because inline CSS/HTML is fiddly.** If the styling takes too long, ship with minimal styling — a plain-text causal chain is still a working demo.
- **Phase 4 is entirely optional.** The system is demoable after Phase 3. Phase 4 features (graph view, LLM explanation) make the demo more impressive but are not required.
- **Phase 5 has 3 hours.** The last 2 hours must be bug fixes and rehearsal only. **No new features after hour 16.**
- **If everything goes well,** the team has a polished demo with graph visualization and LLM explanation. **If things go poorly,** the team still has a working causal chain display with cell navigation — which is the core value proposition.

### Critical Path

```
Phase 1 (AST + Graph) → Phase 2 (Backward Walk) → Phase 3 (Banner Rendering) → Phase 5 (Demo)
```

Phase 4 is off the critical path. It enhances the demo but is not required for it.

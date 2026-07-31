# BookError — Product Requirements Document

## Vision

BookError is a **causal error localizer for Jupyter notebooks** that instantly traces any runtime exception back to its true root cause — the earliest cell execution responsible — without using an LLM. It builds a live dependency graph of every cell execution and, on error, performs a millisecond-scale backward graph walk to produce a short, ordered causal chain from root cause to crash, even when cells were run out of order, re-executed, or edited after downstream cells ran.

An optional, token-efficient LLM explanation layer sits on top — but the core diagnosis is deterministic, instant, and free.

## Goals

### Hackathon Goals (18 Hours)
1. Deliver a working end-to-end demo: execute a notebook out of order → trigger an error → see the causal path instantly highlighted.
2. Demonstrate that the tool works without any LLM calls by default — the graph walk is the diagnosis.
3. Show a side-by-side comparison: BookError's tiny LLM prompt (~100 tokens) vs. a naive paste-the-traceback approach (~1000+ tokens).
4. Produce a compelling 3-minute demo that tells a clear problem → solution → "aha" story.

### Product Goals (Post-Hackathon)
1. Publish as a pip-installable JupyterLab extension.
2. Become the default debugging companion for data science notebooks.
3. Build community adoption through Jupyter ecosystem visibility.

---

## User Personas

### Priya — The Data Science Student
- **Role:** Graduate student working through ML coursework in Jupyter notebooks.
- **Environment:** JupyterLab, Python 3.10+, pandas/scikit-learn/matplotlib.
- **Pain:** Runs cells out of order constantly. Gets `KeyError`, `AttributeError`, or `NameError` exceptions and has no idea which earlier cell caused the problem. Copies the full traceback into ChatGPT and waits 10+ seconds for a generic answer.
- **Wants:** Instantly see *which earlier cell* broke things, without leaving the notebook.
- **Technical comfort:** Moderate. Comfortable with Python but not with debugging tools.

### Marco — The Senior Data Engineer
- **Role:** Data engineer building and maintaining complex ETL/analysis notebooks (50–100+ cells).
- **Environment:** JupyterLab or VS Code with Jupyter extension, Python 3.11+, heavy pandas/PySpark usage.
- **Pain:** Notebooks become stateful messes over long sessions. A `NameError` in cell 47 could trace back to an accidental overwrite in cell 12 that was re-run two hours ago. Reading the traceback gives the *what* but never the *why*.
- **Wants:** A visual dependency graph that shows the notebook's execution history, not just its cell order. One-click navigation to the causal chain.
- **Technical comfort:** High. Would appreciate deterministic, transparent tooling over black-box AI.

---

## User Stories

### Core (MVP — Hackathon)

| ID | Story | Priority |
|---|---|---|
| US-01 | As a notebook user, I want BookError to automatically track every cell execution and its variable reads/writes so that the dependency graph is built incrementally with zero manual steps. | **P0** |
| US-02 | As a notebook user, when a cell raises an exception, I want to see the causal chain (which earlier cells are responsible) appear instantly as an inline banner and ordered list. | **P0** |
| US-03 | As a notebook user, I want to click any hop in the causal chain to scroll to and highlight the responsible cell so that I can navigate the root cause without searching manually. | **P0** |
| US-04 | As a notebook user, I want the causal chain to be accurate even when I run cells out of order or re-execute cells, because the tracker uses execution history, not cell position. | **P0** |
| US-05 | As a notebook user, I want a one-line human-readable summary for each hop in the causal chain (e.g., "Cell 5 dropped column 'age' from df") so that I understand the chain without reading code. | **P0** |

### Important (Hackathon Stretch)

| ID | Story | Priority |
|---|---|---|
| US-06 | As a notebook user, I want to see a small interactive graph view of the notebook's variable dependency DAG with the causal path highlighted, because this is the most compelling visual proof of the tool's value. | **P1** |
| US-07 | As a notebook user, I want to click "Explain in plain English" to get a 2–3 sentence LLM-generated explanation of the causal chain, using minimal tokens. | **P1** |
| US-08 | As a notebook user, I want the tool to warn me when a cell's code has changed since it was last executed, so I know the displayed causal chain reflects stale code. | **P1** |

### Future

| ID | Story | Priority |
|---|---|---|
| US-09 | As a notebook user, I want to see which variables are currently "stale" (their defining cell has been edited but not re-run) so that I can proactively avoid errors. | **P2** |
| US-10 | As a notebook user, I want to export the dependency graph and causal path as a shareable artifact for code reviews or teaching. | **P2** |
| US-11 | As a notebook user, I want support for notebooks using R or Julia kernels. | **P2** |

---

## Functional Requirements

### FR-01: Execution Tracking
- Must hook into IPython's `pre_run_cell` and `post_run_cell` events to capture every cell execution.
- Must use `ast.parse` on each cell's source to extract variable names read (`ast.Load`) and written (`ast.Store`, including `for` targets, `with ... as`, function/class definitions, imports).
- Must maintain a `current_owner` dictionary mapping each variable name to the `exec_id` that last wrote it.
- Must construct dependency graph edges from producer `exec_id` to consumer `exec_id` for each variable read.
- Must capture the exception object and traceback when a cell raises an error.
- Must assign a monotonically increasing `exec_id` per cell run (not per cell identity).

### FR-02: Root-Cause Tracing
- On error, must identify the innermost traceback frame belonging to user notebook code (not library code).
- Must extract the implicated variable(s) from the failing line's AST.
- Must perform a backward graph walk from the failing `exec_id` and implicated variables to find the causal chain.
- Must collapse the raw chain into a chronologically ordered list of `CausalHop` objects.
- Must generate a one-line human-readable summary per hop using AST heuristics and a lookup table of common mutating methods.

### FR-03: Causal Path Presentation
- Must display an inline banner on the erroring cell with a compact summary and a "Show cause →" affordance.
- Must display an ordered, numbered list of causal hops, each clickable to navigate to the responsible cell.
- Each hop must show: cell identity, execution number, variable name, and one-line summary.

### FR-04: Graph Visualization (Stretch)
- Must render the notebook's variable dependency DAG as a small interactive graph.
- Must highlight the causal path in a distinct color against the greyed-out rest of the graph.
- Must be client-side rendered (no server-side graph rendering).

### FR-05: Optional LLM Explanation
- Must be user-triggered (button click), not automatic.
- Must send only the `CausalPath` object, exception type/message, and failing line to the LLM — never the full notebook or traceback.
- Must fall back to deterministic hop summaries if the LLM call fails, times out, or is disabled.
- Must use approximately 60–150 tokens regardless of notebook size.

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| **Tracking overhead** | < 5ms per cell execution (AST parse + graph edge insertion) |
| **Trace latency** | < 50ms from error to causal path displayed (graph walk + collapse) |
| **Graph accuracy** | Correct under arbitrary out-of-order execution, re-runs, and edits |
| **LLM prompt size** | 60–150 tokens for the optional explanation, regardless of notebook size |
| **Installation** | Single `pip install` + JupyterLab extension enable |
| **Privacy** | No data leaves the machine unless the user explicitly clicks "Explain" (LLM call) |
| **Compatibility** | JupyterLab 4.x, Python 3.10+ |
| **Zero configuration** | Works immediately after installation. No API keys required for core functionality. |

---

## Edge Cases

| Scenario | Expected Behavior |
|---|---|
| Variable aliasing (`df2 = df`, then mutate `df2` in-place) | Heuristic pass detects known in-place mutating call patterns (`.append()`, `.loc[...] = ...`) and treats them as writes to the aliased variable. Documented as a best-effort limitation. |
| Function-local variable shadows a global of the same name | Scope-aware AST analysis distinguishes function-local variables from notebook globals. The graph does not incorrectly link them. |
| Cell edited but not re-run | The graph reflects the *last executed* version. The UI shows a "stale code" indicator on cells whose source has changed since last execution. |
| Error occurs in library code (deep traceback) | The tracer skips library frames and finds the innermost user-code frame. If no user-code frame exists, it reports the error without a causal chain. |
| Cell uses `%%` magics or shell-outs | The cell is recorded as an opaque node (no variable reads/writes extracted). It participates in the graph timeline but is not traced into. |
| Multiple variables implicated in the error | The backward walk starts from all implicated variables simultaneously. The resulting chain includes all paths. |
| Very first cell raises an error | No causal chain (no prior executions). The inline banner simply shows the error. |
| Kernel restart mid-session | The dependency graph is cleared. A fresh graph starts from the next execution. This is documented behavior — persistence across restarts is a non-goal. |

---

## Success Criteria

### Hackathon Demo Success
1. A prepared notebook is executed out of order, triggering a `KeyError` caused by a column drop three cells earlier.
2. BookError's inline banner and causal path appear near-instantly (< 1 second visually).
3. The causal path correctly identifies the column-dropping cell as the root cause.
4. Clicking a hop in the causal path scrolls to the responsible cell.
5. The graph view (if completed) shows the highlighted causal chain.
6. The optional "Explain" button produces a ~100-token LLM call vs. a ~1000-token naive approach (shown side-by-side).
7. The entire demo completes in under 3 minutes.

### Product Success (Post-Hackathon)
1. Published as a pip-installable JupyterLab extension.
2. 500+ GitHub stars within 6 months.
3. Referenced in at least 2 Jupyter community guides or tutorials.

---

## Feature Prioritization

```
P0 (Must Have — Hackathon)          P1 (Stretch — Hackathon)             P2 (Future)
─────────────────────────           ────────────────────────             ────────────────────
• Execution tracking (Layer 1)      • Graph visualization (Layer 3+)    • Stale variable detection
• Variable read/write extraction    • LLM explanation (Layer 4)         • Graph export/sharing
• Dependency graph construction     • Stale code warnings               • Multi-kernel support (R, Julia)
• Backward causal trace (Layer 2)   • Demo polish & comparison slide    • Persistence across restarts
• Causal path UI: banner + list                                         • VS Code Jupyter integration
• Cell navigation on hop click
```

---

## Constraints

- **Time:** 18-hour hackathon. Every feature must justify its inclusion against the demo deadline.
- **Team size:** Small team (1–3 developers). The system is designed as a single Python package + JupyterLab extension.
- **Python only:** The MVP traces only Python IPython kernels. No R, Julia, or polyglot support.
- **No persistence:** The dependency graph lives in kernel-process memory. It is lost on kernel restart.
- **No auto-fix:** BookError diagnoses problems. It does not suggest or apply code fixes.
- **LLM is optional:** The tool must be fully functional with zero LLM calls and zero API keys.

---

## Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| AST-based read/write extraction misses edge cases (decorators, comprehensions, walrus operator) | Medium | Medium | Start with the common cases (simple assignment, function calls, imports). Document known gaps. Iterate post-hackathon. |
| In-place mutation detection (aliasing) produces false positives or negatives | High | Medium | Use a conservative heuristic: only flag known pandas/numpy mutating methods. Accept false negatives over false positives. |
| JupyterLab extension development is slow (TypeScript + build tooling) | High | High | **Mitigation: start with a pure-Python IPython extension that outputs to cell output areas.** Build the full JupyterLab panel as a stretch goal. This ensures a working demo even without TypeScript. |
| Scope confusion (function locals vs. globals) produces wrong causal chains | Medium | High | Focus on top-level (global scope) variables first. Function-internal variables are treated as opaque. |
| Demo notebook doesn't produce a visually compelling causal chain | Low | High | Prepare 2–3 demo notebooks with scripted out-of-order execution patterns. Test each before the demo. |
| 18-hour time pressure causes critical bugs in the demo path | High | High | Feature freeze at hour 16. Only bug fixes after that. Rehearse the demo at least 3 times. |

---

## Future Roadmap

### Phase 1: Post-Hackathon Polish (Weeks 1–2)
- Full JupyterLab extension with proper panel UI (if not completed during hackathon).
- Improved AST analysis (comprehensions, walrus operator, augmented assignments).
- Stale variable detection and warnings.
- pip packaging and PyPI release.

### Phase 2: Depth (Weeks 3–6)
- Scope-aware analysis (function locals vs. globals with proper nesting).
- In-place mutation tracking via shallow value snapshots.
- Interactive graph exploration (hover to see variable flow, click to filter).
- Session persistence (save/load dependency graphs).

### Phase 3: Ecosystem (Months 2–3)
- VS Code Jupyter extension support.
- Google Colab compatibility layer.
- Export causal paths as shareable HTML/Markdown reports.
- Community launch and documentation site.

### Phase 4: Growth (Months 3–6)
- Multi-kernel support (R, Julia).
- Collaborative notebook debugging (shared causal paths).
- Integration with notebook version control tools.
- Proactive error prediction ("this cell is likely to fail because...").

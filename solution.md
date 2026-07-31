# solution.md

## Notebook-Aware Error Localizer — Technical Solution Document

**Status:** Hackathon build target
**Scope:** Jupyter notebooks only (single kernel, Python)
**Companion document:** `Notebook-Aware-Debugging-Assistant-Reference.docx` (idea history, rationale, positioning)

This document describes *how* the system is actually built: architecture, data model, algorithms, interfaces, and the build plan. Where the reference doc explains *why* we're building this and *why it's different*, this document explains *what code we're writing*.

---

## 1. Problem Statement (Restated for Engineering)

Given a Jupyter notebook where cells may be executed out of order, re-executed, or edited after downstream cells already ran, and given that a cell has just raised an exception:

**Find the earliest cell execution that is causally responsible for the failure, and produce a short ordered chain of (cell, variable, what happened) linking that cell to the crash — without using an LLM for this step.**

Optionally, hand that chain (and only that chain) to an LLM to phrase a one- or two-sentence plain-language explanation.

---

## 2. System Overview

Three layers, each independently testable:

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Presentation                                      │
│  Jupyter extension UI: causal-path highlight + graph view    │
└───────────────────────────▲───────────────────────────────────┘
                             │ causal path (list of nodes)
┌───────────────────────────┴───────────────────────────────────┐
│  Layer 2 — Root-Cause Tracer                                  │
│  Backward graph walk from the failing node                    │
└───────────────────────────▲───────────────────────────────────┘
                             │ dependency graph (live, in-memory)
┌───────────────────────────┴───────────────────────────────────┐
│  Layer 1 — Execution Tracker                                  │
│  IPython hooks that record cell runs, variable reads/writes   │
└─────────────────────────────────────────────────────────────┘
```

An optional **Layer 4 — Explanation** sits beside Layer 3 and calls an LLM with only the causal path as input. It is decoupled from Layers 1–2 and can be disabled without affecting core functionality.

---

## 3. Layer 1 — Execution Tracker

### 3.1 Goal

Build and continuously update a record of "what ran, in what order, reading what, writing what" — cheaply enough to run on every single cell execution with no perceptible slowdown.

### 3.2 Mechanism

IPython/Jupyter exposes hook points we use instead of parsing notebook files after the fact:

- `pre_run_cell` / `post_run_cell` events (via `IPython.get_ipython().events`) — fire before/after each cell executes, giving us the cell's source code and execution count.
- `ast.parse` on the cell's source to statically extract:
  - **Names read** (`ast.Load` context) — candidate inputs.
  - **Names written** (`ast.Store` context, including `for` targets, `with ... as`, function defs, class defs, imports) — outputs.
  - **Function/class definitions and imports** introduced by this cell.
- Cross-reference read names against the *current* global namespace snapshot (via `get_ipython().user_ns`) to resolve which prior execution last wrote each name — this is what makes the graph accurate even under out-of-order execution, since we always bind to the variable's *actual current source*, not its textual position in the notebook.
- On `post_run_cell`, if the run raised an exception, capture the traceback object directly from the event (`result.error_in_exec`) — we get the real exception, not a re-parsed string.

### 3.3 Data Recorded Per Execution

```python
ExecutionRecord = {
  "exec_id": int,          # monotonically increasing, one per cell run (not per cell!)
  "cell_id": str,           # stable Jupyter cell id, persists across edits/re-runs
  "timestamp": float,
  "source": str,             # exact code that ran
  "reads": set[str],         # variable names read
  "writes": set[str],        # variable names written/defined
  "defines": set[str],       # functions/classes/imports newly introduced
  "raised": Optional[ExceptionInfo],
}
```

Note the distinction between `cell_id` (identity of the cell in the notebook UI) and `exec_id` (identity of one specific run of that cell). A cell can have many `exec_id`s over a session; the graph is built over `exec_id`s, which is what correctly captures re-runs and edits.

### 3.4 Variable Version Table

To resolve "which execution currently owns this variable's value," we maintain:

```python
current_owner: dict[str, int]   # variable name -> exec_id that last wrote it
```

Updated after every `post_run_cell`. This is an O(1) lookup used constantly by both Layer 1 (to build edges) and Layer 2 (to start the backward walk).

### 3.5 Edge Construction

For each execution record `E`, for each name `n` in `E.reads`:

```
if n in current_owner (before E ran):
    add edge:  current_owner[n]  --provides(n)-->  E.exec_id
```

After processing all reads, update `current_owner` with `E.writes`.

This produces a **directed acyclic graph** (DAG) — acyclic because `exec_id`s are monotonically increasing and edges only point from earlier to later executions.

### 3.6 Why This Step Doesn't Need an LLM

Everything above is AST parsing + dictionary lookups + graph edge insertion. On typical notebook cell sizes (a few to a few dozen lines), this completes in low single-digit milliseconds. It runs opportunistically on every cell execution, so by the time an error occurs, the graph is already built — there is no "analyze everything now" step at failure time.

---

## 4. Layer 2 — Root-Cause Tracer

### 4.1 Trigger

Fires from the `post_run_cell` handler when `result.error_in_exec` is not `None`.

### 4.2 Step 1: Identify the Failure Frame

Walk the exception's traceback (`exc.__traceback__`) to find the **innermost frame that belongs to user notebook code** (i.e., its filename matches the IPython cell-execution pattern, not a site-packages/library path). This is the "true" failure point from the user's perspective — we deliberately skip past library-internal frames, the same frames that make raw tracebacks intimidating.

### 4.3 Step 2: Extract Implicated Variables

From that frame's locals and the failing line's AST, extract the variable name(s) directly involved in the exception (e.g., the object `.fit()` was called on; the key that raised `KeyError`; the index that went out of range). This is a small, targeted AST inspection of just the failing line, not the whole cell.

### 4.4 Step 3: Backward Walk

Starting from the failing `exec_id` and its implicated variable(s), perform a **reverse graph traversal**:

```python
def trace_back(graph, failing_exec_id, implicated_vars):
    frontier = [(failing_exec_id, v) for v in implicated_vars]
    visited = set()
    chain = []

    while frontier:
        exec_id, var = frontier.pop()
        if (exec_id, var) in visited:
            continue
        visited.add((exec_id, var))

        producer = graph.edge_source(exec_id, var)   # who last wrote `var` before exec_id ran
        if producer is None:
            break   # bottomed out — var came from outside tracked scope (e.g., a raw literal)

        chain.append(producer)
        # follow the producer's own reads backward too, one hop,
        # to catch compounding causes (e.g. df in cell 5 depended on df in cell 2)
        for upstream_var in producer.reads:
            frontier.append((producer.exec_id, upstream_var))

    return order_chronologically(chain)
```

This is a bounded reverse BFS/DFS over an already-in-memory DAG with, realistically, a few hundred nodes at most for a typical notebook session — a millisecond-scale operation with no external calls.

### 4.5 Step 4: Collapse Into a Causal Path

The raw chain from Step 3 is de-duplicated, sorted chronologically, and collapsed into a small ordered list of "hops":

```python
CausalHop = {
  "cell_id": str,
  "exec_id": int,
  "summary": str,      # e.g. "defined df" / "dropped column 'age' from df" / "reassigned df"
  "variable": str,
}
```

The `summary` field is generated with simple heuristics on the AST diff of what changed for that variable (assignment vs. attribute mutation vs. in-place method call like `.drop()`, `.fillna()`, etc.) — **not** an LLM call. A small lookup table of common pandas/numpy/sklearn mutating methods (`drop`, `dropna`, `fillna`, `astype`, `reset_index`, `merge`, `concat`, `iloc`/`loc` assignment, etc.) is used to produce a readable one-line summary per hop. This keeps Layer 2 fully deterministic.

### 4.6 Output of Layer 2

```python
CausalPath = {
  "failure": { "exec_id": int, "cell_id": str, "exception_type": str, "exception_msg": str, "line": str },
  "hops": list[CausalHop],   # chronological, earliest cause first
}
```

This object is the single artifact passed to Layers 3 and 4. It is small — typically 2 to 6 hops — regardless of how large the notebook or how long the traceback was.

---

## 5. Layer 3 — Presentation

### 5.1 Jupyter Integration

Delivered as a JupyterLab extension (frontend: TypeScript/React panel; backend: a small Python kernel-side extension registering the IPython event hooks from Layer 1).

### 5.2 Views

- **Inline highlight:** on error, the offending cell is annotated with a compact banner: the one-line plain-language summary plus a "Show cause →" affordance.
- **Causal path panel:** an ordered, numbered list of hops (`Cell 2 → Cell 5 → Cell 9`), each clickable to scroll to and highlight that cell.
- **Graph view (stretch goal):** a small force-directed or layered graph (rendered client-side, e.g., with D3 or a lightweight canvas renderer) showing the notebook's variable dependency graph with the causal path highlighted in a distinct color against the greyed-out rest of the graph. This is the single most demo-friendly artifact — it's the visual proof that the tool "sees" the notebook's history, not just the current error.

### 5.3 Design Constraint

All Layer 3 rendering operates only on the `CausalPath` object — it never re-parses the notebook or talks to the kernel directly, keeping the UI layer simple and decoupled.

---

## 6. Layer 4 — Optional LLM Explanation

### 6.1 Trigger

User-initiated (a button: "Explain in plain English"), not automatic — this keeps token spend opt-in and visible.

### 6.2 Prompt Construction

The prompt sent to the LLM contains **only**:
- The `CausalPath` object (hops + summaries), not the full notebook.
- The exception type and message.
- The single failing line of code.

It explicitly excludes: the full traceback, unrelated cells, library source, and any notebook content not on the causal path.

### 6.3 Example Prompt Shape

```
A Jupyter notebook raised an error. Here is the causal chain that led to it,
already identified by static analysis — do not re-diagnose, just explain it
plainly in 2-3 sentences for a student:

1. Cell 2 defined `df` from pd.read_csv(...)
2. Cell 5 dropped column 'age' from `df` (df = df.drop(columns=['age']))
3. Cell 9 crashed calling df[['age','income']] — KeyError: 'age'

Explain what went wrong and what the student should look at, in plain language.
```

### 6.4 Token Footprint

This prompt is typically 60–150 tokens regardless of notebook size, versus a naive approach of pasting a full traceback (which can run 500–2000+ tokens on library-heavy errors, e.g. deep pandas/sklearn stacks) or an entire notebook file. This is the concrete, measurable claim for the demo (see Section 9.3).

### 6.5 Failure Mode Handling

If the LLM call fails, times out, or is disabled, Layer 3 falls back to the deterministic `summary` strings already generated in Layer 2 (Section 4.5). The tool is fully functional with zero LLM calls — this is a deliberate design property, not a fallback bolted on afterward.

---

## 7. Data Model Summary

```
Notebook Session
 ├── ExecutionRecord[]      (Layer 1 output, append-only log)
 ├── current_owner: dict     (Layer 1, mutable index)
 ├── DependencyGraph         (Layer 1, derived, in-memory DAG)
 │      nodes = exec_ids
 │      edges = "provides(var)" from producer exec_id -> consumer exec_id
 └── CausalPath              (Layer 2 output, produced on-demand per error)
        hops: CausalHop[]
```

Nothing here requires persistent storage for the MVP — the graph lives in kernel-process memory for the session. (Persisting across kernel restarts is explicitly out of scope; see Section 10.)

---

## 8. Tech Stack

| Component | Choice | Why |
|---|---|---|
| Kernel-side hooks | Python, IPython `events` API | Native hook points, no notebook file re-parsing needed |
| Static analysis | Python `ast` module | Zero dependencies, fast, sufficient for read/write extraction |
| Graph structure | Plain Python dict/adjacency lists (or `networkx` if time allows) | Graph is small (hundreds of nodes); no need for a graph database |
| Frontend | JupyterLab extension API + React/TypeScript | Standard way to add panels/highlights to JupyterLab |
| Graph visualization | D3.js or a lightweight canvas library | Client-side rendering of a small DAG |
| Optional LLM | Anthropic API (Claude), single `/v1/messages` call | Only for Layer 4; swappable/mockable |
| Packaging | `pip`-installable JupyterLab extension (`jupyter labextension`) | Standard distribution path for the demo |

---

## 9. Demo Plan

### 9.1 Scripted Bug Scenarios

Prepare 2–3 realistic, pre-written notebooks that reliably reproduce an "invisible earlier cause" bug when run in a specific out-of-order sequence, e.g.:

1. Define `df`, drop a column three cells later, then re-run an *earlier* cell that references the dropped column — `KeyError`.
2. Overwrite a model variable name in a later cell with an unrelated value, then call `.predict()` on it from an earlier-numbered cell run afterward — `AttributeError`.

### 9.2 Live Demo Flow

1. Run the notebook live, out of order, in front of judges.
2. Trigger the error live (not pre-recorded).
3. Show the inline banner and causal path panel appearing near-instantly.
4. Click into the graph view to show the highlighted causal chain.
5. Click "Explain in plain English" to show the optional LLM step.

### 9.3 Concrete Comparison to Show On Stage

Side-by-side panel or slide: naive-approach token count (full traceback + surrounding cells, pasted into a generic chat prompt) vs. this tool's prompt token count (Section 6.4), plus a visible timer comparing "time to locate cause" (near-instant, graph walk) vs. "time to get an answer" (multi-second LLM round trip) for a plain copy-paste-into-chat baseline.

---

## 10. Explicit Non-Goals for This Build

- No multi-file / multi-notebook project support.
- No support for notebook kernels other than Python (no R, Julia, etc.).
- No persistence of the dependency graph across kernel restarts.
- No auto-fix or auto-remediation of the bug — diagnosis only.
- No confidence scoring — the causal path is reported as a deterministic fact of the execution history, not a probabilistic guess.
- No attempt to handle notebooks with heavy use of `%%` magics, shell-outs, or non-Python cells in the traced graph (they are recorded as opaque nodes, not traced into).

---

## 11. Build Order (Priority for Limited Time)

1. **Layer 1 core** (execution tracking + graph construction) — highest priority, hardest, most novel.
2. **Layer 2 core** (backward trace + collapse into causal path) — second priority, depends entirely on Layer 1's correctness.
3. **Layer 3 minimal** (inline banner + simple text causal path list) — needed for any demo at all.
4. **Layer 3 stretch** (graph visualization) — high demo value, build if time remains.
5. **Layer 4** (LLM explanation) — lowest priority; the tool must be demoable with this fully disabled.

---

## 12. Open Engineering Risks

- **Aliasing:** if a variable is aliased (`df2 = df`) and only `df2` is later mutated in place, does the graph correctly show `df`'s value also changed? Mutation of mutable objects (e.g., in-place `.append()`, `.loc[...] = ...`) is read-as-write in effect but not syntactically a `Store` — needs a heuristic pass (watch for known in-place-mutating call patterns) rather than pure AST read/write classification.
- **Shadowing across scopes:** function-local variables vs. notebook globals need to be kept distinct so the graph doesn't wrongly link an internal function variable to a global of the same name.
- **Cell edits without re-run:** if a user edits a cell's *source* but doesn't re-run it, the graph should still reflect the *last executed* version of that cell, not the currently displayed text — this must be surfaced clearly in the UI (e.g., "this cell's code has changed since it last ran") to avoid confusing the causal path.

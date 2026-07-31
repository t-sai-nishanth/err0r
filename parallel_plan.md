# BookError — Parallel Work Plan (3 Members)

## Core Strategy: Interface-First, Integrate Later

The key to parallel work is **defining shared data models upfront** so each person builds against agreed contracts, not against each other's code. Each member owns a distinct set of files. Nobody edits anyone else's files until integration.

```
Hour  0     1     3           6           9          12         15         18
      │─────│─────│───────────│───────────│──────────│──────────│──────────│
      Setup │     ──── Parallel Build ────│── Sync ──│── Sync ──│──────────│
      +     │     A: Tracker (Layer 1)    │  Integ.  │  Integ.  │  Demo &  │
      Models│     B: Tracer  (Layer 2)    │  Round 1 │  Round 2 │  Polish  │
            │     C: Display (Layer 3)    │          │          │          │
```

---

## Hour 0–1: Team Setup (All 3 Together — 1 Hour)

> **Do this together on one call before splitting off. This is the most important hour.**

### Tasks (One Person Drives, All Agree)

- [ ] Create the Git repo and push the initial structure.
- [ ] Create **all shared data models** in `bookerrror/models.py` (see Section below).
- [ ] Create **all mock/fixture data** in `tests/fixtures/sample_data.py`.
- [ ] Create skeleton files with empty functions for every module (just signatures + `pass`).
- [ ] Each person clones the repo on their own machine.
- [ ] Each person verifies `%load_ext bookerrror` loads without errors (even if it does nothing).

### The Shared Models File (Critical)

This is the **contract** between all three workstreams. Define it together, commit it, and don't change it without telling everyone.

```python
# bookerrror/models.py — SHARED, DO NOT EDIT WITHOUT TEAM AGREEMENT

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class ExecutionRecord:
    exec_id: int
    cell_id: str
    timestamp: float
    source: str
    reads: set[str] = field(default_factory=set)
    writes: set[str] = field(default_factory=set)
    defines: set[str] = field(default_factory=set)
    raised: Optional['ExceptionInfo'] = None

@dataclass
class ExceptionInfo:
    exc_type: str
    exc_message: str
    failing_line: str
    frame_filename: str
    frame_lineno: int

@dataclass
class Edge:
    producer_exec_id: int
    consumer_exec_id: int
    variable: str

@dataclass
class CausalHop:
    cell_id: str
    exec_id: int
    variable: str
    summary: str
    source_snippet: str
    role: str  # "root_cause" | "intermediate" | "failure"

@dataclass
class CausalPath:
    failure: 'FailureInfo'
    hops: list[CausalHop] = field(default_factory=list)

@dataclass
class FailureInfo:
    cell_id: str
    exec_id: int
    exc_type: str
    exc_message: str
    failing_line: str
```

### The Mock Data File (Critical)

Each person uses these mocks to test their component independently:

```python
# tests/fixtures/sample_data.py

from bookerrror.models import *
import time

# --- Mock Graph Data (for Person B to test tracer) ---
MOCK_RECORDS = [
    ExecutionRecord(exec_id=0, cell_id="cell-1", timestamp=time.time(),
        source="import pandas as pd", reads=set(), writes=set(), defines={"pd"}),
    ExecutionRecord(exec_id=1, cell_id="cell-2", timestamp=time.time(),
        source="df = pd.read_csv('data.csv')", reads={"pd"}, writes={"df"}, defines=set()),
    ExecutionRecord(exec_id=2, cell_id="cell-5", timestamp=time.time(),
        source="df = df.drop(columns=['age'])", reads={"df"}, writes={"df"}, defines=set()),
    ExecutionRecord(exec_id=3, cell_id="cell-9", timestamp=time.time(),
        source="result = df[['age', 'income']]", reads={"df"}, writes={"result"}, defines=set(),
        raised=ExceptionInfo(exc_type="KeyError", exc_message="'age'",
            failing_line="result = df[['age', 'income']]",
            frame_filename="<ipython-input-9>", frame_lineno=1)),
]

MOCK_EDGES = [
    Edge(producer_exec_id=0, consumer_exec_id=1, variable="pd"),
    Edge(producer_exec_id=1, consumer_exec_id=2, variable="df"),
    Edge(producer_exec_id=2, consumer_exec_id=3, variable="df"),
]

# --- Mock CausalPath (for Person C to test display) ---
MOCK_CAUSAL_PATH = CausalPath(
    failure=FailureInfo(cell_id="cell-9", exec_id=3, exc_type="KeyError",
        exc_message="'age'", failing_line="result = df[['age', 'income']]"),
    hops=[
        CausalHop(cell_id="cell-2", exec_id=1, variable="df",
            summary="defined df from pd.read_csv('data.csv')",
            source_snippet="df = pd.read_csv('data.csv')", role="root_cause"),
        CausalHop(cell_id="cell-5", exec_id=2, variable="df",
            summary="dropped column 'age' from df",
            source_snippet="df = df.drop(columns=['age'])", role="intermediate"),
        CausalHop(cell_id="cell-9", exec_id=3, variable="df",
            summary="accessed column 'age' on df",
            source_snippet="result = df[['age', 'income']]", role="failure"),
    ],
)
```

---

## File Ownership Map

> **Rule: You only edit files in your column. Period.**

| Person A (Tracker) | Person B (Tracer) | Person C (Display + Demo) |
|---|---|---|
| `bookerrror/__init__.py` | `bookerrror/tracer/__init__.py` | `bookerrror/presentation/__init__.py` |
| `bookerrror/extension.py` | `bookerrror/tracer/frame_walker.py` | `bookerrror/presentation/banner.py` |
| `bookerrror/tracker/__init__.py` | `bookerrror/tracer/var_extractor.py` | `bookerrror/presentation/path_display.py` |
| `bookerrror/tracker/hooks.py` | `bookerrror/tracer/graph_walker.py` | `bookerrror/presentation/graph_widget.py` |
| `bookerrror/tracker/ast_analyzer.py` | `bookerrror/tracer/collapser.py` | `bookerrror/llm/__init__.py` |
| `bookerrror/tracker/version_table.py` | `bookerrror/tracer/summarizer.py` | `bookerrror/llm/prompt_builder.py` |
| `bookerrror/tracker/graph.py` | `bookerrror/tracer/models.py` *(local helpers only)* | `bookerrror/llm/client.py` |
| `bookerrror/tracker/models.py` *(local helpers only)* | `tests/test_graph_walker.py` | `bookerrror/llm/config.py` |
| `bookerrror/utils/constants.py` | `tests/test_collapser.py` | `demo/demo_keyerror.ipynb` |
| `bookerrror/utils/ipython_helpers.py` | `tests/test_summarizer.py` | `demo/demo_attributeerror.ipynb` |
| `tests/test_ast_analyzer.py` | `tests/test_var_extractor.py` | `demo/data.csv` |
| `tests/test_graph.py` | | `README.md` |
| `pyproject.toml` | | |

### Shared Files (Edit Only During Sync Points)

| File | Owner | Rule |
|---|---|---|
| `bookerrror/models.py` | All (agreed in Hour 0) | **No edits without team agreement.** If you need a new field, message the group first. |
| `tests/fixtures/sample_data.py` | All | Add your own fixtures, don't modify existing ones. |
| `.gitignore` | Person A | Initial setup only. |

---

## Person A: Tracker Engineer (Layer 1)

### What You Build
The execution tracker — IPython hooks, AST analyzer, dependency graph. This is the foundation that makes everything else possible.

### Hour-by-Hour Plan

| Hours | Task | Output |
|---|---|---|
| 0–1 | Team setup (shared models, repo, skeleton files) | Repo ready, all 3 can start |
| 1–4 | **AST Analyzer**: `ast.parse()` → extract reads, writes, defines. Handle assignments, for-loops, imports, function/class defs, known mutating methods. Filter builtins. | `ast_analyzer.py` with `analyze_cell(source: str) -> tuple[set[str], set[str], set[str]]` |
| 4–6 | **Graph Construction**: `DependencyGraph` class. `record_execution()` builds edges from `current_owner`. Variable version table. | `graph.py`, `version_table.py` working and tested |
| 6–8 | **IPython Hooks**: `pre_run_cell` / `post_run_cell` handlers. Wire AST analyzer + graph construction into the hooks. Extract cell_id from Jupyter metadata. | `hooks.py`, `extension.py` — `%load_ext bookerrror` tracks cells |
| 8–9 | **Testing + Debug Tools**: `%bookerrror_debug` magic command to print graph state. Manual testing in a notebook. | Verified: cells build graph correctly |
| 9 | 🔄 **SYNC POINT 1**: Push code, pull Person B's tracer, wire Layer 1 → Layer 2 | Integrated tracker + tracer |
| 9–11 | **Integration work**: Help wire tracker output into Person B's tracer. Fix data model mismatches. | Layer 1 → Layer 2 pipeline working |
| 12 | 🔄 **SYNC POINT 2**: Pull Person C's display, wire Layer 2 → Layer 3 | Full pipeline working |
| 12–15 | **Edge cases + hardening**: Improve AST analysis (augmented assignments, tuple unpacking, comprehension vars). Fix bugs found during integration. | Robust tracker |
| 15–18 | **Demo & polish**: Help with demo prep, fix bugs, rehearse | Ready for demo |

### Your Key Deliverable
A function that, given a cell's source code and the current graph state, produces an updated graph with correct edges — even when cells are run out of order.

### Testing Without Others
```python
# You can test your tracker standalone:
from bookerrror.tracker.ast_analyzer import analyze_cell
from bookerrror.tracker.graph import DependencyGraph

graph = DependencyGraph()

# Simulate cell executions
reads, writes, defines = analyze_cell("df = pd.read_csv('data.csv')")
graph.record_execution(cell_id="cell-1", source="...", reads=reads, writes=writes, defines=defines)

reads, writes, defines = analyze_cell("df = df.drop(columns=['age'])")
graph.record_execution(cell_id="cell-2", source="...", reads=reads, writes=writes, defines=defines)

# Verify edges
print(graph.edges)  # Should show: Edge(0 → 1, variable="df")
print(graph.current_owner)  # Should show: {"df": 1, "pd": 0}
```

---

## Person B: Tracer Engineer (Layer 2)

### What You Build
The root-cause tracer — traceback frame walking, variable extraction, backward graph walk, causal path collapse, and hop summarizer. You take the graph Person A built and turn errors into causal chains.

### Hour-by-Hour Plan

| Hours | Task | Output |
|---|---|---|
| 0–1 | Team setup (shared models, repo, skeleton files) | Repo ready, all 3 can start |
| 1–3 | **Frame Walker**: Walk `exc.__traceback__` to find the innermost user-code frame. Detect IPython cell filenames. Return `FrameInfo`. | `frame_walker.py` tested with synthetic exceptions |
| 3–5 | **Variable Extractor**: AST-parse the failing line. Extract variables by exception type (KeyError → subscript object, AttributeError → accessed object, NameError → the name itself, generic fallback). | `var_extractor.py` tested with common error patterns |
| 5–7 | **Backward Graph Walker**: Reverse BFS from failing `exec_id` + implicated variables. Follow producer edges backward. Return raw chain. | `graph_walker.py` tested with `MOCK_RECORDS` + `MOCK_EDGES` |
| 7–8 | **Collapser + Summarizer**: De-duplicate, sort chronologically, generate one-line summaries via AST heuristics + method lookup table. | `collapser.py`, `summarizer.py` tested |
| 8–9 | **Wire it together**: Create `trace_error(graph, exception) -> CausalPath` function that chains all components. | `tracer/__init__.py` with the main `trace_error()` function |
| 9 | 🔄 **SYNC POINT 1**: Push code, pull Person A's tracker, wire Layer 1 → Layer 2 | Integrated tracker + tracer |
| 9–11 | **Integration testing**: Test with real graph data from Person A's tracker. Fix edge cases. | Verified: real exceptions produce correct causal paths |
| 12 | 🔄 **SYNC POINT 2**: Full integration with Person C's display | Full pipeline working |
| 12–15 | **Improve summarizer**: Better summaries for pandas operations, sklearn calls. Handle edge cases from real testing. Depth-limit the walk to prevent absurdly long chains. | Polished summaries |
| 15–18 | **Demo & polish**: Help with demo prep, fix bugs, rehearse | Ready for demo |

### Your Key Deliverable
A function `trace_error(graph, exception) -> CausalPath` that takes the dependency graph and an exception, and returns a clean, ordered causal chain with human-readable summaries.

### Testing Without Others
```python
# You can test your tracer using mock data — no need for Person A's code:
from bookerrror.tracer.graph_walker import trace_back
from tests.fixtures.sample_data import MOCK_RECORDS, MOCK_EDGES

# Build a mock graph interface
class MockGraph:
    def __init__(self, records, edges):
        self.records = {r.exec_id: r for r in records}
        self.edges = edges

    def get_edges_to(self, exec_id):
        return [e for e in self.edges if e.consumer_exec_id == exec_id]

    def get_record(self, exec_id):
        return self.records.get(exec_id)

graph = MockGraph(MOCK_RECORDS, MOCK_EDGES)

# Test backward walk
chain = trace_back(graph, failing_exec_id=3, implicated_vars={"df"})
print(chain)  # Should trace back: exec_id 3 → 2 → 1
```

> **Important:** Build against the `MockGraph` interface. When Person A's real `DependencyGraph` class is ready, it just needs to implement the same `get_edges_to()` and `get_record()` methods. Agree on this interface in Hour 0.

---

## Person C: Display + Demo Engineer (Layer 3 + Layer 4 + Demo)

### What You Build
Everything the user sees — the HTML banner, hop cards, cell navigation, LLM integration, and the demo notebooks. You make the demo look impressive.

### Hour-by-Hour Plan

| Hours | Task | Output |
|---|---|---|
| 0–1 | Team setup (shared models, repo, skeleton files) | Repo ready, all 3 can start |
| 1–4 | **Banner + Hop Cards**: Build the HTML/CSS renderer. Banner header, hop cards with role colors (🟠🔵🔴), variable arrows, code snippets. All CSS inline. Test with `MOCK_CAUSAL_PATH`. | `banner.py` renders a styled HTML banner in a notebook |
| 4–6 | **Cell Navigation**: JavaScript embedded in HTML to scroll to target cells on "Go →" click. Cell highlight animation (background flash). Test in JupyterLab. | Clicking "Go →" scrolls to and highlights the target cell |
| 6–8 | **"No chain" fallback + Error states**: Render for untraceable errors. Handle empty chains, missing cell IDs. | Robust display for all edge cases |
| 8–9 | **Polish styling**: Dark theme, light theme compatibility. Animation timing. Visual hierarchy. | Professional-looking output |
| 9 | 🔄 **SYNC POINT 1**: Push code, pull A+B's code, help wire Layer 2 → Layer 3 | Display connected to real tracer |
| 9–11 | **Demo Notebooks**: Write 2 demo notebooks (KeyError, AttributeError). Create sample CSV data. Write execution instructions. | `demo/` folder with working demos |
| 11–12 | **LLM Integration** (if time): Prompt builder, API client, "Explain" button. Or skip if tight on time. | Optional LLM explanation working |
| 12 | 🔄 **SYNC POINT 2**: Full integration test with all 3 layers | Full pipeline with display working |
| 12–15 | **Graph Visualization** (stretch): Simple SVG dependency graph with causal path highlighted. Or focus on demo polish. | Optional graph view OR more polish |
| 15–18 | **Demo script + README + rehearsal**: Write the 3-minute demo script. Create README. Rehearse with team. Prepare comparison slide (100 tokens vs 1000 tokens). | Demo-ready |

### Your Key Deliverable
A function `render_causal_path(path: CausalPath)` that calls `display(HTML(...))` and produces a beautiful, interactive causal chain in the notebook output.

### Testing Without Others
```python
# You can test your display using mock data — no need for Person A or B's code:
from bookerrror.presentation.banner import render_causal_path
from tests.fixtures.sample_data import MOCK_CAUSAL_PATH

# In a Jupyter notebook:
render_causal_path(MOCK_CAUSAL_PATH)
# → Should display a styled HTML banner with hop cards
```

> **You are the most independent workstream.** Your input is a `CausalPath` object. You can build and test your entire display using the mock data from Hour 0 without waiting for anyone.

---

## Sync Points (Critical Meetings)

### 🔄 Sync Point 1 — Hour 9 (30–60 minutes)

**Goal:** Connect Layer 1 → Layer 2.

| Who | Does What |
|---|---|
| Person A | Pushes tracker code. Confirms `DependencyGraph` implements `get_edges_to()` and `get_record()`. |
| Person B | Pulls, swaps `MockGraph` for real `DependencyGraph`. Tests `trace_error()` with real graph. |
| Person C | Pushes display code. Starts pulling B's tracer output format to verify compatibility. |
| All | Run a quick end-to-end test: load extension → run 3 cells → trigger error → print CausalPath. Fix any interface mismatches. |

**Merge strategy:** Everyone pushes to their own branch (`feat/tracker`, `feat/tracer`, `feat/display`). Person A merges all into `main` at this sync point.

### 🔄 Sync Point 2 — Hour 12 (30–60 minutes)

**Goal:** Connect the full pipeline: Layer 1 → Layer 2 → Layer 3. Get the demo working end-to-end.

| Who | Does What |
|---|---|
| Person A | Wires `post_run_cell` to call Person B's `trace_error()` on exception, then call Person C's `render_causal_path()`. |
| Person B | Verifies causal paths are correct for the demo scenarios. |
| Person C | Verifies the display renders correctly with real CausalPath data. Tests cell navigation. |
| All | Run the full demo notebook end-to-end. Fix bugs together. |

**After this sync:** The MVP is working. Everyone can see the causal chain appear when an error occurs.

### Hour 15–18: All Together

The last 3 hours are team time. Everyone works on:
- Bug fixes.
- Demo rehearsal (at least 3 full run-throughs).
- README and presentation prep.
- **No new features after hour 16.**

---

## Interface Contracts

These are the function signatures that connect the three workstreams. Agree on these in Hour 0.

### Person A provides → Person B consumes

```python
# bookerrror/tracker/graph.py (Person A writes this)

class DependencyGraph:
    def get_edges_to(self, exec_id: int) -> list[Edge]:
        """Return all edges where consumer_exec_id == exec_id."""
        ...

    def get_record(self, exec_id: int) -> ExecutionRecord | None:
        """Return the ExecutionRecord for a given exec_id."""
        ...

    def get_latest_record(self) -> ExecutionRecord | None:
        """Return the most recent ExecutionRecord (the one that just ran)."""
        ...

    def get_all_records(self) -> list[ExecutionRecord]:
        """Return all execution records in chronological order."""
        ...

    def get_all_edges(self) -> list[Edge]:
        """Return all edges."""
        ...
```

### Person B provides → Person A + C consume

```python
# bookerrror/tracer/__init__.py (Person B writes this)

def trace_error(
    graph: DependencyGraph,
    exception: BaseException,
    exec_id: int,
) -> CausalPath | None:
    """
    Given the dependency graph, an exception, and the exec_id of the
    failing cell, return the CausalPath or None if untraceable.
    """
    ...
```

### Person C provides → Person A consumes

```python
# bookerrror/presentation/__init__.py (Person C writes this)

def render_causal_path(path: CausalPath) -> None:
    """Render the causal path as HTML in the current cell output."""
    ...

def render_no_chain(exc_type: str, exc_message: str) -> None:
    """Render the fallback display when no causal chain is found."""
    ...
```

### Person A wires it all together

```python
# bookerrror/tracker/hooks.py (Person A writes this, uses B+C's code)

def post_run_cell(self, result):
    try:
        # ... record execution in graph ...

        if result.error_in_exec:
            exception = result.error_in_exec
            exec_id = self.graph.get_latest_record().exec_id

            # Call Person B's tracer
            path = trace_error(self.graph, exception, exec_id)

            # Call Person C's display
            if path and path.hops:
                render_causal_path(path)
            else:
                render_no_chain(type(exception).__name__, str(exception))
    except Exception as e:
        logging.getLogger('bookerrror').error(f"BookError: {e}", exc_info=True)
```

---

## Git Workflow

### Branches

```
main                    ← always working, merge here at sync points
├── feat/tracker        ← Person A works here
├── feat/tracer         ← Person B works here
└── feat/display        ← Person C works here
```

### Rules

1. **Never push directly to `main`** except during sync points.
2. **Commit frequently** to your own branch (every 30–60 minutes).
3. **Push to your branch** before each sync point so others can pull.
4. **Person A merges** all branches into `main` at sync points (they own `extension.py` where everything connects).
5. **If you need to change `models.py`** (the shared contract), message the group chat first. Don't surprise anyone.

### Conflict Prevention

- Each person only edits files in their column of the ownership table.
- The only file that all three touch is `models.py`, and it's frozen after Hour 1.
- `extension.py` and `hooks.py` are owned by Person A, who does the final wiring.

---

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Person A's tracker takes too long → B and C are blocked | B and C use mock data from Hour 0. They are **not blocked** — they can build and test 100% of their work independently. Integration happens at Sync Point 1. |
| Interface mismatch at Sync Point 1 | The interfaces are defined in Hour 0 with exact function signatures. If someone needs to change the interface, they message the group immediately. |
| Merge conflicts | Each person owns distinct files. The only shared file (`models.py`) is frozen after Hour 0. Conflicts should be near-zero. |
| One person finishes early | **Person B finishes early →** Help Person A with edge cases or Person C with demo notebooks. **Person C finishes early →** Start on graph visualization (stretch) or LLM integration. **Person A finishes early →** Start hardening AST analysis edge cases or help with integration testing. |
| Demo doesn't work at Hour 15 | The critical path is Phase 1→2→3→Demo. If Layers 1+2 work but Layer 3 has issues, Person C can fall back to plain-text output. If Layer 2 has issues, the demo can show the dependency graph (Layer 1) without causal tracing. Always have a fallback. |

---

## Quick Reference Card

Print this. Keep it visible.

```
┌─────────────────────────────────────────────────────────────────┐
│  PERSON A (Tracker)     PERSON B (Tracer)     PERSON C (Display)│
│  ─────────────────      ─────────────────     ─────────────────  │
│  ast_analyzer.py        frame_walker.py       banner.py          │
│  graph.py               var_extractor.py      path_display.py    │
│  version_table.py       graph_walker.py       graph_widget.py    │
│  hooks.py               collapser.py          llm/*              │
│  extension.py           summarizer.py         demo/*             │
│  utils/*                                      README.md          │
│                                                                  │
│  INPUT: cell source     INPUT: graph + error  INPUT: CausalPath  │
│  OUTPUT: graph edges    OUTPUT: CausalPath    OUTPUT: HTML        │
│                                                                  │
│  SYNC 1: Hour 9    SYNC 2: Hour 12    FREEZE: Hour 16            │
└─────────────────────────────────────────────────────────────────┘
```

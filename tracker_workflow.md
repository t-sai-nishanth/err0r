# Person A — Tracker Engineer: Complete Workflow

> **Your role:** You build Layer 1 — the execution tracker. Everything the team builds depends on your code being correct. You are the foundation.
>
> **Your mantra:** "Track what ran, in what order, reading what, writing what."

---

## Your Journey at a Glance

```
Hour 0          1          4          6          8     9         12        15        18
 │──────────────│──────────│──────────│──────────│─────│─────────│─────────│─────────│
 Team Setup     AST        Graph      IPython    Test  SYNC 1    SYNC 2    Demo
 + Models       Analyzer   Builder    Hooks      +     Wire      Wire      Polish
                                                Debug  L1→L2     L1→L2→L3  Rehearse
```

## Phase 0: Team Setup (Hour 0–1) — WITH TEAM

> You're the one driving this. You create the repo, the shared models, and the skeleton. Your teammates clone and start from what you set up.

### [x] Task 0.1 — Create the Git Repo and Project Structure

**What:** Initialize the Git repo and create every directory and `__init__.py` file the project needs. Even empty files — just get the structure right.

**Why:** Everyone needs to clone this and start working immediately. If the structure is wrong, all three of you waste time fixing paths later.

**Do this:**
```
bookerrror/
├── bookerrror/
│   ├── __init__.py
│   ├── extension.py               ← you'll write this
│   ├── models.py                  ← shared contract (write together)
│   ├── tracker/
│   │   ├── __init__.py
│   │   ├── ast_analyzer.py        ← empty for now
│   │   ├── version_table.py       ← empty for now
│   │   ├── graph.py               ← empty for now
│   │   └── hooks.py               ← empty for now
│   ├── tracer/
│   │   ├── __init__.py
│   │   ├── frame_walker.py
│   │   ├── var_extractor.py
│   │   ├── graph_walker.py
│   │   ├── collapser.py
│   │   └── summarizer.py
│   ├── presentation/
│   │   ├── __init__.py
│   │   ├── banner.py
│   │   ├── path_display.py
│   │   └── graph_widget.py
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── prompt_builder.py
│   │   ├── client.py
│   │   └── config.py
│   └── utils/
│       ├── __init__.py
│       ├── constants.py
│       └── ipython_helpers.py
├── tests/
│   ├── __init__.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   └── sample_data.py
│   ├── test_ast_analyzer.py
│   └── test_graph.py
├── demo/
│   └── README.md
├── pyproject.toml
├── .gitignore
└── README.md
```

---

### [x] Task 0.2 — Write the Shared Models (`models.py`)

**What:** Together with your team, write all the dataclasses that everyone's code will use. This is the contract between Person A, B, and C.

**Why:** If Person B builds their tracer expecting `CausalHop.variable` to be a `str` but you send a `list[str]`, everything breaks at integration. Define it once, agree, freeze it.

**The file should contain these dataclasses:**
- `ExecutionRecord` — what Layer 1 produces per cell run
- `ExceptionInfo` — exception details captured on error
- `Edge` — a dependency link between two executions
- `CausalHop` — one step in the causal chain (Person B produces these)
- `CausalPath` — the full chain from root cause to failure
- `FailureInfo` — metadata about the failing cell

**After this:** Commit, push, tell everyone to pull. **Nobody changes this file without messaging the group.**

---

### [x] Task 0.3 — Write Mock Data (`sample_data.py`)

**What:** Create realistic mock `ExecutionRecord`s, `Edge`s, and a mock `CausalPath` that Person B and C can use to test their code independently.

**Why:** Person B needs a fake graph to test their backward walk. Person C needs a fake `CausalPath` to test their HTML rendering. Without this, they're stuck waiting for your tracker to work first.

---

### [x] Task 0.4 — Write the Extension Entry Point (`extension.py`)

**What:** A minimal `extension.py` that registers with IPython's extension system.

```python
# bookerrror/extension.py

def load_ipython_extension(ipython):
    """Called when user runs %load_ext bookerrror"""
    print("🔍 BookError active. Tracking cell executions.")

def unload_ipython_extension(ipython):
    """Called when user runs %unload_ext bookerrror"""
    print("BookError deactivated.")
```

**Why:** Everyone needs to verify `%load_ext bookerrror` works on their machine before they start coding. This is the "hello world" test.

---

### [x] Task 0.5 — Write `pyproject.toml`

**What:** Basic Python package config so the project is importable.

```toml
[project]
name = "bookerrror"
version = "0.1.0"
requires-python = ">=3.10"

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.backends._legacy:_Backend"
```

**Why:** Without this, `from bookerrror.tracker.ast_analyzer import analyze_cell` won't work.

---

### [x] Task 0.6 — Push, Verify, Split

**What:** Push everything to `main`. Have both teammates clone and run `%load_ext bookerrror` in a Jupyter notebook. Everyone sees "🔍 BookError active." → you're done with setup.

**Now create your branch:**
```bash
git checkout -b feat/tracker
```

**From this point, you work alone on `feat/tracker` until Sync Point 1 at Hour 9.**

---

## Phase 1: AST Analyzer (Hours 1–4) — SOLO

> This is the hardest single component you build. Take your time and get it right. Everything else depends on it.

### [x] Task 1.1 — Basic Variable Read/Write Extraction

**What:** Write a function `analyze_cell(source: str) -> tuple[set[str], set[str], set[str]]` that takes a cell's Python source code and returns `(reads, writes, defines)`.

**How it works:**
1. Call `ast.parse(source)` to get the AST.
2. Walk every node in the AST using `ast.walk()`.
3. For each `ast.Name` node:
   - If its context is `ast.Load` → it's a **read** (the cell used this variable).
   - If its context is `ast.Store` → it's a **write** (the cell created/changed this variable).
   - If its context is `ast.Del` → ignore for now.

**Example:**
```python
source = "df = pd.read_csv('data.csv')"
reads, writes, defines = analyze_cell(source)
# reads  = {"pd"}         ← pd was used (loaded)
# writes = {"df"}         ← df was created (stored)
# defines = set()         ← no functions/classes defined
```

**Why this matters:** This is how the system knows that Cell 5 depends on Cell 2 — because Cell 5 *reads* a variable that Cell 2 *wrote*.

**Start simple.** Handle only:
- `x = ...` (simple assignment → `x` is a write)
- `x` used on the right side (→ read)

Then expand in Task 1.2.

---

### [x] Task 1.2 — Handle All Write Patterns

**What:** Python has many ways to create/modify a variable. Your analyzer needs to catch them all (or at least the common ones).

**Patterns to handle:**

| Pattern | Example | What's written |
|---|---|---|
| Simple assignment | `x = 5` | `x` |
| Multiple assignment | `a, b = 1, 2` | `a`, `b` |
| Augmented assignment | `x += 1` | `x` (also a read!) |
| For-loop target | `for i in range(10):` | `i` |
| With-as target | `with open('f') as fp:` | `fp` |
| Function definition | `def foo():` | `foo` |
| Class definition | `class Bar:` | `Bar` |
| Import | `import pandas as pd` | `pd` |
| From-import | `from sklearn import svm` | `svm` |
| Walrus operator | `if (n := len(x)) > 10:` | `n` |

**How:** Walk the AST and check for `ast.Assign`, `ast.AugAssign`, `ast.For`, `ast.With`, `ast.FunctionDef`, `ast.ClassDef`, `ast.Import`, `ast.ImportFrom`, `ast.NamedExpr`. Each of these creates variables in different ways — extract the target name(s) from each.

**Why augmented assignment is tricky:** `x += 1` means `x = x + 1`. So `x` is **both read AND written**. Make sure it goes into both sets.

---

### [x] Task 1.3 — Detect Known Mutating Methods

**What:** Some method calls *modify* an object in place without reassignment. Your AST can't see this from `Store` context — it looks like a pure read. You need a heuristic.

**Example:**
```python
df.drop(columns=['age'], inplace=True)   # df is mutated, but AST sees only a Load on df
df.fillna(0, inplace=True)               # same problem
```

Even without `inplace=True`:
```python
df = df.drop(columns=['age'])            # This IS a Store on df (reassignment)
```

**What to do:** Build a lookup set of known mutating method names:
```python
MUTATING_METHODS = {
    'drop', 'dropna', 'fillna', 'astype', 'reset_index', 'set_index',
    'rename', 'replace', 'merge', 'concat', 'append', 'pop', 'insert',
    'sort_values', 'sort_index', 'clip', 'apply',
    'fit', 'fit_transform', 'partial_fit',
}
```

When you see an `ast.Call` node where the function is `ast.Attribute` and the attribute name is in `MUTATING_METHODS`, add the receiver object (the thing before the `.`) to the **writes** set too.

**Example AST walk logic:**
```python
for node in ast.walk(tree):
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        if node.func.attr in MUTATING_METHODS:
            # The object being called on is also being written
            if isinstance(node.func.value, ast.Name):
                writes.add(node.func.value.id)
```

**Why:** Without this, `df.drop(columns=['age'])` looks like it only *reads* `df`. The graph won't show that `df` was changed, and the causal chain will miss the root cause.

---

### [x] Task 1.4 — Filter Builtins

**What:** Names like `print`, `range`, `len`, `True`, `False`, `None`, `int`, `str`, `list`, `dict`, `set`, `type`, etc. are Python builtins. They're always available — no cell "wrote" them. Including them in the read set would create false dependency edges.

**What to do:** Maintain a set of builtin names to exclude:
```python
import builtins
BUILTIN_NAMES = set(dir(builtins))
# Also exclude common notebook magics and special names
BUILTIN_NAMES |= {'__name__', '__file__', '__builtins__', 'get_ipython', 'display', 'In', 'Out', '_', '__', '___'}
```

After extracting reads, subtract builtins:
```python
reads = raw_reads - BUILTIN_NAMES
```

**Why:** Without this, every cell that calls `print()` would appear to depend on every other cell that calls `print()`, because `print` would be in both read sets. That's noise, not signal.

---

### [x] Task 1.5 — Filter Function-Local Variables

**What:** If a cell defines a function, the variables inside that function are **local** to it. They shouldn't be tracked as notebook-level reads/writes.

```python
# Cell source:
def process(data):
    result = data * 2    # 'result' and 'data' are LOCAL — don't track them
    return result

output = process(df)     # 'output' is a WRITE, 'process' and 'df' are READS
```

**What to do:** Only track names at the **module level** (top-level scope) of the cell. When you encounter a `FunctionDef` or `AsyncFunctionDef`, skip its body for read/write extraction (but still record the function name itself as a write/define). Same for `ClassDef`.

**How:** Instead of `ast.walk()` (which visits everything recursively), use a selective walk that stops descending into function/class bodies:

```python
def walk_top_level(tree):
    """Walk AST nodes at module scope only. Don't descend into function/class bodies."""
    for node in ast.iter_child_nodes(tree):
        yield node
        # Don't descend into function/class bodies
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            yield from walk_top_level(node)
```

**Why:** Without this, a function with a local variable `df` would create a false edge to every cell that uses a global `df`. Wrong causal chains.

---

### [x] Task 1.6 — Write Tests for the AST Analyzer

**What:** Write test cases for `analyze_cell()` covering the patterns above.

**Test cases to include:**

```python
def test_simple_assignment():
    reads, writes, defines = analyze_cell("x = 5")
    assert reads == set()
    assert writes == {"x"}

def test_read_and_write():
    reads, writes, defines = analyze_cell("df = pd.read_csv('data.csv')")
    assert reads == {"pd"}
    assert writes == {"df"}

def test_augmented_assignment():
    reads, writes, defines = analyze_cell("x += 1")
    assert "x" in reads
    assert "x" in writes

def test_for_loop():
    reads, writes, defines = analyze_cell("for i in range(10):\n    print(i)")
    assert "i" in writes

def test_function_def():
    reads, writes, defines = analyze_cell("def foo(x):\n    return x + 1")
    assert "foo" in writes
    assert "foo" in defines
    assert "x" not in reads  # x is local to foo

def test_import():
    reads, writes, defines = analyze_cell("import pandas as pd")
    assert "pd" in writes
    assert "pd" in defines

def test_mutating_method():
    reads, writes, defines = analyze_cell("df.drop(columns=['age'], inplace=True)")
    assert "df" in reads
    assert "df" in writes  # because .drop() is a known mutating method

def test_builtins_filtered():
    reads, writes, defines = analyze_cell("x = len(mylist)")
    assert "len" not in reads
    assert "mylist" in reads
```

**Why:** The AST analyzer is the most error-prone component. If it reports wrong reads/writes, the entire graph is wrong, and causal chains are useless. Test it early.

---

## Phase 2: Graph Construction (Hours 4–6) — SOLO

> Now you take the reads/writes from the AST analyzer and build the dependency graph — the DAG that Layer 2 will walk backward through.

### [x] Task 2.1 — Implement the Variable Version Table

**What:** A simple dictionary that tracks "which execution currently owns each variable."

```python
# bookerrror/tracker/version_table.py

class VariableVersionTable:
    def __init__(self):
        self._owners: dict[str, int] = {}  # var_name -> exec_id

    def get_owner(self, var: str) -> int | None:
        """Who last wrote this variable? Returns exec_id or None."""
        return self._owners.get(var)

    def update(self, writes: set[str], exec_id: int) -> None:
        """Record that exec_id now owns all variables in writes."""
        for var in writes:
            self._owners[var] = exec_id

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current state (for edge construction)."""
        return self._owners.copy()

    def reset(self) -> None:
        """Clear all ownership (e.g., on kernel restart)."""
        self._owners.clear()
```

**Why this is separate:** The version table is conceptually simple but critically important. Separating it makes it easy to test and reason about.

**Key insight:** This table is what makes BookError work under out-of-order execution. It doesn't care about cell *position* in the notebook — it tracks which *execution* last wrote each variable. If you re-run cell 2, its exec_id changes, and the version table updates accordingly.

---

### [x] Task 2.2 — Implement the Dependency Graph

**What:** The `DependencyGraph` class that stores execution records, builds edges, and exposes query methods for Person B's tracer.

```python
# bookerrror/tracker/graph.py

class DependencyGraph:
    def __init__(self):
        self.records: list[ExecutionRecord] = []
        self.edges: list[Edge] = []
        self._version_table = VariableVersionTable()
        self._next_exec_id: int = 0

    def record_execution(self, cell_id, source, reads, writes, defines, raised=None):
        """Record a cell execution and build dependency edges."""
        exec_id = self._next_exec_id
        self._next_exec_id += 1

        # 1. Build edges: for each variable READ, link to whoever last WROTE it
        for var in reads:
            owner = self._version_table.get_owner(var)
            if owner is not None:
                self.edges.append(Edge(
                    producer_exec_id=owner,
                    consumer_exec_id=exec_id,
                    variable=var,
                ))

        # 2. Update ownership: this execution now owns all written variables
        self._version_table.update(writes | defines, exec_id)

        # 3. Store the record
        record = ExecutionRecord(
            exec_id=exec_id, cell_id=cell_id, timestamp=time.time(),
            source=source, reads=reads, writes=writes, defines=defines,
            raised=raised,
        )
        self.records.append(record)
        return record
```

**Critical detail: Order of operations.** You must build edges BEFORE updating ownership. Why? Because when cell 5 runs `df = df.drop(columns=['age'])`, it *reads* `df` (from whoever last wrote it) and then *writes* `df` (becoming the new owner). If you update ownership first, it would link `df` to itself.

**Also implement these query methods** (Person B's tracer needs them):

```python
    def get_edges_to(self, exec_id: int) -> list[Edge]:
        """Return all edges where this exec_id is the consumer."""
        return [e for e in self.edges if e.consumer_exec_id == exec_id]

    def get_record(self, exec_id: int) -> ExecutionRecord | None:
        """Return the ExecutionRecord for a given exec_id."""
        for r in self.records:
            if r.exec_id == exec_id:
                return r
        return None

    def get_latest_record(self) -> ExecutionRecord | None:
        """Return the most recently recorded execution."""
        return self.records[-1] if self.records else None

    def get_all_records(self) -> list[ExecutionRecord]:
        return list(self.records)

    def get_all_edges(self) -> list[Edge]:
        return list(self.edges)
```

---

### [x] Task 2.3 — Test the Graph with a Simulated Session

**What:** Write a test that simulates the exact demo scenario and verifies the graph is correct.

```python
def test_keyerror_scenario():
    graph = DependencyGraph()

    # Cell 1: import pandas as pd
    graph.record_execution("cell-1", "import pandas as pd",
        reads=set(), writes=set(), defines={"pd"})

    # Cell 2: df = pd.read_csv('data.csv')
    graph.record_execution("cell-2", "df = pd.read_csv('data.csv')",
        reads={"pd"}, writes={"df"}, defines=set())

    # Cell 5: df = df.drop(columns=['age'])
    graph.record_execution("cell-5", "df = df.drop(columns=['age'])",
        reads={"df"}, writes={"df"}, defines=set())

    # Cell 9: result = df[['age', 'income']]  -- ERROR!
    graph.record_execution("cell-9", "result = df[['age', 'income']]",
        reads={"df"}, writes={"result"}, defines=set())

    # Verify edges
    edges_to_cell9 = graph.get_edges_to(3)  # exec_id 3 = cell 9's run
    assert len(edges_to_cell9) == 1
    assert edges_to_cell9[0].producer_exec_id == 2  # cell 5 (the drop)
    assert edges_to_cell9[0].variable == "df"

    # Verify version table: df is now owned by exec_id 2 (cell 5's run)
    # (after cell 9 ran, df ownership didn't change because cell 9 only read df)
```

**Why:** This test is your confidence check. If this passes, your graph is correct for the demo scenario. Person B's tracer will walk backward through exactly these edges.

---

## Phase 3: IPython Hooks (Hours 6–8) — SOLO

> Now you connect the AST analyzer and graph to the actual Jupyter kernel. This is where it becomes real.

### [x] Task 3.1 — Implement the Execution Tracker Class

**What:** A class that holds the graph and responds to IPython's cell execution events.

```python
# bookerrror/tracker/hooks.py

class ExecutionTracker:
    def __init__(self):
        self.graph = DependencyGraph()
        self._pre_run_snapshot = None

    def pre_run_cell(self, info):
        """Called before each cell executes."""
        # Snapshot the current version table state before this cell runs
        # (needed to correctly resolve reads against pre-execution owners)
        self._pre_run_snapshot = self.graph._version_table.snapshot()

    def post_run_cell(self, result):
        """Called after each cell executes."""
        try:
            source = result.info.raw_cell  # the cell's source code
            cell_id = self._get_cell_id(result)

            # Run AST analysis
            reads, writes, defines = analyze_cell(source)

            # Capture exception if any
            raised = None
            if result.error_in_exec is not None:
                raised = self._capture_exception(result.error_in_exec, source)

            # Record in the graph
            record = self.graph.record_execution(
                cell_id=cell_id, source=source,
                reads=reads, writes=writes, defines=defines,
                raised=raised,
            )

            # If there was an error, trigger Layer 2 + Layer 3
            if raised is not None:
                self._handle_error(record)

        except Exception as e:
            # NEVER crash the kernel
            import logging
            logging.getLogger('bookerrror').error(f"BookError: {e}", exc_info=True)
```

**Why `pre_run_cell` takes a snapshot:** When cell 5 runs `df = df.drop(...)`, it reads `df`. But *which* `df`? The one from *before* cell 5 ran, not after. The snapshot captures this "before" state so edge construction uses the right owner.

---

### [x] Task 3.2 — Extract the Cell ID

**What:** Get a stable cell identifier from IPython/Jupyter. This is trickier than it sounds.

```python
def _get_cell_id(self, result) -> str:
    """Extract a stable cell ID from the execution result."""
    # JupyterLab assigns cell IDs in the cell metadata
    # Try to get it from the parent header (Jupyter messaging protocol)
    try:
        ip = get_ipython()
        parent = ip.kernel.get_parent()
        cell_id = parent.get('metadata', {}).get('cellId', None)
        if cell_id:
            return cell_id
    except Exception:
        pass

    # Fallback: use the execution count (less stable but always available)
    return f"cell-exec-{result.execution_count}"
```

**Why it matters:** `cell_id` is how the presentation layer knows which cell to scroll to when the user clicks "Go →". If you use the wrong identifier, navigation breaks.

**Fallback is fine for the hackathon.** The execution count (`In [5]`) is visible in the notebook and good enough for the demo.

---

### [x] Task 3.3 — Capture Exception Info

**What:** When a cell raises an error, extract the relevant details for Layer 2.

```python
def _capture_exception(self, exception: BaseException, source: str) -> ExceptionInfo:
    """Extract exception details for the tracer."""
    import traceback

    exc_type = type(exception).__name__
    exc_message = str(exception)

    # Find the failing line from the traceback
    failing_line = ""
    frame_filename = ""
    frame_lineno = 0

    tb = exception.__traceback__
    while tb is not None:
        filename = tb.tb_frame.f_code.co_filename
        if self._is_notebook_cell(filename):
            frame_filename = filename
            frame_lineno = tb.tb_lineno
            # Extract the actual line of code
            lines = source.splitlines()
            if 0 < tb.tb_lineno <= len(lines):
                failing_line = lines[tb.tb_lineno - 1].strip()
        tb = tb.tb_next

    return ExceptionInfo(
        exc_type=exc_type,
        exc_message=exc_message,
        failing_line=failing_line,
        frame_filename=frame_filename,
        frame_lineno=frame_lineno,
    )

def _is_notebook_cell(self, filename: str) -> bool:
    """Check if a filename belongs to a notebook cell execution."""
    return (
        '<ipython-input-' in filename or
        'ipykernel_' in filename or
        filename.startswith('/tmp/ipykernel') or
        'AppData' in filename and 'ipykernel' in filename  # Windows
    )
```

**Why you walk the traceback:** The raw exception might have library frames (pandas internals, sklearn internals) stacked on top. You want the frame that belongs to the user's cell code — that's where the meaningful failing line is.

---

### [x] Task 3.4 — Wire Hooks into `extension.py`

**What:** Update `extension.py` to create the tracker and register the hooks.

```python
# bookerrror/extension.py

from bookerrror.tracker.hooks import ExecutionTracker

_tracker = None

def load_ipython_extension(ipython):
    global _tracker
    _tracker = ExecutionTracker()
    ipython.events.register('pre_run_cell', _tracker.pre_run_cell)
    ipython.events.register('post_run_cell', _tracker.post_run_cell)

    # Store on IPython instance so other layers can access the graph
    ipython._bookerrror_tracker = _tracker

    print("🔍 BookError active. Tracking cell executions.")

def unload_ipython_extension(ipython):
    global _tracker
    if _tracker:
        ipython.events.unregister('pre_run_cell', _tracker.pre_run_cell)
        ipython.events.unregister('post_run_cell', _tracker.post_run_cell)
        if hasattr(ipython, '_bookerrror_tracker'):
            del ipython._bookerrror_tracker
        _tracker = None
    print("BookError deactivated.")
```

---

### [x] Task 3.5 — Implement the `_handle_error` Method (Stub for Now)

**What:** When an error occurs, this is where you'll call Person B's tracer and Person C's display. For now, just print the error info.

```python
def _handle_error(self, record: ExecutionRecord):
    """Called when a cell raises an exception. Triggers Layer 2 + 3."""
    # STUB — will be wired at Sync Point 1 (Hour 9)
    print(f"[BookError] Error detected in exec #{record.exec_id}: {record.raised.exc_type}")
    print(f"[BookError] Failing line: {record.raised.failing_line}")
    print(f"[BookError] Graph has {len(self.graph.records)} records, {len(self.graph.edges)} edges")
```

**Why a stub:** Person B's tracer and Person C's display aren't ready yet. You'll wire the real calls at Sync Point 1. For now, this print output lets you verify the tracker is working.

---

## Phase 4: Testing & Debug Tools (Hours 8–9) — SOLO

### [x] Task 4.1 — Create the `%bookerrror_debug` Magic Command

**What:** A notebook magic that prints the current graph state. Invaluable for debugging.

```python
# Add to extension.py or a separate file

from IPython.core.magic import register_line_magic

@register_line_magic
def bookerrror_debug(line):
    """Print the current BookError graph state."""
    ip = get_ipython()
    tracker = getattr(ip, '_bookerrror_tracker', None)
    if not tracker:
        print("BookError is not loaded.")
        return

    graph = tracker.graph
    print(f"=== BookError Debug ===")
    print(f"Executions: {len(graph.records)}")
    print(f"Edges: {len(graph.edges)}")
    print(f"\n--- Execution Records ---")
    for r in graph.records:
        status = f" ❌ {r.raised.exc_type}" if r.raised else " ✓"
        print(f"  #{r.exec_id} [{r.cell_id}]{status}")
        print(f"    reads:  {r.reads}")
        print(f"    writes: {r.writes}")
    print(f"\n--- Edges ---")
    for e in graph.edges:
        print(f"  #{e.producer_exec_id} --({e.variable})--> #{e.consumer_exec_id}")
    print(f"\n--- Current Owners ---")
    for var, eid in sorted(graph._version_table._owners.items()):
        print(f"  {var} → exec #{eid}")
```

**Usage in notebook:**
```python
%load_ext bookerrror
# ... run some cells ...
%bookerrror_debug
```

**Why:** This is your lifeline during integration. When something goes wrong, you can see exactly what the graph looks like.

---

### Task 4.2 — Manual End-to-End Test

**What:** Open a Jupyter notebook and manually test the tracker.

**Test script:**
1. `%load_ext bookerrror` → should print "🔍 BookError active."
2. Run: `import pandas as pd` → silent (no error).
3. Run: `df = pd.read_csv('some_file.csv')` → silent (or use a dummy: `df = pd.DataFrame({'age': [1,2], 'income': [3,4]})`).
4. Run: `df = df.drop(columns=['age'])` → silent.
5. Run: `result = df[['age', 'income']]` → ERROR! Should print the stub message: `[BookError] Error detected...`
6. Run: `%bookerrror_debug` → should show 4 execution records, edges linking them via `pd` and `df`.

**Verify:**
- Edge from exec #0 (`import pandas`) to exec #1 (`pd.read_csv`) via `pd` ✓
- Edge from exec #1 (`read_csv`) to exec #2 (`df.drop`) via `df` ✓
- Edge from exec #2 (`df.drop`) to exec #3 (`df[['age']]`) via `df` ✓
- exec #3 has `raised` with `KeyError` ✓

**If all this works, your Layer 1 is done. Push to `feat/tracker` and prepare for Sync Point 1.**

---

## Sync Point 1 — Hour 9 (WITH TEAM)

### Task 5.1 — Push and Merge

```bash
git push origin feat/tracker
```

### Task 5.2 — Wire Person B's Tracer

**What:** Replace the `_handle_error` stub with calls to Person B's `trace_error()` function.

```python
def _handle_error(self, record: ExecutionRecord):
    from bookerrror.tracer import trace_error
    path = trace_error(self.graph, record.raised, record.exec_id)
    # For now, just print it
    if path:
        print(f"[BookError] Causal path found: {len(path.hops)} hops")
        for hop in path.hops:
            print(f"  {hop.role}: Cell [{hop.cell_id}] — {hop.summary}")
    else:
        print(f"[BookError] Could not trace error to earlier cell.")
```

### Task 5.3 — Fix Any Interface Mismatches

Person B built their code against a `MockGraph`. Your real `DependencyGraph` needs to have the same methods they expect. If there are differences, fix them now.

---

## Sync Point 2 — Hour 12 (WITH TEAM)

### Task 6.1 — Wire Person C's Display

**What:** Replace the print statements in `_handle_error` with Person C's display calls.

```python
def _handle_error(self, record: ExecutionRecord):
    from bookerrror.tracer import trace_error
    from bookerrror.presentation import render_causal_path, render_no_chain

    path = trace_error(self.graph, record.raised, record.exec_id)

    if path and path.hops:
        render_causal_path(path)
    else:
        render_no_chain(record.raised.exc_type, record.raised.exc_message)
```

### Task 6.2 — End-to-End Test

Run the demo notebook. Verify: error → causal chain banner appears with correct hops → "Go →" scrolls to root cause cell.

**If this works, the MVP is complete.**

---

## Hours 12–15: Hardening (SOLO)

### Task 7.1 — Handle Comprehension Variables

`[x for x in items]` — the `x` inside the comprehension is scoped, not a notebook-level variable. Filter it out.

### Task 7.2 — Handle Tuple Unpacking

`a, b, c = some_function()` — all three of `a`, `b`, `c` are writes. Make sure your AST walker handles `ast.Tuple` in `ast.Store` context.

### Task 7.3 — Handle Starred Assignments

`first, *rest = my_list` — `first` and `rest` are both writes. Handle `ast.Starred`.

### Task 7.4 — Handle Decorators

```python
@decorator
def foo():
    pass
```
`decorator` is a read. `foo` is a write. Make sure both are captured.

### Task 7.5 — Stress Test with Real Notebooks

Open one of your own data science notebooks. Load BookError. Run cells. Check `%bookerrror_debug`. Look for wrong edges or missing edges.

---

## Hours 15–18: Demo & Polish (WITH TEAM)

### Task 8.1 — Bug Fixes
Fix anything found during rehearsal.

### Task 8.2 — Demo Rehearsal
Run the full demo 3+ times. Time it. Make sure it's under 3 minutes.

### Task 8.3 — Feature Freeze at Hour 16
**Stop writing new code.** Only fix bugs after this point.

---

## Your Complete Checklist

```
Phase 0: Team Setup (Hour 0–1)
  [ ] 0.1  Create Git repo and project structure
  [ ] 0.2  Write shared models.py (with team)
  [ ] 0.3  Write mock data sample_data.py (with team)
  [ ] 0.4  Write extension.py (hello world)
  [ ] 0.5  Write pyproject.toml
  [ ] 0.6  Push, verify %load_ext works, create feat/tracker branch

Phase 1: AST Analyzer (Hours 1–4)
  [ ] 1.1  Basic read/write extraction (ast.Name + Load/Store)
  [ ] 1.2  Handle all write patterns (for, with, import, def, class, walrus)
  [ ] 1.3  Detect known mutating methods (df.drop, df.fillna, etc.)
  [ ] 1.4  Filter builtins (print, range, len, etc.)
  [ ] 1.5  Filter function-local variables (don't descend into def/class bodies)
  [ ] 1.6  Write tests for AST analyzer

Phase 2: Graph Construction (Hours 4–6)
  [ ] 2.1  Implement VariableVersionTable
  [ ] 2.2  Implement DependencyGraph with record_execution + query methods
  [ ] 2.3  Test graph with simulated KeyError scenario

Phase 3: IPython Hooks (Hours 6–8)
  [ ] 3.1  Implement ExecutionTracker class (pre_run_cell, post_run_cell)
  [ ] 3.2  Extract cell ID from Jupyter metadata
  [ ] 3.3  Capture exception info from traceback
  [ ] 3.4  Wire hooks into extension.py
  [ ] 3.5  Implement _handle_error stub

Phase 4: Testing (Hours 8–9)
  [ ] 4.1  Create %bookerrror_debug magic command
  [ ] 4.2  Manual end-to-end test in a real notebook

Sync Point 1 (Hour 9)
  [ ] 5.1  Push feat/tracker branch
  [ ] 5.2  Wire Person B's trace_error() into _handle_error
  [ ] 5.3  Fix any interface mismatches

Sync Point 2 (Hour 12)
  [ ] 6.1  Wire Person C's render_causal_path() into _handle_error
  [ ] 6.2  End-to-end test with full pipeline

Hardening (Hours 12–15)
  [ ] 7.1  Handle comprehension variables
  [ ] 7.2  Handle tuple unpacking
  [ ] 7.3  Handle starred assignments
  [ ] 7.4  Handle decorators
  [ ] 7.5  Stress test with real notebooks

Demo (Hours 15–18)
  [ ] 8.1  Bug fixes
  [ ] 8.2  Demo rehearsal (3+ times)
  [ ] 8.3  Feature freeze at Hour 16
```

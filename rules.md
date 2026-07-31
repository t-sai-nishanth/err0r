# BookError — Project Rules & Conventions

These rules exist to keep the codebase consistent during rapid hackathon development. They are minimal by design — only rules that prevent real confusion or bugs are included.

---

## Folder Organization

```
bookerrror/
├── bookerrror/          # Python package (all source code)
│   ├── tracker/         # Layer 1 — Execution tracking
│   ├── tracer/          # Layer 2 — Root-cause tracing
│   ├── presentation/    # Layer 3 — Display rendering
│   ├── llm/             # Layer 4 — Optional LLM explanation
│   └── utils/           # Shared utilities
├── labextension/        # JupyterLab extension (stretch, TypeScript)
├── demo/                # Demo notebooks and data
├── tests/               # Test suite
└── docs/                # Documentation (this folder)
```

- All Python source code goes in `bookerrror/`. Each layer has its own subdirectory.
- The `labextension/` directory is for the JupyterLab TypeScript extension (stretch goal). It is independent of the Python package.
- Demo notebooks and sample data go in `demo/`.
- Tests go in `tests/`, mirroring the source structure.

---

## Naming Conventions

### Files & Directories

- **Python modules:** `snake_case.py` (`ast_analyzer.py`, `graph_walker.py`, `prompt_builder.py`).
- **Test files:** `test_<module>.py` (`test_ast_analyzer.py`, `test_graph_walker.py`).
- **TypeScript files (stretch):** `PascalCase.tsx` for React components, `camelCase.ts` for utilities.
- **Directories:** `snake_case` for Python, `camelCase` for TypeScript.

### Code

- **Variables and functions:** `snake_case` (`parse_cell`, `exec_id`, `current_owner`).
- **Classes:** `PascalCase` (`ExecutionRecord`, `DependencyGraph`, `CausalPath`).
- **Constants:** `SCREAMING_SNAKE_CASE` (`MUTATING_METHODS`, `BUILTIN_NAMES`, `MAX_CHAIN_DEPTH`).
- **Type hints:** Use Python 3.10+ syntax (`list[str]`, `dict[str, int]`, `str | None`). No `from typing import List`.
- **Dataclasses:** Use `@dataclass` for all data-carrying objects. No plain dictionaries for structured data.

### Domain Terms

Use these terms consistently throughout code, docs, and comments:

| Term | Meaning |
|---|---|
| **exec_id** | A monotonically increasing integer identifying one specific run of a cell. NOT the same as cell position or cell ID. |
| **cell_id** | The stable Jupyter cell identifier that persists across edits and re-runs. |
| **reads** | Variable names read by a cell execution (in `ast.Load` context). |
| **writes** | Variable names written by a cell execution (in `ast.Store` context, plus detected mutations). |
| **defines** | Functions, classes, or imports introduced by a cell execution. Subset of writes. |
| **current_owner** | The mapping from variable name to the `exec_id` that last wrote it. |
| **edge** | A dependency link from a producer `exec_id` to a consumer `exec_id` via a specific variable. |
| **causal path** | The ordered chain of hops from root cause to failure, produced by Layer 2. |
| **hop** | One step in the causal path. Represents a single execution that contributed to the failure. |

---

## Coding Style

### Python

- **Python 3.10+ required.** Use modern syntax: `match` statements, `str | None`, `list[str]`.
- **Type hints on all function signatures.** No `Any` unless absolutely necessary — and if used, add a `# TODO: type properly` comment.
- **Use `@dataclass` for data models.** No `TypedDict`, no plain dicts for structured data.
- **Prefer `set` over `list` for read/write variable sets.** Order doesn't matter; uniqueness does.
- **No mutable default arguments.** Use `field(default_factory=...)` in dataclasses.
- **Error handling:** Always catch exceptions in hook handlers. Never let a BookError bug crash the user's kernel.
- **No `print()` for debugging output.** Use `logging` or IPython's `display()`.

```python
# Good
@dataclass
class ExecutionRecord:
    exec_id: int
    cell_id: str
    reads: set[str] = field(default_factory=set)
    writes: set[str] = field(default_factory=set)

def analyze_cell(source: str) -> tuple[set[str], set[str], set[str]]:
    """Return (reads, writes, defines) for a cell's source code."""
    ...

# Bad
def analyze_cell(source):
    result = {}  # untyped dict instead of dataclass
    ...
```

### HTML/CSS (Inline in Python)

- All CSS must be **inline within the HTML string** passed to `display(HTML(...))`. JupyterLab strips external stylesheet links from cell outputs.
- Use **CSS custom properties** defined in a `<style>` block within the HTML for consistency.
- Keep HTML generation in dedicated rendering functions, not mixed into business logic.
- Escape user-facing strings (cell source code, variable names) to prevent XSS in HTML output.

### TypeScript (Stretch — JupyterLab Extension)

- Same conventions as the TraceGraph project: strict mode, no `any`, named exports, functional React components.
- Not relevant until the stretch goal is attempted.

---

## Git Conventions

### Branching

- `main` — Always working. This is what gets demoed.
- Feature branches: `feat/<short-description>` (e.g., `feat/ast-analyzer`, `feat/banner-rendering`).
- Bug fixes: `fix/<short-description>` (e.g., `fix/scope-handling`).

### Commits

- Use conventional commit format: `type: short description`.
- Types: `feat`, `fix`, `refactor`, `style`, `docs`, `chore`, `test`.
- Keep commits small and focused. One logical change per commit.
- Examples:
  ```
  feat: implement AST analyzer with read/write extraction
  feat: add backward graph walk for causal tracing
  fix: exclude builtins from variable read set
  style: add dark theme CSS to causal chain banner
  docs: add demo notebook for KeyError scenario
  ```

### During the Hackathon

- Commit frequently. At minimum, commit at the end of each phase.
- Don't spend time on code review processes. Trust and move fast.
- If something breaks `main`, fix it immediately or revert.

---

## Error Handling

### Core Principle: Never Break the User's Notebook

Every function that runs inside an IPython event hook must be wrapped in try-except:

```python
def post_run_cell(self, result):
    try:
        self._process_cell(result)
    except Exception as e:
        # Log the error, but never propagate it
        import logging
        logging.getLogger('bookerrror').error(f"BookError error: {e}", exc_info=True)
```

### Layer-Specific Rules

- **Layer 1 (Tracker):** If AST parsing fails, record the cell as opaque (empty reads/writes). If graph construction fails, skip this execution.
- **Layer 2 (Tracer):** If the backward walk fails, return an empty `CausalPath`. The presentation layer shows "Could not trace."
- **Layer 3 (Presentation):** If HTML rendering fails, fall back to plain text output.
- **Layer 4 (LLM):** If the API call fails, show the deterministic summaries with a note.

---

## Logging

- Use Python's `logging` module with logger name `'bookerrror'`.
- Log levels:
  - `DEBUG`: AST analysis details, edge construction, graph walk steps. Off by default.
  - `INFO`: Extension loaded, cell execution tracked, causal path found.
  - `WARNING`: AST parse failure, opaque cell recorded, stale code detected.
  - `ERROR`: Unexpected exceptions in hook handlers (always caught, never propagated).
- Never log the full cell source code at INFO level (can be huge). Log at DEBUG only.

---

## Security Practices

- **Never execute user code.** BookError uses `ast.parse()` to analyze code, never `exec()` or `eval()`.
- **Escape HTML output.** All user-generated strings (cell source, variable names, exception messages) must be HTML-escaped before rendering in `display(HTML(...))`.
- **API keys for Layer 4:** Read from `BOOKERRROR_API_KEY` environment variable. Never log, never include in error reports, never display in notebook output.
- **No telemetry.** No external network calls except the optional, user-triggered LLM API call.

---

## Testing Expectations

### During the Hackathon

- **Manual testing is primary.** Run the demo notebooks, verify the causal chain appears, verify cell navigation works.
- **Write tests only for the AST analyzer.** This is the most error-prone component and benefits most from automated testing.
- **No coverage requirement.** Tests are nice to have but not blocking.
- **Test the demo path repeatedly.** The demo must not fail.

### Post-Hackathon

- Unit tests for: AST analyzer, graph construction, backward walk, hop summarizer.
- Integration tests for: end-to-end (load extension → run cells → trigger error → verify causal path).
- Property-based tests for: AST analyzer edge cases (use `hypothesis` library).

---

## Documentation Expectations

- **Code comments:** Write comments for non-obvious logic, especially in the AST analyzer and graph walker. Do not comment obvious code.
- **Docstrings:** Add a brief docstring to every public function and class.
- **README:** Must contain a one-paragraph description, quick start instructions, and an example output.
- **This `docs/` folder:** Contains all design and architecture documentation. Update `memory.md` as the project evolves.

---

## Configuration

- **No config files during the hackathon.** All configuration via environment variables or IPython magic arguments.
- **Environment variables:**
  - `BOOKERRROR_API_KEY` — API key for the optional LLM explanation (Layer 4).
  - `BOOKERRROR_API_URL` — LLM API endpoint (default: `https://api.openai.com/v1/chat/completions`).
  - `BOOKERRROR_MODEL` — LLM model name (default: `gpt-4o-mini`).
  - `BOOKERRROR_LOG_LEVEL` — Logging level (default: `WARNING`).
- **Magic commands:**
  - `%load_ext bookerrror` — Load the extension.
  - `%bookerrror_debug` — Print the current graph state (development aid).
  - `%bookerrror_trace` — Print the last causal path (development aid).

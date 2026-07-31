# BookError — Project Memory

> **Last updated:** 2026-07-31 (Pre-development)
>
> This is a living document. Update it as the project evolves.

---

## Project Summary

BookError is a notebook-aware causal error localizer for Jupyter. It hooks into IPython's execution events to build a live dependency graph of variable reads and writes across cell executions. When a cell raises an exception, it performs a millisecond-scale backward graph walk to identify the earliest causally responsible cell and produces an ordered causal chain rendered directly in the notebook. An optional LLM layer provides a plain-language explanation using ~100 tokens — 10x fewer than pasting a traceback into ChatGPT.

**Key differentiator:** The core diagnosis is deterministic, instant, and requires zero LLM calls. The LLM is a cosmetic addition, not the engine.

---

## Current Status: Pre-Development

No code has been written. The project is in the documentation and planning phase.

### Completed

- [x] Project concept finalized (from solution.md).
- [x] Documentation set created:
  - `solution.md` — Original technical solution document.
  - `prd.md` — Product requirements.
  - `architecture.md` — Technical architecture.
  - `design.md` — UI/UX design.
  - `phases.md` — Implementation roadmap.
  - `rules.md` — Project conventions.
  - `memory.md` — This file.

### In Progress

- Nothing yet.

### Pending (Next Steps)

1. **Phase 1: Foundation + Tracker** — Create the Python package, implement IPython hooks, build the AST analyzer, construct the dependency graph.
2. Start with the AST analyzer (`ast_analyzer.py`) — it's the most complex individual component and everything depends on its correctness.
3. Get `%load_ext bookerrror` working and printing a "BookError active" message before building any feature code.

---

## Architectural Decisions Made

| Decision | Rationale | Date |
|---|---|---|
| **Pure Python, no external deps for core** | The tracker uses only `ast` (stdlib) and IPython hooks. Zero pip dependencies for Layers 1–2. This means instant "installation" via `%load_ext` from source. | 2026-07-31 |
| **In-process, no server** | The tracker runs inside the Jupyter kernel. Direct access to IPython events, user namespace, and exception objects. No IPC, no serialization overhead. | 2026-07-31 |
| **Inline HTML output (MVP) over JupyterLab extension** | Rendering via `display(HTML(...))` requires zero TypeScript and zero build tooling. A JupyterLab extension panel is a stretch goal. This decision optimizes for hackathon speed. | 2026-07-31 |
| **Dataclasses for all data models** | Type-safe, self-documenting, and IDE-friendly. No plain dicts for structured data. | 2026-07-31 |
| **exec_id (not cell_id) as graph node identity** | A cell can be run multiple times. Each run is a separate graph node. This is what makes the graph correct under out-of-order execution. | 2026-07-31 |
| **Mutations detected via method-name lookup table** | True alias tracking (deep object identity) is too complex for a hackathon. A conservative lookup table of ~20 common pandas/numpy/sklearn methods is sufficient and predictable. | 2026-07-31 |
| **Module-scope variables only (MVP)** | Tracking function-local variables requires full scope analysis. The MVP tracks only top-level notebook variables, which covers the vast majority of notebook debugging scenarios. | 2026-07-31 |
| **No persistence across kernel restarts** | The graph lives in kernel memory. Rebuilding after restart would require re-executing cells, which is impractical. Accept this limitation for the MVP. | 2026-07-31 |
| **LLM is Layer 4, not Layer 1** | The tool's value is in the deterministic graph walk. The LLM just phrases the result nicely. If the LLM is down, the tool is fully functional. | 2026-07-31 |

---

## Technical Constraints

- **Must never crash the kernel.** All hook handlers wrapped in try-except. BookError bugs must be silent, not disruptive.
- **Must never slow down cell execution.** AST parsing + graph edge insertion must complete in < 5ms.
- **Inline CSS only.** JupyterLab strips external stylesheets from cell outputs. All styling must be inline.
- **HTML rendering must HTML-escape user strings.** Cell source code and variable names could contain `<`, `>`, `&`.
- **18-hour time constraint.** Feature freeze at hour 16. Only bug fixes after that.

---

## Assumptions

- Developers use JupyterLab 4.x with a Python 3.10+ kernel.
- Notebooks use standard Python (not R, Julia, or polyglot kernels).
- The most common debugging scenarios involve pandas DataFrames, scikit-learn models, and numpy arrays.
- Cell executions produce a graph of < 500 nodes (typical notebook sessions are 20–100 executions).
- The demo will use prepared notebooks with scripted out-of-order execution.

---

## APIs & Services

| Service | Role | Status |
|---|---|---|
| IPython `events` API | Cell execution hooks (pre_run_cell, post_run_cell) | Not yet integrated |
| Python `ast` module | Static analysis for variable read/write extraction | Not yet integrated |
| IPython `display()` + `HTML()` | Rendering causal chain in cell output | Not yet integrated |
| `httpx` or `requests` | LLM API client (Layer 4, optional) | Not yet integrated |
| OpenAI-compatible API | LLM provider for plain-language explanations | Not yet integrated |

---

## Known Issues & Limitations

None yet (pre-development). Expected issues to watch for:

- **Aliasing false negatives:** `df2 = df` followed by in-place mutation of `df2` may not be detected if the mutation method isn't in the lookup table.
- **Scope confusion:** If a function defines a local variable with the same name as a global, the AST analyzer might incorrectly link them. The MVP avoids this by only tracking module-scope names.
- **`%%` magics:** Cells with `%%timeit`, `%%bash`, etc. will be recorded as opaque nodes. This is acceptable.
- **Comprehension variables:** `[x for x in range(10)]` — the `x` is technically a comprehension-scope variable in Python 3, but `ast` reports it as `ast.Store`. Need to filter these out.
- **HTML output size:** For very long causal chains (unlikely), the HTML output could be large. Cap at 10 hops for the MVP.

---

## Decisions That Should Not Be Changed Unintentionally

1. **exec_id is per-execution, not per-cell.** This is the fundamental design property that makes the graph correct under re-runs and out-of-order execution. Do not change this.
2. **Layers 1–2 are LLM-free.** The causal chain is deterministic. No AI magic in the diagnosis step.
3. **Layer 4 is optional and user-triggered.** The "Explain" button is opt-in. Never auto-call an LLM.
4. **Never crash the kernel.** All hook handlers must be wrapped in try-except.
5. **current_owner tracks the live state, not the cell order.** The mapping always reflects which execution *currently* owns each variable, regardless of notebook cell position.
6. **Inline HTML for MVP.** The JupyterLab extension panel is a stretch goal. The core demo uses `display(HTML(...))`.

---

## Future Improvements Intentionally Postponed

- **Full JupyterLab extension** (TypeScript sidebar panel) — Post-hackathon Phase 6B.
- **Deep scope analysis** (function locals, closures, class methods) — Post-hackathon Phase 6A.
- **Alias tracking via value snapshots** — Post-hackathon Phase 6A.
- **Stale variable detection** (proactive, not just on error) — Post-hackathon Phase 6C.
- **pip packaging and PyPI release** — Post-hackathon Phase 6D.
- **Google Colab compatibility** — Post-hackathon Phase 6D.
- **VS Code Jupyter extension** — Post-hackathon Phase 6D.
- **Session persistence** — Explicitly out of scope, possibly never.

---

## Notes for Future AI Coding Agents

1. **Read `architecture.md` first** for the full system design, data model, layer communication, and tech stack.
2. **Read `phases.md`** to understand what phase the project is in and what to build next.
3. **Read `rules.md`** for naming conventions, coding style, and error handling expectations before writing code.
4. **The demo is the deliverable.** Every feature decision should be evaluated against: "Does this help the 3-minute demo?"
5. **The AST analyzer is the hardest Layer 1 component.** Handle assignments, for-loops, with-statements, imports, function/class definitions, and known mutating methods. Filter builtins. Filter function-local variables.
6. **The backward graph walk is simple but must be correct.** Use BFS from the failing exec_id. Follow producer edges backward. Collect hops. Sort chronologically.
7. **All HTML must be self-contained.** JupyterLab strips external `<link>` tags. Inline all CSS in a `<style>` block within the HTML. HTML-escape all user strings.
8. **Test with real pandas operations early.** The demo scenarios involve DataFrames — make sure `df.drop()`, `df[['col']]`, and similar operations are correctly tracked.
9. **Don't over-engineer the graph layout.** A simple top-to-bottom ordering by exec_id is sufficient for the MVP.
10. **The token comparison is key to the demo narrative.** Calculate and display the token count of BookError's LLM prompt (~100 tokens) vs. a full traceback paste (~1000+ tokens). This is the measurable efficiency claim.

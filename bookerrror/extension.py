"""IPython extension entry points for BookError."""

from __future__ import annotations

from IPython import get_ipython

from bookerrror.tracker.hooks import ExecutionTracker, register_hooks, unregister_hooks


_tracker: ExecutionTracker | None = None


def load_ipython_extension(ipython) -> None:
    """Register the BookError extension."""

    global _tracker
    _tracker = ExecutionTracker()
    register_hooks(ipython, _tracker)
    ipython._bookerrror_tracker = _tracker
    ipython.register_magic_function(bookerrror_debug, "line", "bookerrror_debug")
    print("🔍 BookError active. Tracking cell executions.")


def bookerrror_debug(line: str = "") -> None:
    """Print the current tracker state for debugging."""

    ipython = get_ipython()
    tracker = getattr(ipython, "_bookerrror_tracker", None)
    if tracker is None:
        print("BookError is not loaded.")
        return

    graph = tracker.graph
    print("=== BookError Debug ===")
    print(f"Executions: {len(graph.records)}")
    print(f"Edges: {len(graph.edges)}")
    print("\n--- Execution Records ---")
    for record in graph.records:
        status = f" ❌ {record.raised.exc_type}" if record.raised else " ✓"
        print(f"  #{record.exec_id} [{record.cell_id}]{status}")
        print(f"    reads:  {record.reads}")
        print(f"    writes: {record.writes}")
    print("\n--- Edges ---")
    for edge in graph.edges:
        print(f"  #{edge.producer_exec_id} --({edge.variable})--> #{edge.consumer_exec_id}")
    print("\n--- Current Owners ---")
    for variable, exec_id in sorted(graph._version_table.current_owner.items()):
        print(f"  {variable} -> exec #{exec_id}")


def unload_ipython_extension(ipython) -> None:
    """Unregister the BookError extension."""

    global _tracker
    if _tracker is not None:
        unregister_hooks(ipython, _tracker)
        if hasattr(ipython, "_bookerrror_tracker"):
            delattr(ipython, "_bookerrror_tracker")
        _tracker = None
    print("BookError deactivated.")

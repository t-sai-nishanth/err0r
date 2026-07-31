"""IPython-specific helper functions."""

from __future__ import annotations

from IPython import get_ipython


def get_cell_id(result) -> str | None:
    """Return the current cell identifier from an IPython result object."""

    try:
        ipython = get_ipython()
        if ipython is not None:
            parent = getattr(getattr(ipython, "kernel", None), "get_parent", lambda: {})()
            cell_id = parent.get("metadata", {}).get("cellId")
            if cell_id:
                return str(cell_id)
    except Exception:
        pass

    execution_count = getattr(result, "execution_count", None)
    if execution_count is not None:
        return f"cell-exec-{execution_count}"

    return None

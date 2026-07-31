"""Shared constants for BookError."""

from __future__ import annotations

import builtins


BUILTIN_NAMES: set[str] = set(dir(builtins)) | {
    "In",
    "Out",
    "__",
    "___",
    "__builtins__",
    "__file__",
    "__name__",
    "display",
    "get_ipython",
}
MUTATING_METHODS: set[str] = {
    "append",
    "astype",
    "concat",
    "drop",
    "dropna",
    "fillna",
    "fit",
    "fit_transform",
    "insert",
    "merge",
    "pop",
    "reset_index",
    "replace",
    "rename",
    "set_index",
    "sort_index",
    "sort_values",
    "clip",
    "partial_fit",
    "apply",
}

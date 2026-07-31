"""Shared constants for BookError."""

from __future__ import annotations


BUILTIN_NAMES: set[str] = {"False", "None", "True", "len", "print", "range"}
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
}

"""Generate hop summaries from execution records."""

from __future__ import annotations

import ast

KNOWN_MUTATING_METHODS = {
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


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
        value = node.func.value
        if isinstance(value, ast.Name):
            return value.id
    if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
        return node.value.id
    if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
        return node.value.id
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _first_string_constant(node: ast.AST) -> str:
    for child in ast.walk(node):
        if isinstance(child, ast.Constant) and isinstance(child.value, str):
            return child.value
    return ""


def summarize_hop(record, variable: str) -> str:
    """Return a short human-readable summary for a hop."""

    source = getattr(record, "source", "") if record is not None else ""
    if not source:
        return f"updated {variable}" if variable else "updated value"

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return source[:80]

    stmt = tree.body[0] if tree.body else None

    if isinstance(stmt, ast.Import):
        alias = stmt.names[0]
        return f"imported {alias.asname or alias.name.split('.')[0]}"

    if isinstance(stmt, ast.ImportFrom):
        alias = stmt.names[0]
        return f"imported {alias.asname or alias.name}"

    if isinstance(stmt, ast.Assign) and stmt.targets:
        target = stmt.targets[0]
        target_name = target.id if isinstance(target, ast.Name) else variable
        value = stmt.value

        if isinstance(value, ast.Call):
            method_name = _call_name(value)
            base_name = _base_name(value)
            if method_name in KNOWN_MUTATING_METHODS:
                if method_name == "drop":
                    column = ""
                    for keyword in value.keywords:
                        if keyword.arg == "columns" and keyword.value is not None:
                            column = _first_string_constant(keyword.value)
                    if column:
                        return f"dropped column '{column}' from {base_name or target_name}"
                    return f"dropped columns from {base_name or target_name}"
                if method_name == "fillna":
                    return f"filled NaN values in {base_name or target_name}"
                if method_name == "dropna":
                    return f"dropped missing values from {base_name or target_name}"
                if method_name == "reset_index":
                    return f"reset index on {base_name or target_name}"
                if method_name in {"fit", "fit_transform"}:
                    return f"fit {base_name or target_name}"
                return f"called .{method_name}() on {base_name or target_name}"
            return f"defined {target_name} from {method_name}()"

        if isinstance(value, ast.Subscript):
            base_name = _base_name(value)
            column = _first_string_constant(value)
            if column:
                return f"accessed column '{column}' on {base_name or target_name}"
            return f"indexed {base_name or target_name}"

        if isinstance(value, ast.Name):
            return f"reassigned {target_name}"

        return f"defined {target_name}"

    if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
        method_name = _call_name(stmt.value)
        base_name = _base_name(stmt.value)
        if method_name:
            return f"called .{method_name}() on {base_name or variable}"

    return source[:80]

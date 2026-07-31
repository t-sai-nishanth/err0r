"""Variable extraction helpers for failing lines."""

from __future__ import annotations

import ast
import re

from bookerrror.tracer.models import FrameInfo

BUILTIN_NAMES = {
    "False",
    "None",
    "True",
    "abs",
    "all",
    "any",
    "bool",
    "dict",
    "enumerate",
    "float",
    "int",
    "len",
    "list",
    "max",
    "min",
    "print",
    "range",
    "set",
    "str",
    "sum",
    "tuple",
}


def _load_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load) and child.id not in BUILTIN_NAMES:
            names.add(child.id)
    return names


def _subscript_targets(node: ast.AST) -> set[str]:
    targets: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Subscript):
            value = child.value
            if isinstance(value, ast.Name) and value.id not in BUILTIN_NAMES:
                targets.add(value.id)
            elif isinstance(value, ast.Attribute) and isinstance(value.value, ast.Name):
                targets.add(value.value.id)
    return targets


def _attribute_targets(node: ast.AST) -> set[str]:
    targets: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Attribute):
            value = child.value
            if isinstance(value, ast.Name) and value.id not in BUILTIN_NAMES:
                targets.add(value.id)
    return targets


def _name_from_message(exception: BaseException) -> str | None:
    message = str(exception)
    match = re.search(r"name '([^']+)' is not defined", message)
    if match:
        return match.group(1)
    match = re.search(r"['\"]([^'\"]+)['\"]", message)
    if match:
        return match.group(1)
    return None


def extract_implicated_vars(frame: FrameInfo | None, exception) -> set[str]:
    """Extract variable names implicated by a failing frame."""

    if frame is None:
        return set()

    source_line = frame.source_line.strip()
    if not source_line:
        return set()

    try:
        tree = ast.parse(source_line)
    except SyntaxError:
        return set(_load_names(ast.parse(source_line + "\n"))) if source_line else set()

    exception_name = exception.__class__.__name__ if isinstance(exception, BaseException) else ""

    if exception_name == "NameError":
        name = _name_from_message(exception)
        if name:
            return {name}

    implicated: set[str] = set()
    implicated.update(_load_names(tree))

    if exception_name in {"KeyError", "IndexError"}:
        implicated.update(_subscript_targets(tree))
    elif exception_name == "AttributeError":
        implicated.update(_attribute_targets(tree))
    elif exception_name == "TypeError":
        implicated.update(_attribute_targets(tree))
        implicated.update(_subscript_targets(tree))

    return implicated - BUILTIN_NAMES

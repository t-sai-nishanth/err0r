"""AST analysis for notebook cells."""

from __future__ import annotations

import ast

from bookerrror.utils.constants import BUILTIN_NAMES, MUTATING_METHODS


def analyze_cell(source: str) -> tuple[set[str], set[str], set[str]]:
    """Return the read, write, and define sets for a cell source string."""

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set(), set(), set()

    reads: set[str] = set()
    writes: set[str] = set()
    defines: set[str] = set()

    for node in _walk_module_scope(tree):
        if isinstance(node, ast.Name):
            if node.id in BUILTIN_NAMES:
                continue
            if isinstance(node.ctx, ast.Load):
                reads.add(node.id)
            elif isinstance(node.ctx, ast.Store):
                writes.add(node.id)

        elif isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            reads.update(_extract_comprehension_reads(node))

        elif isinstance(node, ast.Assign):
            for target in node.targets:
                writes.update(_extract_target_names(target))

        elif isinstance(node, ast.AugAssign):
            writes.update(_extract_target_names(node.target))
            reads.update(_extract_load_names(node.target))
            reads.update(_extract_target_names(node.target))

        elif isinstance(node, ast.For):
            writes.update(_extract_target_names(node.target))

        elif isinstance(node, ast.With):
            for item in node.items:
                if item.optional_vars is not None:
                    writes.update(_extract_target_names(item.optional_vars))

        elif isinstance(node, ast.FunctionDef):
            defines.add(node.name)
            writes.add(node.name)

        elif isinstance(node, ast.AsyncFunctionDef):
            defines.add(node.name)
            writes.add(node.name)

        elif isinstance(node, ast.ClassDef):
            defines.add(node.name)
            writes.add(node.name)

        elif isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname or alias.name.split(".", 1)[0]
                defines.add(name)
                writes.add(name)

        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == "*":
                    continue
                name = alias.asname or alias.name
                defines.add(name)
                writes.add(name)

        elif isinstance(node, ast.NamedExpr):
            writes.update(_extract_target_names(node.target))

        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr in MUTATING_METHODS:
                writes.update(_extract_load_names(node.func.value))

    reads.difference_update(BUILTIN_NAMES)
    writes.difference_update(BUILTIN_NAMES)
    defines.difference_update(BUILTIN_NAMES)
    return reads, writes, defines


def _extract_target_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    if isinstance(node, ast.Name):
        names.add(node.id)
    elif isinstance(node, ast.Starred):
        names.update(_extract_target_names(node.value))
    elif isinstance(node, (ast.Tuple, ast.List)):
        for element in node.elts:
            names.update(_extract_target_names(element))
    return names


def _extract_load_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            if child.id not in BUILTIN_NAMES:
                names.add(child.id)
    return names


def _walk_module_scope(tree: ast.AST):
    """Yield module-scope nodes without descending into function or class bodies."""

    for node in ast.iter_child_nodes(tree):
        yield node
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            for decorator in getattr(node, "decorator_list", []):
                yield from ast.walk(decorator)
            for base in getattr(node, "bases", []):
                yield from ast.walk(base)
            for keyword in getattr(node, "keywords", []):
                yield from ast.walk(keyword)
            continue
        if isinstance(node, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            yield node
            continue
        yield from _walk_module_scope(node)


def _extract_comprehension_reads(node: ast.AST) -> set[str]:
    """Extract module-level reads from a comprehension without its local targets."""

    names: set[str] = set()
    local_targets: set[str] = set()

    for generator in getattr(node, "generators", []):
        local_targets.update(_extract_target_names(generator.target))

    parts: list[ast.AST] = []
    if isinstance(node, ast.DictComp):
        parts.extend([node.key, node.value])
    else:
        parts.append(getattr(node, "elt"))
    for generator in getattr(node, "generators", []):
        parts.append(generator.iter)
        parts.extend(generator.ifs)

    for part in parts:
        for child in ast.walk(part):
            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
                if child.id not in BUILTIN_NAMES and child.id not in local_targets:
                    names.add(child.id)
    return names

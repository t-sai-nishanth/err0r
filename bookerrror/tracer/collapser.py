"""Collapse raw graph walks into causal paths."""

from __future__ import annotations

from bookerrror.models import CausalHop, CausalPath, FailureInfo


def collapse_chain(chain) -> CausalPath:
    """Collapse a raw trace chain into a causal path object."""

    if not chain:
        return CausalPath(
            failure=FailureInfo(
                cell_id="",
                exec_id=-1,
                exc_type="",
                exc_message="",
                failing_line="",
            ),
            hops=[],
        )

    unique_nodes = []
    seen: set[tuple[int, str, str]] = set()
    for node in sorted(chain, key=lambda item: item.exec_id):
        key = (node.exec_id, node.variable, node.source_snippet)
        if key in seen:
            continue
        seen.add(key)
        unique_nodes.append(node)

    failure_node = next((node for node in unique_nodes if node.role == "failure" and node.failure), unique_nodes[-1])
    failure_info = failure_node.failure or FailureInfo(
        cell_id=failure_node.cell_id,
        exec_id=failure_node.exec_id,
        exc_type="",
        exc_message="",
        failing_line=failure_node.source_snippet,
    )

    hops: list[CausalHop] = []
    for index, node in enumerate(unique_nodes):
        if node.role == "failure" or node.exec_id == failure_info.exec_id:
            role = "failure"
        elif index == 0:
            role = "root_cause"
        else:
            role = "intermediate"
        hops.append(
            CausalHop(
                cell_id=node.cell_id,
                exec_id=node.exec_id,
                variable=node.variable,
                summary=node.summary,
                source_snippet=node.source_snippet,
                role=role,
            )
        )

    return CausalPath(failure=failure_info, hops=hops)

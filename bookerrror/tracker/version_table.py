"""Variable ownership tracking for the execution graph."""

from __future__ import annotations


class VersionTable:
    """Track the current owner for each variable name."""

    def __init__(self) -> None:
        self.current_owner: dict[str, int] = {}

    def get_owner(self, variable: str) -> int | None:
        """Return the exec_id that currently owns a variable."""

        return self.current_owner.get(variable)

    def set_owner(self, variable: str, exec_id: int) -> None:
        """Record a new owner for a variable."""

        self.current_owner[variable] = exec_id

    def update(self, writes: set[str], exec_id: int) -> None:
        """Record that an execution now owns the given variables."""

        for variable in writes:
            self.current_owner[variable] = exec_id

    def snapshot(self) -> dict[str, int]:
        """Return a copy of the current ownership table."""

        return dict(self.current_owner)

    def reset(self) -> None:
        """Clear all tracked variable ownership."""

        self.current_owner.clear()

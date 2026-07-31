"""Variable ownership tracking for the execution graph."""

from __future__ import annotations


class VersionTable:
    """Track the current owner for each variable name."""

    def __init__(self) -> None:
        self.current_owner: dict[str, int] = {}

    def get_owner(self, variable: str) -> int | None:
        """Return the exec_id that currently owns a variable."""

        pass

    def set_owner(self, variable: str, exec_id: int) -> None:
        """Record a new owner for a variable."""

        pass

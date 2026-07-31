"""IPython hook registration for the tracker."""

from __future__ import annotations


def register_hooks(ipython, tracker) -> None:
    """Register tracker hooks on the active IPython shell."""

    pass


def unregister_hooks(ipython, tracker) -> None:
    """Unregister tracker hooks from the active IPython shell."""

    pass


def pre_run_cell(info) -> None:
    """Handle the pre-run cell hook."""

    pass


def post_run_cell(result) -> None:
    """Handle the post-run cell hook."""

    pass

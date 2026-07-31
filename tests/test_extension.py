"""Tests for the BookError IPython extension entry points."""

from __future__ import annotations

from types import SimpleNamespace

from bookerrror import extension


class FakeEvents:
    def __init__(self) -> None:
        self.registered = []
        self.unregistered = []

    def register(self, name, handler):
        self.registered.append((name, handler))

    def unregister(self, name, handler):
        self.unregistered.append((name, handler))


class FakeIPython:
    def __init__(self) -> None:
        self.events = FakeEvents()
        self.magic_names = []

    def register_magic_function(self, function, magic_kind, magic_name):
        self.magic_names.append((function.__name__, magic_kind, magic_name))


def test_load_and_unload_extension_registers_hooks() -> None:
    ipython = FakeIPython()

    extension.load_ipython_extension(ipython)

    assert hasattr(ipython, "_bookerrror_tracker")
    assert any(name == "pre_run_cell" for name, _ in ipython.events.registered)
    assert any(name == "post_run_cell" for name, _ in ipython.events.registered)
    assert ("bookerrror_debug", "line", "bookerrror_debug") in ipython.magic_names

    extension.unload_ipython_extension(ipython)

    assert not hasattr(ipython, "_bookerrror_tracker")
    assert any(name == "pre_run_cell" for name, _ in ipython.events.unregistered)
    assert any(name == "post_run_cell" for name, _ in ipython.events.unregistered)

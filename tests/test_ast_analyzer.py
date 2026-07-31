"""Tests for AST analysis of notebook cells."""

from __future__ import annotations

from bookerrror.tracker.ast_analyzer import analyze_cell


def test_analyze_cell_basic_assignment() -> None:
    reads, writes, defines = analyze_cell("df = pd.read_csv('data.csv')")

    assert reads == {"pd"}
    assert writes == {"df"}
    assert defines == set()


def test_analyze_cell_handles_common_write_patterns() -> None:
    source = """
import pandas as pd
from sklearn import svm

a, b = 1, 2
x += 1
for i in range(10):
    pass
with open('f') as fp:
    pass

def foo():
    return a

class Bar:
    pass

if (n := len(a)) > 10:
    pass
"""

    reads, writes, defines = analyze_cell(source)

    assert reads == {"a", "x"}
    assert writes == {"pd", "svm", "a", "b", "x", "i", "fp", "foo", "Bar", "n"}
    assert defines == {"pd", "svm", "foo", "Bar"}


def test_analyze_cell_marks_mutating_method_receiver_as_write() -> None:
    reads, writes, defines = analyze_cell("df.drop(columns=['age'])")

    assert reads == {"df"}
    assert writes == {"df"}
    assert defines == set()


def test_analyze_cell_ignores_builtins() -> None:
    reads, writes, defines = analyze_cell("result = len(range(3))")

    assert reads == set()
    assert writes == {"result"}
    assert defines == set()


def test_analyze_cell_ignores_function_local_variables() -> None:
    source = """
def process(data):
    result = data * 2
    return result

output = process(df)
"""

    reads, writes, defines = analyze_cell(source)

    assert reads == {"process", "df"}
    assert writes == {"process", "output"}
    assert defines == {"process"}


def test_analyze_cell_ignores_comprehension_targets() -> None:
    reads, writes, defines = analyze_cell("items = [x for x in values]")

    assert reads == {"values"}
    assert writes == {"items"}
    assert defines == set()


def test_analyze_cell_handles_tuple_and_starred_assignment() -> None:
    reads, writes, defines = analyze_cell("first, *rest = seq")

    assert reads == {"seq"}
    assert writes == {"first", "rest"}
    assert defines == set()


def test_analyze_cell_counts_decorator_reads() -> None:
    reads, writes, defines = analyze_cell("""
@decorator
def foo():
    return 1
""")

    assert reads == {"decorator"}
    assert writes == {"foo"}
    assert defines == {"foo"}

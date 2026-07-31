"""Shared fixture data for BookError tests."""

from __future__ import annotations

import time

from bookerrror.models import CausalHop, CausalPath, Edge, ExecutionRecord, ExceptionInfo, FailureInfo


MOCK_RECORDS = [
    ExecutionRecord(
        exec_id=0,
        cell_id="cell-1",
        timestamp=time.time(),
        source="import pandas as pd",
        reads=set(),
        writes=set(),
        defines={"pd"},
    ),
    ExecutionRecord(
        exec_id=1,
        cell_id="cell-2",
        timestamp=time.time(),
        source="df = pd.read_csv('data.csv')",
        reads={"pd"},
        writes={"df"},
        defines=set(),
    ),
    ExecutionRecord(
        exec_id=2,
        cell_id="cell-5",
        timestamp=time.time(),
        source="df = df.drop(columns=['age'])",
        reads={"df"},
        writes={"df"},
        defines=set(),
    ),
    ExecutionRecord(
        exec_id=3,
        cell_id="cell-9",
        timestamp=time.time(),
        source="result = df[['age', 'income']]",
        reads={"df"},
        writes={"result"},
        defines=set(),
        raised=ExceptionInfo(
            exc_type="KeyError",
            exc_message="'age'",
            failing_line="result = df[['age', 'income']]",
            frame_filename="<ipython-input-9>",
            frame_lineno=1,
        ),
    ),
]

MOCK_EDGES = [
    Edge(producer_exec_id=0, consumer_exec_id=1, variable="pd"),
    Edge(producer_exec_id=1, consumer_exec_id=2, variable="df"),
    Edge(producer_exec_id=2, consumer_exec_id=3, variable="df"),
]

MOCK_CAUSAL_PATH = CausalPath(
    failure=FailureInfo(
        cell_id="cell-9",
        exec_id=3,
        exc_type="KeyError",
        exc_message="'age'",
        failing_line="result = df[['age', 'income']]",
    ),
    hops=[
        CausalHop(
            cell_id="cell-2",
            exec_id=1,
            variable="df",
            summary="defined df from pd.read_csv('data.csv')",
            source_snippet="df = pd.read_csv('data.csv')",
            role="root_cause",
        ),
        CausalHop(
            cell_id="cell-5",
            exec_id=2,
            variable="df",
            summary="dropped column 'age' from df",
            source_snippet="df = df.drop(columns=['age'])",
            role="intermediate",
        ),
        CausalHop(
            cell_id="cell-9",
            exec_id=3,
            variable="df",
            summary="accessed column 'age' on df",
            source_snippet="result = df[['age', 'income']]",
            role="failure",
        ),
    ],
)

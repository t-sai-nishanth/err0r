"""Demo script to execute BookError end-to-end and display results."""

from __future__ import annotations

from types import SimpleNamespace
import os

from bookerrror.tracker.hooks import ExecutionTracker
from bookerrror.tracer import trace_error
from bookerrror.presentation.banner import render_banner
from bookerrror.presentation.path_display import render_path_text
from bookerrror.presentation.graph_widget import render_graph
from bookerrror.llm import explain


def run_demo():
    print("=" * 60)
    print("🚀 RUNNING BOOKERROR END-TO-END DEMO")
    print("=" * 60)

    tracker = ExecutionTracker()

    # Step 1: Execute Cell 1 (Import pandas)
    cell1_source = "import pandas as pd"
    cell1_result = SimpleNamespace(
        info=SimpleNamespace(raw_cell=cell1_source),
        error_in_exec=None,
        execution_count=1,
    )
    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(cell1_result)
    print("✓ Cell 1 executed: import pandas as pd")

    # Step 2: Execute Cell 2 (Read CSV into df)
    cell2_source = "df = pd.read_csv('demo/data.csv')"
    cell2_result = SimpleNamespace(
        info=SimpleNamespace(raw_cell=cell2_source),
        error_in_exec=None,
        execution_count=2,
    )
    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(cell2_result)
    print("✓ Cell 2 executed: df = pd.read_csv('demo/data.csv')")

    # Step 3: Execute Cell 5 (Drop column 'age' from df out of order)
    cell3_source = "df = df.drop(columns=['age'])"
    cell3_result = SimpleNamespace(
        info=SimpleNamespace(raw_cell=cell3_source),
        error_in_exec=None,
        execution_count=5,
    )
    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(cell3_result)
    print("✓ Cell 5 executed: df = df.drop(columns=['age'])")

    # Step 4: Execute Cell 9 (Attempt to access dropped column 'age' -> KeyError)
    cell4_source = "result = df[['age', 'income']]"
    try:
        # Raise real KeyError for traceback frame walker
        raise KeyError("'age'")
    except KeyError as exc:
        err = exc

    cell4_result = SimpleNamespace(
        info=SimpleNamespace(raw_cell=cell4_source),
        error_in_exec=err,
        execution_count=9,
    )

    print("\n💥 Cell 9 raised KeyError: 'age'")

    # Execute post_run_cell on cell 4
    tracker.pre_run_cell(SimpleNamespace())
    tracker.post_run_cell(cell4_result)

    # Extract path for display output verification
    path = trace_error(tracker.graph, err, exec_id=3)

    print("\n" + "=" * 60)
    print("📋 BOOKERROR DETERMINISTIC CAUSAL PATH (TEXT OUTPUT)")
    print("=" * 60)
    print(render_path_text(path))

    print("\n" + "=" * 60)
    print("🤖 BOOKERROR LLM PLAIN-LANGUAGE EXPLANATION")
    print("=" * 60)
    llm_output = explain(path)
    print(llm_output)

    print("\n" + "=" * 60)
    print("🎨 BOOKERROR SCIKIT-LEARN STYLE HTML PIPELINE BANNER")
    print("=" * 60)
    html_banner = render_banner(path, llm_explanation=llm_output)
    print(f"Generated HTML Banner Length: {len(html_banner)} bytes")
    print("HTML Banner contains Scikit-Learn style pipeline nodes:")
    for hop in path.hops:
        print(f"  - [{hop.role.upper()}] {hop.cell_id}: {hop.summary}")

    print("\n" + "=" * 60)
    print("📊 BOOKERROR SVG DEPENDENCY DAG WIDGET")
    print("=" * 60)
    svg_widget = render_graph(causal_path=path)
    print(f"Generated SVG Widget Length: {len(svg_widget)} bytes")

    print("\n✅ DEMO EXECUTION COMPLETE — ALL SYSTEMS OPERATIONAL!")


if __name__ == "__main__":
    run_demo()

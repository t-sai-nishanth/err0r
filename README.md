# BookError — Notebook-Aware Error Localizer ⚡

> **Deterministic, out-of-order root-cause error tracing for Jupyter Notebooks.**

---

## 📌 Overview

Jupyter notebooks are non-linear by design. Cells are often executed out of order, re-executed, or edited after downstream cells have already run. When a cell crashes with a `KeyError` or `AttributeError`, raw tracebacks show **where** it failed, but fail to show **which earlier cell execution caused the invalid state**.

**BookError** tracks execution history and variable mutations in real time. When an error occurs, BookError automatically walks the dependency graph backwards to identify the exact causal chain—and presents it directly inside the cell output block using a **Scikit-Learn style interactive pipeline diagram**.

---

## 🎯 Key Features

- ⚡ **Zero-LLM Core Engine**: The dependency graph construction and backward graph walk are 100% deterministic (millisecond scale).
- 🎨 **Scikit-Learn Style Pipeline Visualizer**: Renders interactive hop nodes directly inside the Jupyter cell output block (`[Cell 2] ➔ [Cell 5] ➔ [Cell 9]`).
- 🎯 **Cell Navigation ("Go ↗")**: Click any hop card to smoothly scroll and highlight the responsible notebook cell.
- 📊 **SVG DAG Graph Diagram**: Toggleable visual dependency graph showing variable flow across executions.
- 🤖 **Token-Efficient LLM Explanations (Layer 4)**: Option to pass *only* the 2-4 hop causal path to an LLM for 1-2 sentence student explanations (~100 tokens vs 1500+ tokens for raw tracebacks).

---

## 🏗 System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3 — Presentation                                      │
│  Scikit-Learn style pipeline banner & SVG graph visualization│
└───────────────────────────▲───────────────────────────────────┘
                             │ CausalPath (list of hops)
┌───────────────────────────┴───────────────────────────────────┐
│  Layer 2 — Root-Cause Tracer                                  │
│  Backward graph walk from the failing node                    │
└───────────────────────────▲───────────────────────────────────┘
                             │ Dependency graph (live DAG)
┌───────────────────────────┴───────────────────────────────────┐
│  Layer 1 — Execution Tracker                                  │
│  IPython hooks recording cell runs, AST reads/writes          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Token Efficiency Comparison

| Approach | Prompt Inputs | Token Count | Cost & Latency |
|---|---|---|---|
| **Naive LLM** | Full notebook text + 200-line raw traceback | ~1,500 - 3,000+ tokens | High cost, 3-5 sec delay |
| **BookError (Layer 4)** | Pre-computed 3-hop causal path string | **60 - 150 tokens** | **95% token savings**, instant local trace |

---

## 🚀 Quick Start

1. Install BookError into your environment:
   ```bash
   pip install -e .
   ```

2. Open a Jupyter Notebook:
   ```python
   %load_ext bookerrror
   import pandas as pd

   # Cell 1
   df = pd.read_csv('demo/data.csv')

   # Cell 2
   df = df.drop(columns=['age'])

   # Cell 3 (Triggers KeyError & BookError Pipeline Banner)
   result = df[['age', 'income']]
   ```

---

## 🧪 Demo Notebooks

Check out the interactive notebooks in the `demo/` directory:
- `demo/demo_keyerror.ipynb`: Out-of-order column drop & access.
- `demo/demo_attributeerror.ipynb`: Out-of-order variable overwrite.

---

## 📜 License

MIT License

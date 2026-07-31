# BookError

BookError is a notebook-aware error localizer for Jupyter. It tracks cell execution, builds a dependency graph, and traces failures back to the earlier cell that most likely caused them.

## Quick Start

1. Load the extension in a notebook.
2. Run a few cells that define and transform variables.
3. Trigger an error to see the causal path output.

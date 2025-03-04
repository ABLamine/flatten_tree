# Flatten Tree

A Python-based solution for flattening decision trees into strategies. The project reads a tree (with OR and simple conditions) from a text file, traverses it using a memory-efficient, streaming DFS, and writes out a set of simplified, non-contradictory strategies.

## Features

- **Data Model:** Uses Python `dataclasses` for strict and clear data modeling.
- **Parsing:** Processes a tree file with nodes in the format:  
  - For condition nodes:  
    `ID:[condition] yes=child_yes,no=child_no`
  - For leaf nodes:  
    `ID:leaf=value`
- **Flattening:**  
  - Transforms each root-to-leaf path into a strategy by accumulating conditions.
  - Prunes branches with contradictory (impossible) conditions.
  - Simplifies conditions (e.g., removing redundant inequalities).
  - Implements a streaming DFS to keep memory footprint below O(n) relative to the file size.
- **Extensible & Testable:**  
  - Fully modular code with unit tests.
  - Configuration via command-line arguments.

## Project Structure

```
flatten_tree/
├── datamodel.py      # Data models using dataclasses
├── parser.py         # Parser for the input tree file
├── flattener.py      # Tree flattening logic with constraint checking
└── main.py           # Main script: parses arguments, flattens tree, writes output

tests/
├── test_parser.py    # Unit tests for the parser
└── test_flattener.py # Unit tests for the flattening logic
```

## Usage

Run the main script from the command line:

```bash
python -m flatten_tree.main --input-path="tree_to_convert.txt" --output-path="strategies.txt" --root-id=0
```

## Running Tests

Make sure you have `pytest` installed, then run:

```bash
pytest
```


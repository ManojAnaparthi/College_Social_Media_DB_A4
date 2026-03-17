# Application Development and Database Index Structure Implementation

## Folder Structure

```text
College_Social_Media_DB/
	.gitignore
	README.md
	Module_A/
		requirements.txt
		report.ipynb
		database/
			__init__.py
			bplustree.py
			bruteforce.py
			table.py
			db_manager.py
			performance.py
			run_performance_tests.py
			visualizations_generator.py
			performance_results_jpgs/
			visualizations/
	Module_B/
		app/
		sql/
		requirements.txt
```

## Setup

Install dependencies from project root:

```bash
.venv\Scripts\python.exe -m pip install -r Module_A/requirements.txt
```

## Run Performance Tests

From project root:

```bash
.venv\Scripts\python.exe Module_A/database/run_performance_tests.py
```

This runs performance testing for different random key set sizes and generates:

- Performance charts in `Module_A/database/performance_results_jpgs/`
- Benchmark JSON in `Module_A/database/visualizations/benchmark_results.json`

## What Is Implemented

- SubTask 1: B+ Tree node/tree classes, insert, delete, search, range query, split/merge
- SubTask 2: PerformanceAnalyzer for timing and memory comparison
- SubTask 3: Graphviz visualization for tree structure and leaf links
- SubTask 4: Performance testing across different random key set sizes with Matplotlib plots
- Additional Layer: In-memory table/database manager API built on top of B+ Tree index

## B+ Tree Implementation (SubTask 1)

- Implemented in: Module_A/database/bplustree.py
- Main classes: BPlusTreeNode, BPlusTree
- Main operations: insert(), delete(), search(), range_query()
- Node balancing: automatic split/merge handled internally during insert/delete

## Performance Analysis (SubTask 2)

- Implemented in: Module_A/database/performance.py
- Main class: PerformanceAnalyzer
- Benchmarks: insert, search, delete, range_query, mixed workload
- Memory measurement: tracemalloc peak memory tracking
- Comparison target: Module_A/database/bruteforce.py (BruteForceDB)

## Graphviz Implementation (SubTask 3)

- Implemented in: Module_A/database/bplustree.py
- Main method: BPlusTree.visualize_tree()
- Helper methods: _add_nodes() and _add_edges()
- Current output folder for visualization files: Module_A/database/visualizations/
- Existing generated files: Module_A/database/visualizations/bplustree_demo.png, Module_A/database/visualizations/bplustree_demo_large.png

## Performance Testing Implementation (SubTask 4)

- Implemented in: Module_A/database/visualizations_generator.py
- Main function: run_full_performance_analysis()
- Benchmarks used from: Module_A/database/performance.py (PerformanceAnalyzer)
- Run file: Module_A/database/run_performance_tests.py
- Output folders for generated artifacts:
	- Module_A/database/performance_results_jpgs/
	- Module_A/database/visualizations/
- Generated files include:
	- JPG charts: performance_insert.jpg, performance_search.jpg, performance_delete.jpg, performance_range_query.jpg, performance_random_workload.jpg, performance_memory_usage.jpg, performance_combined_comparison.jpg, performance_speedup_ratio.jpg
	- Benchmark data: benchmark_results.json

## Table and DB Manager Layer (Additional)

- Implemented in:
	- Module_A/database/table.py
	- Module_A/database/db_manager.py
- Purpose:
	- Provide a simple DBMS-style API over the B+ Tree index.
	- Manage multiple in-memory tables cleanly.

### Features

- Table API:
	- insert(row), upsert(row), get(key), update(key, updates), delete(key)
	- range_query(start_key, end_key), all_rows(), count(), truncate()
- DBManager API:
	- create_table(name, ...), get_table(name), drop_table(name)
	- list_tables(), has_table(name)

### Quick Usage

```python
from Module_A.database import DBManager

db = DBManager()
members = db.create_table(
    name="members",
    primary_key="id",
    schema=["id", "name", "dept"],
    bplustree_order=4,
)

members.insert({"id": 1, "name": "Alice", "dept": "CSE"})
members.upsert({"id": 2, "name": "Bob", "dept": "ECE"})
members.update(1, {"dept": "AIML"})

print(members.get(1))
print(members.range_query(1, 10))
print(db.list_tables())
```

### Notes

- Primary key type is integer (`int`) to match B+ Tree indexing.
- This layer is in-memory only (no persistence yet).

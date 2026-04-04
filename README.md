# Application Development and Database Index Structure Implementation

## Folder Structure

```text
College_Social_Media_DB/
|-- .gitignore
|-- README.md
|-- Module_A/
|   |-- requirements.txt
|   |-- report.ipynb
|   `-- database/
|       |-- __init__.py
|       |-- bplustree.py
|       |-- bruteforce.py
|       |-- table.py
|       |-- db_manager.py
|       |-- transaction_manager.py
|       |-- sql_sanity.py
|       |-- performance.py
|       |-- run_performance_tests.py
|       |-- test_acid_validation.py
|       |-- test_acid_multirelation.py
|       |-- visualizations_generator.py
|       |-- performance_results_jpgs/
|       `-- visualizations/
`-- Module_B/
    |-- requirements.txt
    |-- app/
    |   |-- main.py
    |   |-- database.py
    |   |-- test_db.py
    |   `-- static/
    |       |-- login.html
    |       |-- portfolio.html
    |       |-- create-post.html
    |       |-- posts.html
    |       |-- app.js
    |       `-- styles.css
    |-- sql/
    |   |-- schema.sql
    |   `-- sample_data.sql
```

## Setup

Install dependencies from project root:

```bash
python -m pip install -r Module_A/requirements.txt
```

If you use Conda, run with your Conda Python interpreter instead of `python3` from Windows app aliases.

## Run Performance Tests

From project root:

```bash
python Module_A/database/run_performance_tests.py
```

Alternative (from Module_A/database folder):

```bash
python run_performance_tests.py
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
- Assignment 3 Module A Layer: Multi-relation ACID transactions, failure recovery, and SQL sanity-check validation

## Module A ACID Validation (Assignment 3)

### Design Summary

- B+ Tree is the primary storage for each relation.
- `DBManager` holds multiple relations, each backed by a separate B+ Tree.
- `TransactionManager` provides `BEGIN`, `COMMIT`, and `ROLLBACK` across multiple relations.
- Isolation is implemented as serialized execution (single active write transaction).
- Durability and restart recovery use committed database snapshots.
- SQL (`sqlite3`) is used as a reference/sanity-check store to compare final state with B+ Tree state.

### ACID Components

- Multi-relation transaction coordinator: `Module_A/database/transaction_manager.py`
- Database-level snapshot import/export and persistence: `Module_A/database/db_manager.py`
- Table-level state export/restore helpers: `Module_A/database/table.py`
- SQL reference comparator: `Module_A/database/sql_sanity.py`
- Single-table ACID tests: `Module_A/database/test_acid_validation.py`
- Multi-relation ACID tests (users/products/orders): `Module_A/database/test_acid_multirelation.py`

### Run Module A ACID Tests

From project root:

```bash
python -m unittest Module_A.database.test_acid_validation Module_A.database.test_acid_multirelation -v
```

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
- Helper methods: \_add_nodes() and \_add_edges()
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
  - select(predicate=None, columns=None, limit=None)
  - aggregate(operation, column=None, predicate=None) for count/sum/min/max/avg
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
- Table-level and database-level JSON snapshot persistence is available for recovery testing.


## Module B (Assignment 3): Concurrency, Failure Simulation, and Stress Testing

This repository now includes a dedicated Module B runner for Assignment 3 validation:

- Script: `Module_B/performance/run_module_b_concurrency_stress.py`
- Output artifact: `Module_B/performance/module_b_concurrency_report.json`

What it executes in one run:

- Concurrent usage simulation:
  - High-volume parallel `GET /posts` requests
  - Captures success rate, throughput, and latency (`avg`, `p50`, `p95`)
- Race-condition test (critical operation):
  - Many concurrent `POST /members/{member_id}/follow` attempts
  - Verifies final relationship cardinality is exactly one
- Failure simulation:
  - Mixed valid and intentionally invalid concurrent `POST /posts/{post_id}/comments`
  - Verifies failed operations do not cause partial count inconsistencies
- Consistency checks:
  - Validates `Post.LikeCount` vs `Like` rows
  - Validates `Post.CommentCount` vs active `Comment` rows

### Reproduce results (step-by-step commands)

Run the following from Windows PowerShell (from your cloned project root).

1. Install Module B dependencies.

```powershell
python -m pip install -r Module_B/requirements.txt
```

2. Add DB password and JWT key as environment variables.

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "<your-mysql-password>"
$env:JWT_SECRET_KEY = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

3. Ensure MySQL service is running.

4. Run SQL schema and sample data dumps.

```powershell
mysql -u "$env:DB_USER" -p"$env:DB_PASSWORD" -e "SOURCE Module_B/sql/schema.sql; SOURCE Module_B/sql/sample_data.sql;"
```

If `mysql` is not in PATH, use your local MySQL installation path for `mysql.exe`.

5. Run the app (Terminal A).

```powershell
Set-Location Module_B/app
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

6. Run the Module B stress/failure test script (Terminal B in project root).

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "<your-mysql-password>"
python Module_B/performance/run_module_b_concurrency_stress.py --base-url http://127.0.0.1:8001 --username rahul.sharma@iitgn.ac.in --password password123 --post-id 1 --race-requests 200 --failure-requests 120 --stress-requests 1000
```

Expected output summary:

- `overall_pass: true`
- `race_passed: true`
- `failure_simulation_passed: true`
- `stress_passed: true`

Generated artifact:

- `Module_B/performance/module_b_concurrency_report.json`

### Latest executed run (5 April 2026)

Source artifact:

- `Module_B/performance/module_b_concurrency_report.json`

Executed configuration:

- Base URL: `http://127.0.0.1:8001`
- User: `rahul.sharma@iitgn.ac.in`
- Race test: `200` requests, `40` workers
- Failure simulation: `120` requests, `24` workers
- Stress test: `1000` requests, `80` workers

Observed outcomes:

- `overall_pass = true`
- `race_follow_test.race_passed = true`
- `failure_simulation.failure_simulation_passed = true`
- `stress_reads.stress_passed = true`

Measured metrics:

- Race-condition test (`POST /members/{member_id}/follow`):
  - Success responses: `200/200`
  - Final relation count (`FollowerID`, `FollowingID`): `1`
  - Latency: avg `190.882 ms`, p95 `250.252 ms`
- Failure simulation (`POST /posts/{post_id}/comments`, mixed valid+invalid):
  - HTTP status histogram: `200=60`, `400=60`
  - Expected comment delta: `60`, actual comment delta: `60`
  - Cleanup rows soft-deleted: `60`
  - Post counter consistency remained valid before and after test
- Stress test (parallel `GET /posts`):
  - Success rate: `1.0` (`1000/1000`)
  - Throughput: `295.85 req/s`
  - Latency: avg `259.644 ms`, p95 `300.963 ms`

### Transaction and race-safety hardening in API layer

For Module B Assignment 3 correctness under concurrent writes, critical multi-step write paths in `Module_B/app/main.py` now execute in single DB transactions using `execute_transaction` from `Module_B/app/database.py`:

- `POST /signup` (Member + AuthCredential)
- `POST /admin/members` (Member + AuthCredential)
- `POST /members/{member_id}/follow` (idempotent under races)
- `POST /posts/{post_id}/like/toggle` (like row + counter update)
- `POST /posts/{post_id}/comments` (comment row + counter update)
- `DELETE /comments/{comment_id}` (soft-delete + counter update)

### Module B changes made for Assignment 3 spec compliance

The following changes were implemented to satisfy concurrent workload, failure handling, and correctness requirements.

1. Atomic multi-step write execution

- Added `execute_transaction(...)` in `Module_B/app/database.py` for explicit begin/commit/rollback behavior.
- Added DB error-code propagation (`DatabaseQueryError.error_code`) to handle duplicate-key races cleanly.

2. Race-condition control for shared operations

- Updated follow creation flow in `POST /members/{member_id}/follow` to be idempotent under concurrent attempts.
- Updated post like toggle flow in `POST /posts/{post_id}/like/toggle` to perform row-level lock/read-modify-write in one transaction.

3. Failure handling without partial writes

- Updated comment creation and deletion flows to maintain `Post.CommentCount` atomically with `Comment` row writes.
- Updated signup/admin member creation to ensure `Member` and `AuthCredential` are always inserted together or rolled back together.

4. Stress and correctness validation tooling

- Added `Module_B/performance/run_module_b_concurrency_stress.py` to execute:
  - concurrent usage test
  - race-condition test
  - failure simulation test
  - high-load stress test
- Added consistency assertions in the runner for:
  - `Post.LikeCount` vs `Like` rows
  - `Post.CommentCount` vs active `Comment` rows

5. ACID-oriented validation evidence (Module B scope)

- Atomicity: multi-step writes are wrapped in transactions.
- Consistency: pre/post consistency checks pass in generated report.
- Isolation (practical): race test confirms single follow edge under 200 concurrent attempts.
- Durability: committed changes are persisted in MySQL and captured in report artifacts.

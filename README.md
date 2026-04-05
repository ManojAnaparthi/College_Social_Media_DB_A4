# Application Development and Database Index Structure Implementation

## Folder Structure

```text
College_Social_Media_DB_A3/
|-- .gitignore
|-- README.md
|-- Module_A/
|   |-- requirements.txt
|   |-- report.ipynb
|   |-- run_acid_tests.py           Test runner
|   |-- run_demo.py                 Interactive demo runner
|   |-- video_demo.py               Video demo script
|   `-- database/
|       |-- __init__.py
|       |-- bplustree.py           # B+ Tree storage engine
|       |-- bruteforce.py
|       |-- table.py               # Table abstraction
|       |-- db_manager.py          # Multi-table manager
|       |-- transaction_manager.py # ACID coordinator
|       |-- sql_sanity.py          # SQLite validator
|       |-- test_acid_multirelation.py   Main ACID tests
|       |-- acid_demonstration.py   Interactive demo
|       |-- performance.py
|       |-- run_performance_tests.py
|       |-- visualizations_generator.py
|       |-- performance_results_jpgs/
|       `-- visualizations/
`-- Module_B/
    |-- requirements.txt
    |-- report.ipynb
    |-- report.tex
    |-- modB_dash.png
    |-- locust_dash.png
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
    `-- performance/
        |-- run_module_b_concurrency_stress.py
        |-- run_module_b_locust_profiles.py
        `-- locustfile_module_b.py
```

## Setup

Install dependencies from project root:

```bash
python -m pip install -r Module_A/requirements.txt
```

If you use Conda, run with your Conda Python interpreter instead of `python3` from Windows app aliases.

## Module A: ACID Validation for B+ Tree Database (Assignment 3)

### Overview

Module A extends the B+ Tree database system from Assignment 2 to support **transaction management**, **failure recovery**, and **ACID guarantees** across **at least 3 relations**.

**Key Features:**

-  Atomicity: Multi-relation transactions are all-or-nothing
-  Consistency: Database maintains valid state with constraints
-  Isolation: Transactions execute serially without interference
-  Durability: Committed data persists across system crashes

### Three-Relation Schema (College Social Media)

1. **Members** - User accounts (MemberID, Name, Department, Reputation)
2. **Posts** - User posts (PostID, MemberID, Content, LikeCount)
3. **Comments** - Post comments (CommentID, PostID, MemberID, Content, LikeCount)

**Storage:** Each relation stored in a separate B+ Tree where primary key = B+ Tree key and complete record = B+ Tree value.

### ACID Implementation

**Atomicity:** Deep copy of database state before transaction; restore on rollback

**Consistency:** Schema validation + referential integrity checks

**Isolation:** Threading.RLock ensures serialized execution (one active transaction at a time)

**Durability:** JSON snapshot persisted to disk on COMMIT; loaded on restart

### Quick Start

#### Run ACID Tests

From Module_A directory:

```bash
cd Module_A
python run_acid_tests.py
```

**Expected Output:**

```
test_atomicity_multi_relation_rollback_on_failure ... ok
test_consistency_constraints_after_commit ... ok
test_durability_and_recovery_across_restart ... ok
test_isolation_serialized_execution ... ok

Ran 4 tests in 0.213s
OK 
```

#### Run Interactive Demo

```bash
cd Module_A
python run_demo.py
```

#### Run Video Demo (with step-by-step pauses)

```bash
cd Module_A
python video_demo.py
```

### Key Components

**Core Implementation:**

- `database/bplustree.py` - B+ Tree storage engine
- `database/table.py` - Table abstraction with B+ Tree backing
- `database/db_manager.py` - Multi-table database manager
- `database/transaction_manager.py` - Transaction coordinator (BEGIN/COMMIT/ROLLBACK)
- `database/sql_sanity.py` - SQLite-based validation reference

**Testing:**

- `database/test_acid_multirelation.py` -  Main test suite (all 4 ACID properties across 3 relations)
- `database/acid_demonstration.py` - Interactive demonstration script
- `run_acid_tests.py` - Test runner
- `video_demo.py` - Video demonstration script

### Test Coverage

All 4 tests operate on **3 relations simultaneously**:

| Test                                                  | What It Does                                                                             |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **test_atomicity_multi_relation_rollback_on_failure** | Updates Member + Post + Insert Comment → Simulate failure → Verify complete rollback     |
| **test_consistency_constraints_after_commit**         | Verify referential integrity (Comments reference valid Members & Posts)                  |
| **test_isolation_serialized_execution**               | Start TX1 → Attempt TX2 concurrently → Verify TX2 blocked                                |
| **test_durability_and_recovery_across_restart**       | Commit TX → Start uncommitted TX → Simulate crash → Verify only committed data recovered |

### Demonstration Example

**Atomicity Test - Before/During/After Rollback:**

| Table             | Before TX | During TX | After Rollback |
| ----------------- | --------- | --------- | -------------- |
| Member Reputation | 100       | 85      | 100          |
| Post LikeCount    | 5         | 10      | 5            |
| Comment 1001      | Not exist | Exists  | Not exist    |

**Result:** All 3 tables rolled back together - transaction is atomic!

### Notes

- Primary key type is integer (`int`) to match B+ Tree indexing.
- Table-level and database-level JSON snapshot persistence is available for recovery testing.

## Module B (Assignment 3): Concurrency, Failure Simulation, and Stress Testing

This module contains the FastAPI + MySQL application and Assignment 3 validation workflow for concurrency, race handling, failure simulation, and stress testing.

### What Is In Module B

```text
Module_B/
|-- requirements.txt
|-- report.ipynb
|-- modB_dash.png
|-- locust_dash.png
|-- .gitignore
|-- app/
|   |-- main.py
|   |-- database.py
|   |-- test_db.py
|   `-- static/
|-- sql/
|   |-- schema.sql
|   |-- sample_data.sql
|   `-- sample_passwords.txt
|-- performance/
|   |-- run_module_b_concurrency_stress.py
|   |-- run_module_b_locust_profiles.py
|   |-- locustfile_module_b.py
    |-- module_b_concurrency_report.json
|   `-- index_benchmark_results.json
`-- logs/
    `-- audit.log
```

Generated run artifacts (CSV and JSON reports) are intentionally cleaned before commit.

### Notebook Testing


All reported metrics and dashboard results in this Module B section are generated from notebook execution while the API runs in a background terminal.

The notebook contains an end-to-end flow:

1. environment/path setup
2. test configuration
3. preflight checks (runner + API + auth + feed)
4. expanded workload matrix execution
5. pass/fail summary and assertions
6. artifact export

### Dashboard Snapshots

Main matrix dashboard (Assignment 3 notebook runner):

![Module B Matrix Dashboard](Module_B/modB_dash.png)

Supplementary Locust dashboard (smoke, medium, high):

![Module B Locust Dashboard](Module_B/locust_dash.png)

### Notebook Matrix Configuration

| Profile | Race Req | Race Wk | Fail Req | Fail Wk | Stress Req | Stress Wk |
|---------|----------|---------|----------|---------|------------|-----------|
| smoke   | 200      | 40      | 120      | 24      | 1000       | 80        |
| medium  | 500      | 80      | 300      | 48      | 3000       | 120       |
| high    | 1000     | 120     | 600      | 80      | 5000       | 160       |

### Default Locust Profile Matrix

| Profile | Users | Spawn Rate | Run Time |
|---------|-------|------------|----------|
| smoke   | 30    | 6          | 90s      |
| medium  | 80    | 12         | 3m       |
| high    | 160   | 20         | 5m       |

### Current Notebook State (Latest)

- The notebook has 17 cells total.
- Code cells executed successfully in order.
- Preflight passed (`ready_for_matrix = true`) in the latest run.
- Matrix profiles completed: `smoke`, `medium`, `high`.

### Setup

Run from project root (`DB_A3`).

#### 1) Install dependencies

```powershell
python -m pip install -r Module_B/requirements.txt
```

#### 2) Set environment variables

```powershell
$env:DB_HOST = "localhost"
$env:DB_USER = "root"
$env:DB_PASSWORD = "<your-mysql-password>"
$env:DB_NAME = "college_social_media"
$env:JWT_SECRET_KEY = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

#### 3) Load SQL schema and sample data

```powershell
mysql -u "$env:DB_USER" -p"$env:DB_PASSWORD" -e "SOURCE Module_B/sql/schema.sql; SOURCE Module_B/sql/sample_data.sql;"
```

### Running Module B

#### Terminal A: Start API

```powershell
Set-Location Module_B/app
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

#### Run notebook

Open `Module_B/report.ipynb` and run cells top-to-bottom.

### Testing Range

The notebook uses a profile matrix in its configuration cell:

- smoke: race 200, failure 120, stress 1000
- medium: race 500, failure 300, stress 3000
- high: race 1000, failure 600, stress 5000
- optional extreme profile via `RUN_EXTREME = True`

### CLI Alternative (Optional)

Optional standalone run for manual verification only (not the source of reported results in this README):

```powershell
python Module_B/performance/run_module_b_concurrency_stress.py --base-url http://127.0.0.1:8001 --usernames "rahul.sharma@iitgn.ac.in,priya.patel@iitgn.ac.in,ananya.singh@iitgn.ac.in,neha.desai@iitgn.ac.in,aditya.verma@iitgn.ac.in" --password password123 --post-id 1 --race-requests 200 --failure-requests 120 --stress-requests 1000
```

### Supplementary Extensive Locust Testing (Optional)

Locust testing is also executed through notebook cells in `Module_B/report.ipynb`.
The command below is an optional standalone equivalent for manual runs:

```powershell
python Module_B/performance/run_module_b_locust_profiles.py --base-url http://127.0.0.1:8001 --usernames "rahul.sharma@iitgn.ac.in,priya.patel@iitgn.ac.in,ananya.singh@iitgn.ac.in,neha.desai@iitgn.ac.in,aditya.verma@iitgn.ac.in" --password password123 --post-id 1 --target-member-id 19 --profiles smoke,medium,high --max-error-rate 0.05 --max-p95-ms 1500
```

What this runs:

- profile-based Locust workloads (`smoke`, `medium`, `high`)
- read-heavy traffic plus controlled write round-trips (likes/comments/follows)
- threshold-based pass/fail checks (`error_rate`, optional `p95` cap)

Artifacts generated by notebook Locust cells (and by the optional standalone command):

- `Module_B/performance/locust_smoke_*.csv`
- `Module_B/performance/locust_medium_*.csv`
- `Module_B/performance/locust_high_*.csv`
- `Module_B/performance/module_b_locust_report_smoke.json`
- `Module_B/performance/module_b_locust_report_medium.json`
- `Module_B/performance/module_b_locust_report_high.json`
- `Module_B/performance/module_b_locust_profiles_report.json`

These are generated at runtime and are removed during cleanup so repository commits stay source-focused.

### What Is Validated

- Atomicity of critical multi-step write endpoints
- Race safety for concurrent follow operations
- Failure behavior under mixed valid/invalid writes
- Counter consistency (`Post.LikeCount`, `Post.CommentCount`)
- Stress behavior (success rate, throughput, latency percentiles)

### Changes Implemented in Module B for Assignment 3

#### Database Layer (`database.py`)

- Standard DB connection setup
    One consistent way to handle connections, with or without transactions.
- Centralized query execution
    A single helper handles all SQL operations, giving consistent results and error handling.
- Transaction support
    Auto commit on success and rollback on failure, ensuring safe multi-step operations.
- Audit metadata support
    Every DB write can include metadata like user, action, and endpoint.
- Custom DB exception
    Makes it easier for the API layer to handle database errors cleanly.

#### API Layer (`main.py`)

- Reusable auth and audit helpers
    Standardized admin checks and logging across endpoints.
- Transaction-based endpoints
    Critical operations run safely inside transactions for ACID compliance.
- Row-level locking
    Prevents race conditions in operations like likes and comments.
- Admin audit endpoints
    Allows admins to view logs and track DB/API write changes.

These are the backend changes implemented in Module B for this assignment.



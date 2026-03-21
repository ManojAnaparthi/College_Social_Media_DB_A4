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
|       |-- performance.py
|       |-- run_performance_tests.py
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

- Sampling strategy used in `run_performance_tests.py`:
  - dense at smaller sizes: `range(100, 10100, 1000)`
  - coarser at larger sizes: `range(10100, 100001, 10000)`

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
- This layer is in-memory only (no persistence yet).

## Module B: Local API, UI, and Security (SubTask 1, 2, and 3)

This section documents the implementation status for Module B SubTask 1, SubTask 2, and SubTask 3.

### Scope Covered

- SubTask 1: Local environment setup and core/project data integrity
- SubTask 2: Session-validated APIs and web UI for CRUD + member portfolio with restricted access
- SubTask 3: Strict RBAC and security logging with unauthorized direct-DB-change traceability

### Module B Structure

```text
Module_B/
|-- requirements.txt
|-- app/
|   |-- main.py              # FastAPI app, auth/session, portfolio, post/comment CRUD
|   |-- database.py          # MySQL connection helper
|   |-- test_db.py           # DB connectivity smoke test
|   `-- static/
|       |-- login.html       # Login page
|       |-- signup.html      # Optional demo signup page
|       |-- portfolio.html   # Portfolio page with member profile lookup
|       |-- create-post.html # Dedicated create post page
|       |-- posts.html       # Dedicated posts listing page
|       |-- app.js           # Frontend logic and navigation
|       `-- styles.css       # Shared styles
|-- sql/
|   |-- schema.sql           # Core + project table schema with FK constraints
|   |-- sample_data.sql      # Demo dataset
|   `-- sample_passwords.txt # Sample IDs/emails mapped to shared demo password
`-- logs/
  `-- audit.log            # API security audit trail
```

### Setup (Module B)

1. Install Module B dependencies:

```bash
pip install -r Module_B/requirements.txt
```

2. Run the schema and load sample data in local MySQL:

```sql
SOURCE Module_B/sql/schema.sql;
SOURCE Module_B/sql/sample_data.sql;
```

Sample login note:
- `Module_B/sql/sample_passwords.txt` contains the sample user IDs/emails and their demo credentials.
- All seeded sample users share the same password: `password123`.

3. Run API server:

```bash
cd Module_B/app
uvicorn main:app --reload --port 8001
```

If you are on Windows PowerShell, set the DB password environment variable before starting the API:

```powershell
$env:DB_PASSWORD="<your-mysql-password>"

cd Module_B/app
uvicorn main:app --reload --port 8001
```

Optional (persist across new PowerShell sessions):

```powershell
setx DB_PASSWORD "<your-mysql-password>"
```
**DON'T TRY TO SET THE PASSWORD IN database.py**

## Module B SubTask 4 and 5 (Indexing + Benchmarking)

### What was corrected

- Benchmarking now uses a strict two-stage method in `Module_B/app/run_index_benchmark.py`:
  - `before_indexes`: drops optimization indexes that help tested endpoints.
  - `after_indexes`: creates only targeted optimization indexes.
- FK-support baseline indexes are kept in both stages so schema integrity is preserved.

### Targeted indexes and API mapping

1. `idx_post_active_postdate_postid ON Post(IsActive, PostDate DESC, PostID DESC)`
   - API query pattern: post feed listing
  - Clauses targeted: `WHERE p.IsActive = TRUE`, `ORDER BY p.PostDate DESC, p.PostID DESC`

2. `idx_comment_post_active_date ON Comment(PostID, IsActive, CommentDate ASC)`
   - API query pattern: comments under a post
   - Clauses targeted: `WHERE c.PostID = ? AND c.IsActive = TRUE`, `ORDER BY c.CommentDate ASC`

Schema location: `Module_B/sql/schema.sql`

### Evidence artifacts

- Benchmark output JSON (same params for both stages, API + SQL timings, EXPLAIN):
  - `Module_B/performance/index_benchmark_results.json`
- Benchmark runner:
  - `Module_B/app/run_index_benchmark.py`

### Latest measured impact

- SQL speedup:
  - posts: `1.129x`
  - comments: `1.162x`
- API speedup:
  - posts: `0.983x`
  - comments: `1.045x`

### EXPLAIN plan change proof (comments endpoint)

- Before:
  - key: `idx_comment_post`
  - extra: `Using where; Using filesort`
- After:
  - key: `idx_comment_post_active_date`
  - extra: `Using index condition`

This demonstrates a direct plan change for the comments hotspot after applying the composite index.

4. Open UI:

- http://127.0.0.1:8001/

### SubTask 1: Local Environment Setup and Data Integrity

Implemented:

- Core identity/auth separation:
  - `Member` table stores profile/core member data.
  - `AuthCredential` stores login credentials (linked 1:1 to `Member`).
- Project-specific tables (`Post`, `Comment`, `Follow`, `GroupMember`, etc.) are separated from credential storage.
- Referential integrity is enforced through foreign keys with cascades.
- Schema includes business-rule triggers and consistency constraints.

Evidence in code:

- `Module_B/sql/schema.sql`:
  - `CREATE TABLE Member`
  - `CREATE TABLE AuthCredential` with `FOREIGN KEY (MemberID) REFERENCES Member(MemberID) ON DELETE CASCADE`
  - Project tables with `FOREIGN KEY ... ON DELETE CASCADE`

### SubTask 2: API and UI Development

Implemented APIs (session-aware):

- Auth/session:
  - `POST /signup` (optional demo path; creates `Student` account)
  - `POST /login`
  - `GET /isAuth`
  - `POST /logout`
- Portfolio:
  - `GET /portfolio/{member_id}`
  - `PUT /portfolio/{member_id}`
- Project table CRUD (`Post`):
  - `POST /posts`
  - `GET /posts`
  - `GET /posts/{post_id}`
  - `PUT /posts/{post_id}`
  - `DELETE /posts/{post_id}`
- Additional project CRUD (`Comment`):
  - `POST /posts/{post_id}/comments`
  - `GET /posts/{post_id}/comments`
  - `PUT /comments/{comment_id}`
  - `DELETE /comments/{comment_id}`

Implemented web UI pages:

- `login.html`: authentication page
- `signup.html`: optional demo self-signup page
- `portfolio.html`: own portfolio + restricted member profile lookup by MemberID
- `create-post.html`: dedicated create-post form
- `posts.html`: dedicated all-posts listing with edit/delete controls
  - Current behavior: loads the latest 30 posts per request (`GET /posts?limit=30&offset=0`).

Session validation behavior:

- Protected APIs are guarded using local JWT session validation dependency.
- Login uses bcrypt hash verification only (no dummy-password fallback).
- UI stores session locally and redirects unauthenticated users to login.

Member Portfolio access restriction behavior:

- Only authenticated users can access portfolio pages/endpoints.
- Users can view:
  - their own profile
  - admin-authorized profiles
  - profiles permitted by access rule logic in backend
- Unauthorized profile requests return permission errors and are shown clearly in UI.

### SubTask 3: Role-Based Access Control (RBAC) and Security Logging

Implemented RBAC behavior:

- Admin-only actions are enforced for core administrative operations:
  - Member management (`/admin/members`, `/admin/members/{member_id}`)
  - Group membership administration (`/admin/groups/{group_id}/members`, `/admin/groups/{group_id}/members/{member_id}`)
- Official member creation path is admin-managed via `/admin/members`.
- Public `/signup` is kept only as an optional demo convenience and always creates `Student` role accounts.
- Regular users are restricted to their own modifiable records for portfolio/posts/comments where applicable.
- Unauthorized modification attempts return 403 and are logged.

Implemented logging behavior:

- Local file-based audit log is written to:
  - `Module_B/logs/audit.log`
- API write actions and denied attempts are captured with actor, endpoint, method, table, and outcome metadata.
- Admin endpoint to inspect API audit trail:
  - `GET /admin/audit-log`

Direct database modification traceability (unauthorized detection):

- Dedicated DB write log table:
  - `ApiWriteLog` in `Module_B/sql/schema.sql`
- Triggers record write source for key tables (`Member`, `Post`, `Comment`, `GroupMember`) and classify writes as:
  - `API` (authorized session-validated API write)
  - `DIRECT_DB` (direct SQL write, treated as unauthorized)
- Admin endpoint for DB-level change review:
  - `GET /admin/db-change-log`
  - `GET /admin/db-change-log?unauthorized_only=true`

This ensures any direct DB write that bypasses API/session validation is easily identifiable during log review.

### Requirement-to-Implementation Mapping

- "Develop web-based UI and local APIs for CRUD on project-specific tables":
  - Done via Post and Comment API endpoints + dedicated UI pages.
- "Ensure every API call validates user session via local auth":
  - Done for protected business endpoints through token validation dependency.
- "Member Portfolio with authenticated and permission-restricted viewing":
  - Done via portfolio endpoints and UI lookup workflow with backend authorization checks.
- "Strict RBAC (Admin vs Regular User) for API/UI operations":
  - Done via admin-only endpoint guard and owner/admin checks on update/delete flows.
- "Log all data-modifying API calls locally and identify unauthorized direct DB modifications":
  - Done via `Module_B/logs/audit.log` (API audit) and `ApiWriteLog` + triggers (DB write-source tracing).

### Deliverables Format Check (Up to SubTask 3)

- Source code scripts:
  - Present in `Module_B/app/` and `Module_B/app/static/`
- SQL scripts:
  - Present in `Module_B/sql/schema.sql` and `Module_B/sql/sample_data.sql`
- Security logs:
  - Present in `Module_B/logs/audit.log`

### Notes for Demo

- Recommended login with sample data uses email from `sample_data.sql` and password `password123` (see `Module_B/sql/sample_passwords.txt`).
- Demonstrate both permitted and denied portfolio/profile access in UI for clear evaluation evidence.

# CS 432 - Assignment 4: Sharding of the Developed Application

## Project Objective
Implement logical data partitioning (sharding) across multiple simulated nodes/tables by selecting a suitable shard key, routing queries correctly, and analyzing scalability trade-offs.

## Core Technical Pipeline
- Shard Key Selection
- Data Partitioning
- Query Routing
- Scalability Analysis

## Sub-task 1: Shard Key Selection and Justification

### 1. Chosen Shard Key
Shard key: MemberID

### Why MemberID satisfies the required criteria
1. High cardinality
- MemberID is an auto-increment primary key, so it grows with users and is naturally high-cardinality.

2. Query-aligned
- Many core API routes are member-centric, for example portfolio, follow/follower relations, and member post listing.
- This means routing by MemberID aligns with frequent lookup and write paths.

3. Stable
- MemberID does not change after insertion, so records do not need re-sharding because of key updates.

### 2. Partitioning Strategy
Chosen strategy: Hash-based sharding

Routing function (for 3 shards):

shard_id = MemberID % 3

### Why hash-based is suitable here
- Better balance than range sharding for growing auto-increment IDs.
- Simple deterministic routing in application code.
- Works well for single-key lookups and inserts when MemberID is known.

### 3. Estimated Distribution and Skew Risk

#### Current sample estimate (from seed data)
- Members (20 rows): IDs 1..20 produce near-even distribution across 3 shards
  - Shard 0: 6
  - Shard 1: 7
  - Shard 2: 7

- Posts (20 rows, sharded by author `MemberID`):
  - Shard 0: 4
  - Shard 1: 9
  - Shard 2: 7

- Comments (20 rows, sharded by author `MemberID`):
  - Shard 0: 6
  - Shard 1: 11
  - Shard 2: 3

These post/comment counts come from the current sample workload and show realistic activity skew (power users), even when the shard key itself is reasonable.


#### Skew risks to note
- Power users can create many posts/comments and overload one shard.
- Social graph hotspots (many followers of one member) can create uneven load patterns.
- Global feed/search endpoints may require fan-out queries across shards.

### 4. Note on Candidate Keys Not Chosen
- Department is available but low-cardinality and likely skewed.
- Range-based MemberID sharding could create hot future shards as IDs increase.

Hence, hash(MemberID) is the most practical choice for this codebase.

## Sub-task 2: Implement Data Partitioning

### Shard Tables Created

**File: `sql/sharding.sql`**

Three shard tables are created for each of the three most frequently accessed tables, following the required naming convention:

| Base Table | Shard 0 | Shard 1 | Shard 2 |
|---|---|---|---|
| Member | `shard_0_member` | `shard_1_member` | `shard_2_member` |
| Post | `shard_0_post` | `shard_1_post` | `shard_2_post` |
| Comment | `shard_0_comment` | `shard_1_comment` | `shard_2_comment` |

Each shard table mirrors the source table's schema (without cross-shard foreign keys, which cannot be enforced in a distributed system) and adds a `ShardID` bookkeeping column.

### Migration

Data is migrated from the canonical tables into the shard tables using:

```sql
-- Example for Member shard 0
INSERT INTO shard_0_member (...)
SELECT ... FROM Member WHERE (MemberID % 3) = 0;
```

The same pattern is applied for all three tables across all three shards.

### Verification

The script includes `SELECT COUNT(*)` checks that compare:
- Source table total vs. sum of all shard totals (must be equal — no data loss)
- Cross-shard duplicate check (must return 0 rows — no duplication)

**Expected distribution with 20 members (IDs 1–20):**
- Shard 0 (MemberID % 3 = 0): Members 3, 6, 9, 12, 15, 18 → **6 members**
- Shard 1 (MemberID % 3 = 1): Members 1, 4, 7, 10, 13, 16, 19 → **7 members**
- Shard 2 (MemberID % 3 = 2): Members 2, 5, 8, 11, 14, 17, 20 → **7 members**

Run the sharding script:
```bash
mysql -u root -p college_social_media < sql/sharding.sql
```

### Distributed Shard Deployment (Remote Assignment Environment)

In the assignment deployment, sharding was executed on three real MySQL instances running on one remote host:

- Host: `10.0.116.184`
- Shard 0: port `3307`
- Shard 1: port `3308`
- Shard 2: port `3309`

This means each shard is a separate database server process (separate port), not just separate tables in one local instance.

#### Operational workflow used

For each shard instance:

1. Load schema into `maaps` database
2. Load sample data
3. Drop cross-shard FK constraints for `Post` and `Comment` (to avoid cascade deletions during horizontal filtering)
4. Apply shard filter script to keep only that shard's partition by hash rule

Applied filter rule:

```
shard_id = MemberID % 3
```

#### Why a no-trigger schema file was required

Remote shard servers had binary logging enabled and restricted privileges, so trigger creation failed with:

```
ERROR 1419 (HY000): You do not have the SUPER privilege ...
```

To stay within assignment rules (no admin/system changes), deployment used `sql/schema_maaps_no_triggers.sql`, which preserves core tables and indexes but omits trigger definitions.

#### Why FK removal was required before filtering

The base schema defines FK relationships such as `Comment -> Post` and `Comment -> Member` with cascade behavior.
If rows are filtered independently by shard, cross-shard parent-child references can trigger unintended cascade deletes.

To prevent this, `sql/distributed_drop_cross_shard_fks.sql` was executed before shard filtering.

#### Verified final shard distribution (20-row sample)

- Shard 0 (`3307` / host `977af97a9799`):
  - Member: 6
  - Post: 4
  - Comment: 6
- Shard 1 (`3308` / host `2cffc9b7df77`):
  - Member: 7
  - Post: 9
  - Comment: 11
- Shard 2 (`3309` / host `5629a0278cb0`):
  - Member: 7
  - Post: 7
  - Comment: 3

These totals match hash-partition expectations for the provided sample workload and confirm that data was distributed across all three shards without loss.

#### Runbook: Remote 3-Shard Setup

Run the following from the project root (`College_Social_Media_DB_A4`):

```bash
# -----------------------------
# Shard 1 (port 3308): keep MemberID % 3 = 1
# -----------------------------
mysql -h 10.0.116.184 -P 3308 -u maaps -p maaps < sql/schema_maaps_no_triggers.sql
mysql -h 10.0.116.184 -P 3308 -u maaps -p maaps < sql/sample_data_maaps.sql
mysql -h 10.0.116.184 -P 3308 -u maaps -p maaps < sql/distributed_drop_cross_shard_fks.sql
mysql -h 10.0.116.184 -P 3308 -u maaps -p maaps < sql/distributed_shard1_filter.sql

# -----------------------------
# Shard 2 (port 3309): keep MemberID % 3 = 2
# -----------------------------
mysql -h 10.0.116.184 -P 3309 -u maaps -p maaps < sql/schema_maaps_no_triggers.sql
mysql -h 10.0.116.184 -P 3309 -u maaps -p maaps < sql/sample_data_maaps.sql
mysql -h 10.0.116.184 -P 3309 -u maaps -p maaps < sql/distributed_drop_cross_shard_fks.sql
mysql -h 10.0.116.184 -P 3309 -u maaps -p maaps < sql/distributed_shard2_filter.sql

# -----------------------------
# Shard 0 (port 3307): keep MemberID % 3 = 0
# -----------------------------
mysql -h 10.0.116.184 -P 3307 -u maaps -p maaps < sql/schema_maaps_no_triggers.sql
mysql -h 10.0.116.184 -P 3307 -u maaps -p maaps < sql/sample_data_maaps.sql
mysql -h 10.0.116.184 -P 3307 -u maaps -p maaps < sql/distributed_drop_cross_shard_fks.sql
mysql -h 10.0.116.184 -P 3307 -u maaps -p maaps < sql/distributed_shard0_filter.sql
```

Quick verification (run on each shard after setup):

```sql
SELECT @@hostname;
SELECT COUNT(*) AS MemberCount  FROM Member;
SELECT COUNT(*) AS PostCount    FROM Post;
SELECT COUNT(*) AS CommentCount FROM Comment;
```

---

## Sub-task 3: Implement Query Routing

### Routing Module

**File: `app/shard_router.py`**

Central routing module that has three helpers:

```python
get_shard_id(member_id)           # → 0, 1, or 2
get_shard_table(table, member_id) # → e.g. "shard_1_post"
all_shard_tables(table)           # → ["shard_0_post", "shard_1_post", "shard_2_post"]
```

All application routing logic imports from this single module so that the shard function (`MemberID % NUM_SHARDS`) is defined once and easy to change.

### Distributed Routing Configuration

Routing now supports both modes:

1. Local simulated shard-table mode (single DB instance with `shard_*_*` tables)
2. Remote distributed shard-node mode (separate MySQL instances on ports `3307/3308/3309`)

Enable distributed routing with environment variables:

```bash
USE_DISTRIBUTED_SHARDS=1
SHARD_HOST=10.0.116.184
SHARD_DB=maaps
SHARD_PORTS=3307,3308,3309
DB_USER=maaps
DB_PASSWORD=password@123
```

In distributed mode, queries are executed against the shard node selected by `get_shard_id(MemberID)`.
Fan-out queries execute on all shard nodes and merge results in application code.

### New API Endpoints

The following shard-aware endpoints are added to `app/main.py` under the `/shards/` prefix:

| Endpoint | Method | Routing type | Description |
|---|---|---|---|
| `/shards/info` | GET | Fan-out | Shows member/post/comment counts per shard |
| `/shards/members/{member_id}` | GET | Single-key lookup | Looks up member in the correct shard |
| `/shards/members/{member_id}/posts` | GET | Single-key lookup | Gets all posts by a member from their shard |
| `/shards/members/{member_id}/comments` | GET | Single-key lookup | Gets all comments by a member from their shard |
| `/shards/posts` | GET | Fan-out (range) | Fetches public posts from all shards, merges and sorts |
| `/shards/posts` | POST | Routed insert | Creates post in canonical table + routes insert to correct shard |

In distributed mode, canonical `Member`, `Post`, and `Comment` tables on each shard node are treated as that node's local partition.
In local mode, `shard_*_*` tables are used.

#### Single-key lookup example (MemberID = 1)
```
shard_id = 1 % 3 = 1  →  query goes to shard_1_member
```

#### Range query (global feed)
All three `shard_*_post` tables are queried in parallel via fan-out, results are merged and sorted by `PostDate DESC`.

#### Insert routing (POST /shards/posts)
1. Compute `N = member_id % 3`
2. Open transaction on shard node `N`
3. Insert into that node's local `Post` table

### Assignment 2 Endpoint Routing Updates

Beyond `/shards/*`, core Assignment 2 member/post/comment API paths were updated to use shard-aware execution:

- Single-member lookups and member-centric operations route by `MemberID`
- Post/comment point operations first resolve owning shard, then execute on that shard
- Range/feed/search fan out across all shard nodes, then merge/sort/limit in app layer

This satisfies Sub-task 3 requirements for lookup routing, insert routing, and range-query fan-out in both simulated and distributed environments.

---

## Sub-task 4: Scalability and Trade-offs Analysis


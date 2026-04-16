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

#### Single-key lookup example (MemberID = 1)
```
shard_id = 1 % 3 = 1  →  query goes to shard_1_member
```

#### Range query (global feed)
All three `shard_*_post` tables are queried in parallel via fan-out, results are merged and sorted by `PostDate DESC`.

#### Insert routing (POST /shards/posts)
1. Insert into canonical `Post` table (for transactional consistency)
2. Mirror insert into `shard_{N}_post` where `N = member_id % 3`

---

## Sub-task 4: Scalability and Trade-offs Analysis


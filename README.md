# CS 432 Assignment 4: Sharding of the Developed Application

## 1. Project Objective

Implement horizontal data partitioning (sharding) for the developed social media application.

Core pipeline:

1. Shard Key Selection
2. Data Partitioning
3. Query Routing
4. Scalability and Trade-offs Analysis

This assignment extends Assignment 1 (schema), Assignment 2 (APIs/indexing), and Assignment 3 (transactions).

## 2. Implementation Summary

1. Shard key: `MemberID`
2. Strategy: Hash-based sharding

Shard function:

```text
shard_id = CRC32(str(MemberID)) % 3
```

3. Sharded entities: `Member`, `Post`, `Comment`
4. Modes supported:
   - Local simulated shard tables (`shard_0_*`, `shard_1_*`, `shard_2_*`)
   - Remote distributed shard nodes (ports `3307`, `3308`, `3309`)

## 3. Relevant Files

1. Routing helpers: `app/shard_router.py`
2. API routing logic: `app/main.py`
3. DB connections and shard config: `app/database.py`
4. Local shard SQL: `sql/sharding.sql`
5. Remote shard filters:
   - `sql/distributed_shard0_filter.sql`
   - `sql/distributed_shard1_filter.sql`
   - `sql/distributed_shard2_filter.sql`
6. FK cleanup for distributed filtering: `sql/distributed_drop_cross_shard_fks.sql`

## 4. Subtask 1: Shard Key Selection and Justification

### 4.1 Chosen Key

`MemberID`

### 4.2 Why it fits

1. High cardinality: primary key with many distinct values.
2. Query aligned: many APIs are member-centric.
3. Stable: does not change after insert.

### 4.3 Strategy Choice

Hash-based sharding (`CRC32(str(MemberID)) % 3`) was chosen for deterministic routing and good balance over time.

### 4.4 Skew Risks

1. Power users can create shard hotspots.
2. Social graph hotspots can create uneven traffic.
3. Fan-out queries are required for global feeds/search.

## 5. Subtask 2: Data Partitioning

### 5.1 Local Simulated Shards

Create and populate local shard tables:

```bash
mysql -u root -p college_social_media < sql/sharding.sql
```

### 5.2 Remote 3-Shard Deployment (PowerShell)

Target environment:

1. Host: `10.0.116.184`
2. Ports: `3307`, `3308`, `3309`
3. User/DB: `maaps`
4. Password: `password@123`

Set password:

```powershell
$env:MYSQL_PWD = "password@123"
```

Apply setup to each shard:

```powershell
Set-Location ".\sql"

# Shard 1 (port 3308): keep CRC32(str(MemberID)) % 3 = 1
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "source schema_maaps_no_triggers.sql"
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "source sample_data_maaps.sql"
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "source distributed_drop_cross_shard_fks.sql"
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "source distributed_shard1_filter.sql"

# Shard 2 (port 3309): keep CRC32(str(MemberID)) % 3 = 2
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "source schema_maaps_no_triggers.sql"
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "source sample_data_maaps.sql"
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "source distributed_drop_cross_shard_fks.sql"
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "source distributed_shard2_filter.sql"

# Shard 0 (port 3307): keep CRC32(str(MemberID)) % 3 = 0
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "source schema_maaps_no_triggers.sql"
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "source sample_data_maaps.sql"
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "source distributed_drop_cross_shard_fks.sql"
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "source distributed_shard0_filter.sql"

Set-Location ".."
```

### 5.3 Partition Verification Queries

Counts per shard:

```powershell
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "SELECT @@hostname; SELECT COUNT(*) MemberCount FROM Member; SELECT COUNT(*) PostCount FROM Post; SELECT COUNT(*) CommentCount FROM Comment;"
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "SELECT @@hostname; SELECT COUNT(*) MemberCount FROM Member; SELECT COUNT(*) PostCount FROM Post; SELECT COUNT(*) CommentCount FROM Comment;"
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "SELECT @@hostname; SELECT COUNT(*) MemberCount FROM Member; SELECT COUNT(*) PostCount FROM Post; SELECT COUNT(*) CommentCount FROM Comment;"
```

Purity checks (must all be `0`):

```powershell
# 3307 should contain only CRC32(str(MemberID)) % 3 = 0
mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "SELECT COUNT(*) AS bad_members FROM Member WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 0; SELECT COUNT(*) AS bad_posts FROM Post WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 0; SELECT COUNT(*) AS bad_comments FROM Comment WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 0;"

# 3308 should contain only CRC32(str(MemberID)) % 3 = 1
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "SELECT COUNT(*) AS bad_members FROM Member WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1; SELECT COUNT(*) AS bad_posts FROM Post WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1; SELECT COUNT(*) AS bad_comments FROM Comment WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 1;"

# 3309 should contain only CRC32(str(MemberID)) % 3 = 2
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "SELECT COUNT(*) AS bad_members FROM Member WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 2; SELECT COUNT(*) AS bad_posts FROM Post WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 2; SELECT COUNT(*) AS bad_comments FROM Comment WHERE MOD(CRC32(CAST(MemberID AS CHAR)), 3) <> 2;"
```

## 6. Subtask 3: Query Routing

### 6.1 Start API in Distributed Mode

From project root:

```powershell
$env:JWT_SECRET_KEY = [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
$env:USE_DISTRIBUTED_SHARDS = "1"
$env:SHARD_HOST = "10.0.116.184"
$env:SHARD_PORTS = "3307,3308,3309"
$env:SHARD_DB = "maaps"
$env:DB_USER = "maaps"
$env:DB_PASSWORD = "password@123"

cd app
python -m uvicorn main:app --host 127.0.0.1 --port 8001
```

URL:

```text
http://127.0.0.1:8001/
```

### 6.2 Shard-Aware Endpoints

1. `GET /shards/info`
2. `GET /shards/members/{member_id}`
3. `GET /shards/members/{member_id}/posts`
4. `GET /shards/members/{member_id}/comments`
5. `GET /shards/posts` (fan-out range query)
6. `POST /shards/posts` (routed insert)

### 6.3 Routing Verification Procedure

1. Login and capture `session_token`.
2. Call `GET /isAuth` and note member id `M`.
3. Call `GET /shards/members/M`.
   - Expected: `shard_id = CRC32(str(M)) % 3`
4. Call `POST /shards/posts` and note `post_id = P` and returned shard id.
   - Verify `P` exists on exactly one shard.
5. Call `GET /shards/posts?limit=10`.
   - Expected: `shard_meta` contains 3 entries.
6. Optional strong proof:
   - Comment on a post from a different member.
   - Fetch `GET /posts/{post_id}/comments` and show the new comment appears.
7. We have also verified these in the UI.

Cross-check inserted post placement:

```powershell
# Use the numeric post_id returned by POST /shards/posts
$P = 20

mysql -h 10.0.116.184 -P 3307 -u maaps maaps -e "SELECT PostID, MemberID FROM Post WHERE PostID = $P;"
mysql -h 10.0.116.184 -P 3308 -u maaps maaps -e "SELECT PostID, MemberID FROM Post WHERE PostID = $P;"
mysql -h 10.0.116.184 -P 3309 -u maaps maaps -e "SELECT PostID, MemberID FROM Post WHERE PostID = $P;"
```

## 7. Subtask 4: Scalability and Trade-offs Analysis

Include the following in your report:

1. Horizontal vs Vertical Scaling
   - Explain why adding shards scales write/read capacity better than a single bigger server.
2. Consistency
   - Discuss where cross-shard operations can become stale or eventually consistent.
3. Availability
   - Explain impact when one shard is unavailable.
4. Partition Tolerance
   - Explain behavior when the app can reach some shards but not all.
5. Observations and limitations
   - Mention fan-out query cost and operational complexity.

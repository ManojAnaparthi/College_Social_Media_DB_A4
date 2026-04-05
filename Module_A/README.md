# Module A: ACID Validation for B+ Tree Database

## Assignment Requirements

Extend the B+ Tree database system to support **transaction management**, **failure recovery**, and **ACID guarantees** across **at least 3 relations**.

## 🎯 Quick Start

### Option 1: Interactive Demonstration (Recommended)

Shows all ACID properties with clear, visual output:

```bash
cd Module_A
python run_demo.py
```

### Option 2: Run Unit Tests

Automated test suite for validation:

```bash
cd Module_A
python run_acid_tests.py
```

## ✅ What's Implemented

### ACID Properties Across 3 Relations

- **A**tomicity: Multi-relation transactions are all-or-nothing
- **C**onsistency: Database maintains valid state with constraints
- **I**solation: Transactions execute serially without interference
- **D**urability: Committed data persists across system crashes

### Three-Relation Schema (College Social Media)

1. **Members** - User accounts (MemberID, Name, Department, Reputation)
2. **Posts** - User posts (PostID, MemberID, Content, LikeCount)
3. **Comments** - Post comments (CommentID, PostID, MemberID, Content, LikeCount)

## 🧪 Test Files

**Essential Files** (as per Module A requirements):

- `database/test_acid_multirelation.py` - ⭐ **Main test file** - Tests all ACID properties across 3 relations
- `database/acid_demonstration.py` - Interactive demo with clear output for understanding

**Supporting Implementation**:

- `database/transaction_manager.py` - BEGIN/COMMIT/ROLLBACK/Recovery
- `database/db_manager.py` - Multi-table coordinator
- `database/table.py` - B+ Tree-backed table abstraction
- `database/bplustree.py` - B+ Tree storage engine

## 📊 Test Coverage

### Multi-Relation Tests (test_acid_multirelation.py)

All 4 tests operate on **3 relations simultaneously**:

| Test                                                  | What It Does                                                                             |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| **test_atomicity_multi_relation_rollback_on_failure** | Updates Member + Post + Insert Comment → Simulate failure → Verify complete rollback     |
| **test_consistency_constraints_after_commit**         | Verify referential integrity (Comments reference valid Members & Posts)                  |
| **test_isolation_serialized_execution**               | Start TX1 → Attempt TX2 concurrently → Verify TX2 blocked                                |
| **test_durability_and_recovery_across_restart**       | Commit TX → Start uncommitted TX → Simulate crash → Verify only committed data recovered |

## 🏗️ Architecture

```
Transaction Manager (ACID Coordinator)
    │
    ├── BEGIN: Deep copy database state
    ├── COMMIT: Save snapshot to disk
    ├── ROLLBACK: Restore from snapshot
    └── RECOVER: Load last committed snapshot

    ↓ Manages ↓

Database Manager (3 Relations)
    │
    ├── Members Table → B+ Tree (MemberID → Record)
    ├── Posts Table → B+ Tree (PostID → Record)
    └── Comments Table → B+ Tree (CommentID → Record)
```

### ACID Implementation Details

**Atomicity**: Deep copy entire DB state before transaction; restore on rollback  
**Consistency**: Schema validation + referential integrity checks  
**Isolation**: Threading.RLock ensures serialized execution (one active TX at a time)  
**Durability**: JSON snapshot persisted to disk on COMMIT; loaded on restart

## 📝 Example Test Output

```
test_atomicity_multi_relation_rollback_on_failure ... ok
test_consistency_constraints_after_commit ... ok
test_isolation_serialized_execution ... ok
test_durability_and_recovery_across_restart ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.245s

OK ✅
```

### Interactive Demo Output Preview

```
================================================================================
  TEST 1: ATOMICITY (All-or-Nothing)
================================================================================

--- State Before Transaction ---
📊 Members: ID 1 (Reputation: 100)
📝 Posts: ID 10 (Likes: 5)

🔄 Transaction STARTED
  ✓ Updated Member 1 reputation → 85
  ✓ Updated Post 10 likes → 8
  ✓ Inserted Comment 1001
  ⚠️  SIMULATING FAILURE...
⏪ ROLLING BACK

--- State After Rollback ---
📊 Members: ID 1 (Reputation: 100) ← Reverted
📝 Posts: ID 10 (Likes: 5) ← Reverted
💬 Comments: No Comment 1001 ← Cancelled

✅ ATOMICITY VERIFIED: All changes rolled back
```

## 🔑 Key Features

1. ✅ **B+ Tree as Primary Storage** (not auxiliary index)
2. ✅ **Multi-Relation Transactions** (operates on 3+ tables)
3. ✅ **Crash Recovery** (automatic recovery from snapshots)
4. ✅ **Clear Test Outputs** (easy to verify correctness)
5. ✅ **SQL Validation** (cross-check against SQLite reference)

## 🛠️ Requirements

- Python 3.8+
- No external dependencies for core functionality
- Standard library only (json, threading, pathlib, unittest, etc.)

## 📦 Project Structure

```
Module_A/
├── database/
│   ├── bplustree.py                  # B+ Tree storage
│   ├── table.py                      # Table abstraction
│   ├── db_manager.py                 # Multi-table manager
│   ├── transaction_manager.py        # Transaction coordinator
│   ├── sql_sanity.py                 # SQLite validator
│   ├── test_acid_multirelation.py    # ⭐ Main tests (3 relations)
│   └── acid_demonstration.py         # ⭐ Interactive demo
├── run_acid_tests.py                 # ⭐ Test runner
├── run_demo.py                       # ⭐ Demo runner
├── README.md                         # This file
└── requirements.txt                  # Dependencies
```

## 🎓 How to Verify

### Step 1: Run Main Tests

```bash
cd Module_A
python run_acid_tests.py
```

**Expected**: All 4 tests pass ✅

### Step 2: Run Interactive Demo (for understanding)

```bash
cd Module_A
python run_demo.py
```
```

**Expected**: Clear output showing each ACID property with before/after states

### Step 3: Verify Multi-Relation Operations

Check test output confirms:

- All operations span 3 relations (Member, Post, Comment)
- Atomicity: Rollback affects all tables
- Consistency: Cross-relation constraints maintained
- Isolation: Concurrent transactions blocked
- Durability: Committed data survives crashes

## ❓ Common Questions

**Q: Where is the data stored?**  
A: Directly in B+ Trees. Each table = one B+ Tree. The B+ Tree IS the storage, not an index.

**Q: How does rollback work?**  
A: Deep copy entire database state before transaction. On rollback, swap back to the copy.

**Q: How many relations are tested?**  
A: All tests use 3 relations (Members, Posts, Comments) as required.

**Q: What if tests fail?**  
A: Ensure you're in Module_A directory and Python 3.8+. Check write permissions for temp files.

## ✅ Verification Checklist

- ✅ B+ Tree used as primary storage (not auxiliary index)
- ✅ Three relations implemented (Member, Post, Comment)
- ✅ Multi-relation transactions supported
- ✅ BEGIN/COMMIT/ROLLBACK operations working
- ✅ Atomicity: Full rollback on failure across all tables
- ✅ Consistency: Schema validation and constraint checks
- ✅ Isolation: Serialized execution (one active transaction)
- ✅ Durability: Persistence across simulated crashes
- ✅ Clear test outputs for verification

---

**Status**: ✅ Module A Complete - Ready for Evaluation

All ACID properties implemented and tested across 3+ relations as required.

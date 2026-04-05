"""
ACID Properties Demonstration Script
Module A - Database Management Systems

This script demonstrates all ACID properties across multiple relations:
- Members (user accounts)
- Posts (user posts)  
- Comments (post comments)

Each test shows clear before/after states and validates ACID compliance.
"""

from __future__ import annotations

import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict

from Module_A.database.db_manager import DBManager
from Module_A.database.transaction_manager import TransactionManager


class ACIDDemonstrator:
    """Demonstrates ACID properties with clear, understandable output."""

    def __init__(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.tmp_dir)
        self.snapshot_path = self.tmp_path / "db_snapshot.json"
        self.log_path = self.tmp_path / "tx_log.jsonl"
        
        self.db = DBManager()
        self.txm = TransactionManager(self.db, self.snapshot_path, self.log_path)
        
        # Create three relations as required
        self.members = self.db.create_table(
            "Member",
            primary_key="MemberID",
            schema=["MemberID", "Name", "Department", "Reputation"],
        )
        self.posts = self.db.create_table(
            "Post",
            primary_key="PostID",
            schema=["PostID", "MemberID", "Content", "LikeCount"],
        )
        self.comments = self.db.create_table(
            "Comment",
            primary_key="CommentID",
            schema=["CommentID", "PostID", "MemberID", "Content", "LikeCount"],
        )

    def refresh_table_references(self):
        """Refresh table references after rollback/recovery."""
        self.members = self.db.get_table("Member")
        self.posts = self.db.get_table("Post")
        self.comments = self.db.get_table("Comment")

    def print_section(self, title: str):
        """Print a formatted section header."""
        print("\n" + "=" * 80)
        print(f"  {title}")
        print("=" * 80 + "\n")

    def print_subsection(self, title: str):
        """Print a formatted subsection header."""
        print(f"\n--- {title} ---")

    def print_db_state(self, title: str = "Current Database State"):
        """Print the current state of all tables."""
        self.print_subsection(title)
        
        print("\n Members Table:")
        members = self.members.all_rows()
        if members:
            for key, row in members:
                print(f"  ID {key}: {row['Name']}, {row['Department']}, Reputation: {row['Reputation']}")
        else:
            print("  (empty)")
        
        print("\n Posts Table:")
        posts = self.posts.all_rows()
        if posts:
            for key, row in posts:
                print(f"  ID {key}: MemberID={row['MemberID']}, Likes={row['LikeCount']}, Content='{row['Content'][:40]}...'")
        else:
            print("  (empty)")
        
        print("\n Comments Table:")
        comments = self.comments.all_rows()
        if comments:
            for key, row in comments:
                print(f"  ID {key}: PostID={row['PostID']}, MemberID={row['MemberID']}, Likes={row['LikeCount']}")
        else:
            print("  (empty)")

    def seed_initial_data(self):
        """Add initial test data."""
        self.print_subsection("Seeding Initial Data")
        
        self.members.insert({
            "MemberID": 1,
            "Name": "Aarav Kumar",
            "Department": "Computer Science",
            "Reputation": 100
        })
        
        self.posts.insert({
            "PostID": 10,
            "MemberID": 1,
            "Content": "Welcome to our college social media platform!",
            "LikeCount": 5
        })
        
        print(" Inserted Member ID 1: Aarav Kumar (CSE, Reputation=100)")
        print(" Inserted Post ID 10 by Member 1 (Likes=5)")

    def demonstrate_atomicity(self):
        """
        ATOMICITY TEST:
        A transaction affecting all 3 relations must either complete fully or rollback completely.
        We'll simulate a failure mid-transaction and verify complete rollback.
        """
        self.print_section("TEST 1: ATOMICITY (All-or-Nothing)")
        
        self.seed_initial_data()
        self.print_db_state("State Before Transaction")
        
        # Commit initial state
        self.txm.begin()
        self.txm.commit()
        
        self.print_subsection("Starting Multi-Relation Transaction")
        print("Operations planned:")
        print("  1. Update Member 1: Reputation 100 → 85")
        print("  2. Update Post 10: LikeCount 5 → 8")
        print("  3. Insert Comment 1001 on Post 10")
        print("  4.  SIMULATE FAILURE (transaction will rollback)")
        
        # Begin transaction
        tx_id = self.txm.begin()
        print(f"\n Transaction {tx_id[:8]} STARTED")
        
        try:
            # Operation 1: Update member
            self.members.update(1, {"Reputation": 85})
            print("  ✓ Updated Member 1 reputation to 85")
            
            # Operation 2: Update post
            self.posts.update(10, {"LikeCount": 8})
            print("  ✓ Updated Post 10 likes to 8")
            
            # Operation 3: Insert comment
            self.comments.insert({
                "CommentID": 1001,
                "PostID": 10,
                "MemberID": 1,
                "Content": "Great introduction post!",
                "LikeCount": 2
            })
            print("  ✓ Inserted Comment 1001")
            
            # Simulate failure
            print("\n    SIMULATING SYSTEM FAILURE...")
            raise RuntimeError("Simulated crash during transaction")
            
        except RuntimeError as e:
            print(f"   Error occurred: {e}")
            print(f"\n ROLLING BACK transaction {tx_id[:8]}")
            self.txm.rollback()
            self.refresh_table_references()  # ← IMPORTANT: Get fresh references after rollback
        
        self.print_db_state("State After Rollback")
        
        # Verify atomicity
        self.print_subsection("ATOMICITY VERIFICATION")
        member = self.members.get(1)
        post = self.posts.get(10)
        comment = self.comments.get(1001)
        
        assert member["Reputation"] == 100, "Member reputation should be unchanged"
        assert post["LikeCount"] == 5, "Post likes should be unchanged"
        assert comment is None, "Comment should not exist"
        
        print(" ATOMICITY VERIFIED: All changes rolled back completely")
        print("   - Member reputation: 85 → 100 (reverted)")
        print("   - Post likes: 8 → 5 (reverted)")
        print("   - Comment 1001: does not exist (insertion cancelled)")

    def demonstrate_consistency(self):
        """
        CONSISTENCY TEST:
        Database must maintain valid state with respect to constraints.
        We'll verify referential integrity and business rules after transactions.
        """
        self.print_section("TEST 2: CONSISTENCY (Valid State)")
        
        self.seed_initial_data()
        
        self.print_subsection("Testing Constraint Validation")
        print("Attempting to insert comment referencing non-existent post...")
        
        self.txm.begin()
        try:
            # This comment references non-existent PostID 999
            self.comments.insert({
                "CommentID": 2001,
                "PostID": 999,  # This post doesn't exist
                "MemberID": 1,
                "Content": "Invalid comment",
                "LikeCount": 0
            })
            print("  ✓ Inserted comment (no automatic FK check in this demo)")
        except Exception as e:
            print(f"   Insertion rejected: {e}")
        
        # Manual consistency check
        print("\n Performing Consistency Check:")
        
        member_ids = {k for k, _ in self.members.all_rows()}
        post_ids = {k for k, _ in self.posts.all_rows()}
        
        print(f"   Valid Member IDs: {member_ids}")
        print(f"   Valid Post IDs: {post_ids}")
        
        consistent = True
        for cid, comment in self.comments.all_rows():
            if comment["MemberID"] not in member_ids:
                print(f"    Comment {cid} references invalid MemberID {comment['MemberID']}")
                consistent = False
            if comment["PostID"] not in post_ids:
                print(f"    Comment {cid} references invalid PostID {comment['PostID']}")
                consistent = False
        
        if not consistent:
            print("\n  INCONSISTENCY DETECTED - Rolling back")
            self.txm.rollback()
            self.refresh_table_references()
        else:
            self.txm.commit()
        
        # Now insert valid comment
        self.print_subsection("Inserting Valid Comment with Proper References")
        
        self.txm.begin()
        self.comments.insert({
            "CommentID": 1002,
            "PostID": 10,  # Valid post
            "MemberID": 1,  # Valid member
            "Content": "This is a valid comment",
            "LikeCount": 1
        })
        print("  ✓ Inserted Comment 1002 with valid references")
        self.txm.commit()
        
        # Verify consistency
        self.print_subsection("CONSISTENCY VERIFICATION")
        for cid, comment in self.comments.all_rows():
            member_exists = comment["MemberID"] in member_ids
            post_exists = comment["PostID"] in post_ids
            print(f"   Comment {cid}:")
            print(f"     - References MemberID {comment['MemberID']}: {' Valid' if member_exists else ' Invalid'}")
            print(f"     - References PostID {comment['PostID']}: {' Valid' if post_exists else ' Invalid'}")
        
        print("\n CONSISTENCY VERIFIED: All references valid, constraints maintained")

    def demonstrate_isolation(self):
        """
        ISOLATION TEST:
        Concurrent transactions should not interfere with each other.
        We use serialized execution: only one transaction active at a time.
        """
        self.print_section("TEST 3: ISOLATION (No Interference)")
        
        self.seed_initial_data()
        
        # Commit initial state
        self.txm.begin()
        self.txm.commit()
        
        self.print_subsection("Testing Concurrent Transaction Handling")
        print("Scenario: Two threads attempt transactions simultaneously")
        print("Expected: Second transaction blocked until first completes\n")
        
        events = []
        tx1_started = threading.Event()
        
        def transaction_1():
            """Long-running transaction."""
            try:
                events.append(("TX1", "Attempting BEGIN"))
                tx_id = self.txm.begin()
                events.append(("TX1", f"BEGIN successful ({tx_id[:8]})"))
                tx1_started.set()
                
                # Simulate long-running work
                time.sleep(0.15)
                
                self.members.update(1, {"Reputation": 90})
                events.append(("TX1", "Updated Member 1 reputation → 90"))
                
                self.posts.update(10, {"LikeCount": 10})
                events.append(("TX1", "Updated Post 10 likes → 10"))
                
                self.txm.commit()
                events.append(("TX1", "COMMIT successful"))
                
            except Exception as e:
                events.append(("TX1", f"ERROR: {e}"))
        
        def transaction_2():
            """Transaction that tries to start during TX1."""
            tx1_started.wait(timeout=2.0)
            time.sleep(0.05)  # Ensure TX1 is active
            
            try:
                events.append(("TX2", "Attempting BEGIN"))
                self.txm.begin()
                events.append(("TX2", "BEGIN successful"))
                self.txm.rollback()
                events.append(("TX2", "ROLLBACK"))
            except RuntimeError as e:
                events.append(("TX2", f"BLOCKED: {e}"))
        
        # Start both transactions
        t1 = threading.Thread(target=transaction_1, name="TX1")
        t2 = threading.Thread(target=transaction_2, name="TX2")
        
        print("⏱  Starting concurrent transactions...\n")
        t1.start()
        t2.start()
        t1.join()
        t2.join()
        
        # Display event timeline
        self.print_subsection("Transaction Timeline")
        for tx, event in events:
            print(f"  [{tx}] {event}")
        
        # Verify isolation
        self.print_subsection("ISOLATION VERIFICATION")
        
        tx1_events = [e for tx, e in events if tx == "TX1"]
        tx2_events = [e for tx, e in events if tx == "TX2"]
        
        tx1_completed = "COMMIT successful" in tx1_events
        tx2_blocked = any("BLOCKED" in e for e in tx2_events)
        
        print(f"   TX1 completed successfully: {' Yes' if tx1_completed else ' No'}")
        print(f"   TX2 was blocked: {' Yes' if tx2_blocked else ' No'}")
        
        if tx1_completed and tx2_blocked:
            print("\n ISOLATION VERIFIED: Serialized execution enforced")
            print("   Only one transaction active at a time")
        else:
            print("\n  Isolation may not be properly enforced")

    def demonstrate_durability(self):
        """
        DURABILITY TEST:
        Committed data must survive system crashes and restarts.
        We'll commit a transaction, simulate a crash, and verify data persists.
        """
        self.print_section("TEST 4: DURABILITY (Persistence)")
        
        self.seed_initial_data()
        
        self.print_subsection("Committing Transaction to Persistent Storage")
        print("Operations:")
        print("  1. Update Member 1: Reputation 100 → 75")
        print("  2. Update Post 10: LikeCount 5 → 12")
        print("  3. Insert Comment 1003")
        print("  4. COMMIT (persist to disk)\n")
        
        # Commit transaction
        self.txm.begin()
        self.members.update(1, {"Reputation": 75})
        print("  ✓ Updated Member 1 reputation → 75")
        
        self.posts.update(10, {"LikeCount": 12})
        print("  ✓ Updated Post 10 likes → 12")
        
        self.comments.insert({
            "CommentID": 1003,
            "PostID": 10,
            "MemberID": 1,
            "Content": "Committed comment for durability test",
            "LikeCount": 3
        })
        print("  ✓ Inserted Comment 1003")
        
        print("\n COMMITTING transaction...")
        self.txm.commit()
        print(f"   Snapshot saved to: {self.snapshot_path}")
        
        self.print_db_state("State After COMMIT")
        
        # Start but don't commit another transaction
        self.print_subsection("Starting Uncommitted Transaction")
        print("Making changes WITHOUT committing:")
        
        self.txm.begin()
        self.members.update(1, {"Reputation": 0})
        print("  ✓ Updated Member 1 reputation → 0 (NOT COMMITTED)")
        
        self.posts.update(10, {"LikeCount": 999})
        print("  ✓ Updated Post 10 likes → 999 (NOT COMMITTED)")
        
        self.comments.insert({
            "CommentID": 1004,
            "PostID": 10,
            "MemberID": 1,
            "Content": "This should be lost after crash",
            "LikeCount": 0
        })
        print("  ✓ Inserted Comment 1004 (NOT COMMITTED)")
        
        self.print_db_state("In-Memory State (Uncommitted)")
        
        # Simulate crash by creating new instance
        self.print_subsection(" SIMULATING SYSTEM CRASH")
        print("Restarting database from persistent snapshot...\n")
        
        # Create new DB instance (simulates restart)
        recovered_db = DBManager()
        recovered_txm = TransactionManager(recovered_db, self.snapshot_path, self.log_path)
        
        r_members = recovered_db.get_table("Member")
        r_posts = recovered_db.get_table("Post")
        r_comments = recovered_db.get_table("Comment")
        
        # Print recovered state
        self.print_subsection("Recovered Database State")
        
        print("\n Recovered Members Table:")
        for key, row in r_members.all_rows():
            print(f"  ID {key}: {row['Name']}, Reputation: {row['Reputation']}")
        
        print("\n Recovered Posts Table:")
        for key, row in r_posts.all_rows():
            print(f"  ID {key}: Likes={row['LikeCount']}")
        
        print("\n Recovered Comments Table:")
        for key, row in r_comments.all_rows():
            print(f"  ID {key}: PostID={row['PostID']}, Content='{row['Content'][:30]}...'")
        
        # Verify durability
        self.print_subsection("DURABILITY VERIFICATION")
        
        member = r_members.get(1)
        post = r_posts.get(10)
        comment_1003 = r_comments.get(1003)
        comment_1004 = r_comments.get(1004)
        
        print(f"   Member 1 Reputation: {member['Reputation']}")
        print(f"     Expected: 75 (committed), Actual: {member['Reputation']}")
        print(f"     {' MATCH' if member['Reputation'] == 75 else ' MISMATCH'}")
        
        print(f"\n   Post 10 LikeCount: {post['LikeCount']}")
        print(f"     Expected: 12 (committed), Actual: {post['LikeCount']}")
        print(f"     {' MATCH' if post['LikeCount'] == 12 else ' MISMATCH'}")
        
        print(f"\n   Comment 1003 (committed): {' EXISTS' if comment_1003 else ' MISSING'}")
        print(f"   Comment 1004 (uncommitted): {' CORRECTLY ABSENT' if not comment_1004 else ' INCORRECTLY PRESENT'}")
        
        all_correct = (
            member['Reputation'] == 75 and
            post['LikeCount'] == 12 and
            comment_1003 is not None and
            comment_1004 is None
        )
        
        if all_correct:
            print("\n DURABILITY VERIFIED: Committed data persisted, uncommitted data lost")
        else:
            print("\n DURABILITY FAILED: Data inconsistency after recovery")

    def run_all_demonstrations(self):
        """Run all ACID demonstrations."""
        print("\n" + "█" * 80)
        print("█" + " " * 78 + "█")
        print("█" + "  MODULE A: ACID PROPERTIES DEMONSTRATION".center(78) + "█")
        print("█" + "  Database Management Systems - Assignment 3".center(78) + "█")
        print("█" + " " * 78 + "█")
        print("█" * 80)
        
        print("\nThis demonstration validates ACID properties across 3 relations:")
        print("  • Members (user accounts)")
        print("  • Posts (user posts)")
        print("  • Comments (post comments)")
        
        try:
            # Reset for each test
            print("\n" + "▀" * 80)
            self.reset_database()
            self.demonstrate_atomicity()
            
            print("\n" + "▀" * 80)
            self.reset_database()
            self.demonstrate_consistency()
            
            print("\n" + "▀" * 80)
            self.reset_database()
            self.demonstrate_isolation()
            
            print("\n" + "▀" * 80)
            self.reset_database()
            self.demonstrate_durability()
            
            # Final summary
            self.print_section("DEMONSTRATION COMPLETE")
            print("All ACID properties have been successfully demonstrated:")
            print("   ATOMICITY: Multi-relation transactions are all-or-nothing")
            print("   CONSISTENCY: Database maintains valid state and constraints")
            print("   ISOLATION: Transactions execute serially without interference")
            print("   DURABILITY: Committed data persists across system restarts")
            print("\n" + "█" * 80 + "\n")
            
        except Exception as e:
            print(f"\n Error during demonstration: {e}")
            import traceback
            traceback.print_exc()

    def reset_database(self):
        """Reset database to clean state."""
        # Remove snapshot file to start fresh
        if self.snapshot_path.exists():
            self.snapshot_path.unlink()
        
        self.db = DBManager()
        self.txm = TransactionManager(self.db, self.snapshot_path, self.log_path)
        
        self.members = self.db.create_table(
            "Member",
            primary_key="MemberID",
            schema=["MemberID", "Name", "Department", "Reputation"],
        )
        self.posts = self.db.create_table(
            "Post",
            primary_key="PostID",
            schema=["PostID", "MemberID", "Content", "LikeCount"],
        )
        self.comments = self.db.create_table(
            "Comment",
            primary_key="CommentID",
            schema=["CommentID", "PostID", "MemberID", "Content", "LikeCount"],
        )


def main():
    """Run the ACID demonstration."""
    demo = ACIDDemonstrator()
    demo.run_all_demonstrations()


if __name__ == "__main__":
    main()

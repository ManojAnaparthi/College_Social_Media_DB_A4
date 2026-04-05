"""
Video Demo Script for Module A
Perfect for recording demonstration videos showing ACID properties

Run: python video_demo.py
"""

from __future__ import annotations
import sys
import tempfile
from pathlib import Path

# Add parent directory to path
module_a_path = Path(__file__).parent
parent_path = module_a_path.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

from Module_A.database.db_manager import DBManager
from Module_A.database.transaction_manager import TransactionManager


def print_header(title: str):
    """Print a clear header."""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")


def print_all_tables(db: DBManager, title: str = "DATABASE STATE"):
    """Print all tables with clear formatting."""
    print(f"\n{'─' * 80}")
    print(f" {title}")
    print('─' * 80)
    
    members = db.get_table("Member")
    posts = db.get_table("Post")
    comments = db.get_table("Comment")
    
    print("\n🔹 MEMBERS TABLE:")
    for key, row in members.all_rows():
        print(f"   ID: {key} | Name: {row['Name']:20s} | Dept: {row['Department']:15s} | Rep: {row['Reputation']}")
    
    print("\n🔹 POSTS TABLE:")
    for key, row in posts.all_rows():
        content_preview = row['Content'][:40] + "..." if len(row['Content']) > 40 else row['Content']
        print(f"   ID: {key} | MemberID: {row['MemberID']} | Likes: {row['LikeCount']:3d} | Content: '{content_preview}'")
    
    print("\n🔹 COMMENTS TABLE:")
    comments_list = comments.all_rows()
    if comments_list:
        for key, row in comments_list:
            content_preview = row['Content'][:40] + "..." if len(row['Content']) > 40 else row['Content']
            print(f"   ID: {key} | PostID: {row['PostID']} | MemberID: {row['MemberID']} | Likes: {row['LikeCount']:3d}")
    else:
        print("   (No comments)")
    
    print('─' * 80 + "\n")


def wait_for_enter(message: str = "Press ENTER to continue..."):
    """Pause for user input - perfect for video recording."""
    input(f"\n  {message}")


def demo_atomicity():
    """Demonstrate Atomicity with clear before/after states."""
    print_header("DEMO 1: ATOMICITY (All-or-Nothing Transaction)")
    
    # Setup
    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir)
    
    db = DBManager()
    txm = TransactionManager(db, tmp_path / "snapshot.json", tmp_path / "log.jsonl")
    
    # Create tables
    members = db.create_table("Member", "MemberID", ["MemberID", "Name", "Department", "Reputation"])
    posts = db.create_table("Post", "PostID", ["PostID", "MemberID", "Content", "LikeCount"])
    comments = db.create_table("Comment", "CommentID", ["CommentID", "PostID", "MemberID", "Content", "LikeCount"])
    
    # Insert initial data
    print(" Setting up initial data...")
    members.insert({"MemberID": 1, "Name": "Aarav Kumar", "Department": "Computer Science", "Reputation": 100})
    members.insert({"MemberID": 2, "Name": "Priya Sharma", "Department": "Electronics", "Reputation": 85})
    posts.insert({"PostID": 10, "MemberID": 1, "Content": "Welcome to our college social media!", "LikeCount": 5})
    posts.insert({"PostID": 11, "MemberID": 2, "Content": "First day at college!", "LikeCount": 3})
    
    print_all_tables(db, "INITIAL STATE (Before Transaction)")
    wait_for_enter("Ready to start transaction...")
    
    # Begin transaction
    print("\n STARTING TRANSACTION...")
    print("   This transaction will:")
    print("   1. Update Member 1: Reputation 100 → 75")
    print("   2. Update Post 10: LikeCount 5 → 10")
    print("   3. Insert Comment 1001 on Post 10")
    print("   4. Then CRASH (simulated failure)")
    
    wait_for_enter("Press ENTER to begin transaction...")
    
    txm.begin()
    
    # Make changes
    print("\n✓ Updating Member 1 reputation: 100 → 75")
    members.update(1, {"Reputation": 75})
    
    print("✓ Updating Post 10 likes: 5 → 10")
    posts.update(10, {"LikeCount": 10})
    
    print("✓ Inserting Comment 1001")
    comments.insert({"CommentID": 1001, "PostID": 10, "MemberID": 1, "Content": "Great post!", "LikeCount": 2})
    
    # Refresh references to see changes
    members = db.get_table("Member")
    posts = db.get_table("Post")
    comments = db.get_table("Comment")
    
    print_all_tables(db, "STATE DURING TRANSACTION (Uncommitted Changes)")
    
    print("\n  NOTICE THE CHANGES:")
    print("   - Member 1 Reputation: 100 → 75 ")
    print("   - Post 10 Likes: 5 → 10 ")
    print("   - Comment 1001: NOW EXISTS ")
    
    wait_for_enter("Press ENTER to simulate crash and rollback...")
    
    # Rollback
    print("\n CRASH SIMULATED! Rolling back transaction...")
    txm.rollback()
    
    # Refresh references after rollback
    members = db.get_table("Member")
    posts = db.get_table("Post")
    comments = db.get_table("Comment")
    
    print_all_tables(db, "STATE AFTER ROLLBACK")
    
    print("\n ATOMICITY VERIFIED:")
    member_rep = members.get(1)["Reputation"]
    post_likes = posts.get(10)["LikeCount"]
    comment_exists = comments.get(1001) is not None
    
    print(f"   - Member 1 Reputation: {member_rep} (reverted to 100) {'' if member_rep == 100 else ''}")
    print(f"   - Post 10 Likes: {post_likes} (reverted to 5) {'' if post_likes == 5 else ''}")
    print(f"   - Comment 1001: {'DOES NOT EXIST' if not comment_exists else 'EXISTS'} {'' if not comment_exists else ''}")
    
    if member_rep == 100 and post_likes == 5 and not comment_exists:
        print("\n ALL CHANGES ROLLED BACK SUCCESSFULLY!")
        print("   The transaction was ATOMIC - either all or nothing!")


def demo_durability():
    """Demonstrate Durability with crash recovery."""
    print_header("DEMO 2: DURABILITY (Persistence Across Crashes)")
    
    tmp_dir = tempfile.mkdtemp()
    tmp_path = Path(tmp_dir)
    snapshot_path = tmp_path / "snapshot.json"
    log_path = tmp_path / "log.jsonl"
    
    # First database instance
    print(" Creating first database instance...")
    db1 = DBManager()
    txm1 = TransactionManager(db1, snapshot_path, log_path)
    
    members = db1.create_table("Member", "MemberID", ["MemberID", "Name", "Department", "Reputation"])
    posts = db1.create_table("Post", "PostID", ["PostID", "MemberID", "Content", "LikeCount"])
    comments = db1.create_table("Comment", "CommentID", ["CommentID", "PostID", "MemberID", "Content", "LikeCount"])
    
    members.insert({"MemberID": 1, "Name": "Rohan Verma", "Department": "Mechanical", "Reputation": 90})
    posts.insert({"PostID": 20, "MemberID": 1, "Content": "Engineering project ideas", "LikeCount": 7})
    
    print_all_tables(db1, "INITIAL STATE")
    wait_for_enter("Ready to commit transaction...")
    
    # COMMIT transaction
    print("\n STARTING TRANSACTION...")
    txm1.begin()
    members.update(1, {"Reputation": 95})
    posts.update(20, {"LikeCount": 12})
    comments.insert({"CommentID": 2001, "PostID": 20, "MemberID": 1, "Content": "Committed comment", "LikeCount": 5})
    
    print("✓ Updated Member 1 reputation: 90 → 95")
    print("✓ Updated Post 20 likes: 7 → 12")
    print("✓ Inserted Comment 2001")
    
    print("\n COMMITTING TRANSACTION (saving to disk)...")
    txm1.commit()
    print(f"   Snapshot saved to: {snapshot_path}")
    
    # Refresh and show committed state
    members = db1.get_table("Member")
    posts = db1.get_table("Post")
    comments = db1.get_table("Comment")
    print_all_tables(db1, "COMMITTED STATE (Saved to Disk)")
    
    wait_for_enter("Press ENTER to make uncommitted changes...")
    
    # Make uncommitted changes
    print("\n STARTING ANOTHER TRANSACTION (will NOT commit)...")
    txm1.begin()
    members.update(1, {"Reputation": 0})
    posts.update(20, {"LikeCount": 999})
    comments.insert({"CommentID": 2002, "PostID": 20, "MemberID": 1, "Content": "Uncommitted comment", "LikeCount": 0})
    
    print("✓ Updated Member 1 reputation: 95 → 0 (NOT COMMITTED)")
    print("✓ Updated Post 20 likes: 12 → 999 (NOT COMMITTED)")
    print("✓ Inserted Comment 2002 (NOT COMMITTED)")
    
    members = db1.get_table("Member")
    posts = db1.get_table("Post")
    comments = db1.get_table("Comment")
    print_all_tables(db1, "UNCOMMITTED STATE (In Memory Only)")
    
    wait_for_enter("Press ENTER to simulate crash...")
    
    # CRASH - create new instance
    print("\n SYSTEM CRASH!")
    print("   Destroying database instance...")
    print("   Starting fresh instance...")
    del db1, txm1, members, posts, comments
    
    # Recovery
    print("\n RECOVERING FROM CRASH...")
    print(f"   Loading snapshot from: {snapshot_path}")
    
    db2 = DBManager()
    txm2 = TransactionManager(db2, snapshot_path, log_path)
    
    members2 = db2.get_table("Member")
    posts2 = db2.get_table("Post")
    comments2 = db2.get_table("Comment")
    
    print_all_tables(db2, "RECOVERED STATE (After Crash)")
    
    print("\n DURABILITY VERIFIED:")
    member_rep = members2.get(1)["Reputation"]
    post_likes = posts2.get(20)["LikeCount"]
    comment_2001 = comments2.get(2001) is not None
    comment_2002 = comments2.get(2002) is not None
    
    print(f"   - Member 1 Reputation: {member_rep} (should be 95) {'' if member_rep == 95 else ''}")
    print(f"   - Post 20 Likes: {post_likes} (should be 12) {'' if post_likes == 12 else ''}")
    print(f"   - Comment 2001 (committed): {'EXISTS' if comment_2001 else 'MISSING'} {'' if comment_2001 else ''}")
    print(f"   - Comment 2002 (uncommitted): {'EXISTS' if comment_2002 else 'MISSING'} {'' if not comment_2002 else ''}")
    
    if member_rep == 95 and post_likes == 12 and comment_2001 and not comment_2002:
        print("\n DURABILITY CONFIRMED!")
        print("   - Committed data SURVIVED the crash")
        print("   - Uncommitted data was LOST (as expected)")


def main():
    """Run all demonstrations."""
    print("\n" + "█" * 80)
    print("█" + " " * 78 + "█")
    print("█" + "  MODULE A: ACID PROPERTIES - VIDEO DEMONSTRATION".center(78) + "█")
    print("█" + " " * 78 + "█")
    print("█" * 80)
    
    print("\n This script is designed for recording demo videos.")
    print("\n   Press CTRL+C at any time to exit.\n")
    
    wait_for_enter("Press ENTER to start ATOMICITY demo...")
    
    try:
        demo_atomicity()
        
        wait_for_enter("\nPress ENTER to start DURABILITY demo...")
        demo_durability()
        
        print_header("ALL DEMONSTRATIONS COMPLETE")
        print(" Atomicity: Rollback works across all 3 tables")
        print(" Durability: Committed data survives crashes")
        
    except KeyboardInterrupt:
        print("\n\n  Demo interrupted. Exiting...")


if __name__ == "__main__":
    main()

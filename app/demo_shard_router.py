"""
Demo script for shard routing behavior.

What this script does:
1) Runs only the pure shard-router unit tests (no DB needed).
2) Prints how MemberID 1..20 map to shards and shard tables.
3) Shows the final distribution per shard.

Run:
    python app/demo_shard_router.py
"""

from __future__ import annotations

import unittest

from shard_router import ALL_SHARDS, NUM_SHARDS, all_shard_tables, get_shard_id, get_shard_table


class DemoShardRouterTests(unittest.TestCase):
    """Router-only tests; intentionally avoids DB imports/dependencies."""

    def test_get_shard_id_for_first_20_members(self):
        expected = {0: 9, 1: 7, 2: 4}
        counts = {0: 0, 1: 0, 2: 0}

        for member_id in range(1, 21):
            shard_id = get_shard_id(member_id)
            self.assertIn(shard_id, ALL_SHARDS)
            counts[shard_id] += 1

        self.assertEqual(counts, expected)

    def test_get_shard_table(self):
        self.assertEqual(get_shard_table("member", 1), "shard_2_member")
        self.assertEqual(get_shard_table("post", 3), "shard_1_post")
        self.assertEqual(get_shard_table("comment", 20), "shard_0_comment")
        self.assertEqual(get_shard_table("MeMbEr", 4), "shard_1_member")

    def test_all_shard_tables(self):
        self.assertEqual(
            all_shard_tables("post"),
            ["shard_0_post", "shard_1_post", "shard_2_post"],
        )
        self.assertEqual(len(all_shard_tables("member")), NUM_SHARDS)


def run_router_tests() -> bool:
    print("=" * 72)
    print("STEP 1: Running shard-router unit tests (no database required)")
    print("=" * 72)

    suite = unittest.TestLoader().loadTestsFromTestCase(DemoShardRouterTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)

    if result.wasSuccessful():
        print("\nResult: PASS - all shard-router function tests succeeded.")
        return True

    print("\nResult: FAIL - one or more shard-router tests failed.")
    return False


def print_routing_demo() -> None:
    print("\n" + "=" * 72)
    print("STEP 2: Visual shard routing demo for MemberID 1..20")
    print("Rule: shard_id = CRC32(str(MemberID)) % NUM_SHARDS, where NUM_SHARDS = 3")
    print("=" * 72)

    header = f"{'MemberID':>8}  {'Hash % 3':>12}  {'Member Table':>18}  {'Post Table':>15}  {'Comment Table':>18}"
    print(header)
    print("-" * len(header))

    counts = {shard_id: 0 for shard_id in ALL_SHARDS}

    for member_id in range(1, 21):
        shard_id = get_shard_id(member_id)
        counts[shard_id] += 1

        member_table = get_shard_table("member", member_id)
        post_table = get_shard_table("post", member_id)
        comment_table = get_shard_table("comment", member_id)

        print(
            f"{member_id:>8}  {shard_id:>12}  {member_table:>18}  {post_table:>15}  {comment_table:>18}"
        )

    print("\n" + "=" * 72)
    print("STEP 3: Distribution summary for MemberID 1..20")
    print("Expected: shard_0 -> 9, shard_1 -> 7, shard_2 -> 4")
    print("=" * 72)
    for shard_id in ALL_SHARDS:
        print(f"shard_{shard_id}: {counts[shard_id]} members")

    print("\nAll shard tables per entity type:")
    for base in ("member", "post", "comment"):
        print(f"- {base}: {all_shard_tables(base)}")


def main() -> None:
    tests_ok = run_router_tests()
    print_routing_demo()

    print("\n" + "=" * 72)
    print("FINAL STATUS")
    print("=" * 72)
    if tests_ok:
        print("Shard router functions are working as expected.")
    else:
        print("Shard router functions need fixes before DB-level testing.")

    print("\nTip: Run `python app/test_sharding.py` for full test suite (includes DB checks).")


if __name__ == "__main__":
    main()
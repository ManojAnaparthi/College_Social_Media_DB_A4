import unittest

from database import get_db_connection
from shard_router import ALL_SHARDS, NUM_SHARDS, all_shard_tables, get_shard_id, get_shard_table


class TestShardRouterFunctions(unittest.TestCase):
    def test_get_shard_id_for_first_20_members(self):
        expected = {0: 6, 1: 7, 2: 7}
        counts = {0: 0, 1: 0, 2: 0}

        for member_id in range(1, 21):
            shard_id = get_shard_id(member_id)
            self.assertIn(shard_id, ALL_SHARDS)
            counts[shard_id] += 1

        self.assertEqual(counts, expected)

    def test_get_shard_table(self):
        self.assertEqual(get_shard_table("member", 1), "shard_1_member")
        self.assertEqual(get_shard_table("post", 3), "shard_0_post")
        self.assertEqual(get_shard_table("comment", 20), "shard_2_comment")
        self.assertEqual(get_shard_table("MeMbEr", 4), "shard_1_member")

    def test_all_shard_tables(self):
        self.assertEqual(
            all_shard_tables("post"),
            ["shard_0_post", "shard_1_post", "shard_2_post"],
        )
        self.assertEqual(len(all_shard_tables("member")), NUM_SHARDS)


class TestShardDatabaseIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            cls.conn = get_db_connection()
        except Exception as exc:
            raise unittest.SkipTest(f"Database connection unavailable: {exc}") from exc

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def _fetch_scalar(self, query, params=None):
        with self.conn.cursor() as cursor:
            cursor.execute(query, params)
            row = cursor.fetchone()
            return list(row.values())[0]

    def _verify_table_sharding(self, base_table, key_column, id_column):
        source_total = self._fetch_scalar(f"SELECT COUNT(*) FROM {base_table}")
        shard_total = 0

        for shard_id in ALL_SHARDS:
            shard_table = f"shard_{shard_id}_{base_table.lower()}"
            shard_count = self._fetch_scalar(f"SELECT COUNT(*) FROM {shard_table}")
            shard_total += shard_count

            expected_by_hash = self._fetch_scalar(
                f"SELECT COUNT(*) FROM {base_table} WHERE ({key_column} %% {NUM_SHARDS}) = %s",
                (shard_id,),
            )
            self.assertEqual(
                shard_count,
                expected_by_hash,
                msg=(
                    f"Hash distribution mismatch for {shard_table}: "
                    f"actual={shard_count}, expected={expected_by_hash}"
                ),
            )

        self.assertEqual(
            source_total,
            shard_total,
            msg=f"Row count mismatch for {base_table}: source={source_total}, shards={shard_total}",
        )

        with self.conn.cursor() as cursor:
            cursor.execute(
                f"""
                SELECT {id_column}, COUNT(*) AS c
                FROM (
                    SELECT {id_column} FROM shard_0_{base_table.lower()}
                    UNION ALL
                    SELECT {id_column} FROM shard_1_{base_table.lower()}
                    UNION ALL
                    SELECT {id_column} FROM shard_2_{base_table.lower()}
                ) t
                GROUP BY {id_column}
                HAVING COUNT(*) > 1
                """
            )
            duplicates = cursor.fetchall()
            self.assertEqual(
                len(duplicates),
                0,
                msg=f"Duplicate IDs found across shards for {base_table}: {duplicates}",
            )

    def test_member_shards(self):
        self._verify_table_sharding(base_table="Member", key_column="MemberID", id_column="MemberID")

    def test_post_shards(self):
        self._verify_table_sharding(base_table="Post", key_column="MemberID", id_column="PostID")

    def test_comment_shards(self):
        self._verify_table_sharding(base_table="Comment", key_column="MemberID", id_column="CommentID")


if __name__ == "__main__":
    unittest.main(verbosity=2)
import json
import random
import statistics
import time
from pathlib import Path
from urllib import request as urlrequest

import pymysql

from database import DB_HOST, DB_NAME, DB_PASSWORD, DB_USER, get_db_connection

BENCH_PREFIX = "[BENCH]"
TARGET_BENCH_POSTS = 3000
COMMENTS_PER_BENCH_POST = 3
TARGET_HOT_POST_COMMENTS = 2500
ITERATIONS = 40
WARMUP = 5
API_BASE = "http://127.0.0.1:8001"

LIST_POSTS_SQL = """
    SELECT
        p.PostID,
        p.MemberID,
        m.Name AS AuthorName,
        p.Content,
        p.MediaURL,
        p.MediaType,
        p.PostDate,
        p.LastEditDate,
        p.Visibility,
        p.LikeCount,
        p.CommentCount
    FROM Post p
    JOIN Member m ON p.MemberID = m.MemberID
    WHERE p.IsActive = TRUE
    ORDER BY p.PostDate DESC
    LIMIT %s OFFSET %s
"""

LIST_COMMENTS_SQL = """
    SELECT
        c.CommentID,
        c.PostID,
        c.MemberID,
        m.Name AS AuthorName,
        c.Content,
        c.CommentDate,
        c.LastEditDate,
        c.LikeCount,
        c.IsActive
    FROM Comment c
    JOIN Member m ON c.MemberID = m.MemberID
    WHERE c.PostID = %s AND c.IsActive = TRUE
    ORDER BY c.CommentDate ASC
"""

INDEX_DEFS = [
    (
        "Comment",
        "idx_comment_post_active_date",
        "CREATE INDEX idx_comment_post_active_date ON Comment(PostID, IsActive, CommentDate ASC)",
    ),
]

LEGACY_EXPERIMENT_INDEXES = [
    ("Post", "idx_post_active_date_member"),
    ("Post", "idx_post_date_active"),
]


def safe_drop_index(cursor, table_name, index_name):
    try:
        cursor.execute(f"DROP INDEX {index_name} ON {table_name}")
    except pymysql.MySQLError:
        pass


def ensure_benchmark_data():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS c FROM Post WHERE Content LIKE %s",
                (f"{BENCH_PREFIX}%",),
            )
            existing_posts = cursor.fetchone()["c"]

            to_add = max(0, TARGET_BENCH_POSTS - existing_posts)
            if to_add > 0:
                post_values = []
                for i in range(to_add):
                    post_values.append(
                        (
                            1,
                            f"{BENCH_PREFIX} synthetic post {existing_posts + i + 1}",
                            None,
                            "None",
                            "Public",
                        )
                    )

                cursor.executemany(
                    """
                    INSERT INTO Post (MemberID, Content, MediaURL, MediaType, Visibility)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    post_values,
                )

                cursor.execute(
                    """
                    SELECT PostID
                    FROM Post
                    WHERE Content LIKE %s
                    ORDER BY PostID DESC
                    LIMIT %s
                    """,
                    (f"{BENCH_PREFIX}%", to_add),
                )
                inserted_posts = [row["PostID"] for row in cursor.fetchall()]

                comment_values = []
                for post_id in inserted_posts:
                    for j in range(COMMENTS_PER_BENCH_POST):
                        comment_values.append((post_id, 1, f"{BENCH_PREFIX} synthetic comment {j + 1} for post {post_id}"))

                cursor.executemany(
                    """
                    INSERT INTO Comment (PostID, MemberID, Content)
                    VALUES (%s, %s, %s)
                    """,
                    comment_values,
                )

            cursor.execute(
                """
                SELECT PostID
                FROM Post
                WHERE Content = %s
                LIMIT 1
                """,
                (f"{BENCH_PREFIX} hotspot post",),
            )
            hotspot = cursor.fetchone()
            if hotspot:
                hotspot_post_id = hotspot["PostID"]
            else:
                cursor.execute(
                    """
                    INSERT INTO Post (MemberID, Content, MediaURL, MediaType, Visibility)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (1, f"{BENCH_PREFIX} hotspot post", None, "None", "Public"),
                )
                hotspot_post_id = cursor.lastrowid

            cursor.execute(
                """
                SELECT COUNT(*) AS c
                FROM Comment
                WHERE PostID = %s AND Content LIKE %s
                """,
                (hotspot_post_id, f"{BENCH_PREFIX} hotspot comment%"),
            )
            existing_hot_comments = cursor.fetchone()["c"]
            to_add_hot = max(0, TARGET_HOT_POST_COMMENTS - existing_hot_comments)
            if to_add_hot > 0:
                hot_comment_values = [
                    (hotspot_post_id, 1, f"{BENCH_PREFIX} hotspot comment {existing_hot_comments + i + 1}")
                    for i in range(to_add_hot)
                ]
                cursor.executemany(
                    """
                    INSERT INTO Comment (PostID, MemberID, Content)
                    VALUES (%s, %s, %s)
                    """,
                    hot_comment_values,
                )

            return hotspot_post_id
    finally:
        conn.close()


def percentile(values, pct):
    if not values:
        return 0.0
    idx = int(round((pct / 100.0) * (len(values) - 1)))
    return sorted(values)[idx]


def summarize_times(values):
    return {
        "avg_ms": round(statistics.mean(values), 3),
        "p95_ms": round(percentile(values, 95), 3),
        "min_ms": round(min(values), 3),
        "max_ms": round(max(values), 3),
    }


def run_sql_timing(sql, params_builder):
    conn = get_db_connection()
    durations = []
    try:
        with conn.cursor() as cursor:
            for _ in range(WARMUP):
                cursor.execute(sql, params_builder())
                cursor.fetchall()

            for _ in range(ITERATIONS):
                params = params_builder()
                start = time.perf_counter()
                cursor.execute(sql, params)
                cursor.fetchall()
                end = time.perf_counter()
                durations.append((end - start) * 1000.0)
    finally:
        conn.close()
    return durations


def get_explain(sql, params):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("EXPLAIN " + sql, params)
            rows = cursor.fetchall()
    finally:
        conn.close()

    compact = []
    for row in rows:
        compact.append(
            {
                "table": row.get("table"),
                "type": row.get("type"),
                "key": row.get("key"),
                "rows": row.get("rows"),
                "extra": row.get("Extra"),
            }
        )
    return compact


def run_api_timing(limit, offset, post_id):
    login_req = urlrequest.Request(
        f"{API_BASE}/login",
        data=json.dumps({"username": "rahul.sharma@iitgn.ac.in", "password": "password123"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urlrequest.urlopen(login_req, timeout=20) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Login failed during benchmark: {resp.status}")
        token = json.loads(resp.read().decode("utf-8"))["session_token"]

    auth_headers = {
        "session-token": token,
        "Content-Type": "application/json",
    }

    def api_get(path):
        req = urlrequest.Request(f"{API_BASE}{path}", headers=auth_headers, method="GET")
        with urlrequest.urlopen(req, timeout=20) as resp:
            payload = resp.read().decode("utf-8")
            return resp.status, payload

    posts_api_times = []
    comments_api_times = []

    for _ in range(WARMUP):
        api_get(f"/posts?limit={limit}&offset={offset}")
        api_get(f"/posts/{post_id}/comments")

    for _ in range(ITERATIONS):
        start = time.perf_counter()
        posts_status, posts_payload = api_get(f"/posts?limit={limit}&offset={offset}")
        end = time.perf_counter()
        if posts_status != 200:
            raise RuntimeError(f"/posts failed: {posts_status} {posts_payload}")
        posts_api_times.append((end - start) * 1000.0)

        start = time.perf_counter()
        comments_status, comments_payload = api_get(f"/posts/{post_id}/comments")
        end = time.perf_counter()
        if comments_status != 200:
            raise RuntimeError(f"/posts/{{id}}/comments failed: {comments_status} {comments_payload}")
        comments_api_times.append((end - start) * 1000.0)

    return posts_api_times, comments_api_times


def choose_benchmark_params():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS c FROM Post WHERE IsActive = TRUE")
            total_active_posts = cursor.fetchone()["c"]
    finally:
        conn.close()

    limit = 20
    offset = 0
    if total_active_posts > limit:
        offset = min(total_active_posts - limit, total_active_posts // 2)
    return limit, offset


def set_indexes(enabled):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            for table_name, index_name in LEGACY_EXPERIMENT_INDEXES:
                safe_drop_index(cursor, table_name, index_name)
            for table_name, index_name, ddl in INDEX_DEFS:
                safe_drop_index(cursor, table_name, index_name)
            if enabled:
                for _, _, ddl in INDEX_DEFS:
                    cursor.execute(ddl)
    finally:
        conn.close()


def run_stage(stage_name, index_enabled, limit, offset, post_id):
    set_indexes(index_enabled)

    posts_sql_times = run_sql_timing(LIST_POSTS_SQL, lambda: (limit, offset))
    comments_sql_times = run_sql_timing(LIST_COMMENTS_SQL, lambda: (post_id,))
    posts_api_times, comments_api_times = run_api_timing(limit, offset, post_id)

    explain_posts = get_explain(LIST_POSTS_SQL, (limit, offset))
    explain_comments = get_explain(LIST_COMMENTS_SQL, (post_id,))

    return {
        "stage": stage_name,
        "indexes_enabled": index_enabled,
        "sql_ms": {
            "list_posts": summarize_times(posts_sql_times),
            "list_comments": summarize_times(comments_sql_times),
        },
        "api_ms": {
            "list_posts": summarize_times(posts_api_times),
            "list_comments": summarize_times(comments_api_times),
        },
        "explain": {
            "list_posts": explain_posts,
            "list_comments": explain_comments,
        },
    }


def speedup(before_ms, after_ms):
    if after_ms == 0:
        return None
    return round(before_ms / after_ms, 3)


def main():
    hotspot_post_id = ensure_benchmark_data()
    limit, offset = choose_benchmark_params()
    post_id = hotspot_post_id

    before = run_stage("before_indexes", False, limit, offset, post_id)
    after = run_stage("after_indexes", True, limit, offset, post_id)

    summary = {
        "posts_sql_speedup": speedup(before["sql_ms"]["list_posts"]["avg_ms"], after["sql_ms"]["list_posts"]["avg_ms"]),
        "comments_sql_speedup": speedup(before["sql_ms"]["list_comments"]["avg_ms"], after["sql_ms"]["list_comments"]["avg_ms"]),
        "posts_api_speedup": speedup(before["api_ms"]["list_posts"]["avg_ms"], after["api_ms"]["list_posts"]["avg_ms"]),
        "comments_api_speedup": speedup(before["api_ms"]["list_comments"]["avg_ms"], after["api_ms"]["list_comments"]["avg_ms"]),
    }

    output = {
        "db_config": {
            "host": DB_HOST,
            "user": DB_USER,
            "database": DB_NAME,
        },
        "benchmark_params": {
            "iterations": ITERATIONS,
            "warmup": WARMUP,
            "limit": limit,
            "offset": offset,
            "comment_post_id": post_id,
        },
        "stages": [before, after],
        "speedup": summary,
    }

    out_dir = Path(__file__).resolve().parent.parent / "performance"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "index_benchmark_results.json"
    out_file.write_text(json.dumps(output, indent=2), encoding="utf-8")

    print("Benchmark complete")
    print(f"Results: {out_file}")
    print("Speedup summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}x")


if __name__ == "__main__":
    main()

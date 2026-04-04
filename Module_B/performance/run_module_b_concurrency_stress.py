#!/usr/bin/env python3
"""
Module B concurrency and stress runner.

What this script validates:
1. Concurrent usage behavior under load (read-heavy stress).
2. Race-condition safety on follow creation.
3. Failure handling with mixed valid/invalid writes.
4. Consistency checks between materialized counters and base rows.

Prerequisites:
- FastAPI server is running.
- MySQL schema/data are loaded.
- DB_* environment variables are set if non-default values are used.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error as urlerror
from urllib import request as urlrequest

import pymysql
from pymysql.cursors import DictCursor


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "college_social_media")


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _db_connect():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=True,
    )


def _api_request(
    *,
    base_url: str,
    method: str,
    path: str,
    token: str | None = None,
    payload: dict[str, Any] | None = None,
    timeout_s: int = 20,
) -> dict[str, Any]:
    data = None
    headers = {"Content-Type": "application/json"}
    if token:
        headers["session-token"] = token
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    req = urlrequest.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers=headers,
        method=method,
    )

    started = time.perf_counter()
    try:
        with urlrequest.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8")
            elapsed_ms = (time.perf_counter() - started) * 1000.0
            body = json.loads(raw) if raw else {}
            return {
                "ok": 200 <= resp.status < 300,
                "status": resp.status,
                "body": body,
                "elapsed_ms": elapsed_ms,
            }
    except urlerror.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp is not None else ""
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        try:
            body = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            body = {"detail": raw}
        return {
            "ok": False,
            "status": exc.code,
            "body": body,
            "elapsed_ms": elapsed_ms,
        }
    except Exception as exc:  # noqa: BLE001
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        return {
            "ok": False,
            "status": 0,
            "body": {"detail": str(exc)},
            "elapsed_ms": elapsed_ms,
        }


def _login(base_url: str, username: str, password: str) -> str:
    resp = _api_request(
        base_url=base_url,
        method="POST",
        path="/login",
        payload={"username": username, "password": password},
    )
    if not resp["ok"]:
        raise RuntimeError(f"Login failed: HTTP {resp['status']} {resp['body']}")
    token = resp["body"].get("session_token")
    if not token:
        raise RuntimeError("Login response did not include session_token")
    return token


def _latency_stats(values_ms: list[float]) -> dict[str, float]:
    if not values_ms:
        return {
            "avg_ms": 0.0,
            "min_ms": 0.0,
            "max_ms": 0.0,
            "p50_ms": 0.0,
            "p95_ms": 0.0,
        }

    ordered = sorted(values_ms)

    def percentile(p: float) -> float:
        if len(ordered) == 1:
            return ordered[0]
        idx = round((p / 100.0) * (len(ordered) - 1))
        return ordered[idx]

    return {
        "avg_ms": round(statistics.mean(ordered), 3),
        "min_ms": round(ordered[0], 3),
        "max_ms": round(ordered[-1], 3),
        "p50_ms": round(percentile(50), 3),
        "p95_ms": round(percentile(95), 3),
    }


def _run_parallel(total_requests: int, workers: int, fn):
    out: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(fn, i) for i in range(total_requests)]
        for fut in as_completed(futures):
            out.append(fut.result())
    return out


def _fetch_post_consistency(post_id: int) -> dict[str, Any]:
    conn = _db_connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT PostID, LikeCount, CommentCount
                FROM Post
                WHERE PostID = %s
                """,
                (post_id,),
            )
            post = cursor.fetchone()
            if not post:
                raise RuntimeError(f"Post {post_id} not found")

            cursor.execute(
                """
                SELECT COUNT(*) AS c
                FROM `Like`
                WHERE TargetType = 'Post' AND TargetID = %s
                """,
                (post_id,),
            )
            likes = cursor.fetchone()

            cursor.execute(
                """
                SELECT COUNT(*) AS c
                FROM Comment
                WHERE PostID = %s AND IsActive = TRUE
                """,
                (post_id,),
            )
            comments = cursor.fetchone()

            like_rows = int(likes["c"])
            active_comment_rows = int(comments["c"])
            post_like_count = int(post["LikeCount"])
            post_comment_count = int(post["CommentCount"])

            return {
                "post_id": int(post["PostID"]),
                "post_like_count": post_like_count,
                "like_rows": like_rows,
                "post_comment_count": post_comment_count,
                "active_comment_rows": active_comment_rows,
                "like_count_consistent": post_like_count == like_rows,
                "comment_count_consistent": post_comment_count == active_comment_rows,
            }
    finally:
        conn.close()


def _fetch_follow_relation_count(follower_id: int, following_id: int) -> int:
    conn = _db_connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) AS c FROM Follow WHERE FollowerID = %s AND FollowingID = %s",
                (follower_id, following_id),
            )
            row = cursor.fetchone()
            return int(row["c"])
    finally:
        conn.close()


def _fetch_member_id_by_email(email: str) -> int:
    conn = _db_connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MemberID FROM Member WHERE Email = %s", (email,))
            row = cursor.fetchone()
            if row is None:
                raise RuntimeError(f"No Member row found for email {email}")
            return int(row["MemberID"])
    finally:
        conn.close()


def _cleanup_generated_comments(post_id: int, content_prefix: str) -> int:
    conn = _db_connect()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*) AS c
                FROM Comment
                WHERE PostID = %s AND IsActive = TRUE AND Content LIKE %s
                """,
                (post_id, f"{content_prefix}%"),
            )
            row = cursor.fetchone()
            active_rows = int(row["c"])
            if active_rows == 0:
                return 0

            cursor.execute(
                """
                UPDATE Comment
                SET IsActive = FALSE
                WHERE PostID = %s AND IsActive = TRUE AND Content LIKE %s
                """,
                (post_id, f"{content_prefix}%"),
            )
            cursor.execute(
                """
                UPDATE Post
                SET CommentCount = GREATEST(CommentCount - %s, 0)
                WHERE PostID = %s
                """,
                (active_rows, post_id),
            )
            return active_rows
    finally:
        conn.close()


def run_follow_race_test(
    *,
    base_url: str,
    token: str,
    follower_id: int,
    target_member_id: int,
    race_requests: int,
    race_workers: int,
) -> dict[str, Any]:
    _api_request(base_url=base_url, method="DELETE", path=f"/members/{target_member_id}/follow", token=token)

    started = time.perf_counter()
    lock = threading.Lock()
    statuses: list[int] = []
    latencies: list[float] = []

    def worker(_: int) -> dict[str, Any]:
        resp = _api_request(
            base_url=base_url,
            method="POST",
            path=f"/members/{target_member_id}/follow",
            token=token,
        )
        with lock:
            statuses.append(int(resp["status"]))
            latencies.append(float(resp["elapsed_ms"]))
        return resp

    responses = _run_parallel(race_requests, race_workers, worker)
    elapsed = time.perf_counter() - started

    relation_count = _fetch_follow_relation_count(follower_id, target_member_id)
    ok_statuses = sum(1 for s in statuses if s == 200)
    relation_is_unique = relation_count == 1

    return {
        "requests": race_requests,
        "workers": race_workers,
        "elapsed_s": round(elapsed, 3),
        "status_histogram": {
            str(code): statuses.count(code) for code in sorted(set(statuses))
        },
        "success_responses": ok_statuses,
        "latency": _latency_stats(latencies),
        "follow_relation_count": relation_count,
        "race_passed": relation_is_unique,
        "details": "Pass requires exactly one follow edge after all concurrent attempts",
        "sample_response": responses[0]["body"] if responses else {},
    }


def run_failure_simulation(
    *,
    base_url: str,
    token: str,
    post_id: int,
    total_requests: int,
    workers: int,
    keep_generated_comments: bool,
) -> dict[str, Any]:
    before = _fetch_post_consistency(post_id)
    content_prefix = f"[module-b-failure-test-{int(time.time())}]"

    lock = threading.Lock()
    latencies: list[float] = []
    statuses: list[int] = []

    def worker(i: int) -> dict[str, Any]:
        expected_valid = i % 2 == 0
        if expected_valid:
            payload = {"content": f"{content_prefix} valid-{i}"}
        else:
            payload = {"content": "   "}

        resp = _api_request(
            base_url=base_url,
            method="POST",
            path=f"/posts/{post_id}/comments",
            token=token,
            payload=payload,
        )
        resp["expected_valid"] = expected_valid
        with lock:
            latencies.append(float(resp["elapsed_ms"]))
            statuses.append(int(resp["status"]))
        return resp

    started = time.perf_counter()
    responses = _run_parallel(total_requests, workers, worker)
    elapsed = time.perf_counter() - started

    valid_success = sum(1 for r in responses if r.get("expected_valid") and r["status"] == 200)
    invalid_requests = sum(1 for r in responses if not r.get("expected_valid"))
    invalid_failures = sum(
        1 for r in responses if (not r.get("expected_valid")) and r["status"] in (400, 404)
    )

    after = _fetch_post_consistency(post_id)
    expected_delta = valid_success
    actual_delta = after["active_comment_rows"] - before["active_comment_rows"]

    cleaned_rows = 0
    if not keep_generated_comments:
        cleaned_rows = _cleanup_generated_comments(post_id, content_prefix)
        after = _fetch_post_consistency(post_id)

    return {
        "requests": total_requests,
        "workers": workers,
        "elapsed_s": round(elapsed, 3),
        "status_histogram": {
            str(code): statuses.count(code) for code in sorted(set(statuses))
        },
        "latency": _latency_stats(latencies),
        "before": before,
        "after": after,
        "valid_success_responses": valid_success,
        "invalid_expected_failures": invalid_failures,
        "expected_comment_delta": expected_delta,
        "actual_comment_delta": actual_delta,
        "cleanup_performed": not keep_generated_comments,
        "cleaned_comment_rows": cleaned_rows,
        "failure_simulation_passed": (actual_delta == expected_delta) and (invalid_failures == invalid_requests),
        "details": "Pass requires failed writes to leave no partial comment-count effects",
    }


def run_stress_reads(
    *,
    base_url: str,
    token: str,
    total_requests: int,
    workers: int,
    offset_window: int,
) -> dict[str, Any]:
    lock = threading.Lock()
    latencies: list[float] = []
    statuses: list[int] = []

    def worker(_: int) -> dict[str, Any]:
        offset = random.randint(0, max(offset_window, 0))
        resp = _api_request(
            base_url=base_url,
            method="GET",
            path=f"/posts?limit=20&offset={offset}",
            token=token,
        )
        with lock:
            latencies.append(float(resp["elapsed_ms"]))
            statuses.append(int(resp["status"]))
        return resp

    started = time.perf_counter()
    _run_parallel(total_requests, workers, worker)
    elapsed = time.perf_counter() - started

    successes = sum(1 for code in statuses if code == 200)
    success_rate = (successes / total_requests) if total_requests > 0 else 0.0
    throughput = (total_requests / elapsed) if elapsed > 0 else 0.0

    return {
        "requests": total_requests,
        "workers": workers,
        "elapsed_s": round(elapsed, 3),
        "throughput_req_per_s": round(throughput, 3),
        "success_count": successes,
        "success_rate": round(success_rate, 4),
        "status_histogram": {
            str(code): statuses.count(code) for code in sorted(set(statuses))
        },
        "latency": _latency_stats(latencies),
        "stress_passed": success_rate >= 0.95,
        "details": "Pass threshold uses >=95% successful responses under configured load",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run Module B concurrency, race, and stress tests")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--username", default="rahul.sharma@iitgn.ac.in")
    parser.add_argument("--password", default="password123")
    parser.add_argument("--target-member-id", type=int, default=19)
    parser.add_argument("--post-id", type=int, default=1)

    parser.add_argument("--race-requests", type=int, default=200)
    parser.add_argument("--race-workers", type=int, default=40)

    parser.add_argument("--failure-requests", type=int, default=120)
    parser.add_argument("--failure-workers", type=int, default=24)

    parser.add_argument("--stress-requests", type=int, default=1000)
    parser.add_argument("--stress-workers", type=int, default=80)
    parser.add_argument("--offset-window", type=int, default=1500)

    parser.add_argument(
        "--output",
        default="Module_B/performance/module_b_concurrency_report.json",
        help="Output JSON report path",
    )
    parser.add_argument(
        "--keep-generated-comments",
        action="store_true",
        help="Do not soft-delete comments generated by failure simulation",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()

    token = _login(args.base_url, args.username, args.password)
    follower_id = _fetch_member_id_by_email(args.username)

    before = _fetch_post_consistency(args.post_id)

    race_result = run_follow_race_test(
        base_url=args.base_url,
        token=token,
        follower_id=follower_id,
        target_member_id=args.target_member_id,
        race_requests=args.race_requests,
        race_workers=args.race_workers,
    )
    failure_result = run_failure_simulation(
        base_url=args.base_url,
        token=token,
        post_id=args.post_id,
        total_requests=args.failure_requests,
        workers=args.failure_workers,
        keep_generated_comments=args.keep_generated_comments,
    )
    stress_result = run_stress_reads(
        base_url=args.base_url,
        token=token,
        total_requests=args.stress_requests,
        workers=args.stress_workers,
        offset_window=args.offset_window,
    )

    after = _fetch_post_consistency(args.post_id)

    overall_pass = (
        before["like_count_consistent"]
        and before["comment_count_consistent"]
        and race_result["race_passed"]
        and failure_result["failure_simulation_passed"]
        and stress_result["stress_passed"]
        and after["like_count_consistent"]
        and after["comment_count_consistent"]
    )

    report = {
        "timestamp_utc": _now_utc_iso(),
        "config": {
            "base_url": args.base_url,
            "username": args.username,
            "target_member_id": args.target_member_id,
            "post_id": args.post_id,
            "race_requests": args.race_requests,
            "race_workers": args.race_workers,
            "failure_requests": args.failure_requests,
            "failure_workers": args.failure_workers,
            "stress_requests": args.stress_requests,
            "stress_workers": args.stress_workers,
            "offset_window": args.offset_window,
            "keep_generated_comments": args.keep_generated_comments,
        },
        "db_config": {
            "host": DB_HOST,
            "user": DB_USER,
            "database": DB_NAME,
        },
        "consistency_before": before,
        "race_follow_test": race_result,
        "failure_simulation": failure_result,
        "stress_reads": stress_result,
        "consistency_after": after,
        "overall_pass": overall_pass,
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(json.dumps(
        {
            "overall_pass": overall_pass,
            "race_passed": race_result["race_passed"],
            "failure_simulation_passed": failure_result["failure_simulation_passed"],
            "stress_passed": stress_result["stress_passed"],
            "output": str(output_path),
        },
        indent=2,
    ))


if __name__ == "__main__":
    main()

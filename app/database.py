import os
from typing import Any, Callable, TypeVar

import pymysql
from pymysql.cursors import DictCursor

# Database configuration - in a real app, use environment variables
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "college_social_media")


def _env_flag(name: str, default: str = "0") -> bool:
    value = os.getenv(name, default)
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


USE_DISTRIBUTED_SHARDS = _env_flag("USE_DISTRIBUTED_SHARDS", "0")
SHARD_HOST = os.getenv("SHARD_HOST", DB_HOST)
SHARD_DB = os.getenv("SHARD_DB", DB_NAME)


def _parse_shard_ports() -> list[int]:
    raw = os.getenv("SHARD_PORTS", "3307,3308,3309")
    ports = []
    for part in raw.split(","):
        token = part.strip()
        if not token:
            continue
        try:
            ports.append(int(token))
        except ValueError:
            continue
    return ports if ports else [3307, 3308, 3309]


SHARD_PORTS = _parse_shard_ports()

T = TypeVar("T")


class DatabaseQueryError(Exception):
    """Raised when a database operation cannot be completed."""

    def __init__(self, message: str, error_code: int | None = None) -> None:
        super().__init__(message)
        self.error_code = error_code


def is_distributed_shards_enabled() -> bool:
    return USE_DISTRIBUTED_SHARDS


def get_db_connection(*, autocommit: bool = True):
    """
    Establishes and returns a connection to the local MySQL database.
    Uses DictCursor so results are returned as dictionaries instead of tuples.
    """
    connection = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=DictCursor,
        autocommit=autocommit,
    )
    return connection


def get_shard_connection(shard_id: int, *, autocommit: bool = True):
    """
    Connect to one distributed shard node (same DB/user, different port).
    """
    if shard_id < 0 or shard_id >= len(SHARD_PORTS):
        raise ValueError(f"Invalid shard_id={shard_id}; expected 0..{len(SHARD_PORTS)-1}")

    connection = pymysql.connect(
        host=SHARD_HOST,
        port=SHARD_PORTS[shard_id],
        user=DB_USER,
        password=DB_PASSWORD,
        database=SHARD_DB,
        cursorclass=DictCursor,
        autocommit=autocommit,
    )
    return connection


def _apply_audit_context(cursor, audit_context: dict[str, Any]) -> None:
    cursor.execute(
        """
        SET
            @api_authorized = %s,
            @api_actor_id = %s,
            @api_action = %s,
            @api_endpoint = %s,
            @api_method = %s
        """,
        (
            1,
            audit_context.get("actor_id"),
            audit_context.get("action"),
            audit_context.get("endpoint"),
            audit_context.get("method"),
        ),
    )


def execute_query(query, params=None, fetchall=False, fetchone=False, audit_context: dict[str, Any] | None = None):
    """
    Helper function to safely execute SQL queries.
    """
    conn = None
    try:
        conn = get_db_connection(autocommit=True)
        with conn.cursor() as cursor:
            if audit_context is not None:
                _apply_audit_context(cursor, audit_context)
            cursor.execute(query, params)
            if fetchall:
                return cursor.fetchall()
            if fetchone:
                return cursor.fetchone()
            return cursor.lastrowid
    except pymysql.MySQLError as exc:
        error_code = exc.args[0] if exc.args else None
        raise DatabaseQueryError("Database operation failed", error_code=error_code) from exc
    finally:
        if conn is not None:
            conn.close()


def execute_query_on_shard(
    shard_id: int,
    query,
    params=None,
    fetchall: bool = False,
    fetchone: bool = False,
    audit_context: dict[str, Any] | None = None,
):
    """
    Execute a query on a specific shard node.
    """
    conn = None
    try:
        conn = get_shard_connection(shard_id, autocommit=True)
        with conn.cursor() as cursor:
            if audit_context is not None:
                _apply_audit_context(cursor, audit_context)
            cursor.execute(query, params)
            if fetchall:
                return cursor.fetchall()
            if fetchone:
                return cursor.fetchone()
            return cursor.lastrowid
    except pymysql.MySQLError as exc:
        error_code = exc.args[0] if exc.args else None
        raise DatabaseQueryError("Database operation failed", error_code=error_code) from exc
    finally:
        if conn is not None:
            conn.close()


def execute_query_all_shards(
    query,
    params=None,
    *,
    include_shard_id: bool = False,
) -> list[dict[str, Any]]:
    """
    Fan-out query execution to every shard and merge results.
    """
    merged: list[dict[str, Any]] = []
    for shard_id in range(len(SHARD_PORTS)):
        rows = execute_query_on_shard(shard_id, query, params, fetchall=True)
        if include_shard_id:
            for row in rows:
                row["_shard_id"] = shard_id
        merged.extend(rows)
    return merged


def execute_transaction(
    transaction_fn: Callable[[Any], T],
    audit_context: dict[str, Any] | None = None,
) -> T:
    """
    Execute multiple SQL operations atomically in a single DB transaction.
    """
    conn = None
    try:
        conn = get_db_connection(autocommit=False)
        with conn.cursor() as cursor:
            if audit_context is not None:
                _apply_audit_context(cursor, audit_context)
            result = transaction_fn(cursor)
        conn.commit()
        return result
    except pymysql.MySQLError as exc:
        if conn is not None:
            conn.rollback()
        error_code = exc.args[0] if exc.args else None
        raise DatabaseQueryError("Database operation failed", error_code=error_code) from exc
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()


def execute_transaction_on_shard(
    shard_id: int,
    transaction_fn: Callable[[Any], T],
    audit_context: dict[str, Any] | None = None,
) -> T:
    """
    Execute multiple SQL operations atomically on one shard.
    """
    conn = None
    try:
        conn = get_shard_connection(shard_id, autocommit=False)
        with conn.cursor() as cursor:
            if audit_context is not None:
                _apply_audit_context(cursor, audit_context)
            result = transaction_fn(cursor)
        conn.commit()
        return result
    except pymysql.MySQLError as exc:
        if conn is not None:
            conn.rollback()
        error_code = exc.args[0] if exc.args else None
        raise DatabaseQueryError("Database operation failed", error_code=error_code) from exc
    except Exception:
        if conn is not None:
            conn.rollback()
        raise
    finally:
        if conn is not None:
            conn.close()

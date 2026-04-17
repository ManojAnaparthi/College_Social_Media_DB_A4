"""
shard_router.py  –  CS 432 Assignment 4: Sub-Task 3 (Query Routing)

Central routing module for hash-based sharding.

Strategy
--------
    shard_id = CRC32(str(MemberID)) % NUM_SHARDS

All application logic that needs to read from / write to a shard table
imports from this module to keep the routing rule in one place.
"""

from __future__ import annotations

import zlib

NUM_SHARDS = 3
ALL_SHARDS = list(range(NUM_SHARDS))   # [0, 1, 2]

# Tables that are sharded (maps base name → shard prefix pattern)
SHARDED_TABLES = ("member", "post", "comment")


def hash_member_id(member_id: int) -> int:
    """Return a deterministic integer hash for the given shard key."""
    return zlib.crc32(str(member_id).encode("utf-8"))


def get_shard_id(member_id: int) -> int:
    """
    Compute which shard a given MemberID belongs to.

    Parameters
    ----------
    member_id : int
        The MemberID extracted from the request or record.

    Returns
    -------
    int
        Shard index in [0, NUM_SHARDS).
    """
    return hash_member_id(member_id) % NUM_SHARDS


def get_shard_table(base_table: str, member_id: int) -> str:
    """
    Return the fully-qualified shard table name for a given base table and member.

    Examples
    --------
    >>> get_shard_table("member", 1)
    'shard_2_member'
    >>> get_shard_table("post", 3)
    'shard_1_post'
    """
    shard_id = get_shard_id(member_id)
    return f"shard_{shard_id}_{base_table.lower()}"


def all_shard_tables(base_table: str) -> list[str]:
    """
    Return a list of all shard table names for *base_table* (for fan-out queries).

    Example
    -------
    >>> all_shard_tables("post")
    ['shard_0_post', 'shard_1_post', 'shard_2_post']
    """
    return [f"shard_{i}_{base_table.lower()}" for i in ALL_SHARDS]

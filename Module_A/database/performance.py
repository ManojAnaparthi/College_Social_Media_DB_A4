from __future__ import annotations

import random
import time
import tracemalloc
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from .bplustree import BPlusTree
from .bruteforce import BruteForceDB


@dataclass
class BenchmarkConfig:
    sizes: Tuple[int, ...] = (100, 500, 1000, 5000)
    seed: int = 42
    bplustree_order: int = 4


class PerformanceAnalyzer:
    """Automated benchmark suite for B+ Tree vs brute-force baseline."""

    def __init__(self, config: BenchmarkConfig | None = None) -> None:
        self.config = config or BenchmarkConfig()

    def run_all_benchmarks(self) -> Dict[str, Any]:
        random.seed(self.config.seed)
        results: List[Dict[str, Any]] = []

        for size in self.config.sizes:
            keys = random.sample(range(size * 20), size)
            values = [f"v_{k}" for k in keys]

            search_keys = random.sample(keys, max(1, min(size, size // 5)))
            missing_keys = [size * 25 + i for i in range(len(search_keys))]
            mixed_search = search_keys + missing_keys
            random.shuffle(mixed_search)

            delete_keys = random.sample(keys, max(1, min(size, size // 5)))

            low = min(keys) + (max(keys) - min(keys)) // 4
            high = min(keys) + 3 * (max(keys) - min(keys)) // 4
            range_windows = [(low, high), (min(keys), max(keys)), (low - 10, high + 10)]
            random_workload = self._generate_random_workload(size, max(keys) + size * 10 if keys else 1000)

            bplus_metrics = self._benchmark_structure(
                lambda: BPlusTree(order=self.config.bplustree_order),
                keys,
                values,
                mixed_search,
                delete_keys,
                range_windows,
                random_workload,
            )

            brute_metrics = self._benchmark_structure(
                BruteForceDB,
                keys,
                values,
                mixed_search,
                delete_keys,
                range_windows,
                random_workload,
            )

            results.append(
                {
                    "size": size,
                    "bplustree": bplus_metrics,
                    "bruteforce": brute_metrics,
                }
            )

        return {
            "config": {
                "sizes": list(self.config.sizes),
                "seed": self.config.seed,
                "bplustree_order": self.config.bplustree_order,
            },
            "results": results,
        }

    def to_table_rows(self, benchmark_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        for item in benchmark_results["results"]:
            n = item["size"]
            rows.append(self._row("bplustree", n, item["bplustree"]))
            rows.append(self._row("bruteforce", n, item["bruteforce"]))

        return rows

    def _row(self, engine: str, size: int, metrics: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "engine": engine,
            "size": size,
            "insert_sec": metrics["insert_time_sec"],
            "search_sec": metrics["search_time_sec"],
            "delete_sec": metrics["delete_time_sec"],
            "range_sec": metrics["range_query_time_sec"],
            "mixed_sec": metrics["random_workload_time_sec"],
            "peak_memory_kib": metrics["peak_memory_bytes"] / 1024.0,
        }

    def _benchmark_structure(
        self,
        factory,
        keys: List[int],
        values: List[Any],
        search_keys: List[int],
        delete_keys: List[int],
        range_windows: List[Tuple[int, int]],
        random_workload: List[Tuple[str, Any]],
    ) -> Dict[str, Any]:
        insert_time = self._time_insert(factory, keys, values)
        search_time = self._time_search(factory, keys, values, search_keys)
        delete_time = self._time_delete(factory, keys, values, delete_keys)
        range_time = self._time_range(factory, keys, values, range_windows)
        random_time = self._time_random_workload(factory, random_workload)
        peak_memory = self._measure_peak_memory(factory, keys, values)

        return {
            "insert_time_sec": insert_time,
            "search_time_sec": search_time,
            "delete_time_sec": delete_time,
            "range_query_time_sec": range_time,
            "random_workload_time_sec": random_time,
            "peak_memory_bytes": peak_memory,
        }

    def _time_insert(self, factory, keys: List[int], values: List[Any]) -> float:
        ds = factory()
        start = time.perf_counter()
        for k, v in zip(keys, values):
            ds.insert(k, v)
        return time.perf_counter() - start

    def _time_search(self, factory, keys: List[int], values: List[Any], search_keys: List[int]) -> float:
        ds = self._build(factory, keys, values)
        start = time.perf_counter()
        for k in search_keys:
            ds.search(k)
        return time.perf_counter() - start

    def _time_delete(self, factory, keys: List[int], values: List[Any], delete_keys: List[int]) -> float:
        ds = self._build(factory, keys, values)
        start = time.perf_counter()
        for k in delete_keys:
            ds.delete(k)
        return time.perf_counter() - start

    def _time_range(self, factory, keys: List[int], values: List[Any], ranges: List[Tuple[int, int]]) -> float:
        ds = self._build(factory, keys, values)
        start = time.perf_counter()
        for low, high in ranges:
            ds.range_query(low, high)
        return time.perf_counter() - start

    def _time_random_workload(self, factory, workload: List[Tuple[str, Any]]) -> float:
        ds = factory()

        start = time.perf_counter()
        for op, payload in workload:
            if op == "insert":
                key, value = payload
                ds.insert(key, value)
            elif op == "search":
                ds.search(payload)
            elif op == "delete":
                ds.delete(payload)
            else:
                low, high = payload
                ds.range_query(low, high)

        return time.perf_counter() - start

    def _generate_random_workload(self, size: int, key_space: int) -> List[Tuple[str, Any]]:
        workload: List[Tuple[str, Any]] = []
        existing = set()

        for _ in range(max(50, size)):
            op = random.choices(
                ["insert", "search", "delete", "range"],
                weights=[0.35, 0.30, 0.20, 0.15],
                k=1,
            )[0]

            if op == "insert":
                key = random.randint(0, key_space)
                existing.add(key)
                workload.append(("insert", (key, f"v_{key}")))
            elif op == "search":
                if existing and random.random() < 0.7:
                    key = random.choice(list(existing))
                else:
                    key = random.randint(0, key_space)
                workload.append(("search", key))
            elif op == "delete":
                if existing:
                    key = random.choice(list(existing))
                    existing.remove(key)
                else:
                    key = random.randint(0, key_space)
                workload.append(("delete", key))
            else:
                a = random.randint(0, key_space)
                b = random.randint(0, key_space)
                low, high = (a, b) if a <= b else (b, a)
                workload.append(("range", (low, high)))

        return workload

    def _measure_peak_memory(self, factory, keys: List[int], values: List[Any]) -> int:
        tracemalloc.start()
        ds = factory()
        for k, v in zip(keys, values):
            ds.insert(k, v)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return peak

    def _build(self, factory, keys: List[int], values: List[Any]):
        ds = factory()
        for k, v in zip(keys, values):
            ds.insert(k, v)
        return ds

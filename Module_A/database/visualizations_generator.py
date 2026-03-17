"""
Performance visualization module for B+ Tree vs Brute Force comparison.
Generates comprehensive matplotlib plots comparing different operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend for Windows
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from matplotlib.figure import Figure


class PerformanceVisualizer:
    """Generate comprehensive performance comparison visualizations."""

    def __init__(self, output_dir: str | Path = "visualizations") -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.jpg_output_dir = self.output_dir.parent / "performance_results_jpgs"
        self.jpg_output_dir.mkdir(parents=True, exist_ok=True)

    def _save_figure(self, fig: Figure, base_name: str) -> None:
        """Save each chart as JPG in the dedicated performance results folder."""
        jpg_path = self.jpg_output_dir / f"{base_name}.jpg"
        fig.savefig(jpg_path, dpi=300, bbox_inches='tight')

    def visualize_benchmarks(self, benchmark_results: Dict[str, Any]) -> None:
        """
        Create multiple comparison plots from benchmark results.
        Generates separate plots for each operation type.
        """
        results = benchmark_results["results"]
        sizes = [r["size"] for r in results]

        # Extract metrics
        bplus_insert = [r["bplustree"]["insert_time_sec"] for r in results]
        brute_insert = [r["bruteforce"]["insert_time_sec"] for r in results]

        bplus_search = [r["bplustree"]["search_time_sec"] for r in results]
        brute_search = [r["bruteforce"]["search_time_sec"] for r in results]

        bplus_delete = [r["bplustree"]["delete_time_sec"] for r in results]
        brute_delete = [r["bruteforce"]["delete_time_sec"] for r in results]

        bplus_range = [r["bplustree"]["range_query_time_sec"] for r in results]
        brute_range = [r["bruteforce"]["range_query_time_sec"] for r in results]

        bplus_workload = [r["bplustree"]["random_workload_time_sec"] for r in results]
        brute_workload = [r["bruteforce"]["random_workload_time_sec"] for r in results]

        bplus_memory = [r["bplustree"]["peak_memory_bytes"] / 1024 / 1024 for r in results]
        brute_memory = [r["bruteforce"]["peak_memory_bytes"] / 1024 / 1024 for r in results]

        # Create individual plots
        self._plot_operation("Insert", sizes, bplus_insert, brute_insert)
        self._plot_operation("Search", sizes, bplus_search, brute_search)
        self._plot_operation("Delete", sizes, bplus_delete, brute_delete)
        self._plot_operation("Range Query", sizes, bplus_range, brute_range)
        self._plot_operation("Random Workload", sizes, bplus_workload, brute_workload)
        self._plot_memory_usage(sizes, bplus_memory, brute_memory)

        # Create combined comparison plot
        self._plot_combined_comparison(
            sizes, bplus_insert, brute_insert, bplus_search, brute_search,
            bplus_delete, brute_delete, bplus_range, brute_range
        )

        # Create performance ratio plot
        self._plot_performance_ratio(
            sizes, bplus_insert, brute_insert, bplus_search, brute_search,
            bplus_delete, brute_delete, bplus_range, brute_range
        )

        print(f"[OK] JPG visualizations saved to {self.jpg_output_dir}")

    def _plot_operation(self, operation: str, sizes: List[int], bplus_times: List[float], brute_times: List[float]) -> None:
        """Create a comparison plot for a single operation."""
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(sizes, bplus_times, marker='o', linewidth=2.5, markersize=8, label='B+ Tree', color='#2E86AB')
        ax.plot(sizes, brute_times, marker='s', linewidth=2.5, markersize=8, label='Brute Force', color='#A23B72')

        ax.set_xlabel('Dataset Size', fontsize=12, fontweight='bold')
        ax.set_ylabel('Execution Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_title(f'{operation} Operation Performance', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')

        # Format y-axis to show milliseconds for better readability on small values
        ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: '{:.4f}'.format(y)))

        plt.tight_layout()
        base_name = f"performance_{operation.lower().replace(' ', '_')}"
        self._save_figure(fig, base_name)
        plt.close()

    def _plot_memory_usage(self, sizes: List[int], bplus_memory: List[float], brute_memory: List[float]) -> None:
        """Create a memory usage comparison plot."""
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(sizes, bplus_memory, marker='o', linewidth=2.5, markersize=8, label='B+ Tree', color='#2E86AB')
        ax.plot(sizes, brute_memory, marker='s', linewidth=2.5, markersize=8, label='Brute Force', color='#A23B72')

        ax.set_xlabel('Dataset Size', fontsize=12, fontweight='bold')
        ax.set_ylabel('Peak Memory (MB)', fontsize=12, fontweight='bold')
        ax.set_title('Peak Memory Usage Comparison', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        self._save_figure(fig, "performance_memory_usage")
        plt.close()

    def _plot_combined_comparison(
        self,
        sizes: List[int],
        bplus_insert: List[float],
        brute_insert: List[float],
        bplus_search: List[float],
        brute_search: List[float],
        bplus_delete: List[float],
        brute_delete: List[float],
        bplus_range: List[float],
        brute_range: List[float],
    ) -> None:
        """Create a 2x2 subplot comparing all operations."""
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Performance Comparison: B+ Tree vs Brute Force', fontsize=16, fontweight='bold', y=0.995)

        operations = [
            ("Insert", bplus_insert, brute_insert),
            ("Search", bplus_search, brute_search),
            ("Delete", bplus_delete, brute_delete),
            ("Range Query", bplus_range, brute_range),
        ]

        for idx, (op_name, bplus_times, brute_times) in enumerate(operations):
            ax = axes[idx // 2, idx % 2]

            ax.plot(sizes, bplus_times, marker='o', linewidth=2.5, markersize=7, label='B+ Tree', color='#2E86AB')
            ax.plot(sizes, brute_times, marker='s', linewidth=2.5, markersize=7, label='Brute Force', color='#A23B72')

            ax.set_xlabel('Dataset Size', fontsize=10, fontweight='bold')
            ax.set_ylabel('Time (seconds)', fontsize=10, fontweight='bold')
            ax.set_title(f'{op_name} Operation', fontsize=12, fontweight='bold')
            ax.legend(fontsize=9)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda y, _: '{:.4f}'.format(y)))

        plt.tight_layout()
        self._save_figure(fig, "performance_combined_comparison")
        plt.close()

    def _plot_performance_ratio(
        self,
        sizes: List[int],
        bplus_insert: List[float],
        brute_insert: List[float],
        bplus_search: List[float],
        brute_search: List[float],
        bplus_delete: List[float],
        brute_delete: List[float],
        bplus_range: List[float],
        brute_range: List[float],
    ) -> None:
        """
        Create a plot showing speedup ratio (Brute Force / B+ Tree).
        Values > 1 indicate B+ Tree is faster.
        """
        fig, ax = plt.subplots(figsize=(12, 7))

        # Calculate ratios (avoid division by zero)
        insert_ratio = [b / (p + 1e-9) for p, b in zip(bplus_insert, brute_insert)]
        search_ratio = [b / (p + 1e-9) for p, b in zip(bplus_search, brute_search)]
        delete_ratio = [b / (p + 1e-9) for p, b in zip(bplus_delete, brute_delete)]
        range_ratio = [b / (p + 1e-9) for p, b in zip(bplus_range, brute_range)]

        ax.plot(sizes, insert_ratio, marker='o', linewidth=2.5, markersize=8, label='Insert', color='#2E86AB')
        ax.plot(sizes, search_ratio, marker='s', linewidth=2.5, markersize=8, label='Search', color='#A23B72')
        ax.plot(sizes, delete_ratio, marker='^', linewidth=2.5, markersize=8, label='Delete', color='#F18F01')
        ax.plot(sizes, range_ratio, marker='d', linewidth=2.5, markersize=8, label='Range Query', color='#06A77D')

        ax.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Equal Performance', alpha=0.7)

        ax.set_xlabel('Dataset Size', fontsize=12, fontweight='bold')
        ax.set_ylabel('Speedup Ratio (Brute Force / B+ Tree)', fontsize=12, fontweight='bold')
        ax.set_title('B+ Tree Performance Advantage (Higher = Faster)', fontsize=14, fontweight='bold')
        ax.legend(fontsize=11, loc='best')
        ax.grid(True, alpha=0.3, linestyle='--')

        plt.tight_layout()
        self._save_figure(fig, "performance_speedup_ratio")
        plt.close()

    def save_results_to_json(self, benchmark_results: Dict[str, Any], filename: str = "benchmark_results.json") -> None:
        """Save benchmark results to JSON file for later analysis."""
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(benchmark_results, f, indent=2)
        print(f"[OK] Results saved to {filepath}")

    def print_summary_table(self, benchmark_results: Dict[str, Any]) -> None:
        """Print a formatted summary table of results."""
        results = benchmark_results["results"]

        print("\n" + "=" * 110)
        print(f"{'Size':<10} {'Structure':<15} {'Insert (s)':<15} {'Search (s)':<15} {'Delete (s)':<15} {'Range (s)':<15} {'Memory (MB)':<15}")
        print("=" * 110)

        for result in results:
            size = result["size"]
            for struct_name in ["bplustree", "bruteforce"]:
                metrics = result[struct_name]
                print(
                    f"{size:<10} {struct_name:<15} "
                    f"{metrics['insert_time_sec']:<15.6f} "
                    f"{metrics['search_time_sec']:<15.6f} "
                    f"{metrics['delete_time_sec']:<15.6f} "
                    f"{metrics['range_query_time_sec']:<15.6f} "
                    f"{metrics['peak_memory_bytes']/1024/1024:<15.4f}"
                )

        print("=" * 110 + "\n")


def run_full_performance_analysis(
    output_dir: str | Path = "visualizations",
    sizes: tuple | None = None,
    bplustree_order: int = 4,
) -> Dict[str, Any]:
    """
    Run complete performance analysis with visualization.

    Args:
        output_dir: Directory to save visualization files
        sizes: Tuple of dataset sizes to test (default: range 100-10000 by 1000)
        bplustree_order: B+ tree order parameter

    Returns:
        Benchmark results dictionary
    """
    from .performance import BenchmarkConfig, PerformanceAnalyzer

    # Use custom sizes if provided
    if sizes is None:
        sizes = tuple(range(100, 10001, 1000))

    config = BenchmarkConfig(sizes=sizes, bplustree_order=bplustree_order)
    analyzer = PerformanceAnalyzer(config)

    print("Running comprehensive performance benchmarks...")
    print(f"Testing sizes: {config.sizes}")
    print()

    # Run benchmarks
    results = analyzer.run_all_benchmarks()

    # Print summary
    visualizer = PerformanceVisualizer(output_dir)
    visualizer.print_summary_table(results)

    # Generate visualizations
    visualizer.visualize_benchmarks(results)

    # Save results
    visualizer.save_results_to_json(results)

    return results


if __name__ == "__main__":
    # Example usage
    results = run_full_performance_analysis()

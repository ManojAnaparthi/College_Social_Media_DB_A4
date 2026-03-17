#!/usr/bin/env python3
"""
Performance Testing Script for B+ Tree vs Brute Force Comparison.
"""

from __future__ import annotations

from pathlib import Path
import sys

# Ensure Module_A is importable when running this file directly.
MODULE_A_DIR = Path(__file__).resolve().parent.parent
if str(MODULE_A_DIR) not in sys.path:
    sys.path.insert(0, str(MODULE_A_DIR))

from database.visualizations_generator import run_full_performance_analysis


def main() -> None:
    print("=" * 80)
    print("B+ Tree vs Brute Force Performance Comparison")
    print("=" * 80)
    print()

    test_sizes = tuple(range(100, 10001, 1000))

    # Use absolute path based on script location
    output_dir = Path(__file__).resolve().parent / "visualizations"

    print("Configuration:")
    print(f"  - Test Sizes: {test_sizes}")
    print("  - B+ Tree Order: 4")
    print(f"  - Output Directory: {output_dir}")
    print()

    run_full_performance_analysis(
        output_dir=str(output_dir),
        sizes=test_sizes,
        bplustree_order=4,
    )


if __name__ == "__main__":
    main()

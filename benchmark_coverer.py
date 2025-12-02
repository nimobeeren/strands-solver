#!/usr/bin/env python3
"""Benchmark script to measure performance across all puzzles."""

import json
import logging
import multiprocessing
import sys
import time
from pathlib import Path

from src.strands_solver.coverer import Coverer
from src.strands_solver.finder import Finder
from src.strands_solver.solver import Solver
from src.strands_solver.spangram_finder import SpangramFinder

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

TIMEOUT_SECONDS = 90


def solve_puzzle(puzzle_path: Path, result_queue: multiprocessing.Queue) -> None:
    """Solve a single puzzle and put result in queue."""
    puzzle_name = puzzle_path.stem
    result = {
        "puzzle": puzzle_name,
        "status": "unknown",
        "time_seconds": None,
        "num_words": None,
        "num_covers": None,
        "num_solutions": None,
    }

    try:
        with open(puzzle_path, "r") as f:
            puzzle = json.load(f)
            grid = puzzle["grid"]
            num_words = puzzle["num_words"]

        start_time = time.time()

        finder = Finder(grid)
        coverer = Coverer(grid)
        spangram_finder = SpangramFinder(grid, num_words=num_words)
        solver = Solver(finder=finder, coverer=coverer, spangram_finder=spangram_finder)

        words = finder.find_all_words()
        result["num_words"] = len(words)

        covers = coverer.cover(words)
        result["num_covers"] = len(covers)

        solutions = spangram_finder.find_spangrams(covers)
        result["num_solutions"] = len(solutions)

        elapsed = time.time() - start_time
        result["time_seconds"] = round(elapsed, 2)
        result["status"] = "success"

    except Exception as e:
        result["status"] = f"error: {e}"

    result_queue.put(result)


def run_with_timeout(puzzle_path: Path) -> dict:
    """Run solve_puzzle with a hard timeout using process termination."""
    result_queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=solve_puzzle, args=(puzzle_path, result_queue)
    )

    process.start()
    process.join(timeout=TIMEOUT_SECONDS)

    if process.is_alive():
        # Timeout - kill the process
        process.terminate()
        process.join(timeout=5)
        if process.is_alive():
            process.kill()
            process.join()
        return {
            "puzzle": puzzle_path.stem,
            "status": "timeout",
            "time_seconds": TIMEOUT_SECONDS,
            "num_words": None,
            "num_covers": None,
            "num_solutions": None,
        }

    # Get result from queue
    if not result_queue.empty():
        return result_queue.get()
    else:
        return {
            "puzzle": puzzle_path.stem,
            "status": "error: no result",
            "time_seconds": None,
            "num_words": None,
            "num_covers": None,
            "num_solutions": None,
        }


def main():
    puzzles_dir = Path("puzzles")
    puzzle_files = sorted(puzzles_dir.glob("*.json"))

    if not puzzle_files:
        logger.error("No puzzle files found in puzzles/")
        sys.exit(1)

    logger.info(f"Found {len(puzzle_files)} puzzles to benchmark")

    # Run puzzles sequentially with individual timeouts
    results = []
    for puzzle_path in puzzle_files:
        logger.info(f"Running {puzzle_path.stem}...")
        result = run_with_timeout(puzzle_path)
        results.append(result)

        status_icon = (
            "✓"
            if result["status"] == "success"
            else "⏱"
            if result["status"] == "timeout"
            else "✗"
        )
        time_str = f"{result['time_seconds']}s" if result["time_seconds"] else "-"
        logger.info(
            f"{status_icon} {result['puzzle']}: {result['status']} in {time_str}"
        )

    # Print summary
    print("\n" + "=" * 80)
    print("BENCHMARK RESULTS")
    print("=" * 80)
    print(
        f"{'Puzzle':<20} {'Status':<10} {'Time (s)':<10} {'Words':<8} {'Covers':<10} {'Solutions':<10}"
    )
    print("-" * 80)
    for r in sorted(results, key=lambda x: x["puzzle"]):
        time_str = f"{r['time_seconds']}" if r["time_seconds"] is not None else "-"
        words_str = f"{r['num_words']}" if r["num_words"] is not None else "-"
        covers_str = f"{r['num_covers']}" if r["num_covers"] is not None else "-"
        solutions_str = (
            f"{r['num_solutions']}" if r["num_solutions"] is not None else "-"
        )
        print(
            f"{r['puzzle']:<20} {r['status']:<10} {time_str:<10} {words_str:<8} {covers_str:<10} {solutions_str:<10}"
        )
    print("=" * 80)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Compare the original GridCoverer with the CP-SAT coverer."""

import json
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_solver.common import Puzzle
from strands_solver.cpsat_coverer import CPSATGridCoverer
from strands_solver.grid_coverer import GridCoverer
from strands_solver.word_finder import WordFinder


def load_puzzle(path: str) -> Puzzle:
    with open(path) as f:
        data = json.load(f)
    return Puzzle(
        name=Path(path).stem,
        theme=data["theme"],
        grid=data["grid"],
        num_words=data["num_words"],
    )


def benchmark_coverer(name: str, coverer, words, timeout: float = 60.0):
    """Benchmark a coverer and return results."""
    import signal
    
    print(f"\n--- {name} ---", flush=True)
    start = time.perf_counter()
    
    def timeout_handler(signum, frame):
        raise TimeoutError(f"Exceeded {timeout}s timeout")
    
    # Only use signal timeout for non-CPSAT coverers (CPSAT has internal timeout)
    use_signal_timeout = not hasattr(coverer, '_timeout_seconds')
    
    if use_signal_timeout:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(int(timeout) + 1)
    
    try:
        covers = coverer.cover(words)
        elapsed = time.perf_counter() - start
        if use_signal_timeout:
            signal.alarm(0)
        print(f"  Time: {elapsed:.3f}s")
        print(f"  Covers found: {len(covers)}")
        timed_out = elapsed >= timeout - 1  # Consider it a timeout if very close
        return {"time": elapsed, "covers": len(covers), "timeout": timed_out}
    except TimeoutError:
        elapsed = time.perf_counter() - start
        if use_signal_timeout:
            signal.alarm(0)
        print(f"  ⏱️ TIMEOUT after {elapsed:.3f}s")
        return {"time": elapsed, "covers": 0, "timeout": True}
    except Exception as e:
        elapsed = time.perf_counter() - start
        if use_signal_timeout:
            signal.alarm(0)
        print(f"  Error after {elapsed:.3f}s: {e}")
        return {"time": elapsed, "covers": 0, "timeout": False, "error": str(e)}
    finally:
        if use_signal_timeout:
            signal.signal(signal.SIGALRM, old_handler)


def main():
    if len(sys.argv) < 2:
        print("Usage: python compare_coverers.py <puzzle_path> [timeout_seconds] [max_solutions]")
        sys.exit(1)

    puzzle_path = sys.argv[1]
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    max_solutions = int(sys.argv[3]) if len(sys.argv) > 3 else 100000

    print(f"Loading puzzle: {puzzle_path}")
    puzzle = load_puzzle(puzzle_path)
    print(f"Theme: {puzzle.theme}")
    print(f"Grid: {len(puzzle.grid)}x{len(puzzle.grid[0])}")
    print(f"Timeout: {timeout}s, Max solutions: {max_solutions}")

    print("\nFinding words...")
    finder = WordFinder(puzzle.grid)
    start = time.perf_counter()
    words = finder.find_all_words()
    word_time = time.perf_counter() - start
    print(f"Found {len(words)} words in {word_time:.3f}s")

    # Test original coverer (no solution limit)
    original = GridCoverer(puzzle.grid)
    original_results = benchmark_coverer("Original GridCoverer", original, words, timeout)

    # Test CP-SAT coverer with solution limit
    cpsat = CPSATGridCoverer(puzzle.grid, timeout_seconds=timeout, max_solutions=max_solutions)
    cpsat_results = benchmark_coverer("CP-SAT GridCoverer", cpsat, words, timeout)

    # Compare results
    print("\n=== Comparison ===")
    if original_results["timeout"] and not cpsat_results["timeout"]:
        print(f"✅ CP-SAT completed ({cpsat_results['covers']} covers) while Original timed out")
    elif cpsat_results["timeout"] and not original_results["timeout"]:
        print(f"📉 Original completed ({original_results['covers']} covers) while CP-SAT timed out")
    elif original_results["covers"] == cpsat_results["covers"]:
        print(f"✅ Both found {original_results['covers']} covers")
    else:
        print(f"⚠️ Cover count differs: Original={original_results['covers']}, CP-SAT={cpsat_results['covers']}")

    if not original_results["timeout"] and not cpsat_results["timeout"]:
        if original_results["time"] > 0 and cpsat_results["time"] > 0:
            speedup = original_results["time"] / cpsat_results["time"]
            if speedup > 1:
                print(f"⚡ CP-SAT is {speedup:.2f}x faster")
            else:
                print(f"📉 Original is {1/speedup:.2f}x faster")


if __name__ == "__main__":
    main()

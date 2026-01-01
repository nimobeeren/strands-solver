#!/usr/bin/env python3
"""Benchmark the solver against a set of puzzles and validate results."""

import argparse
import asyncio
import datetime
import logging
import multiprocessing
import time
from pathlib import Path

import mdpd
import pandas as pd
from dotenv import load_dotenv

from strands_solver.common import Puzzle, Solution
from strands_solver.puzzle_fetcher import PuzzleFetcher
from strands_solver.solver import Solver

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# The first puzzle published by NYT
FIRST_PUZZLE_DATE = datetime.date(2024, 3, 4)


def parse_date(date_str: str) -> datetime.date:
    if date_str == "today":
        return datetime.date.today()
    return datetime.date.fromisoformat(date_str)


def _solve_in_process(puzzle: Puzzle, queue: multiprocessing.Queue) -> None:
    """Worker function that runs solver in a subprocess."""
    load_dotenv()
    try:
        solver = Solver(puzzle)
        solutions = asyncio.run(solver.solve())
        # Only return the best solution to avoid slow pickling of large lists
        best = solutions[0] if solutions else None
        queue.put(("success", best))
    except Exception as e:
        queue.put(("error", str(e)))


def run_solver_with_timeout(
    puzzle: Puzzle,
    timeout: float | None,
) -> tuple[Solution | None, float]:
    """Run the solver in a subprocess with optional timeout. Returns the best solution."""
    queue: multiprocessing.Queue = multiprocessing.Queue()
    process = multiprocessing.Process(
        target=_solve_in_process,
        args=(puzzle, queue),
    )

    start = time.perf_counter()
    process.start()
    process.join(timeout=timeout)
    elapsed = time.perf_counter() - start

    if process.is_alive():
        process.terminate()
        process.join()
        raise TimeoutError(f"Solver timed out after {timeout}s")

    if queue.empty():
        raise RuntimeError("Solver process ended without returning a result")

    status, result = queue.get()
    if status == "error":
        raise RuntimeError(result)

    return result, elapsed


def load_existing_results(path: Path) -> pd.DataFrame:
    """Load existing results from markdown file."""
    if not path.exists():
        return pd.DataFrame(columns=pd.Index(["Puzzle Date", "Result", "Time (s)"]))

    try:
        with open(path) as f:
            content = f.read()
        df = mdpd.from_md(content)
        return df
    except Exception:
        return pd.DataFrame(columns=pd.Index(["Puzzle Date", "Result", "Time (s)"]))


def save_results(df: pd.DataFrame, path: Path) -> None:
    """Save results as markdown table."""
    # Sort by date
    df = df.sort_values("Puzzle Date").reset_index(drop=True)

    # Calculate pass rate
    total = len(df)
    passed = df["Result"].str.contains("PASS").sum()
    pass_rate = (passed / total) if total > 0 else 0

    with open(path, "w") as f:
        markdown = df.to_markdown(index=False, colalign=("left", "left", "right"))
        assert markdown is not None
        f.write(markdown)
        f.write(f"\n\nPass rate: **{pass_rate:.3f}** ({passed}/{total})\n")


async def benchmark(
    start_date: datetime.date,
    end_date: datetime.date,
    timeout: float | None,
    results_path: Path,
) -> None:
    """Run benchmark on puzzles in date range."""
    fetcher = PuzzleFetcher()

    # Load existing results
    existing_df = load_existing_results(results_path)
    results: list[dict[str, str]] = []

    # Generate date range
    current = start_date
    dates = []
    while current <= end_date:
        dates.append(current)
        current += datetime.timedelta(days=1)

    logger.info(f"Running benchmark on {len(dates)} puzzles")

    for date in dates:
        date_str = date.isoformat()
        logger.info(f"Starting {date_str}")

        result_status = ""
        elapsed_str = ""

        try:
            puzzle = fetcher.fetch_puzzle(date)
            logger.info(f"Solving {date_str}")
            solution, elapsed = run_solver_with_timeout(puzzle, timeout)
            logger.info(f"Completed {date_str}")
            elapsed_str = f"{elapsed:.1f}"

            if solution is None:
                result_status = "❌ FAIL"
                logger.info(
                    f"Result of {date_str}: {result_status} (no solutions found)"
                )
            else:
                official = fetcher.fetch_solution(date)
                if solution.equivalent(official):
                    result_status = "✅ PASS"
                    logger.info(
                        f"Result of {date_str}: {result_status} ({elapsed_str}s)"
                    )
                else:
                    result_status = "❌ FAIL"
                    logger.info(
                        f"Result of {date_str}: {result_status} (solution mismatch)"
                    )

        except TimeoutError:
            result_status = "⏱️ TIMEOUT"
            elapsed_str = f">{timeout:.0f}" if timeout else ""
            logger.info(f"Result of {date_str}: {result_status} ({elapsed_str}s)")

        except Exception as e:
            result_status = "⚠️ ERROR"
            logger.error(f"Result of {date_str}: {result_status} ({e})")

        results.append(
            {
                "Puzzle Date": date_str,
                "Result": result_status,
                "Time (s)": elapsed_str,
            }
        )

    # Merge results
    new_df = pd.DataFrame(results)

    # Combine with existing, updating rows for dates we just ran
    if not existing_df.empty:
        # Remove dates we're updating
        new_dates = list(new_df["Puzzle Date"])
        filtered_df = existing_df[~existing_df["Puzzle Date"].isin(new_dates)]
        merged_df = pd.concat([filtered_df, new_df], ignore_index=True)
    else:
        merged_df = new_df

    assert isinstance(merged_df, pd.DataFrame)
    save_results(merged_df, results_path)
    logger.info(f"Results saved to {results_path}")


async def main() -> int:
    parser = argparse.ArgumentParser(
        description="Benchmark the solver against a set of puzzles."
    )
    parser.add_argument(
        "-s",
        "--start-date",
        type=str,
        default="2025-09-01",
        help="Start date (YYYY-MM-DD or 'today'). Default: 2025-09-01",
    )
    parser.add_argument(
        "-e",
        "--end-date",
        type=str,
        default="2025-09-30",
        help="End date (YYYY-MM-DD or 'today'). Default: 2025-09-30",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=90,
        help="Timeout in seconds per puzzle. Set to 0 to disable. Default: 90s",
    )
    parser.add_argument(
        "-r",
        "--results",
        type=Path,
        default=Path("RESULTS.md"),
        help="Path to a file where benchmark results are written in a Markdown table. Default: ./RESULTS.md",
    )
    args = parser.parse_args()

    try:
        start_date = parse_date(args.start_date)
        end_date = parse_date(args.end_date)
    except ValueError as e:
        logger.error(f"Invalid date: {e}")
        return 1

    if start_date > end_date:
        logger.error("Start date must be before or equal to end date")
        return 1

    # Treat timeout <= 0 as no timeout
    timeout = args.timeout if args.timeout > 0 else None

    await benchmark(start_date, end_date, timeout, args.results)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

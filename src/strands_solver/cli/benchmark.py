import asyncio
import datetime
import logging
import multiprocessing
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import pandas as pd
import typer
from dotenv import load_dotenv

from ..common import Puzzle, Solution
from ..nyt import NYT
from ..solver import Solver, SolverStats

logger = logging.getLogger(__name__)


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
        best = solutions[0] if solutions else None
        queue.put(("success", best, solver.stats))
    except Exception as e:
        queue.put(("error", str(e), None))


def run_solver_with_timeout(
    puzzle: Puzzle,
    timeout: float | None,
) -> tuple[Solution | None, SolverStats | None, float]:
    """Runs the solver in a subprocess with optional timeout. Returns the best solution and stats."""
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

    status, result, stats = queue.get()
    if status == "error":
        raise RuntimeError(result)

    return result, stats, elapsed


RESULT_COLUMNS = ["Puzzle Date", "Result", "Time (s)", "Words", "Covers", "Solutions"]


@dataclass
class BenchmarkSummary:
    num_puzzles: int
    num_passed: int
    total_time_seconds: float
    api_key_used: bool

    @property
    def pass_rate(self) -> float:
        return self.num_passed / self.num_puzzles if self.num_puzzles > 0 else 0


def load_existing_results(report_dir: Path) -> pd.DataFrame:
    """Loads existing results from CSV file."""
    results_path = report_dir / "results.csv"
    if not results_path.exists():
        return pd.DataFrame(columns=pd.Index(RESULT_COLUMNS))

    try:
        df = pd.read_csv(results_path)
        # Add missing columns for backwards compatibility
        for col in RESULT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        return df
    except Exception:
        return pd.DataFrame(columns=pd.Index(RESULT_COLUMNS))


def save_results(df: pd.DataFrame, report_dir: Path, summary: BenchmarkSummary) -> None:
    """Saves results to CSV files in the report directory."""
    report_dir.mkdir(parents=True, exist_ok=True)

    # Ensure columns are in the correct order
    df = pd.DataFrame(df[RESULT_COLUMNS])
    df = df.sort_values("Puzzle Date").reset_index(drop=True)

    # Save results CSV
    results_path = report_dir / "results.csv"
    df.to_csv(results_path, index=False)

    # Save summary CSV (transposed: metrics as rows)
    summary_data = {
        "Metric": ["Puzzles", "Passed", "Pass Rate", "Total Time (s)", "Used API"],
        "Value": [
            summary.num_puzzles,
            summary.num_passed,
            round(summary.pass_rate, 3),
            round(summary.total_time_seconds, 1),
            summary.api_key_used,
        ],
    }
    summary_df = pd.DataFrame(summary_data)
    summary_path = report_dir / "summary.csv"
    summary_df.to_csv(summary_path, index=False)


async def async_benchmark(
    start_date: datetime.date,
    end_date: datetime.date,
    timeout: float | None,
    report_dir: Path,
) -> None:
    """Runs the benchmark on a set of puzzles."""
    nyt = NYT()
    api_key_used = bool(os.getenv("GEMINI_API_KEY"))

    existing_df = load_existing_results(report_dir)
    results: list[dict[str, str]] = []
    total_time = 0.0

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
        words_str = ""
        covers_str = ""
        solutions_str = ""
        elapsed = 0.0

        try:
            puzzle = nyt.fetch_puzzle(date)
            logger.info(f"Solving {date_str}")
            solution, stats, elapsed = run_solver_with_timeout(puzzle, timeout)
            logger.info(f"Completed {date_str}")
            elapsed_str = f"{elapsed:.1f}"

            if stats is not None:
                if stats.num_words is not None:
                    words_str = str(stats.num_words)
                if stats.num_covers is not None:
                    covers_str = str(stats.num_covers)
                if stats.num_solutions is not None:
                    solutions_str = str(stats.num_solutions)

            if solution is None:
                result_status = "FAIL"
                logger.info(
                    f"Result of {date_str}: {result_status} (no solutions found)"
                )
            else:
                official = nyt.fetch_solution(date)
                if solution.equivalent(official):
                    result_status = "PASS"
                    logger.info(
                        f"Result of {date_str}: {result_status} ({elapsed_str}s)"
                    )
                else:
                    result_status = "FAIL"
                    logger.info(
                        f"Result of {date_str}: {result_status} (solution mismatch)"
                    )

        except TimeoutError:
            result_status = "TIMEOUT"
            elapsed = timeout if timeout else 0.0
            elapsed_str = f">{timeout:.0f}" if timeout else ""
            logger.info(f"Result of {date_str}: {result_status} ({elapsed_str}s)")

        except Exception as e:
            result_status = "ERROR"
            logger.error(f"Result of {date_str}: {result_status} ({e})")

        total_time += elapsed

        results.append(
            {
                "Puzzle Date": date_str,
                "Result": result_status,
                "Time (s)": elapsed_str,
                "Words": words_str,
                "Covers": covers_str,
                "Solutions": solutions_str,
            }
        )

    new_df = pd.DataFrame(results)

    if not existing_df.empty:
        new_dates = list(new_df["Puzzle Date"])
        filtered_df = existing_df[~existing_df["Puzzle Date"].isin(new_dates)]
        merged_df = pd.concat([filtered_df, new_df], ignore_index=True)
    else:
        merged_df = new_df

    assert isinstance(merged_df, pd.DataFrame)

    # Calculate summary from merged results
    num_puzzles = len(merged_df)
    num_passed = int(merged_df["Result"].str.contains("PASS").sum())

    # Sum up total time from all results
    def parse_time(t: str) -> float:
        if not t:
            return 0.0
        if t.startswith(">"):
            return float(t[1:])
        return float(t)

    merged_total_time = merged_df["Time (s)"].apply(parse_time).sum()

    summary = BenchmarkSummary(
        num_puzzles=num_puzzles,
        num_passed=num_passed,
        total_time_seconds=merged_total_time,
        api_key_used=api_key_used,
    )

    save_results(merged_df, report_dir, summary)
    logger.info(f"Results saved to {report_dir}")


def benchmark(
    start_date: Annotated[
        str,
        typer.Option(
            "--start-date",
            "-s",
            help="Start date (YYYY-MM-DD or 'today')",
        ),
    ] = "2025-09-01",
    end_date: Annotated[
        str,
        typer.Option(
            "--end-date",
            "-e",
            help="End date (YYYY-MM-DD or 'today')",
        ),
    ] = "2025-12-31",
    timeout: Annotated[
        float,
        typer.Option(
            "--timeout",
            "-t",
            help="Timeout in seconds per puzzle. Set to 0 to disable.",
        ),
    ] = 90,
    report_dir: Annotated[
        Path,
        typer.Option(
            "--report-dir",
            "-r",
            help="Directory where benchmark results are written (summary.csv and results.csv).",
        ),
    ] = Path("reports"),
) -> None:
    """Benchmark the solver against a set of puzzles."""
    try:
        parsed_start = parse_date(start_date)
        parsed_end = parse_date(end_date)
    except ValueError as e:
        logger.error(f"Invalid date: {e}")
        raise typer.Exit(1)

    if parsed_start > parsed_end:
        logger.error("Start date must be before or equal to end date")
        raise typer.Exit(1)

    effective_timeout = timeout if timeout > 0 else None

    asyncio.run(
        async_benchmark(parsed_start, parsed_end, effective_timeout, report_dir)
    )

import datetime
import subprocess
import sys
import pytest

from strands_solver.nyt import NYT
from strands_solver.solver import Solver

# Mark all tests in this file as end-to-end tests
pytestmark = pytest.mark.e2e


@pytest.mark.asyncio
async def test_solve():
    """Solve a real puzzle and assert that the best found solution is equivalent to the
    offical NY Times solution."""
    date = datetime.date(2025, 9, 23)

    nyt = NYT()
    puzzle = nyt.fetch_puzzle(date)
    expected_solution = nyt.fetch_solution(date)
    solver = Solver(puzzle)

    found_solutions = await solver.solve()
    best_found_solution = found_solutions[0]

    assert best_found_solution.equivalent(expected_solution)


def run_cli(args: str) -> subprocess.CompletedProcess[str]:
    """Run the strands-solver CLI with the given arguments."""
    return subprocess.run(
        [sys.executable, "-m", "strands_solver.cli.main", *args.split()],
        capture_output=True,
        text=True,
    )


def test_cli_solve():
    """Solve a real puzzle through the CLI and assert that a solution is output."""
    result = run_cli("solve 2025-09-23")
    assert result.returncode == 0
    assert "COLLEGE" in result.stdout


def test_cli_show():
    """Display the official solution for a puzzle."""
    result = run_cli("show 2025-10-03")
    assert result.returncode == 0
    assert "LEADERSHIP" in result.stdout


def test_cli_benchmark(tmp_path):
    """Run benchmark on a single puzzle and verify results are written."""
    results_file = tmp_path / "results.md"
    result = run_cli(
        f"benchmark --start-date 2025-09-23 --end-date 2025-09-23 --timeout 90 --results {results_file}"
    )
    assert result.returncode == 0
    assert results_file.exists()
    content = results_file.read_text()
    assert "2025-09-23" in content

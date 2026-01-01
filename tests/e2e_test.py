import datetime
import pytest

from strands_solver.cli import main
from strands_solver.nyt import NYT
from strands_solver.solver import Solver

# Mark all tests in this file as end-to-end tests
pytestmark = pytest.mark.e2e


def test_cli(monkeypatch, caplog):
    """Solve a real puzzle through the CLI and assert that a solution is logged."""
    date = "2025-09-23"
    monkeypatch.setattr("sys.argv", ["strands-solver", date])

    with caplog.at_level("INFO"):
        main()

    assert any(record.message.startswith("Solution:") for record in caplog.records)


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

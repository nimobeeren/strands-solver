import datetime

import pytest

from strands_solver.nyt import NYT
from strands_solver.solver import Solver


@pytest.mark.integration
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

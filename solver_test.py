from solver import Solver
from common import Strand


def test_solve():
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]
    solver = Solver(grid)
    solutions = solver.solve()

    # Should find at least one solution
    assert len(solutions) >= 1

    # The expected solution should be in the solutions list
    expected = [
        Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string="EASY"),
        Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string="WORD"),
        Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string="TEST"),
        Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string="COOL"),
    ]
    assert expected in solutions

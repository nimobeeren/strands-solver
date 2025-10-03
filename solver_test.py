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


def test_solve_single_spangram():
    grid = [
        ["W", "A", "T", "E", "R", "T", "O", "A", "D"],
        ["F", "R", "O", "G", "M", "E", "L", "O", "N"],
    ]

    # There exist solutions which do not conain a spangram, for example:
    # WATER + TOAD + FROG + MELON
    # But there is only one solution which does contain a spangram, namely:
    # WATERMELON (spangram) + TOAD + FROG

    solver = Solver(grid)
    solutions = solver.solve()

    assert len(solutions) == 1

    expected = [
        Strand(
            positions=[
                (0, 0),
                (1, 0),
                (2, 0),
                (3, 0),
                (4, 0),
                (4, 1),
                (5, 1),
                (6, 1),
                (7, 1),
                (8, 1),
            ],
            string="WATERMELON",
        ),
        Strand(
            positions=[(5, 0), (6, 0), (7, 0), (8, 0)],
            string="TOAD",
        ),
        Strand(
            positions=[(0, 1), (1, 1), (2, 1), (3, 1)],
            string="FROG",
        ),
    ]
    assert solutions[0] == expected

from ocr import load_grid_from_csv
from solver import Solver
from common import Strand


def test_solve():
    grid = load_grid_from_csv("./puzzles/example.csv")
    solver = Solver(grid)
    solution = solver.solve()
    # Note: this is just one solution, there may be other valid solutions
    assert solution == [
        Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string="WORD"),
        Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string="EASY"),
        Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string="TEST"),
        Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string="COOL"),
    ]

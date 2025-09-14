from ocr import load_grid_from_csv
from solver import Solver


test_grid = load_grid_from_csv("./puzzles/2025-09-14.csv")


def test_find_words():
    solver = Solver(test_grid)
    words = solver.find_words(x=0, y=0)
    # removed self-overlapping words here
    assert words == {
        "THEY",
        "THE",
        "TH",
        "TEAL",
        "TEHSIL",
        "TESS",
        "THEA",
        "TEAD",
        "TEADISH",
        "TEDA",
        "T",
        "TEA",
        "THY",
        "TE",
    }

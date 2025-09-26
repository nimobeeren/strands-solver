from ocr import load_grid_from_csv
from solver import Solver


test_grid = load_grid_from_csv("./puzzles/2025-09-14.csv")


def test_find_words_no_min_length():
    solver = Solver(test_grid)
    words = solver.find_words(current_pos=(0, 0), min_length=0)
    assert words == {
        "TED",
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
        "TEASLE",
        "TSS",
        "TSH",
        "TESLA",
        "TSA",
    }


def test_find_words():
    solver = Solver(test_grid)
    words = solver.find_words(current_pos=(0, 0))
    assert words == {
        "THEY",
        "TEAL",
        "TEHSIL",
        "TESS",
        "THEA",
        "TEAD",
        "TEADISH",
        "TEDA",
        "TESLA",
        "TEASLE",
    }

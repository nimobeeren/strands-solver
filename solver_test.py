import pytest

from coverer import Coverer
from finder import Finder
from solver import Solver
from common import Strand


def test_solve():
    # Simple grid where each word appears only once
    grid = [
        ["E", "A", "S", "Y", "S"],
        ["C", "O", "O", "L", "P"],
        ["T", "E", "S", "T", "A"],
        ["W", "O", "R", "D", "N"],
    ]

    finder = Finder(grid)
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=5)
    solutions = solver.solve()

    # Should find at least one solution
    assert len(solutions) >= 1

    # The expected solution should be in the solutions set
    expected = frozenset(
        [
            Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="EASY"),
            Strand(positions=((4, 0), (4, 1), (4, 2), (4, 3)), string="SPAN"),
            Strand(positions=((0, 1), (1, 1), (2, 1), (3, 1)), string="COOL"),
            Strand(positions=((0, 2), (1, 2), (2, 2), (3, 2)), string="TEST"),
            Strand(positions=((0, 3), (1, 3), (2, 3), (3, 3)), string="WORD"),
        ]
    )
    assert expected in solutions


def test_solve_single_spangram():
    grid = [
        ["A", "B", "C", "D", "E", "K", "L", "M", "N"],
        ["O", "P", "Q", "R", "F", "G", "H", "I", "J"],
    ]

    # There is only one solution with 3 words:
    # {ABCDEFGHIJ, KLMN, OPQR}

    finder = Finder(grid, dictionary={"ABCDEFGHIJ", "KLMN", "OPQR"})
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=3)
    solutions = solver.solve()

    expected = {
        frozenset(
            [
                Strand(
                    positions=(
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
                    ),
                    string="ABCDEFGHIJ",
                ),
                Strand(
                    positions=((5, 0), (6, 0), (7, 0), (8, 0)),
                    string="KLMN",
                ),
                Strand(
                    positions=((0, 1), (1, 1), (2, 1), (3, 1)),
                    string="OPQR",
                ),
            ]
        )
    }

    assert solutions == expected


def test_solve_concatenated_spangram():
    grid = [
        ["A", "B", "C", "D", "E", "F", "G", "H"],
        ["I", "J", "K", "L", "M", "N", "O", "P"],
        ["Q", "R", "S", "T", "U", "V", "W", "X"],
    ]

    # There is only one solution with 3 words:
    # {ABCDEFGH, IJKLMNOP, QRSTUVWX}
    # and it requires concatenating IJKL and MNOP to form the spangram

    finder = Finder(grid, dictionary={"ABCDEFGH", "IJKL", "MNOP", "QRSTUVWX"})
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=3)
    solutions = solver.solve()

    expected = {
        frozenset(
            [
                Strand(
                    positions=(
                        (0, 0),
                        (1, 0),
                        (2, 0),
                        (3, 0),
                        (4, 0),
                        (5, 0),
                        (6, 0),
                        (7, 0),
                    ),
                    string="ABCDEFGH",
                ),
                Strand(
                    positions=(
                        (0, 1),
                        (1, 1),
                        (2, 1),
                        (3, 1),
                        (4, 1),
                        (5, 1),
                        (6, 1),
                        (7, 1),
                    ),
                    string="IJKLMNOP",
                ),
                Strand(
                    positions=(
                        (0, 2),
                        (1, 2),
                        (2, 2),
                        (3, 2),
                        (4, 2),
                        (5, 2),
                        (6, 2),
                        (7, 2),
                    ),
                    string="QRSTUVWX",
                ),
            ]
        )
    }
    assert solutions == expected


def test_solve_cant_concatenate_if_not_spangram():
    """Test that we don't concatenate words if they don't form a spangram."""
    grid = [
        list("ABCDEFGHKL"),
        list("MNOPQRSTJI"),
    ]

    finder = Finder(grid, dictionary={"ABCD", "EFGH", "IJKL", "MNOPQRST"})
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=3)
    solutions = solver.solve()

    # This puzzle is solvable with 4 words: {ABCD, EFGH, IJKL, MNOPQRST}
    # If it was allowed to concatenate ABCD + EFGH, then it could be solved in 3
    # But since ABCDEFGH is not a spangram, this is not allowed.
    # Hence, there are no solutions with 3 words.
    assert len(solutions) == 0


@pytest.mark.skip("Not fixed yet")
def test_solve_spangram_with_duplicate_word():
    """Edge case where the spangram is a concatenation of words where one word appears
    in multiple places in the grid (duplicate). Normally, this duplicate would get
    filtered out, but if it's part of a concatenated spangram, it should be kept."""
    # NOTE: commenting out _filter_duplicate_words in solver.py fixes this, but
    # increases running time a lot
    grid = [
        ["A", "B", "C", "D", "E", "F", "G", "H"],
        ["L", "K", "J", "I", "E", "F", "G", "H"],
    ]

    finder = Finder(grid, dictionary={"ABCD", "EFGH", "IJKL"})
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer, num_words=3)
    solutions = solver.solve()

    expected = frozenset(
        {
            # Spangram consisting of ABCD + EFGH
            Strand(
                string="ABCDEFGH",
                positions=(
                    (0, 0),
                    (1, 0),
                    (2, 0),
                    (3, 0),
                    (4, 0),
                    (5, 0),
                    (6, 0),
                    (7, 0),
                ),
            ),
            Strand(string="EFGH", positions=((4, 1), (5, 1), (6, 1), (7, 1))),
            Strand(string="IJKL", positions=((3, 1), (2, 1), (1, 1), (0, 1))),
        }
    )

    assert expected in solutions


def test_filter_duplicate_words():
    """Test that words with multiple instances using different position sets are filtered out."""
    words = {
        # FOOD appears once - should be kept
        Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="FOOD"),
        # BOSS appears twice using the exact same set of positions (different traversal)
        # Only one should be kept (the one with lexicographically smallest positions)
        Strand(positions=((5, 2), (5, 1), (4, 0), (5, 0)), string="BOSS"),
        Strand(positions=((5, 2), (5, 1), (5, 0), (4, 0)), string="BOSS"),
        # TEST appears twice in completely different locations - should be filtered out
        Strand(positions=((0, 1), (1, 1), (2, 1), (3, 1)), string="TEST"),
        Strand(positions=((0, 5), (1, 5), (2, 5), (3, 5)), string="TEST"),
        # WORD appears 3 times, all different position sets - should be filtered out
        Strand(positions=((0, 2), (1, 2), (2, 2), (3, 2)), string="WORD"),
        Strand(positions=((0, 3), (1, 3), (2, 3), (3, 3)), string="WORD"),
        Strand(positions=((0, 4), (1, 4), (2, 4), (3, 4)), string="WORD"),
        # WAYS appears twice with partial overlap but different position sets - should be filtered out
        Strand(positions=((1, 0), (1, 1), (1, 0), (0, 0)), string="WAYS"),
        Strand(positions=((1, 0), (1, 1), (1, 2), (0, 2)), string="WAYS"),
    }

    expected = {
        # FOOD - unique word
        Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="FOOD"),
        # BOSS - same position set (just different traversal order), keep the lexicographically smallest
        Strand(positions=((5, 2), (5, 1), (4, 0), (5, 0)), string="BOSS"),
        # TEST, WORD and WAYS filtered out (different position sets)
    }

    filtered = Solver._filter_duplicate_words(words)

    assert filtered == expected

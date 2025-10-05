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
    solver = Solver(grid, finder=finder, coverer=coverer)
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
        ["W", "A", "T", "E", "R", "T", "O", "A", "D"],
        ["F", "R", "O", "G", "M", "E", "L", "O", "N"],
    ]

    # There exist solutions which do not conain a spangram, for example:
    # WATER + TOAD + FROG + MELON
    # But there is only one solution which does contain a spangram, namely:
    # WATERMELON (spangram) + TOAD + FROG

    finder = Finder(grid)
    coverer = Coverer(grid)
    solver = Solver(grid, finder=finder, coverer=coverer)
    solutions = solver.solve()

    assert len(solutions) == 1

    expected = frozenset(
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
                string="WATERMELON",
            ),
            Strand(
                positions=((5, 0), (6, 0), (7, 0), (8, 0)),
                string="TOAD",
            ),
            Strand(
                positions=((0, 1), (1, 1), (2, 1), (3, 1)),
                string="FROG",
            ),
        ]
    )
    # Get the single solution from the set
    (solution,) = solutions
    assert solution == expected


def test_filter_duplicate_words():
    """Test that words with multiple instances using different position sets are filtered out."""
    words = {
        # FOOD appears once - should be kept
        Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="FOOD"),
        # BOSS appears twice using the exact same set of positions (different traversal)
        # Should be kept - covering algorithm will choose one path
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
        # BOSS - same position set (just different traversal order)
        Strand(positions=((5, 2), (5, 1), (4, 0), (5, 0)), string="BOSS"),
        Strand(positions=((5, 2), (5, 1), (5, 0), (4, 0)), string="BOSS"),
        # TEST, WORD and WAYS filtered out (different position sets)
    }

    filtered = Solver._filter_duplicate_words(words)

    assert filtered == expected

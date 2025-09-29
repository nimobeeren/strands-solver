from common import Strand
from grid_coverer import GridCoverer


def test_cover():
    """Test that GridCoverer finds the unique solution when given a constrained set of words.

    We provide 5 words:
    - WORD (row 0)
    - TEST (row 1)
    - COOL (row 2)
    - EASY (row 3)
    - WORST (W->O->R->S->T, diagonal from top-left)

    Only the first 4 words can cover the entire grid (one solution).
    WORST conflicts with all of them, so it cannot be part of the solution.
    """
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]

    # Create strands for each word
    # WORD: horizontal across row 0
    word = Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string="WORD")

    # TEST: horizontal across row 1
    test = Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string="TEST")

    # COOL: horizontal across row 2
    cool = Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string="COOL")

    # EASY: horizontal across row 3
    easy = Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string="EASY")

    # WORST: diagonal/zigzag from W(0,0) -> O(1,0) -> R(2,0) -> S(2,1) -> T(3,1)
    # This conflicts with WORD and TEST, so it cannot be in the solution
    worst = Strand(positions=[(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)], string="WORST")

    # Provide all 5 words to the coverer
    words = [word, test, cool, easy, worst]

    coverer = GridCoverer(grid=grid, words=words)
    solution = coverer.cover()

    # Check that the solution matches exactly
    expected = [word, test, cool, easy]
    assert solution == expected

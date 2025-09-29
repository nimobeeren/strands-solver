from common import Strand
from grid_coverer import GridCoverer


def test_cover():
    grid = [
        ["W", "O", "R", "D"],
        ["T", "E", "S", "T"],
        ["C", "O", "O", "L"],
        ["E", "A", "S", "Y"],
    ]

    # WORD: horizontal across row 0
    word = Strand(positions=[(0, 0), (1, 0), (2, 0), (3, 0)], string="WORD")
    # TEST: horizontal across row 1
    test = Strand(positions=[(0, 1), (1, 1), (2, 1), (3, 1)], string="TEST")
    # COOL: horizontal across row 2
    cool = Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2)], string="COOL")
    # EASY: horizontal across row 3
    easy = Strand(positions=[(0, 3), (1, 3), (2, 3), (3, 3)], string="EASY")

    # WORST: diagonal from top-left
    # This conflicts with WORD and TEST, so it cannot be in the solution
    worst = Strand(positions=[(0, 0), (1, 0), (2, 0), (2, 1), (3, 1)], string="WORST")

    # Provide all 5 words to the coverer
    strands = [word, test, cool, easy, worst]
    coverer = GridCoverer(grid=grid, strands=strands)
    solution = coverer.cover()

    # Check that the solution matches exactly
    expected = [word, test, cool, easy]
    assert solution == expected

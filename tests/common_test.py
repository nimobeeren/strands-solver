import pytest

from strands_solver.common import Solution, Strand


def test_overlaps():
    """Two strands that share a position should overlap."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((2, 0), (2, 1), (2, 2)), string="CDE")
    assert strand1.overlaps(strand2)


def test_no_overlap():
    """Two strands that share no positions should not overlap."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((3, 0), (4, 0), (4, 1)), string="DEF")
    assert not strand1.overlaps(strand2)


def test_horizontal_spangram():
    """A strand that touches both left and right edges should be a valid spangram."""
    strand = Strand(positions=((0, 2), (1, 2), (2, 2), (3, 2), (2, 1)), string="HELLO")
    assert strand.is_spangram(grid_rows=4, grid_cols=4)


def test_vertical_spangram():
    """A strand that touches both top and bottom edges should be a valid spangram."""
    strand = Strand(positions=((2, 0), (2, 1), (2, 2), (2, 3), (2, 4)), string="WORLD")
    assert strand.is_spangram(grid_rows=5, grid_cols=5)


def test_not_a_spangram():
    """A strand that doesn't touch opposite edges should not be a spangram."""
    strand = Strand(positions=((0, 1), (1, 1), (1, 0)), string="HEY")
    assert not strand.is_spangram(grid_rows=5, grid_cols=5)


def test_can_concatenate():
    """If the last position of strand A is adjacent to the first position of strand B,
    then strand A can be concatenated with strand B (but not necessarily the other way
    around)."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((3, 0), (4, 0), (5, 0)), string="DEF")
    assert strand1.can_concatenate(strand2)
    assert not strand2.can_concatenate(strand1)

    # Can be diagonally adjacent
    strand1 = Strand(positions=((0, 0), (1, 1), (2, 2)), string="ABC")
    strand2 = Strand(positions=((3, 3), (4, 4), (5, 5)), string="DEF")
    assert strand1.can_concatenate(strand2)
    assert not strand2.can_concatenate(strand1)

    # Doesn't matter if the strands overlap
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((1, 0), (1, 1), (1, 2)), string="DEF")
    assert strand1.can_concatenate(strand2)
    assert not strand2.can_concatenate(strand1)

    # Can concatenate three in sequence
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((3, 0), (4, 0), (5, 0)), string="DEF")
    strand3 = Strand(positions=((6, 0), (7, 0), (8, 0)), string="GHI")
    assert strand1.can_concatenate(strand2, strand3)


def test_cannot_concatenate():
    """If the last position of strand A is not adjacent to the first position of strand B,
    then strand A cannot be concatenated with strand B."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((0, 0), (0, 1), (0, 2)), string="DEF")
    assert not strand1.can_concatenate(strand2)
    assert not strand2.can_concatenate(strand1)

    # Raises an error if no other strands are provided
    with pytest.raises(ValueError):
        strand1.can_concatenate()


def test_concatenate():
    """Concatenating two strands should create a new strand with their positions and strings concatenated."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((3, 0), (4, 0), (5, 0)), string="DEF")
    strand3 = Strand(positions=((6, 0), (7, 0), (8, 0)), string="GHI")
    assert strand1.concatenate(strand2) == Strand(
        positions=((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)), string="ABCDEF"
    )

    # Works with multiple strands in sequence
    assert strand1.concatenate(strand2, strand3) == Strand(
        positions=(
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (5, 0),
            (6, 0),
            (7, 0),
            (8, 0),
        ),
        string="ABCDEFGHI",
    )


def test_no_self_crossing_straight_line():
    """A straight line should not have a self-crossing."""
    strand = Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="ABCD")
    assert not strand.has_self_crossing()


def test_no_self_crossing_l_shape():
    """An L-shape should not have a self-crossing."""
    strand = Strand(positions=((0, 0), (1, 0), (2, 0), (2, 1)), string="ABCD")
    assert not strand.has_self_crossing()


def test_self_crossing_x_pattern():
    """An X pattern should be detected as having a self-crossing."""
    # Grid: C B
    #       A D
    # Path: A(0,1) -> B(1,0) -> C(0,0) -> D(1,1)
    strand = Strand(positions=((0, 1), (1, 0), (0, 0), (1, 1)), string="ABCD")
    assert strand.has_self_crossing()


def test_no_crossing_between_non_overlapping_strands():
    """Two parallel horizontal strands should not cross each other."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((0, 1), (1, 1), (2, 1)), string="DEF")
    assert not strand1.crosses(strand2)
    assert not strand2.crosses(strand1)


def test_crossing_between_strands():
    """Two strands that form an X pattern should cross each other."""
    # Grid: C B
    #       A D
    # Strand1: A(0,1) -> B(1,0)
    # Strand2: C(0,0) -> D(1,1)
    strand1 = Strand(positions=((0, 1), (1, 0)), string="AB")
    strand2 = Strand(positions=((0, 0), (1, 1)), string="CD")
    assert strand1.crosses(strand2)
    assert strand2.crosses(strand1)


def test_no_crossing_when_strands_share_endpoint():
    """Strands that share an endpoint should not count as crossing."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((2, 0), (2, 1), (2, 2)), string="DEF")
    assert not strand1.crosses(strand2)


def test_solution_equivalent_identical():
    """Two identical solutions should be equivalent."""
    spangram = (Strand(positions=((0, 0), (1, 0), (2, 0)), string="SPAN"),)
    non_spangram = frozenset(
        {
            Strand(positions=((0, 1), (1, 1)), string="AB"),
            Strand(positions=((0, 2), (1, 2)), string="CD"),
        }
    )
    solution1 = Solution(spangram=spangram, non_spangram_strands=non_spangram)
    solution2 = Solution(spangram=spangram, non_spangram_strands=non_spangram)
    assert solution1.equivalent(solution2)


def test_solution_equivalent_concatenated_spangram():
    """A split spangram should be equivalent to a single concatenated spangram strand."""
    solution1 = Solution(
        spangram=(
            Strand(positions=((0, 0), (1, 0)), string="SPAN"),
            Strand(positions=((2, 0), (3, 0)), string="GRAM"),
        ),
        non_spangram_strands=frozenset(),
    )
    solution2 = Solution(
        spangram=(
            Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="SPANGRAM"),
        ),
        non_spangram_strands=frozenset(),
    )
    assert solution1.equivalent(solution2)


def test_solution_not_equivalent_different_positions():
    """Solutions with same words but different positions should not be equivalent."""
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0), (2, 0)), string="SPAN"),),
        non_spangram_strands=frozenset(
            {Strand(positions=((0, 1), (1, 1)), string="WORD")}
        ),
    )
    solution2 = Solution(
        spangram=(Strand(positions=((3, 3), (4, 3), (5, 3)), string="SPAN"),),
        non_spangram_strands=frozenset(
            {Strand(positions=((3, 4), (4, 4)), string="WORD")}
        ),
    )
    assert not solution1.equivalent(solution2)


def test_solution_equivalent_different_letter_order():
    """Solutions with same words but different positions should not be equivalent."""
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0), (0, 1)), string="AA"),),
        non_spangram_strands=frozenset(),
    )
    solution2 = Solution(
        spangram=(Strand(positions=((0, 1), (0, 0)), string="AA"),),
        non_spangram_strands=frozenset(),
    )
    assert solution1.equivalent(solution2)


def test_solution_not_equivalent_different_spangram():
    """Solutions with different spangrams should not be equivalent."""
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="SPAN"),),
        non_spangram_strands=frozenset(),
    )
    solution2 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="GRAM"),),
        non_spangram_strands=frozenset(),
    )
    assert not solution1.equivalent(solution2)


def test_solution_not_equivalent_different_words():
    """Solutions with different non-spangram words should not be equivalent."""
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="SPAN"),),
        non_spangram_strands=frozenset(
            {Strand(positions=((0, 1), (1, 1)), string="APPLE")}
        ),
    )
    solution2 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="SPAN"),),
        non_spangram_strands=frozenset(
            {Strand(positions=((0, 1), (1, 1)), string="BANANA")}
        ),
    )
    assert not solution1.equivalent(solution2)

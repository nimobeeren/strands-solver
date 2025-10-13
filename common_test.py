import pytest

from common import Strand


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


def test_cannot_concatenate():
    """If the last position of strand A is not adjacent to the first position of strand B,
    then strand A cannot be concatenated with strand B."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((0, 0), (0, 1), (0, 2)), string="DEF")
    assert not strand1.can_concatenate(strand2)
    assert not strand2.can_concatenate(strand1)


def test_concatenate():
    """Concatenating two strands should create a new strand with their positions and strings concatenated."""
    strand1 = Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC")
    strand2 = Strand(positions=((3, 0), (4, 0), (5, 0)), string="DEF")
    assert strand1.concatenate(strand2) == Strand(
        positions=((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)), string="ABCDEF"
    )

    # Should raise an error if the strands cannot be concatenated
    with pytest.raises(ValueError):
        strand2.concatenate(strand1)

from common import Strand


def test_overlaps():
    """Two strands that share a position should overlap."""
    strand1 = Strand(positions=[(0, 0), (1, 0), (2, 0)], string="ABC")
    strand2 = Strand(positions=[(2, 0), (2, 1), (2, 2)], string="CDE")
    assert strand1.overlaps(strand2)


def test_no_overlap():
    """Two strands that share no positions should not overlap."""
    strand1 = Strand(positions=[(0, 0), (1, 0), (2, 0)], string="ABC")
    strand2 = Strand(positions=[(3, 0), (4, 0), (4, 1)], string="DEF")
    assert not strand1.overlaps(strand2)


def test_horizontal_spangram():
    """A strand that touches both left and right edges should be a valid spangram."""
    strand = Strand(positions=[(0, 2), (1, 2), (2, 2), (3, 2), (2, 1)], string="HELLO")
    assert strand.is_spangram(grid_rows=4, grid_cols=4)


def test_vertical_spangram():
    """A strand that touches both top and bottom edges should be a valid spangram."""
    strand = Strand(positions=[(2, 0), (2, 1), (2, 2), (2, 3), (2, 4)], string="WORLD")
    assert strand.is_spangram(grid_rows=5, grid_cols=5)


def test_not_a_spangram():
    """A strand that doesn't touch opposite edges should not be a spangram."""
    strand = Strand(positions=[(0, 1), (1, 1), (1, 0)], string="HEY")
    assert not strand.is_spangram(grid_rows=5, grid_cols=5)

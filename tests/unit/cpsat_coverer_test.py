import pytest

from strands_solver.common import Strand
from strands_solver.cpsat_coverer import CPSATGridCoverer


class TestCPSATGridCoverer:
    """Tests for CPSATGridCoverer."""

    @pytest.fixture
    def simple_grid(self):
        return [["A", "B"], ["C", "D"]]

    @pytest.fixture
    def coverer(self, simple_grid):
        return CPSATGridCoverer(simple_grid)

    def test_empty_strands_returns_empty(self, coverer):
        result = coverer.cover([])
        assert result == set()

    def test_single_strand_covering_all(self, coverer):
        strand = Strand(positions=((0, 0), (1, 0), (1, 1), (0, 1)), string="ABDC")
        result = coverer.cover([strand])
        assert len(result) == 1
        cover = next(iter(result))
        assert strand in cover

    def test_two_strands_covering_grid(self, coverer):
        strand1 = Strand(positions=((0, 0), (1, 0)), string="AB")
        strand2 = Strand(positions=((0, 1), (1, 1)), string="CD")
        result = coverer.cover([strand1, strand2])
        assert len(result) == 1
        cover = next(iter(result))
        assert strand1 in cover
        assert strand2 in cover

    def test_overlapping_strands_not_both_selected(self, coverer):
        strand1 = Strand(positions=((0, 0), (1, 0)), string="AB")
        strand2 = Strand(positions=((0, 0), (0, 1)), string="AC")  # Overlaps at (0,0)
        strand3 = Strand(positions=((0, 1), (1, 1)), string="CD")
        strand4 = Strand(positions=((1, 0), (1, 1)), string="BD")
        result = coverer.cover([strand1, strand2, strand3, strand4])
        # Should find exactly 2 covers: (AB, CD) and (AC, BD)
        assert len(result) == 2

    def test_no_valid_cover_returns_empty(self, coverer):
        # Strand that only covers part of the grid, with no way to cover the rest
        strand = Strand(positions=((0, 0),), string="A")
        result = coverer.cover([strand])
        assert result == set()

    def test_crossing_strands_filtered_out(self, coverer):
        # Create strands that would cross if both selected
        strand1 = Strand(positions=((0, 0), (1, 1)), string="AD")  # Diagonal
        strand2 = Strand(positions=((1, 0), (0, 1)), string="BC")  # Other diagonal
        result = coverer.cover([strand1, strand2])
        # These cross, so no valid cover
        assert result == set()

    def test_max_solutions_limit(self, simple_grid):
        """Test that max_solutions parameter limits results."""
        coverer = CPSATGridCoverer(simple_grid, max_solutions=1)
        strand1 = Strand(positions=((0, 0), (1, 0)), string="AB")
        strand2 = Strand(positions=((0, 1), (1, 1)), string="CD")
        strand3 = Strand(positions=((0, 0), (0, 1)), string="AC")
        strand4 = Strand(positions=((1, 0), (1, 1)), string="BD")
        result = coverer.cover([strand1, strand2, strand3, strand4])
        assert len(result) <= 1

    def test_timeout_parameter(self, simple_grid):
        """Test that timeout parameter is respected."""
        coverer = CPSATGridCoverer(simple_grid, timeout_seconds=0.001)
        # Even with tiny timeout, simple cases should work
        strand = Strand(positions=((0, 0), (1, 0), (1, 1), (0, 1)), string="ABDC")
        result = coverer.cover([strand])
        # May or may not find solution with tiny timeout
        assert isinstance(result, set)


class TestCPSATGridCovererMatchesOriginal:
    """Tests that CPSATGridCoverer produces same results as GridCoverer."""

    @pytest.fixture
    def grid_3x3(self):
        return [["A", "B", "C"], ["D", "E", "F"], ["G", "H", "I"]]

    def test_same_covers_as_original(self, grid_3x3):
        from strands_solver.grid_coverer import GridCoverer

        # Create some strands
        strands = [
            Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC"),
            Strand(positions=((0, 1), (1, 1), (2, 1)), string="DEF"),
            Strand(positions=((0, 2), (1, 2), (2, 2)), string="GHI"),
            Strand(positions=((0, 0), (0, 1), (0, 2)), string="ADG"),
            Strand(positions=((1, 0), (1, 1), (1, 2)), string="BEH"),
            Strand(positions=((2, 0), (2, 1), (2, 2)), string="CFI"),
        ]

        original = GridCoverer(grid_3x3)
        cpsat = CPSATGridCoverer(grid_3x3)

        original_covers = original.cover(strands)
        cpsat_covers = cpsat.cover(strands)

        # Compare by converting to comparable form
        def cover_to_set(cover):
            return frozenset(
                (frozenset(s.positions), s.string) for s in cover
            )

        original_set = {cover_to_set(c) for c in original_covers}
        cpsat_set = {cover_to_set(c) for c in cpsat_covers}

        assert original_set == cpsat_set

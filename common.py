from dataclasses import dataclass


@dataclass(frozen=True)
class Strand:
    positions: tuple[tuple[int, int], ...]
    """Sequence of positions that the strand occupies."""
    string: str
    """String formed by concatenating the letters in the grid at each position."""

    def overlaps(self, other: "Strand"):
        """Checks whether the strand overlaps with another strand in at least one
        position."""
        return len(set(self.positions) & set(other.positions)) > 0

    def is_spangram(self, grid_rows: int, grid_cols: int):
        """Checks whether the strand is a valid spangram in a grid of specified size.

        A valid spangram must touch the left and right edge or the top and bottom edge
        of the grid."""
        touches_right = False
        touches_bottom = False
        touches_left = False
        touches_top = False
        for x, y in self.positions:
            if x == 0:
                touches_left = True
            if x == grid_cols - 1:
                touches_right = True
            if y == 0:
                touches_top = True
            if y == grid_rows - 1:
                touches_bottom = True
        return (touches_left and touches_right) or (touches_top and touches_bottom)

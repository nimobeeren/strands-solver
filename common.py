from dataclasses import dataclass
from enum import Enum


class Direction(Enum):
    RIGHT = (1, 0)
    DOWN_RIGHT = (1, 1)
    DOWN = (0, 1)
    DOWN_LEFT = (-1, 1)
    LEFT = (-1, 0)
    UP_LEFT = (-1, -1)
    UP = (0, -1)
    UP_RIGHT = (1, -1)


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

    def can_concatenate(self, other: "Strand") -> bool:
        """Checks whether the last position of this strand is adjacent to the first
        position of another strand."""
        for direction in Direction:
            dx, dy = direction.value
            if (
                self.positions[-1][0] + dx == other.positions[0][0]
                and self.positions[-1][1] + dy == other.positions[0][1]
            ):
                return True
        return False

    def concatenate(self, other: "Strand") -> "Strand":
        """Creates a new strand by concatenating this strand with another strand."""
        if not self.can_concatenate(other):
            raise ValueError("Strands cannot be concatenated")
        return Strand(
            positions=self.positions + other.positions,
            string=self.string + other.string,
        )

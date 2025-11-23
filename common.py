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

    def can_concatenate(self, *others: "Strand") -> bool:
        """Checks whether this strand can be concatenated with one or more other strands.

        For multiple strands, checks if they can be concatenated in sequence:
        self -> others[0] -> others[1] -> ...
        """
        if not others:
            raise ValueError("Cannot check concatenation with no other strands")

        strands = [self] + list(others)

        # Check each adjacent pair in the sequence
        for i in range(len(strands) - 1):
            if not strands[i]._can_concatenate_single(strands[i + 1]):
                return False

        return True

    def concatenate(self, *others: "Strand") -> "Strand":
        """Creates a new strand by concatenating this strand with one or more other strands.

        For multiple strands, concatenates them in sequence:
        self + others[0] + others[1] + ...

        Behavior is undefined when concatenating strands for which can_concatenate
        returns False.
        """
        result = self
        for other in others:
            result = result._concatenate_single(other)
        return result

    def _can_concatenate_single(self, other: "Strand") -> bool:
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

    def _concatenate_single(self, other: "Strand") -> "Strand":
        """Creates a new strand by concatenating this strand with another strand."""
        return Strand(
            positions=self.positions + other.positions,
            string=self.string + other.string,
        )

    def has_self_crossing(self) -> bool:
        """Checks whether the strand crosses itself.

        A strand crosses itself if any of its line segments intersect with any
        other non-adjacent line segment.
        """
        if len(self.positions) < 4:
            # Need at least 4 positions to have a self-crossing
            return False

        # Check each pair of non-adjacent segments
        for i in range(len(self.positions) - 1):
            for j in range(i + 2, len(self.positions) - 1):
                # Skip adjacent segments (they share an endpoint)
                if j == i + 1:
                    continue

                seg1 = (self.positions[i], self.positions[i + 1])
                seg2 = (self.positions[j], self.positions[j + 1])

                if _segments_intersect(seg1, seg2):
                    return True

        return False

    def crosses(self, other: "Strand") -> bool:
        """Checks whether this strand crosses another strand.

        Two strands cross if any of their line segments intersect.
        """
        for i in range(len(self.positions) - 1):
            for j in range(len(other.positions) - 1):
                seg1 = (self.positions[i], self.positions[i + 1])
                seg2 = (other.positions[j], other.positions[j + 1])

                if _segments_intersect(seg1, seg2):
                    return True

        return False


def _segments_intersect(
    seg1: tuple[tuple[int, int], tuple[int, int]],
    seg2: tuple[tuple[int, int], tuple[int, int]],
) -> bool:
    """Checks whether two line segments intersect.

    Two segments intersect if they cross each other (not just touch at endpoints).
    Uses the orientation method to determine if segments intersect.
    """
    p1, p2 = seg1
    p3, p4 = seg2

    # Segments that share an endpoint don't count as crossing
    if p1 == p3 or p1 == p4 or p2 == p3 or p2 == p4:
        return False

    # Check if the segments intersect using the orientation test
    # Two segments (p1,p2) and (p3,p4) intersect if:
    # - p1 and p2 are on opposite sides of the line through p3,p4
    # - AND p3 and p4 are on opposite sides of the line through p1,p2

    o1 = _orientation(p1, p2, p3)
    o2 = _orientation(p1, p2, p4)
    o3 = _orientation(p3, p4, p1)
    o4 = _orientation(p3, p4, p2)

    # General case: segments intersect if orientations differ
    if o1 != o2 and o3 != o4:
        return True

    return False


def _orientation(p: tuple[int, int], q: tuple[int, int], r: tuple[int, int]) -> int:
    """Returns the orientation of the ordered triplet (p, q, r).

    Returns:
        0 if p, q, r are collinear
        1 if clockwise
        -1 if counterclockwise
    """
    # Calculate the cross product of vectors (q-p) and (r-q)
    val = (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

    if val == 0:
        return 0  # collinear
    return 1 if val > 0 else -1  # clockwise or counterclockwise


class Cover(frozenset[Strand]):
    """A set of strands which exactly covers the grid, i.e. each cell in the grid is covered
    by exactly one strand in the set.

    Note: there is no check that a cover is valid."""

    pass


@dataclass(frozen=True)
class Solution:
    """A set of strands, which form a solution to a puzzle.

    Note: there is no check that a solution is valid."""

    spangram: tuple[Strand, ...]
    non_spangram_strands: frozenset[Strand]

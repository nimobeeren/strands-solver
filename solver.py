import bisect
from dataclasses import dataclass
from enum import Enum

from words import get_wordset


class Direction(Enum):
    RIGHT = (1, 0)
    DOWN_RIGHT = (1, 1)
    DOWN = (0, 1)
    DOWN_LEFT = (-1, 1)
    LEFT = (-1, 0)
    UP_LEFT = (-1, -1)
    UP = (0, -1)
    UP_RIGHT = (1, -1)


@dataclass
class Strand:
    positions: list[tuple[int, int]]
    """Sequence of positions that the strand occupies."""
    string: str
    """String formed by concatenating the letters in the grid at each position."""


class Solver:
    def __init__(
        self,
        grid: list[list[str]],
        *,
        rows=6,
        cols=8,
        wordset: set[str] = get_wordset(),
    ):
        self.grid = grid
        self.rows = rows
        self.cols = cols
        self.wordset = wordset
        self.wordlist = sorted(wordset)

    def find_all_words(self):
        """Finds all strands forming words in the grid, allowing overlap between
        different strands."""
        words: list[Strand] = []
        for x in range(self.cols):
            for y in range(self.rows):
                words += self.find_words(current_pos=(x, y))
        return words

    def find_words(
        self,
        *,
        current_pos: tuple[int, int],
        prefix: Strand = Strand(positions=[], string=""),
        min_length=4,
    ) -> list[Strand]:
        """Finds strands forming words in the grid starting with the `prefix` strand and
        continuing at `current_pos` without overlapping with the `prefix` strand."""
        words: list[Strand] = []
        x, y = current_pos

        # Create a candidate strand by taking the prefix strand and adding the letter at `current_pos` to it
        candidate = Strand(
            positions=prefix.positions + [(x, y)],
            string=prefix.string + self.grid[x][y],
        )

        if not self.is_word_prefix(candidate.string):
            return words

        if len(candidate.string) >= min_length and self.is_word(candidate.string):
            print(f"Found word: {candidate.string}")
            words.append(candidate)

        for dir in Direction:
            dx, dy = dir.value
            next_x, next_y = (x + dx, y + dy)

            if next_x < 0 or next_x >= self.cols or next_y < 0 or next_y >= self.rows:
                continue  # next position is out of bounds
            if (next_x, next_y) in candidate.positions:
                continue  # next position overlaps

            words += self.find_words(
                current_pos=(next_x, next_y),
                prefix=candidate,
                min_length=min_length,
            )

        return words

    def is_word(self, candidate: str):
        return candidate in self.wordset

    def is_word_prefix(self, candidate: str):
        candidate = candidate.upper()
        i = bisect.bisect_left(self.wordlist, candidate)
        return i < len(self.wordlist) and self.wordlist[i].startswith(candidate)

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

    def overlaps(self, other: "Strand"):
        return len(set(self.positions) & set(other.positions)) > 0


class Solver:
    def __init__(
        self,
        grid: list[list[str]],
        *,
        wordset: set[str] = get_wordset(),
    ):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0])
        self.wordset = wordset
        self.wordlist = sorted(wordset)

    def solve(
        self, *, words: list[Strand] | None = None, used_words: list[Strand] = []
    ) -> list[Strand] | None:
        """Solve the puzzle by choosing from `words` and using at least the words in
        `used_words`. If `words` is not provided, will find all words in the grid first."""
        if self.is_valid_solution(used_words):
            return used_words

        if words is None:
            words = self.find_all_words()
            print(f"Found {len(words)} words")

        for i, word in enumerate(words):
            if any(uw.overlaps(word) for uw in used_words):
                continue  # word overlaps with a used word
            words_to_try = words[i + 1 :]  # don't try words we've already tried
            solution = self.solve(words=words_to_try, used_words=used_words + [word])
            if solution is not None:
                return solution

        return None

    def is_valid_solution(self, strands: list[Strand]) -> bool:
        """Checks that all positions in the grid are occupied by at least one strand.
        Note: we don't check that the strands are valid and non-overlapping; this must
        be maintained during construction."""
        for x in range(self.cols):
            for y in range(self.rows):
                if not any((x, y) in s.positions for s in strands):
                    return False
        return True

    def find_all_words(self) -> list[Strand]:
        """Finds all strands forming words in the grid."""
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
            string=prefix.string + self.grid[y][x],
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

    def is_word(self, candidate: str) -> bool:
        return candidate in self.wordset

    def is_word_prefix(self, candidate: str) -> bool:
        candidate = candidate.upper()
        i = bisect.bisect_left(self.wordlist, candidate)
        return i < len(self.wordlist) and self.wordlist[i].startswith(candidate)

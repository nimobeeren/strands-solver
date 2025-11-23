import bisect
import logging

from .common import Strand, Direction
from .dictionary import load_dictionary

logger = logging.getLogger(__name__)


class Finder:
    """Finds strands forming words given a grid and an optional dictionary and minimum
    word length."""

    def __init__(
        self,
        grid: list[list[str]],
        *,
        dictionary: set[str] | None = None,
        min_length: int | None = 4,
    ) -> None:
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.min_length = 1 if min_length is None else min_length

        logger.info("Loading dictionary")
        if dictionary is None:
            dictionary = load_dictionary()
        self.dictionary = dictionary
        self.sorted_dictionary = sorted(dictionary)
        logger.info(f"Loaded {len(dictionary)} words")

    def find_all_words(self) -> set[Strand]:
        """Finds all strands forming words in the grid."""
        words: set[Strand] = set()
        for x in range(self.num_cols):
            for y in range(self.num_rows):
                words |= self.find_words(current_pos=(x, y))
        return words

    def find_words(
        self,
        *,
        current_pos: tuple[int, int],
        prefix: Strand = Strand(positions=(), string=""),
    ) -> set[Strand]:
        """Finds strands forming words in the grid starting with the `prefix` strand and
        continuing at `current_pos` without overlapping with the `prefix` strand."""
        words: set[Strand] = set()
        x, y = current_pos

        # Create a candidate strand by taking the prefix strand and adding the letter at `current_pos` to it
        candidate = Strand(
            positions=prefix.positions + ((x, y),),
            string=prefix.string + self.grid[y][x],
        )

        # Prune if not a word prefix
        if not self.is_word_prefix(candidate.string):
            return words

        # Prune if the candidate strand crosses itself
        if candidate.has_self_crossing():
            return words

        if len(candidate.string) >= self.min_length and self.is_word(candidate.string):
            logger.debug(f"Found word: {candidate.string}")
            words.add(candidate)

        for dir in Direction:
            dx, dy = dir.value
            next_x, next_y = (x + dx, y + dy)

            if (
                next_x < 0
                or next_x >= self.num_cols
                or next_y < 0
                or next_y >= self.num_rows
            ):
                continue  # next position is out of bounds
            if (next_x, next_y) in candidate.positions:
                continue  # next position overlaps

            words |= self.find_words(
                current_pos=(next_x, next_y),
                prefix=candidate,
            )

        return words

    def is_word(self, candidate: str) -> bool:
        return candidate in self.dictionary

    def is_word_prefix(self, candidate: str) -> bool:
        candidate = candidate.upper()
        i = bisect.bisect_left(self.sorted_dictionary, candidate)
        return i < len(self.sorted_dictionary) and self.sorted_dictionary[i].startswith(
            candidate
        )

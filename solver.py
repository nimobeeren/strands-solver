import logging

from common import Strand
from coverer import Coverer
from finder import Finder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(
        self,
        grid: list[list[str]],
        *,
        finder: Finder,
        coverer: Coverer,
        num_words: int | None = None,
    ):
        self.grid = grid
        self.finder = finder
        self.coverer = coverer
        self.num_words = num_words
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])

    def solve(self) -> set[frozenset[Strand]]:
        """Solve the puzzle by finding all words in the grid and then finding all ways
        to exactly cover the grid with those words.

        Returns a set of solutions, where each solution is a set of strands covering
        the grid.
        """

        logger.info("Finding all words")
        words = self.finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        words = self._filter_duplicate_words(words)
        logger.info(f"After filtering duplicates: {len(words)} words")

        logger.info("Covering grid")
        covers = self.coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        covers = self._filter_covers_by_num_words(covers)
        logger.info(f"After filtering by number of words: {len(covers)} covers")

        covers = self._filter_covers_by_spangram(covers)
        logger.info(f"After filtering by spangram: {len(covers)} covers")

        return covers

    @staticmethod
    def _filter_duplicate_words(words: set[Strand]) -> set[Strand]:
        """Filter out words that appear in different places.

        If a word appears multiple times using different sets of positions, we filter
        out all instances, since we know the final solution never contains a word which
        could be formed using different sets of positions.

        If a word appears multiple times using the exact same set of grid positions
        (just traced in different orders), we keep only one."""
        # Group strands by their word string
        words_by_string: dict[str, list[Strand]] = {}
        for strand in words:
            if strand.string not in words_by_string:
                words_by_string[strand.string] = []
            words_by_string[strand.string].append(strand)

        # Filter out words that have instances with different position sets
        filtered = set()
        for word_string, strands in words_by_string.items():
            if len(strands) == 1:
                # Only one instance, keep it
                filtered.update(strands)
            else:
                # Check if all instances use the exact same set of positions
                first_positions = set(strands[0].positions)
                all_same_positions = all(
                    set(strand.positions) == first_positions for strand in strands[1:]
                )

                if all_same_positions:
                    # All instances use the same positions (different traversal orders)
                    # Keep the one with lexicographically smallest positions tuple
                    # This is an arbitrary but consistent way to choose one
                    filtered.add(min(strands, key=lambda s: s.positions))
                # Otherwise, filter out all instances (different position sets)

        return filtered

    def _filter_covers_by_num_words(
        self, covers: set[frozenset[Strand]]
    ) -> set[frozenset[Strand]]:
        """Filter covers to only include those with the correct number of words.

        If a cover has too many words, attempts to reduce the count by concatenating
        pairs of words that can form a spangram.
        """
        if self.num_words is None:
            raise NotImplementedError()  # TODO

        # Find covers which have the correct number of words
        covers_with_correct_num_words = set[frozenset[Strand]]()
        for cover in covers:
            # If cover doesn't have enough words, skip it
            if len(cover) < self.num_words:
                continue
            # If a cover has exactly enough words, it's trivially correct
            elif len(cover) == self.num_words:
                covers_with_correct_num_words.add(cover)
            # If a cover has too many words, we may be able to reduce the number by
            # concatenating some words
            elif len(cover) == self.num_words + 1:
                pairs: set[tuple[Strand, Strand]] = set()
                for word1 in cover:
                    for word2 in cover - {word1}:
                        pairs.add((word1, word2))

                for word1, word2 in pairs:
                    if word1.can_concatenate(word2):
                        concatenated = word1.concatenate(word2)
                        if concatenated.is_spangram(self.num_rows, self.num_cols):
                            covers_with_correct_num_words.add(
                                frozenset((cover - {word1, word2}) | {concatenated})
                            )
            else:
                # TODO generalize to cases where cover has more than `num_words + 1`
                # words, requiring multiple concatenations
                continue

        return covers_with_correct_num_words

    def _filter_covers_by_spangram(
        self, covers: set[frozenset[Strand]]
    ) -> set[frozenset[Strand]]:
        """Filter covers to only include those that contain at least one spangram."""
        covers_with_spangram = set[frozenset[Strand]]()
        for cover in covers:
            if any(
                strand
                for strand in cover
                if strand.is_spangram(self.num_rows, self.num_cols)
            ):
                covers_with_spangram.add(cover)
        return covers_with_spangram

import logging
from itertools import combinations, permutations

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
        spangram_max_words=5,
    ):
        """
        Parameters:
        - grid: the grid of the puzzle
        - finder: the finder object
        - coverer: the coverer object
        - num_words: the number of words that should be in the solution
        - spangram_max_words: the maximum number of words that can be concatenated to
            form a spangram (we assume this is no higher than 5 in real solutions)
        """
        self.grid = grid
        self.finder = finder
        self.coverer = coverer
        self.num_words = num_words
        self.spangram_max_words = spangram_max_words

        self.num_rows = len(grid)
        self.num_cols = len(grid[0])

    def solve(self) -> set[frozenset[Strand]]:
        """Solve the puzzle by finding all words in the grid and then finding all ways
        to exactly cover the grid with those words.

        Returns a set of solutions, where each solution is a set of strands covering
        the grid including at least one spangram.
        """

        logger.info("Finding all words")
        words = self.finder.find_all_words()
        logger.info(f"Found {len(words)} words")

        words = self._filter_duplicate_words(words)
        logger.info(f"After filtering duplicates: {len(words)} words")

        logger.info("Covering grid")
        covers = self.coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        if self.num_words is not None:
            covers = self._try_concatenate_words(covers, self.num_words)
            logger.info(f"After concaenating words: {len(covers)} covers")

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

    def _try_concatenate_words(
        self, covers: set[frozenset[Strand]], num_words: int
    ) -> set[frozenset[Strand]]:
        """For covers with too many words, attempts to reduce the count by concatenating
        words that can form a spangram.

        Covers with too few words are filtered out.

        Returns a set of covers with the correct number of words, which may or may not
        contain a (concatenated) spangram.
        """
        # Find covers which have the correct number of words
        covers_with_correct_num_words = set[frozenset[Strand]]()
        for cover in covers:
            # If cover doesn't have enough words, skip it
            if len(cover) < num_words:
                continue
            # If a cover has exactly enough words, it's trivially correct
            elif len(cover) == num_words:
                covers_with_correct_num_words.add(cover)
            # If a cover has too many words, we may be able to reduce the number by
            # concatenating some words
            elif len(cover) > num_words:
                # Number of words that need to be concatenated into one
                num_to_concat = len(cover) - num_words + 1

                # ASSUMPTION: spangrams never consist of this many words
                if num_to_concat > self.spangram_max_words:
                    continue

                # Try all combinations of words that could be concatenated
                for words_to_concat in combinations(cover, num_to_concat):
                    # Try all permutations since concatenation order matters
                    for word_order in permutations(words_to_concat):
                        # Try to concatenate the words in this order
                        first_word = word_order[0]
                        other_words = word_order[1:]

                        if first_word.can_concatenate(*other_words):
                            concatenated = first_word.concatenate(*other_words)
                            if concatenated.is_spangram(self.num_rows, self.num_cols):
                                # Create new cover with concatenated word replacing individual words
                                new_cover = frozenset(
                                    (cover - set(words_to_concat)) | {concatenated}
                                )
                                covers_with_correct_num_words.add(new_cover)

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

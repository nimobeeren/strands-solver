import logging

from common import Strand
from coverer import Coverer
from finder import Finder

logger = logging.getLogger(__name__)


class Solver:
    def __init__(self, grid: list[list[str]], *, finder: Finder, coverer: Coverer):
        self.grid = grid
        self.finder = finder
        self.coverer = coverer
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

        # Filter out words that appear in different places
        # The words in the final solution never appear in more than one place in
        # the grid
        words = self._filter_duplicate_words(words)
        logger.info(f"After filtering duplicates: {len(words)} words")

        logger.info("Covering grid")
        covers = self.coverer.cover(words)
        logger.info(f"Found {len(covers)} covers")

        # Find covers which contain at least one spangram
        solutions = set()
        for cover in covers:
            if any(
                strand
                for strand in cover
                if strand.is_spangram(self.num_rows, self.num_cols)
            ):
                solutions.add(cover)
        logger.info(f"Found {len(solutions)} covers with a spangram")

        return solutions

    @staticmethod
    def _filter_duplicate_words(words: set[Strand]) -> set[Strand]:
        """Filter out words that appear in different places.

        If a word appears multiple times using different sets of positions, we filter
        out all instances, since we know the final solution never contains a word which
        could be formed using different sets of positions.

        If a word appears multiple times using the exact same set of grid positions
        (just traced in different orders), we keep all instances and let the covering
        algorithm choose which path to use.
        """
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

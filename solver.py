from common import Strand
from grid_coverer import GridCoverer
from word_finder import WordFinder


class Solver:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid

    def solve(self) -> list[Strand] | None:
        """Solve the puzzle by finding all words in the grid and then finding the words
        which exactly cover the grid.

        This implementation uses a bitset-based exact-cover style search with MRV:
        - Represent the grid coverage as a 48-bit mask (one bit per cell)
        - For each candidate `Strand`, precompute a bit mask of its covered cells
        - At each step, choose the uncovered cell with the fewest available candidates (MRV)
        - Branch only on words that cover that cell and do not overlap already covered cells

        Returns a collection of `Strand`s covering the grid or None if unsatisfiable.
        """

        print("Finding all words")
        word_finder = WordFinder(grid=self.grid)
        words = word_finder.find_all_words()
        print(f"Found {len(words)} words")

        print("Covering grid")
        coverer = GridCoverer(grid=self.grid, words=words)
        solution = coverer.cover()
        print("Covered grid")

        return solution

from common import Strand
from word_finder import WordFinder


class Solver:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.num_cells = self.num_rows * self.num_cols

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

        print("Building indices")
        word_masks, cell_to_words = self.build_indices(words)
        print("Built indices")

        # Core MRV backtracking using bitsets
        solution_indices = self.cover(
            word_masks=word_masks, cell_to_words=cell_to_words
        )

        if solution_indices is None:
            return None

        # Map indices back to Strands
        return [words[i] for i in solution_indices]

    def build_indices(self, words: list[Strand]):
        """Computes:
        - `word_masks`: bit mask per word (1 bit per grid cell it covers)
        - `cell_to_words`: for each cell index, list of word indices that cover it
        """
        word_masks: list[int] = []
        cell_to_words: list[list[int]] = [[] for _ in range(self.num_cells)]

        for i, strand in enumerate(words):
            mask = 0
            for x, y in strand.positions:
                bit_index = y * self.num_cols + x
                mask |= 1 << bit_index
                cell_to_words[bit_index].append(i)
            word_masks.append(mask)

        return word_masks, cell_to_words

    def cover(
        self,
        *,
        word_masks: list[int],
        cell_to_words: list[list[int]],
        covered_mask: int = 0,
    ) -> list[int] | None:
        """Backtracking search that covers all cells exactly once using MRV branching.

        Returns a list of word indices forming a cover, or None if no cover exists.
        """
        # If fully covered, we are done
        all_cells_mask = (1 << self.num_cells) - 1
        if covered_mask == all_cells_mask:
            return []

        num_cells = self.num_rows * self.num_cols

        # MRV: choose the uncovered cell with the fewest available non-overlapping words
        best_candidates: list[int] | None = None

        for cell_index in range(num_cells):
            if (covered_mask >> cell_index) & 1:
                continue  # already covered

            candidates = [
                w_idx
                for w_idx in cell_to_words[cell_index]
                if (word_masks[w_idx] & covered_mask) == 0
            ]

            if not candidates:
                return None  # dead end: uncovered cell has no valid words

            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                if len(best_candidates) == 1:
                    break  # small early exit when forced

        assert best_candidates is not None

        # Try candidates for the most constrained cell
        for w_idx in best_candidates:
            new_mask = covered_mask | word_masks[w_idx]
            result = self.cover(
                word_masks=word_masks,
                cell_to_words=cell_to_words,
                covered_mask=new_mask,
            )
            if result is not None:
                return [w_idx] + result

        return None

import logging

from common import Strand

logger = logging.getLogger(__name__)


class Coverer:
    """Given a grid and a list of strands, tries to find ways to cover every cell of
    the grid with a subset of the strands without overlapping."""

    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.num_cells = self.num_rows * self.num_cols

    def cover(self, strands: set[Strand] | list[Strand]) -> set[frozenset[Strand]]:
        """Finds ways to cover the entire grid with strands without overlapping."""
        # Convert to list for indexing
        strands_list = list(strands)
        self.strand_masks, self.cell_to_strand_idx = self._build_indices(strands_list)
        results = self._cover_rec()

        # Map indices back to Strands
        return {frozenset(strands_list[i] for i in result) for result in results}

    def _cover_rec(self, *, covered_mask: int = 0) -> list[list[int]]:
        """Recursive backtracking search that covers all grid cells exactly once using
        MRV (Minimum Remaining Values) branching.

        Returns a list of sub-solutions, where each sub-solution is a list of strand
        indices which, together with covered_mask, cover the entire grid.

        This implementation uses a bitset-based exact-cover style search with MRV:

        - Represent the grid coverage as a 48-bit mask (one bit per cell)
        - For each candidate `Strand`, precompute a bit mask of its covered cells
        - At each step, choose the uncovered cell with the fewest available candidates (MRV)
        - Branch only on strands that cover that cell and do not overlap already covered cells
        """
        # If fully covered, we found a solution
        all_cells_mask = (1 << self.num_cells) - 1
        if covered_mask == all_cells_mask:
            # There is exactly one sub-solution and it contains no strands
            return [[]]

        num_cells = self.num_rows * self.num_cols

        # MRV: choose the uncovered cell with the fewest available non-overlapping
        # strands
        best_candidates: list[int] | None = None

        for cell_index in range(num_cells):
            if (covered_mask >> cell_index) & 1:
                continue  # cell is already covered

            candidates = [
                w_idx
                for w_idx in self.cell_to_strand_idx[cell_index]
                if (self.strand_masks[w_idx] & covered_mask) == 0
            ]

            if not candidates:
                return []  # dead end: uncovered cell has no valid strands

            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                if len(best_candidates) == 1:
                    break  # small early exit when forced

        assert best_candidates is not None

        # Try candidates for the most constrained cell
        solutions = []
        for w_idx in best_candidates:
            new_mask = covered_mask | self.strand_masks[w_idx]
            sub_solutions = self._cover_rec(covered_mask=new_mask)
            # Prepend w_idx to each sub-solution
            for sub in sub_solutions:
                solutions.append([w_idx] + sub)

        return solutions

    def _build_indices(self, strands: list[Strand]):
        """Computes:
        - `strand_masks`: bit mask per strand (1 bit per grid cell it covers)
        - `cell_to_strands`: for each cell index, list of strand indices that cover it
        """
        strand_masks: list[int] = []
        cell_to_strands: list[list[int]] = [[] for _ in range(self.num_cells)]

        for i, strand in enumerate(strands):
            mask = 0
            for x, y in strand.positions:
                bit_index = y * self.num_cols + x
                mask |= 1 << bit_index
                cell_to_strands[bit_index].append(i)
            strand_masks.append(mask)

        return strand_masks, cell_to_strands

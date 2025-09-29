import logging

from common import Strand

logger = logging.getLogger(__name__)


class GridCoverer:
    """Given a grid and a list of strands, tries to find a way to cover every cell of
    the grid with a subset of the strands without overlapping."""

    def __init__(self, *, grid: list[list[str]], strands: list[Strand]):
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.num_cells = self.num_rows * self.num_cols
        self.strands = strands

        logger.info("Building indices")
        self.strand_masks, self.cell_to_strand_idx = self._build_indices()
        logger.info("Built indices")

    def cover(self) -> list[Strand] | None:
        """Finds a way to cover the entire grid with strands without overlapping."""
        result = self._cover_rec()

        if result is None:
            return None

        # Map indices back to Strands
        return [self.strands[i] for i in result]

    def _cover_rec(self, *, covered_mask: int = 0) -> list[int] | None:
        """Recursive backtracking search that covers all grid cells exactly once using
        MRV (Minimum Remaining Values) branching.

        Returns a list of strand indices forming a cover, or None if no cover exists.

        This implementation uses a bitset-based exact-cover style search with MRV:

        - Represent the grid coverage as a 48-bit mask (one bit per cell)
        - For each candidate `Strand`, precompute a bit mask of its covered cells
        - At each step, choose the uncovered cell with the fewest available candidates (MRV)
        - Branch only on strands that cover that cell and do not overlap already covered cells
        """
        # If fully covered, we are done
        all_cells_mask = (1 << self.num_cells) - 1
        if covered_mask == all_cells_mask:
            return []

        num_cells = self.num_rows * self.num_cols

        # MRV: choose the uncovered cell with the fewest available non-overlapping
        # strands
        best_candidates: list[int] | None = None

        for cell_index in range(num_cells):
            if (covered_mask >> cell_index) & 1:
                continue  # already covered

            candidates = [
                w_idx
                for w_idx in self.cell_to_strand_idx[cell_index]
                if (self.strand_masks[w_idx] & covered_mask) == 0
            ]

            if not candidates:
                return None  # dead end: uncovered cell has no valid strands

            if best_candidates is None or len(candidates) < len(best_candidates):
                best_candidates = candidates
                if len(best_candidates) == 1:
                    break  # small early exit when forced

        assert best_candidates is not None

        # Try candidates for the most constrained cell
        for w_idx in best_candidates:
            new_mask = covered_mask | self.strand_masks[w_idx]
            result = self._cover_rec(
                covered_mask=new_mask,
            )
            if result is not None:
                return [w_idx] + result

        return None

    def _build_indices(self):
        """Computes:
        - `strand_masks`: bit mask per strand (1 bit per grid cell it covers)
        - `cell_to_strands`: for each cell index, list of strand indices that cover it
        """
        strand_masks: list[int] = []
        cell_to_strands: list[list[int]] = [[] for _ in range(self.num_cells)]

        for i, strand in enumerate(self.strands):
            mask = 0
            for x, y in strand.positions:
                bit_index = y * self.num_cols + x
                mask |= 1 << bit_index
                cell_to_strands[bit_index].append(i)
            strand_masks.append(mask)

        return strand_masks, cell_to_strands

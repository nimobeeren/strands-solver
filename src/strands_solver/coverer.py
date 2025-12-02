"""Exact cover solver using Algorithm X.

This module implements Donald Knuth's Algorithm X for solving the exact cover problem.
Given a grid and a set of strands (words found in the grid), it finds all ways to cover
every cell of the grid with a subset of strands without overlapping.

Optimizations:
- Bitmask representation for cell coverage (fast overlap detection)
- MRV (Minimum Remaining Values) heuristic for column selection
- Unit propagation: forced cells (single candidate) processed without branching
"""

import logging

from .common import Cover, Strand

logger = logging.getLogger(__name__)


class Coverer:
    """Given a grid and a set of strands, tries to find ways to cover every cell of
    the grid with a subset of the strands without overlapping."""

    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.num_rows = len(grid)
        self.num_cols = len(grid[0])
        self.num_cells = self.num_rows * self.num_cols

    def cover(self, strands: set[Strand] | list[Strand]) -> set[Cover]:
        """Finds ways to cover the entire grid with strands without overlapping."""
        strands_list = list(strands)
        num_strands = len(strands_list)

        logger.info(f"Covering grid with {num_strands} candidate strands")

        # Build data structures for Algorithm X
        num_cells = self.num_cells
        num_cols = self.num_cols

        # strand_masks[i] = bitmask of cells covered by strand i
        strand_masks: list[int] = []
        # cell_strands[c] = tuple of strand indices that cover cell c
        cell_strands_lists: list[list[int]] = [[] for _ in range(num_cells)]

        for i, strand in enumerate(strands_list):
            mask = 0
            for x, y in strand.positions:
                cell_idx = y * num_cols + x
                mask |= 1 << cell_idx
                cell_strands_lists[cell_idx].append(i)
            strand_masks.append(mask)

        # Convert to tuples for faster iteration
        cell_strands = tuple(tuple(cs) for cs in cell_strands_lists)
        strand_masks_tuple = tuple(strand_masks)

        # Run Algorithm X
        results: list[list[int]] = []

        _algorithm_x_rec(
            covered_mask=0,
            all_cells_mask=(1 << num_cells) - 1,
            num_cells=num_cells,
            strand_masks=strand_masks_tuple,
            cell_strands=cell_strands,
            partial=[],
            results=results,
        )

        logger.info(f"Algorithm X found {len(results)} covers (before crossing filter)")

        # Convert index lists to Cover objects
        all_covers = {Cover(strands_list[i] for i in result) for result in results}

        # Filter out covers with crossing strands
        valid_covers = set()
        for cover in all_covers:
            if not _cover_has_crossing(cover):
                valid_covers.add(cover)

        logger.info(f"After crossing filter: {len(valid_covers)} valid covers")
        return valid_covers


def _algorithm_x_rec(
    *,
    covered_mask: int,
    all_cells_mask: int,
    num_cells: int,
    strand_masks: tuple[int, ...],
    cell_strands: tuple[tuple[int, ...], ...],
    partial: list[int],
    results: list[list[int]],
) -> None:
    """Recursive Algorithm X with MRV heuristic and unit propagation."""
    num_strands = len(strand_masks)
    original_len = len(partial)

    # Unit propagation + MRV selection loop
    while True:
        # Base case: all cells covered
        if covered_mask == all_cells_mask:
            results.append(list(partial))
            # Backtrack unit propagation
            del partial[original_len:]
            return

        # Find MRV cell (uncovered cell with fewest valid candidates)
        min_count = num_strands + 1
        best_cell = -1
        best_first = -1  # First candidate for forced moves

        for cell_idx in range(num_cells):
            if (covered_mask >> cell_idx) & 1:
                continue  # already covered

            # Count valid strands for this cell
            count = 0
            first = -1
            for s_idx in cell_strands[cell_idx]:
                if (strand_masks[s_idx] & covered_mask) == 0:
                    if first == -1:
                        first = s_idx
                    count += 1
                    if count >= min_count:
                        break

            if count == 0:
                # Dead end: uncovered cell with no valid strands
                del partial[original_len:]
                return

            if count < min_count:
                min_count = count
                best_cell = cell_idx
                best_first = first
                if count == 1:
                    break  # Can't do better

        if min_count == 1:
            # Forced move - select without branching
            partial.append(best_first)
            covered_mask |= strand_masks[best_first]
        else:
            break

    # Branch on all candidates for the MRV cell
    for s_idx in cell_strands[best_cell]:
        if (strand_masks[s_idx] & covered_mask) == 0:
            partial.append(s_idx)
            _algorithm_x_rec(
                covered_mask=covered_mask | strand_masks[s_idx],
                all_cells_mask=all_cells_mask,
                num_cells=num_cells,
                strand_masks=strand_masks,
                cell_strands=cell_strands,
                partial=partial,
                results=results,
            )
            partial.pop()

    # Backtrack unit propagation
    del partial[original_len:]


def _cover_has_crossing(cover: Cover) -> bool:
    """Checks if any strands in the cover cross each other."""
    strands = list(cover)
    for i in range(len(strands)):
        for j in range(i + 1, len(strands)):
            if strands[i].crosses(strands[j]):
                return True
    return False

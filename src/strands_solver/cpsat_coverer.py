import logging
from typing import Iterable

from ortools.sat.python import cp_model

from .common import Cover, Strand

logger = logging.getLogger(__name__)


class CoverSolutionCollector(cp_model.CpSolverSolutionCallback):
    """Collects all solutions found by the CP-SAT solver."""

    def __init__(
        self,
        strand_vars: list[cp_model.IntVar],
        strands: list[Strand],
        max_solutions: int,
    ):
        super().__init__()
        self._strand_vars = strand_vars
        self._strands = strands
        self._max_solutions = max_solutions
        self.covers: list[Cover] = []

    def on_solution_callback(self) -> None:
        if len(self.covers) >= self._max_solutions:
            self.StopSearch()
            return

        selected = [
            self._strands[i]
            for i, v in enumerate(self._strand_vars)
            if self.Value(v)
        ]
        self.covers.append(Cover(selected))


class CPSATGridCoverer:
    """Finds ways to cover every cell of a grid with non-overlapping strands using CP-SAT."""

    def __init__(
        self,
        grid: list[list[str]],
        *,
        timeout_seconds: float = 60.0,
        max_solutions: int = 100000,
    ):
        self._grid = grid
        self._num_rows = len(grid)
        self._num_cols = len(grid[0])
        self._num_cells = self._num_rows * self._num_cols
        self._timeout_seconds = timeout_seconds
        self._max_solutions = max_solutions

    def cover(self, strands: Iterable[Strand]) -> set[Cover]:
        """Finds ways to cover the grid by choosing a subset of the strands without overlapping."""
        strands_list = list(strands)

        if not strands_list:
            return set()

        # Build cell -> strand indices mapping
        cell_to_strand_indices: list[list[int]] = [[] for _ in range(self._num_cells)]
        for i, strand in enumerate(strands_list):
            for x, y in strand.positions:
                cell_idx = y * self._num_cols + x
                cell_to_strand_indices[cell_idx].append(i)

        # Check if any cell has no covering strands
        for cell_idx, covering in enumerate(cell_to_strand_indices):
            if not covering:
                logger.debug(f"Cell {cell_idx} has no covering strands, no solutions")
                return set()

        # Build CP-SAT model
        model = cp_model.CpModel()

        # Boolean variable for each strand: 1 if strand is selected
        strand_vars = [model.NewBoolVar(f"s{i}") for i in range(len(strands_list))]

        # Constraint: exactly one strand per cell
        for cell_idx, covering_strand_indices in enumerate(cell_to_strand_indices):
            model.AddExactlyOne(strand_vars[i] for i in covering_strand_indices)

        # Solve and enumerate all solutions
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = self._timeout_seconds
        solver.parameters.enumerate_all_solutions = True

        collector = CoverSolutionCollector(
            strand_vars, strands_list, self._max_solutions
        )
        status = solver.Solve(model, collector)

        if status == cp_model.INFEASIBLE:
            logger.debug("CP-SAT found problem infeasible")
            return set()

        logger.debug(f"CP-SAT found {len(collector.covers)} covers")

        # Filter out covers with crossing strands (same as original)
        valid_covers = set()
        for cover in collector.covers:
            if not self._cover_has_crossing(cover):
                valid_covers.add(cover)

        return valid_covers

    def _cover_has_crossing(self, cover: Cover) -> bool:
        """Checks if any strands in the cover cross each other."""
        strands = list(cover)
        for i in range(len(strands)):
            for j in range(i + 1, len(strands)):
                if strands[i].crosses(strands[j]):
                    return True
        return False

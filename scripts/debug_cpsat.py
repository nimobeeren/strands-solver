#!/usr/bin/env python3
"""Debug CP-SAT behavior to understand solution counts."""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_solver.common import Puzzle
from strands_solver.word_finder import WordFinder
from ortools.sat.python import cp_model


def load_puzzle(path: str) -> Puzzle:
    with open(path) as f:
        data = json.load(f)
    return Puzzle(
        name=Path(path).stem,
        theme=data["theme"],
        grid=data["grid"],
        num_words=data["num_words"],
    )


class DebugSolutionCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, num_strands: int, max_solutions: int):
        super().__init__()
        self._num_strands = num_strands
        self._max_solutions = max_solutions
        self.solution_count = 0

    def on_solution_callback(self) -> None:
        self.solution_count += 1
        if self.solution_count >= self._max_solutions:
            print(f"  Hit max_solutions limit at {self.solution_count}")
            self.StopSearch()


def main():
    puzzle_path = sys.argv[1] if len(sys.argv) > 1 else "puzzles/2025-10-04.json"
    timeout = float(sys.argv[2]) if len(sys.argv) > 2 else 30.0
    max_solutions = int(sys.argv[3]) if len(sys.argv) > 3 else 5000

    print(f"Loading puzzle: {puzzle_path}")
    puzzle = load_puzzle(puzzle_path)
    num_rows = len(puzzle.grid)
    num_cols = len(puzzle.grid[0])
    num_cells = num_rows * num_cols

    print("Finding words...")
    finder = WordFinder(puzzle.grid)
    words = list(finder.find_all_words())
    print(f"Found {len(words)} words")

    # Build cell -> strand indices mapping
    cell_to_strand_indices = [[] for _ in range(num_cells)]
    for i, strand in enumerate(words):
        for x, y in strand.positions:
            cell_idx = y * num_cols + x
            cell_to_strand_indices[cell_idx].append(i)

    # Build CP-SAT model
    print(f"\nBuilding CP-SAT model...")
    model = cp_model.CpModel()
    strand_vars = [model.NewBoolVar(f"s{i}") for i in range(len(words))]

    for cell_idx, covering in enumerate(cell_to_strand_indices):
        if covering:
            model.AddExactlyOne(strand_vars[i] for i in covering)

    # Solve
    print(f"Solving with timeout={timeout}s, max_solutions={max_solutions}...")
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = timeout
    solver.parameters.enumerate_all_solutions = True

    collector = DebugSolutionCollector(len(words), max_solutions)
    start = time.perf_counter()
    status = solver.Solve(model, collector)
    elapsed = time.perf_counter() - start

    print(f"\nResults:")
    print(f"  Status: {solver.StatusName(status)}")
    print(f"  Time: {elapsed:.3f}s")
    print(f"  Solutions found by CP-SAT: {collector.solution_count}")
    print(f"  Wall time: {solver.WallTime():.3f}s")
    
    if status == cp_model.OPTIMAL:
        print("  → OPTIMAL means ALL solutions were enumerated")
    elif status == cp_model.FEASIBLE:
        print("  → FEASIBLE means search was stopped early (timeout or limit)")


if __name__ == "__main__":
    main()

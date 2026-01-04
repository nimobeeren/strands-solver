#!/usr/bin/env python3
"""Verify that covers from both coverers are valid and equivalent."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from strands_solver.common import Puzzle
from strands_solver.cpsat_coverer import CPSATGridCoverer
from strands_solver.grid_coverer import GridCoverer
from strands_solver.word_finder import WordFinder


def load_puzzle(path: str) -> Puzzle:
    with open(path) as f:
        data = json.load(f)
    return Puzzle(
        name=Path(path).stem,
        theme=data["theme"],
        grid=data["grid"],
        num_words=data["num_words"],
    )


def cover_signature(cover) -> frozenset:
    """Create a signature for a cover (set of (positions, string) pairs)."""
    return frozenset(
        (frozenset(strand.positions), strand.string.upper()) 
        for strand in cover
    )


def verify_cover(cover, num_rows, num_cols):
    """Verify a cover is valid: covers all cells exactly once, no crossings."""
    all_positions = set()
    for strand in cover:
        for pos in strand.positions:
            if pos in all_positions:
                return False, f"Duplicate position {pos}"
            all_positions.add(pos)
    
    expected = {(x, y) for x in range(num_cols) for y in range(num_rows)}
    if all_positions != expected:
        missing = expected - all_positions
        extra = all_positions - expected
        return False, f"Missing: {missing}, Extra: {extra}"
    
    # Check no crossings
    strands = list(cover)
    for i in range(len(strands)):
        for j in range(i + 1, len(strands)):
            if strands[i].crosses(strands[j]):
                return False, f"Crossing between {strands[i].string} and {strands[j].string}"
    
    return True, "OK"


def main():
    puzzle_path = sys.argv[1] if len(sys.argv) > 1 else "puzzles/2025-09-23.json"
    max_solutions = int(sys.argv[2]) if len(sys.argv) > 2 else 500
    
    print(f"Loading puzzle: {puzzle_path}")
    puzzle = load_puzzle(puzzle_path)
    
    print("Finding words...")
    finder = WordFinder(puzzle.grid)
    words = finder.find_all_words()
    print(f"Found {len(words)} words")
    
    print(f"\nTesting with max {max_solutions} solutions...")
    
    # Get covers from CP-SAT
    cpsat = CPSATGridCoverer(puzzle.grid, timeout_seconds=30, max_solutions=max_solutions)
    cpsat_covers = cpsat.cover(words)
    print(f"CP-SAT found {len(cpsat_covers)} covers")
    
    # Verify CP-SAT covers
    invalid_count = 0
    for cover in cpsat_covers:
        valid, msg = verify_cover(cover, len(puzzle.grid), len(puzzle.grid[0]))
        if not valid:
            invalid_count += 1
            print(f"  Invalid cover: {msg}")
    
    if invalid_count == 0:
        print("✅ All CP-SAT covers are valid")
    else:
        print(f"❌ {invalid_count} invalid CP-SAT covers")
    
    # Get covers from original (with same limit via early termination check)
    original = GridCoverer(puzzle.grid)
    original_covers = original.cover(words)
    print(f"\nOriginal found {len(original_covers)} covers")
    
    # Compare overlap using position-based signatures
    cpsat_sigs = {cover_signature(c) for c in cpsat_covers}
    original_sigs = {cover_signature(c) for c in original_covers}
    
    print(f"\nUnique position signatures:")
    print(f"  CP-SAT: {len(cpsat_sigs)}")
    print(f"  Original: {len(original_sigs)}")
    
    common = cpsat_sigs & original_sigs
    only_cpsat = cpsat_sigs - original_sigs
    only_original = original_sigs - cpsat_sigs
    
    print(f"\nCommon signatures: {len(common)}")
    print(f"Only in CP-SAT: {len(only_cpsat)}")
    print(f"Only in Original: {len(only_original)}")
    
    if len(only_cpsat) == 0 and len(only_original) == 0:
        print("\n✅ Both coverers find equivalent sets of covers (by position)")
    else:
        if only_cpsat:
            print("\n⚠️ CP-SAT found covers not found by Original!")
        if only_original:
            print("\n⚠️ Original found covers not found by CP-SAT!")


if __name__ == "__main__":
    main()

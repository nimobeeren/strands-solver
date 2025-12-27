#!/usr/bin/env python3
"""Displays the official solution for a Strands puzzle from the NY Times API."""

import argparse
import datetime

from strands_solver.drawing import draw
from strands_solver.puzzle_fetcher import PuzzleFetcher


def get_date(date_arg: str) -> datetime.date:
    if date_arg == "today":
        return datetime.date.today()
    try:
        return datetime.date.fromisoformat(date_arg)
    except ValueError:
        raise ValueError(f"Invalid date argument: {date_arg}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Display the official solution for a Strands puzzle."
    )
    parser.add_argument(
        "date",
        type=str,
        help="The date of the puzzle. Can be 'today' or a date in YYYY-MM-DD format.",
    )
    args = parser.parse_args()

    try:
        date = get_date(args.date)
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    fetcher = PuzzleFetcher()
    puzzle = fetcher.fetch_puzzle(date)
    solution = fetcher.fetch_solution(date)

    print(f"Theme: {puzzle.theme}\n")
    draw(puzzle.grid, solution)
    print()

    print(f"🟡 {solution.spangram[0].string} (spangram)")
    for strand in sorted(solution.non_spangram_strands, key=lambda s: s.string):
        print(f"🔵 {strand.string}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

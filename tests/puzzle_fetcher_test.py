import datetime

from strands_solver.puzzle_fetcher import Puzzle, PuzzleFetcher


def test_fetch_puzzle_returns_puzzle():
    fetcher = PuzzleFetcher()
    date = datetime.date(2025, 12, 2)
    puzzle = fetcher.fetch_puzzle(date)
    assert isinstance(puzzle, Puzzle)

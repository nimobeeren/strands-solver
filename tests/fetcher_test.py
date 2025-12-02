import datetime

from strands_solver.fetcher import Fetcher, Puzzle


def test_fetch_puzzle_returns_puzzle():
    fetcher = Fetcher()
    date = datetime.date(2025, 12, 2)
    puzzle = fetcher.fetch_puzzle(date)
    assert isinstance(puzzle, Puzzle)

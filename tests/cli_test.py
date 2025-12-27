from pathlib import Path

from strands_solver.cli import get_puzzle
from strands_solver.common import Puzzle


def test_get_puzzle_with_path():
    """Test get_puzzle with a path to a JSON file."""
    puzzle_path = Path(__file__).parent.parent / "puzzles" / "2025-11-30.json"
    puzzle = get_puzzle(str(puzzle_path))

    assert isinstance(puzzle, Puzzle)
    assert puzzle.name == "2025-11-30"
    assert puzzle.theme == "Group membership"
    assert puzzle.num_words == 9
    assert len(puzzle.grid) == 8
    assert len(puzzle.grid[0]) == 6


def test_get_puzzle_with_date():
    """Test get_puzzle with a date string."""
    puzzle = get_puzzle("2025-11-30")

    assert isinstance(puzzle, Puzzle)
    assert puzzle.name == "2025-11-30"


def test_get_puzzle_with_today():
    """Test get_puzzle with 'today' string."""
    puzzle = get_puzzle("today")

    assert isinstance(puzzle, Puzzle)

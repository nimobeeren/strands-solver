import json
from pathlib import Path

import pytest

from strands_solver.common import Puzzle, Solution, Strand
from strands_solver.solver import Solver
from strands_solver.spangram_finder import SpangramFinder
from strands_solver.word_finder import WordFinder

PUZZLES_DIR = Path(__file__).parent.parent.parent / "puzzles"


def load_puzzle(date: str) -> Puzzle:
    with open(PUZZLES_DIR / f"{date}.json") as f:
        data = json.load(f)
    return Puzzle(
        name=date,
        theme=data["theme"],
        grid=data["grid"],
        num_words=data["num_words"],
    )


def load_solution(date: str, grid: list[list[str]]) -> Solution:
    with open(PUZZLES_DIR / f"{date}_solution.json") as f:
        data = json.load(f)

    def coords_to_strand(word: str, coords: list[list[int]]) -> Strand:
        # API returns [row, col], convert to (col, row) = (x, y)
        positions = tuple((col, row) for row, col in coords)
        return Strand(positions=positions, string=word)

    # Build spangram strand
    spangram_coords = data["spangram_coords"]
    spangram_word = "".join(grid[row][col] for row, col in spangram_coords)
    spangram = coords_to_strand(spangram_word, spangram_coords)

    # Build theme word strands
    theme_strands: set[Strand] = set()
    for word, coords in data["theme_coords"].items():
        theme_strands.add(coords_to_strand(word, coords))

    return Solution(spangram=(spangram,), non_spangram_strands=frozenset(theme_strands))


@pytest.mark.integration
@pytest.mark.asyncio
async def test_solve():
    """Solve a real puzzle and assert that the official NY Times solution is among the
    found solutions."""
    puzzle = load_puzzle("2025-09-23")
    expected_solution = load_solution("2025-09-23", puzzle.grid)
    solver = Solver(puzzle)

    found_solutions = await solver.solve()

    assert any(s.equivalent(expected_solution) for s in found_solutions)


@pytest.mark.integration
def test_find_all_solutions():
    # Simple grid where each word appears only once
    grid = [
        ["E", "A", "S", "Y", "S"],
        ["C", "O", "O", "L", "P"],
        ["T", "E", "S", "T", "A"],
        ["W", "O", "R", "D", "N"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=5)

    finder = WordFinder(grid, dictionary={"EASY", "COOL", "TEST", "WORD", "SPAN"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Should find at least one solution
    assert len(solutions) >= 1

    # The expected solution should be in the solutions set
    expected = Solution(
        spangram=(Strand(positions=((4, 0), (4, 1), (4, 2), (4, 3)), string="SPAN"),),
        non_spangram_strands=frozenset(
            (
                Strand(positions=((0, 0), (1, 0), (2, 0), (3, 0)), string="EASY"),
                Strand(positions=((0, 1), (1, 1), (2, 1), (3, 1)), string="COOL"),
                Strand(positions=((0, 2), (1, 2), (2, 2), (3, 2)), string="TEST"),
                Strand(positions=((0, 3), (1, 3), (2, 3), (3, 3)), string="WORD"),
            )
        ),
    )
    assert expected in solutions


@pytest.mark.integration
def test_find_all_solutions_single_spangram():
    grid = [
        ["A", "B", "C", "D", "E", "K", "L", "M", "N"],
        ["O", "P", "Q", "R", "F", "G", "H", "I", "J"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=3)

    # There is only one solution with 3 words:
    # {ABCDEFGHIJ, KLMN, OPQR}

    finder = WordFinder(grid, dictionary={"ABCDEFGHIJ", "KLMN", "OPQR"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    expected = {
        Solution(
            spangram=(
                Strand(
                    positions=(
                        (0, 0),
                        (1, 0),
                        (2, 0),
                        (3, 0),
                        (4, 0),
                        (4, 1),
                        (5, 1),
                        (6, 1),
                        (7, 1),
                        (8, 1),
                    ),
                    string="ABCDEFGHIJ",
                ),
            ),
            non_spangram_strands=frozenset(
                (
                    Strand(
                        positions=((5, 0), (6, 0), (7, 0), (8, 0)),
                        string="KLMN",
                    ),
                    Strand(
                        positions=((0, 1), (1, 1), (2, 1), (3, 1)),
                        string="OPQR",
                    ),
                )
            ),
        )
    }

    assert solutions == expected


@pytest.mark.integration
def test_find_all_solutions_concatenated_spangram():
    grid = [
        ["A", "B", "C", "D", "E", "F", "G", "H"],
        ["I", "J", "K", "L", "M", "N", "O", "P"],
        ["Q", "R", "S", "T", "U", "V", "W", "X"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=3)

    # There is only one solution with 3 words:
    # {ABCDEFGH, IJKLMNOP, QRSTUVWX}
    # and it requires concatenating IJKL and MNOP to form the spangram

    finder = WordFinder(grid, dictionary={"ABCDEFGH", "IJKL", "MNOP", "QRSTUVWX"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    expected = {
        Solution(
            spangram=(
                Strand(
                    positions=(
                        (0, 1),
                        (1, 1),
                        (2, 1),
                        (3, 1),
                    ),
                    string="IJKL",
                ),
                Strand(
                    positions=(
                        (4, 1),
                        (5, 1),
                        (6, 1),
                        (7, 1),
                    ),
                    string="MNOP",
                ),
            ),
            non_spangram_strands=frozenset(
                (
                    Strand(
                        positions=(
                            (0, 0),
                            (1, 0),
                            (2, 0),
                            (3, 0),
                            (4, 0),
                            (5, 0),
                            (6, 0),
                            (7, 0),
                        ),
                        string="ABCDEFGH",
                    ),
                    Strand(
                        positions=(
                            (0, 2),
                            (1, 2),
                            (2, 2),
                            (3, 2),
                            (4, 2),
                            (5, 2),
                            (6, 2),
                            (7, 2),
                        ),
                        string="QRSTUVWX",
                    ),
                )
            ),
        )
    }
    assert solutions == expected


@pytest.mark.integration
def test_find_all_solutions_cant_concatenate_if_not_spangram():
    """Test that we don't concatenate words if they don't form a spangram."""
    grid = [
        list("ABCDEFGHKL"),
        list("MNOPQRSTJI"),
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=3)

    finder = WordFinder(grid, dictionary={"ABCD", "EFGH", "IJKL", "MNOPQRST"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # This puzzle is solvable with 4 words: {ABCD, EFGH, IJKL, MNOPQRST}
    # If it was allowed to concatenate ABCD + EFGH, then it could be solved in 3
    # But since ABCDEFGH is not a spangram, this is not allowed.
    # Hence, there are no solutions with 3 words.
    assert len(solutions) == 0


@pytest.mark.integration
def test_find_all_solutions_three_word_spangram():
    """Test that we can concatenate 3 words to form a spangram."""
    grid = [["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    # There is only one solution with 1 word: ABCDEFGHIJKL (spangram made from ABCD + EFGH + IJKL)
    # This requires concatenating 3 words to form the spangram

    finder = WordFinder(grid, dictionary={"ABCD", "EFGH", "IJKL"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    expected = {
        Solution(
            spangram=(
                Strand(
                    positions=(
                        (0, 0),
                        (1, 0),
                        (2, 0),
                        (3, 0),
                    ),
                    string="ABCD",
                ),
                Strand(
                    positions=(
                        (4, 0),
                        (5, 0),
                        (6, 0),
                        (7, 0),
                    ),
                    string="EFGH",
                ),
                Strand(
                    positions=(
                        (8, 0),
                        (9, 0),
                        (10, 0),
                        (11, 0),
                    ),
                    string="IJKL",
                ),
            ),
            non_spangram_strands=frozenset(),
        )
    }

    assert solutions == expected


@pytest.mark.integration
def test_find_all_solutions_four_word_spangram():
    """Test that we can concatenate 4 words to form a spangram."""
    grid = [
        ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P"]
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    # There is only one solution with 1 word: ABCDEFGHIJKLMNOP (spangram made from ABCD + EFGH + IJKL + MNOP)
    # This requires concatenating 4 words to form the spangram

    finder = WordFinder(grid, dictionary={"ABCD", "EFGH", "IJKL", "MNOP"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    expected = {
        Solution(
            spangram=(
                Strand(
                    positions=(
                        (0, 0),
                        (1, 0),
                        (2, 0),
                        (3, 0),
                    ),
                    string="ABCD",
                ),
                Strand(
                    positions=(
                        (4, 0),
                        (5, 0),
                        (6, 0),
                        (7, 0),
                    ),
                    string="EFGH",
                ),
                Strand(
                    positions=(
                        (8, 0),
                        (9, 0),
                        (10, 0),
                        (11, 0),
                    ),
                    string="IJKL",
                ),
                Strand(
                    positions=(
                        (12, 0),
                        (13, 0),
                        (14, 0),
                        (15, 0),
                    ),
                    string="MNOP",
                ),
            ),
            non_spangram_strands=frozenset(),
        )
    }

    assert solutions == expected


@pytest.mark.integration
def test_find_all_solutions_spangram_with_duplicate_word():
    """Edge case where the spangram is a concatenation of words where one word appears
    in multiple places in the grid (duplicate). Normally, this duplicate would get
    filtered out, but if it's part of a concatenated spangram, it should be kept."""
    grid = [
        ["A", "B"],
        ["A", "C"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    finder = WordFinder(grid, dictionary={"A", "B", "AC"}, min_length=1)
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    expected = Solution(
        # Spangram consisting of A + AC (A is a duplicate)
        spangram=(
            Strand(positions=((0, 0),), string="A"),
            Strand(positions=((0, 1), (1, 1)), string="AC"),
        ),
        non_spangram_strands=frozenset(
            (
                # Regular word B
                Strand(positions=((1, 0),), string="B"),
            )
        ),
    )

    assert expected in solutions


@pytest.mark.integration
def test_find_all_solutions_no_solutions_crossing():
    """Test that we don't find solutions where a strand crosses another strand."""
    # fmt: off
    grid = [
        ["C", "B"],
        ["A", "D"]
    ]
    # fmt: on
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    finder = WordFinder(grid, dictionary={"AB", "CD"}, min_length=2)
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    assert len(solutions) == 0


@pytest.mark.integration
def test_find_all_solutions_no_solutions_self_crossing():
    """Test that we don't find solutions where a strand crosses itself."""
    # fmt: off
    grid = [
        ["C", "B"],
        ["A", "D"]
    ]
    # fmt: on
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    finder = WordFinder(grid, dictionary={"ABCD"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    assert len(solutions) == 0


@pytest.mark.integration
def test_find_all_solutions_no_solutions_self_crossing_spangram():
    grid = [
        ["H", "G", "F", "S"],
        ["I", "D", "E", "T"],
        ["C", "J", "K", "L"],
        ["B", "Q", "R", "M"],
        ["A", "P", "O", "N"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    # {ABC, DEFGHI, JKLMNOPQR, ST} is a valid cover without any (self-)crossings
    # and there is only one solution with exactly 2 words, which is:
    # - ABC + DEFGHI + JKLMNOPQR (spangram)
    # - ST
    # but this would require a self-crossing in the spangram
    # (segments CD and IJ would cross)
    # so there are no valid solutions (unless we allow self-crossing spangrams)

    finder = WordFinder(
        grid, dictionary={"ABC", "DEFGHI", "JKLMNOPQR", "ST"}, min_length=2
    )
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()
    assert len(solutions) == 0


@pytest.mark.integration
def test_find_all_solutions_no_solutions_connecting_segment_crosses_strand():
    """Test that we don't find solutions where the connecting segment between two
    words of a concatenated spangram crosses another strand.

    The connecting segment is the implicit segment created when concatenating
    two strands - it goes from the last position of the first word to the first
    position of the second word.
    """
    grid = [
        ["A", "B", "C"],
        ["D", "E", "F"],
        ["G", "H", "I"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    # Words:
    # - CB: C(2,0) -> B(1,0) - ends at B(1,0)
    # - DGHI: D(0,1) -> G(0,2) -> H(1,2) -> I(2,2) - starts at D(0,1)
    # - AEF: A(0,0) -> E(1,1) -> F(2,1) - contains diagonal A->E
    finder = WordFinder(grid, dictionary={"CB", "DGHI", "AEF"}, min_length=2)
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Spangram CB+DGHI would create a crossing (B->D crosses AEF's A->E segment), so it
    # must be filtered out. Spangram CB+AEF is valid and should be found.
    assert len(solutions) >= 1
    for solution in solutions:
        spangram_words = {s.string for s in solution.spangram}
        assert spangram_words != {"CB", "DGHI"}, (
            "spangram CB+DGHI should be filtered out"
        )


@pytest.mark.integration
def test_find_all_solutions_no_solutions_spangram_max_words():
    """Test that we don't find solutions where the spangram consists of more than
    spangram_max_words words."""
    grid = [["A", "B", "C", "D"]]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    finder = WordFinder(grid, dictionary={"A", "B", "C", "D"}, min_length=1)
    spangram_finder = SpangramFinder(grid, num_words=1, spangram_max_words=3)
    solver = Solver(puzzle, finder=finder, spangram_finder=spangram_finder)
    solutions = solver.find_all_solutions()
    assert len(solutions) == 0


@pytest.mark.integration
def test_find_all_solutions_no_equivalent_solutions_traversal_order():
    """Test that equivalent solutions (same cells, different traversal order) are
    deduplicated."""
    # Grid where "SPPT" can be spelled via two different paths through the same cells:
    # Path 1: S(0,0) → P(1,0) → P(0,1) → T(1,1)
    # Path 2: S(0,0) → P(0,1) → P(1,0) → T(1,1)
    grid = [
        ["S", "P"],
        ["P", "T"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    finder = WordFinder(grid, dictionary={"SPPT"})
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Should find exactly 1 solution, not 2 equivalent ones
    assert len(solutions) == 1

    # Verify the solution covers all cells
    solution = list(solutions)[0]
    all_positions = set()
    for strand in solution.spangram:
        all_positions.update(strand.positions)
    assert all_positions == {(0, 0), (1, 0), (0, 1), (1, 1)}


@pytest.mark.integration
def test_find_all_solutions_no_equivalent_solutions_spangram_split():
    """Test that equivalent solutions (same spangram cells, different word splits) are
    deduplicated.

    E.g. spangram TRETS+LOBS vs TRET+SLOBS both cover the same cells and spell the same
    concatenated string, so they should be deduplicated.
    """
    # Grid: A B C D E F G H (single row, 8 columns)
    # Two valid covers: {ABCD, EFGH} and {AB, CDEFGH}
    # Both can form spangram ABCDEFGH via concatenation
    # But they're equivalent (same cells, same concatenated string)
    grid = [["A", "B", "C", "D", "E", "F", "G", "H"]]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=1)

    finder = WordFinder(grid, dictionary={"ABCD", "EFGH", "AB", "CDEFGH"}, min_length=2)
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Should find exactly 1 solution (ABCD+EFGH and AB+CDEFGH are equivalent)
    assert len(solutions) == 1

    # Verify the spangram covers all cells
    solution = list(solutions)[0]
    spangram_positions = set()
    for strand in solution.spangram:
        spangram_positions.update(strand.positions)
    assert spangram_positions == {(i, 0) for i in range(8)}


@pytest.mark.integration
def test_find_all_solutions_spangram_with_short_word():
    """Test that short words (< 4 letters) can be part of a spangram concatenation.

    Short words should be automatically found for spangram consideration, even when
    the default min_length=4 is used for regular words. They should only be allowed
    as part of a concatenated spangram, not as standalone words.
    """
    # Grid: A B C | D E F
    #       G H I | J K L
    # The spangram could be ABC + DEF (spans top row from left to right)
    # Non-spangram words: GHIJKL (bottom row)
    grid = [
        ["A", "B", "C", "D", "E", "F"],
        ["G", "H", "I", "J", "K", "L"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    # ABC is a short word (3 letters) that should only be part of the spangram
    # DEF is also short (3 letters)
    # GHIJKL is a regular word (6 letters)
    # The solver should automatically find short words for spangram consideration
    finder = WordFinder(
        grid, dictionary={"ABC", "DEF", "GHIJKL"}
    )  # default min_length=4
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Should find exactly 1 solution with the short words concatenated as spangram
    assert len(solutions) >= 1

    expected = Solution(
        spangram=(
            Strand(positions=((0, 0), (1, 0), (2, 0)), string="ABC"),
            Strand(positions=((3, 0), (4, 0), (5, 0)), string="DEF"),
        ),
        non_spangram_strands=frozenset(
            (
                Strand(
                    positions=((0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1)),
                    string="GHIJKL",
                ),
            )
        ),
    )
    assert expected in solutions


@pytest.mark.integration
def test_find_all_solutions_short_word_not_standalone():
    """Test that short words cannot appear as standalone non-spangram words.

    A short word (< 4 letters) can only be used if it's part of a concatenated
    spangram. If a cover would require a short word as a standalone non-spangram
    word, that cover should be rejected (no valid solution can be formed from it).
    """
    # Grid: A B C D E F
    #       G H I J K L
    # Dictionary has:
    # - ABC (short, 3 letters)
    # - DEF (short, 3 letters)
    # - GHIJKL (regular, 6 letters)
    # - ABCDEF (can be used as full spangram)
    #
    # There are two possible covers:
    # 1. {ABCDEF, GHIJKL} - valid solution with ABCDEF as spangram
    # 2. {ABC, DEF, GHIJKL} - would require ABC or DEF as standalone non-spangram
    #
    # Only cover 1 should produce a valid solution, or cover 2 with ABC+DEF
    # concatenated as spangram.
    grid = [
        ["A", "B", "C", "D", "E", "F"],
        ["G", "H", "I", "J", "K", "L"],
    ]
    puzzle = Puzzle(name="test", theme="test", grid=grid, num_words=2)

    finder = WordFinder(
        grid, dictionary={"ABC", "DEF", "GHIJKL", "ABCDEF"}, min_length=1
    )
    solver = Solver(puzzle, finder=finder)
    solutions = solver.find_all_solutions()

    # Should find solutions
    assert len(solutions) >= 1

    # All solutions should have no short words as non-spangram strands
    for solution in solutions:
        for strand in solution.non_spangram_strands:
            assert len(strand.string) >= 4, (
                f"Short word '{strand.string}' should not appear as non-spangram"
            )

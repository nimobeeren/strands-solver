from strands_solver.common import Puzzle, Solution, Strand
from strands_solver.solver import Solver
from strands_solver.spangram_finder import SpangramFinder
from strands_solver.word_finder import WordFinder


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

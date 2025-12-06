from strands_solver.common import Solution, Strand
from strands_solver.ranker import Ranker


def test_find_best():
    ranker = Ranker()
    # Has a spangram consisting of two concatenated (strands)
    solution1 = Solution(
        spangram=(
            Strand(positions=((0, 0),), string="A"),
            Strand(positions=((1, 0),), string="B"),
        ),
        non_spangram_strands=frozenset({Strand(positions=((2, 0),), string="C")}),
    )
    # Has a spangram consisting of a single strand
    solution2 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0)), string="AB"),),
        non_spangram_strands=frozenset({Strand(positions=((2, 0),), string="C")}),
    )

    # Solution 2 has a spangram consisting of the least strands so it is best
    best = ranker.find_best({solution1, solution2})
    assert best == solution2

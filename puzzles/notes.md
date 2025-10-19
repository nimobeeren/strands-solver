2025-10-03 is one of the easier puzzles to solve since its solution has a spangram consisting of a single word and it contains relatively few (1294) words of length 4 or more.

2025-09-15 contains a spangram consisting of two concatenated words: TAROT + CARDS. But the words CARDS can be formed in two different ways (we call this a duplicate). Since we remove these duplicates as an optimization, the correct solution is not found. The test `test_solve_spangram_with_duplicate_word` in `solver_test.py` fails due to this issue (currently skipped).

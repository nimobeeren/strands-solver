# Estimating complexity of backtracking algorithms
_Exported on 12/12/2025 at 23:28:12 GMT+1 from Cursor (2.2.20)_

---

**User**

how do i estimate the computational complexity of a backtracking algorithm?

---

**Cursor**

### Short answer
- Worst-case time is usually exponential. A common upper bound is O(b^d), where:
  - b = maximum branching factor (choices per step)
  - d = maximum depth (steps until a complete solution)
- Tighter bounds come from counting the number of states actually explored, using constraints/pruning to reduce b, and considering duplicates/symmetries.
- Practical complexity is best estimated by combining a theoretical upper bound with empirical node counts from instrumented runs.

### How to estimate systematically
1. Define the search tree
   - **State**: what a node represents.
   - **Branching factor (b)**: max number of children per node.
   - **Depth (d)**: max number of decisions until a terminal state.

2. Compute simple upper bound
   - **Tree-size bound**: 1 + b + b^2 + … + b^d = O(b^d).
   - If b varies by level i, use ∏_{i=1..d} b_i.

3. Use combinatorial counts for tighter bounds
   - Replace b^d with a direct count of candidates at each level.
   - Examples: choose-k positions → C(n, k); permutations → n!, partial permutations → P(n, k) = n!/(n−k)!.
   - Apply approximations (e.g., Stirling) to simplify n!, C(n, k).

4. Account for pruning and constraints
   - **Constraint propagation** reduces effective branching b_eff(i) at level i.
   - **Early failure probability**: If a fraction p_i of nodes at level i are cut, expected nodes ≈ ∏_{i}( (1 − p_i) b_i ).
   - **Bounding functions (branch-and-bound)**: Only nodes with bound ≥ current best survive.

5. Handle duplicates/symmetry
   - **Memoization/visited set**: bound by number of reachable distinct states N, so time ≤ O(N + edges).
   - **Symmetry breaking**: divide state count by symmetry group size when valid.

6. Recurrence formulation (when structure depends on subproblems)
   - Write T(n) = Σ_j T(n_j) + O(1) based on how choices shrink the problem.
   - Solve/upper-bound using:
     - Dominant branch (if one choice shrinks slowest)
     - Measure-and-conquer: define a weighted size measure that decreases each step to get T(n) ≤ c^n.

7. Best/average/worst cases
   - **Worst**: no pruning help → exponential upper bound.
   - **Average**: model random pruning; use expected b_eff.
   - **Best**: heuristic finds solution early → near O(d) nodes.

8. Empirical estimation (highly recommended)
   - Instrument the solver to count:
     - total nodes visited, per-depth node counts, prune rates, branching distributions.
   - Fit observed nodes vs. problem size n to c^n (log-linear fit) or to combinatorial model parameters.
   - Compare different heuristics by their effective c.

### Quick examples
- N-Queens: naive ≈ O(n!) (placing queens per column). With pruning/diagonals, effective base c < n; empirically ≈ O(c^n) with c ≈ 1.5–2 for good heuristics.
- Sudoku: worst-case exponential in number of blanks k; with constraint propagation, practical growth ~ O(c^k) with small c.
- Subset sum: backtracking ≈ O(2^n), pruning via bounds reduces c.

### Practical tips
- Prefer counting states over depth-branching when constraints dominate.
- Use measure-and-conquer: pick a size measure that drops more when “hard” moves are made to prove smaller c.
- Always validate with instrumentation; report both theoretical bound and observed node growth.

If you want, I can add lightweight instrumentation to your solver to log per-depth branching and prune rates, then fit c from runs on your `puzzles/` set.

---

**User**

how would you estimate my algo in @solver.py? start simple and add more nuance after

---

**Cursor**

### Simple view (big picture)
- **Overall time**: Exponential. Two phases:
  - Candidate generation (find all words in the grid)
  - Backtracking over subsets of those words to cover the grid

- Rough worst-case: O(candidate_generation + 2^M), where M = number of candidate words found.

### Where this comes from in your code
```43:63:/Users/nimo.beeren/Development/strands-solver/solver.py
def solve(
    self, *, words: list[Strand] | None = None, used_words: list[Strand] = []
) -> list[Strand] | None:
    """Solve the puzzle by choosing from `words` and using at least the words in
    `used_words`. If `words` is not provided, will find all words in the grid first."""
    if self.is_valid_solution(used_words):
        return used_words

    if words is None:
        words = self.find_all_words()
        print(f"Found {len(words)} words")

    for i, word in enumerate(words):
        if any(uw.overlaps(word) for uw in used_words):
            continue  # word overlaps with a used word
        words_to_try = words[i + 1 :]  # don't try words we've already tried
        solution = self.solve(words=words_to_try, used_words=used_words + [word])
        if solution is not None:
            return solution

    return None
```

```75:83:/Users/nimo.beeren/Development/strands-solver/solver.py
def find_all_words(self) -> list[Strand]:
    """Finds all strands forming words in the grid."""
    words: list[Strand] = []
    for x in range(self.cols):
        for y in range(self.rows):
            words += self.find_words(current_pos=(x, y))
    return words
```

```101:121:/Users/nimo.beeren/Development/strands-solver/solver.py
if not self.is_word_prefix(candidate.string):
    return words

if len(candidate.string) >= min_length and self.is_word(candidate.string):
    print(f"Found word: {candidate.string}")
    words.append(candidate)

for dir in Direction:
    dx, dy = dir.value
    next_x, next_y = (x + dx, y + dy)

    if next_x < 0 or next_x >= self.cols or next_y < 0 or next_y >= self.rows:
        continue  # next position is out of bounds
    if (next_x, next_y) in candidate.positions:
        continue  # next position overlaps

    words += self.find_words(
        current_pos=(next_x, next_y),
        prefix=candidate,
        min_length=min_length,
    )
```

### More nuance

- Candidate generation (`find_all_words`):
  - Each start cell expands to up to 8 directions, and paths cannot revisit cells.
  - Upper bound on length‑k paths from one start: 8·7^(k−1). With a grid of N = rows·cols cells, k ≤ N, so a very loose worst-case is O(N·7^N).
  - Strong pruning from `is_word_prefix` makes the real count far smaller: actual cost ≈ number_of_prefixes_examined × (O(log W) for the bisect prefix check + O(1) set check), where W = |dictionary|.
  - In practice this phase behaves like O(C · log W), where C is the number of dictionary prefixes that appear along self-avoiding walks in the grid.

- Backtracking (`solve`):
  - You try combinations without reordering (`words[i+1:]`), so the search over non-overlapping words is a subset search.
  - Worst-case nodes ≈ sum_k C(M, k) = O(2^M), where M = number of candidate words.
  - Early pruning:
    - Overlap filter prunes many branches.
    - Depth is bounded by total coverage: since each word length ≥ 4, recursion depth ≤ N/4.
    - The terminal check `is_valid_solution` costs O(N · |used_words|) per hit; this is small relative to the exponential branching unless N is large.

- Space:
  - Candidate generation uses recursion depth up to word length (≤ N).
  - Backtracking holds a path of up to N/4 words. So O(N) stack/auxiliary.

### Tighter, problem-shaped bounds

- Candidate enumeration:
  - Let b_eff(k) be the average number of valid next letters at depth k after prefix pruning. Then expected nodes ≈ Σ_k ∏_{i=1..k} b_eff(i) over k up to max word length.
  - With real English dictionaries, b_eff quickly drops, so enumeration often looks like O(c1^N) with c1 much smaller than 7, sometimes sub-exponential on small grids.

- Subset search:
  - Let r be the fraction of pairs that overlap; higher r shrinks the independent set size.
  - If the conflict graph among words is dense, effective search size is closer to the number of maximal independent sets (Moon–Moser bound ~ O(3^{M/3})) but typically far less in practice due to coverage constraint.
  - A practical upper bound remains O(2^M), but effective base often looks like O(c2^M) with c2 << 2.

### Quick practical estimation for your runs
- Measure:
  - C = number of prefixes visited during `find_all_words`
  - M = number of words found
  - Nodes_solve = number of recursive calls in `solve`
- Then report:
  - Candidate phase ≈ C · (const + log W)
  - Solve phase ≈ Nodes_solve
  - Fit Nodes_solve vs. M across puzzles to an exponential c2^M (log-linear fit) and report c2.

If you want, I can add lightweight counters around `find_words` and the `solve` recursion to print C, M, and Nodes_solve for a few puzzles so you get concrete c1 and c2 estimates.

```python
def solve(
    self, *, words: list[Strand] | None = None, used_words: list[Strand] = []
) -> list[Strand] | None:
    """Solve the puzzle by choosing from `words` and using at least the words in
    `used_words`. If `words` is not provided, will find all words in the grid first."""
    if self.is_valid_solution(used_words):
        return used_words

    if words is None:
        words = self.find_all_words()
        print(f"Found {len(words)} words")

    for i, word in enumerate(words):
        if any(uw.overlaps(word) for uw in used_words):
            continue  # word overlaps with a used word
        words_to_try = words[i + 1 :]  # don't try words we've already tried
        solution = self.solve(words=words_to_try, used_words=used_words + [word])
        if solution is not None:
            return solution

    return None
```

```python
def find_all_words(self) -> list[Strand]:
    """Finds all strands forming words in the grid."""
    words: list[Strand] = []
    for x in range(self.cols):
        for y in range(self.rows):
            words += self.find_words(current_pos=(x, y))
    return words
```

```python
if not self.is_word_prefix(candidate.string):
    return words

if len(candidate.string) >= min_length and self.is_word(candidate.string):
    print(f"Found word: {candidate.string}")
    words.append(candidate)

for dir in Direction:
    dx, dy = dir.value
    next_x, next_y = (x + dx, y + dy)

    if next_x < 0 or next_x >= self.cols or next_y < 0 or next_y >= self.rows:
        continue  # next position is out of bounds
    if (next_x, next_y) in candidate.positions:
        continue  # next position overlaps

    words += self.find_words(
        current_pos=(next_x, next_y),
        prefix=candidate,
        min_length=min_length,
    )
```

---

**User**

can you clarify why O(2^M)? Based on your first answer I thought b = M and d = N/4 since we can choose from M words at each step and the solution contains at most N/4 words. Assuming N is number of cells (rows x cols) and M is number of candidate words.

---

**Cursor**

### Key point
- Your recursion explores subsets of the M candidates (combinations, not ordered sequences). The natural upper bound is O(2^M), not O(M^(N/4)).

### Why it’s 2^M
- Think of processing the candidate list left-to-right. For each word, there are two conceptual choices: skip it or include it (if non-overlapping with the current set). This yields at most 2^M branches overall.
- Your implementation enforces “combinations” via `words[i+1:]` (strictly increasing indices). Skips are realized by the loop moving i forward; includes are realized by the recursive call with `used_words + [word]`. Enumerating all include/skip patterns over M items gives 2^M potential subsets.
- Overlap constraints only cut branches, so they can’t increase the count above 2^M.

### Why b = M, d = N/4 is not appropriate here
- That assumes:
  - order matters (it doesn’t: you constrain to increasing indices),
  - choices are with replacement (they aren’t: each word can be used at most once),
  - branching stays ~M at every level (it shrinks as i increases and due to overlaps).
- The “depth ≤ N/4” cap is real (min word length 4), but combining it with a fixed b=M yields an over-loose M^(N/4).
- A tighter combinatorial cap that respects “choose at most N/4 words” is:
  - sum_{k=0..N/4} C(M, k) ≤ 2^M.
  - If N/4 ≪ M, this is much smaller than 2^M; asymptotically it’s about 2^{H(α)·M} with α = (N/4)/M and H the binary entropy.

### Clean bounds to remember
- Worst-case backtracking nodes: ≤ 2^M.
- With depth cap: ≤ Σ_{k=0}^{min(M, N/4)} C(M, k).
- Practical complexity is lower due to overlaps and early coverage failure.

If helpful, I can instrument `solve` to count explored nodes and per-depth choices, then we can fit an empirical base c where nodes ≈ c^M and compare puzzles.

---

**User**

The puzzles I want to solve have N = 48 and M ~= 2000. What are some ways I could improve my algorithm in @solver.py to make this tractable? Think about different angles, start with the simplest/closest to my current algo and give 2 better options if they exist.

---

**Cursor**

### TL;DR
- With N=48 and M≈2000, treat selection as an exact-cover of cells by disjoint strands.
- Easiest big win: keep your current structure but switch to bitmasks + “pick the most constrained cell first”.
- Two stronger options: (1) Knuth’s Algorithm X with Dancing Links (DLX), (2) a tiny MILP/CP-SAT model. Both are very fast at this size.

### Closest to your current algorithm (simple to adopt, big payoff)
Replace subset search over words with an exact-cover style search driven by cells, and use bitsets:
- Represent coverage
  - Map each cell to a bit index i in [0, N).
  - For each candidate word j, precompute `mask[j]` (64-bit int; N=48 fits).
  - Keep `covered_mask`; a word is compatible iff `(mask[j] & covered_mask) == 0`.
- Pick next decision by cell, not by word (MRV heuristic)
  - Among uncovered cells, choose cell c with the fewest compatible words.
  - Try only words that cover c and don’t overlap `covered_mask`. This collapses branching drastically.
- Fast checks and pruning
  - Done when `covered_mask == full_mask`.
  - If any uncovered cell has zero compatible words, backtrack immediately.
  - Optional bound: let R = popcount(~covered_mask & full_mask), Lmax = max remaining word length; if current_depth + ceil(R / Lmax) > best_bound, prune.
- Precompute for speed
  - `candidates_by_cell[c] = [j | c in mask[j]]`.
  - Sort each list by a helpful heuristic (e.g., longer words first, or those covering other rare cells).
- Why this helps
  - You stop exploring arbitrary include/skip patterns and instead solve the constrained column first (classic exact-cover heuristic).
  - Bit operations make overlap/coverage O(1).

Example sketch for the core loop:
```python
def search(covered_mask):
    if covered_mask == full_mask:
        return True
    c = pick_uncovered_cell_with_fewest_options(covered_mask)
    for j in compatible_candidates(c, covered_mask):
        if search(covered_mask | mask[j]):
            take(j); return True
    return False
```

### Better option 1: Algorithm X / Dancing Links (DLX)
- Model: 48 primary columns (cells). Each candidate word = a row with 1s in the cells it covers.
- Goal: choose rows so every column is covered exactly once.
- DLX dynamically maintains column/row links and always chooses the smallest column next (MRV built-in), which is extremely effective.
- Scale: 48 columns, ~2000 rows is well within the sweet spot; DLX is typically lightning fast here.
- Pros: very fast backtracking with minimal overhead; finds all solutions if needed.
- Cons: a bit more code to implement than the bitset approach.

### Better option 2: MILP/CP-SAT
- Variables: x_j ∈ {0,1} for each candidate word j.
- Constraints: for each cell i, Σ_{j covers i} x_j = 1 (exact cover).
- Objective: none (feasibility). Or optionally minimize number of words or lexicographic tie-breakers.
- Tools: OR-Tools CP-SAT, PuLP with CBC/HiGHS, or Pyomo. With 48 constraints and 2000 binaries, modern solvers typically solve in milliseconds–seconds.
- Pros: easiest to get right, robust, you get proofs of infeasibility; adding extra constraints is trivial.
- Cons: external dependency; black-box (less control over branching).

### Extra (optional) speedups, orthogonal to the above
- Faster prefix checks: switch `is_word_prefix` from bisect on a sorted list to a trie to reduce candidate enumeration time.
- Dedupe identical coverage: if multiple different strings produce the exact same cell mask, keep one representative; it cuts symmetric choices without removing any covering possibility.
- Cap word length if puzzle rules allow (e.g., ignore words > L_max).
- Pre-sort cells by frequency: compute how many candidates cover each cell; start with the rarest cell to maximize pruning from the first step.

If you want, I can implement the bitset + “pick most constrained cell” search inside `solver.py` (minimal changes, preserves your current structure). Or I can add a clean DLX/CP-SAT path side-by-side so you can compare.

```python
def search(covered_mask):
    if covered_mask == full_mask:
        return True
    c = pick_uncovered_cell_with_fewest_options(covered_mask)
    for j in compatible_candidates(c, covered_mask):
        if search(covered_mask | mask[j]):
            take(j); return True
    return False
```

---

**User**

what is MRV in this context?

---

**Cursor**

**MRV** stands for **Minimum Remaining Values**.  
It’s a classic heuristic from constraint satisfaction problems (CSPs), often called the “most constrained variable” heuristic.

### In this context (grid covering with words):

- **Variables**: The grid cells that need to be covered.
- **Values**: The candidate words that can cover each cell.

**MRV means:**  
> At each step, pick the cell that has the fewest possible candidate words left that could cover it.

#### Why is this good?
- If a cell has only one or two possible words that can cover it, you want to decide on those first. If you leave them for later, you might make choices that block all options for that cell, leading to dead ends deeper in the search.
- By always picking the “most constrained” cell (the one with the minimum remaining values), you maximize the chance of early pruning and reduce wasted search.

#### Example
Suppose you have a 6x8 grid (N=48), and after filtering, cell (2,3) can only be covered by 2 words, while cell (5,5) can be covered by 20 words.  
**MRV says:** Try to cover (2,3) first, using one of its 2 words, before making choices for less-constrained cells.

#### In code
- For each uncovered cell, count how many candidate words could cover it (and don’t overlap with already chosen words).
- Pick the cell with the smallest count.
- Try all possible words for that cell recursively.

#### Summary
**MRV = “pick the cell with the fewest options left.”**  
It’s a powerful way to make backtracking/covering algorithms much faster, especially when some cells are much harder to cover than others.


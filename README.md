# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Prerequisites

- Install the [uv](https://docs.astral.sh/uv/) package manager.
- (Optional) Set the `GEMINI_API_KEY` environment variable to a valid [Gemini API key](https://ai.google.dev/gemini-api/docs/api-key). A free tier key is sufficient for solving puzzles, though it may take longer due to rate limits. Using a paid tier key is faster but incurs a tiny cost: typically $0.00001–$0.0001 per puzzle.

> [!NOTE]
> Without a `GEMINI_API_KEY` the solver will try to find valid solutions but it can't accurately determine which solution is best.

## Basic Usage

```bash
uvx strands-solver solve today                # solve today's puzzle
uvx strands-solver solve YYYY-MM-DD           # solve another day's puzzle
uvx strands-solver solve path_to_puzzle.json  # solve puzzle from a file
```

See also [Advanced Usage](#advanced-usage).

## Goal

This program attempts to solve Strands puzzles in one shot, i.e. without a way to iteratively determine whether the chosen words are correct or not.

More precisely, given

- a rectangular grid of letters
- a phrase describing a theme
- a number specifying the number of words (or, more accurately: strands) in the solution

the solver attempts to find the set of _strands_ (sequences of adjacent letters in the grid) for which

- the number of strands matches the given number of words
- every letter in the grid is covered exactly once
- every strand is at least 4 letters long
- there is at least one strand (called the _spangram_) which spans the entire grid vertically or horizontally
- every strand spells out a valid word (though the spangram may be a concatenation of multiple words)
- all strands are maximally related to the theme (in a semantic, possibly cryptic way)

### Example

This is the puzzle of 2025-10-03:

```
Theme: Who's in charge?

 A     M     E     L     S     S

 N     A     A     F     E     O

 G     E     R     D     I     B

 E     A     D     E     H     S

 O     H     R     C     I     O

 R     T     C     S     V     R

 D     E     P     H     R     S

 I     R     I     E     P     U

Number of words: 7
```

The goal is then to find this solution:

<img alt="The same grid of letters as earlier, with the word LEADERSHIP highlighted in yellow and the words BOSS, CHIEF, DIRECTOR, MANAGE, SUPERVISOR and HEARD highlighted in blue." src="./assets/example_solution.png" width="300" />

where the strands are

```
🟡 LEADERSHIP (spangram)
🔵 BOSS
🔵 CHIEF
🔵 DIRECTOR
🔵 MANAGER
🔵 SUPERVISOR
🔵 HEAD
```

This is the "correct" solution as provided by the New York Times. There are other valid solutions, but they don't match the theme quite as well.

## Results

The solver has been validated and benchmarked on a set of official puzzles. Currently, it solves a subset of puzzles correctly. Results are recorded in [`results.md`](./results.md), which includes a summary and results for each puzzle.

## Limitations

- Some puzzles can't be solved in a reasonable amount of time (see [results](./results.md)).
- The solver will only find a solution if the spangram is a single word or a concatenation of words which are each 4 letters or longer. In reality, the words in a concatenated spangram may be shorter than 4 letters.
- The solver usually finds multiple solutions but it doesn't always choose the solution that best fits the theme.
- The solver will not find solutions where the spangram contains a contraction (like YOURE), which does appear in real solutions.
- The dictionary ([`dictionary.py`](./src/strands_solver/dictionary.py)) uses the [ENABLE1](https://rressler.quarto.pub/i_data_sets/data_word_lists.html) word list, which is comprehensive but may occasionally miss some valid words or include uncommon ones. This may cause the solver to fail to find a valid solution.

Some ideas for tackling these limitations are listed in [IDEAS.md](./IDEAS.md).

## Advanced Usage

The CLI provides four commands: `solve`, `show`, `benchmark`, and `embed`.

### `solve`

Solve a Strands puzzle.

```bash
uvx strands-solver solve today                 # solve today's puzzle
uvx strands-solver solve YYYY-MM-DD            # solve another day's puzzle
uvx strands-solver solve path_to_puzzle.json   # solve puzzle from a file
uvx strands-solver solve today -o ./solutions  # write all solutions to a directory
```

### `show`

Display the official solution for a puzzle from the NY Times API (not used for solving).

```bash
uvx strands-solver show today
uvx strands-solver show YYYY-MM-DD
```

### `benchmark`

Benchmark the solver against a set of puzzles. A report of the results is saved to a Markdown file.

```bash
uvx strands-solver benchmark                              # default: 2025-09-01 to 2025-12-31
uvx strands-solver benchmark -s 2025-10-01 -e 2025-10-31  # custom date range
uvx strands-solver benchmark -t 30                        # 30 second timeout per puzzle
uvx strands-solver benchmark -r ./my_results.md           # custom report file
```

### `embed`

The solver uses semantic embeddings to determine which solution best fits the theme. These embeddings are
generated while solving a puzzle and cached for future re-use. However, when solving many puzzles (such as when
running a benchmark), you may run into rate limits for the embedding API. To avoid this, you can generate
embeddings ahead of time.

Embedding the entire dictionary costs about $0.10 and takes about 60 minutes on a paid (Tier 1) Gemini project
(based on 2025-12-30 pricing and rate limits). While it's technically possible to do on the free tier, this would
take a very long time due to rate limits. Storing the embeddings database also uses about 2 GB of disk space.

To generate dictionary embeddings:

```bash
uvx strands-solver embed           # embed words not already cached
uvx strands-solver embed --reload  # re-embed all words
```

The embeddings database is stored in the user cache directory (`~/.cache/strands-solver/embeddings.db` on Linux, `~/Library/Caches/strands-solver/embeddings.db` on macOS, `%LOCALAPPDATA%\strands-solver\Cache\embeddings.db` on Windows).

## How It Works

The solver finds solutions using a 4-phase algorithm:

1. [`WordFinder`](./src/strands_solver/word_finder.py) — Find all strands in the grid that spell dictionary words. Starting from each cell, recursively take a step in all directions (using [DFS](https://en.wikipedia.org/wiki/Depth-first_search)), stopping if there is no word in the dictionary which starts with the strand so far.

   > [!TIP]
   > While legal, official solutions never _require_ a strand to cross itself. Therefore, we filter out self-crossing strands during word finding. This optimization reduces the total number of words and primarily speeds up following phases.

2. [`GridCoverer`](./src/strands_solver/grid_coverer.py) — Find all ways to cover all cells of the grid exactly once using a subset of the words found in phase 1. This is an [exact cover](https://en.wikipedia.org/wiki/Exact_cover) problem solved with a backtracking algorithm that uses the [MRV (Minimum Remaining Values)](https://cs50.harvard.edu/extension/ai/2020/fall/notes/3/#backtracking-search) heuristic: always branch on the cell with the fewest covering strands.

   > [!TIP]
   > Official solutions never contain strands that cross each other. Therefore, we prevent this during covering. This optimization speeds up the covering phase by pruning branches early.

3. [`SpangramFinder`](./src/strands_solver/spangram_finder.py) — Filter covers found in phase 2 to those containing a spangram. If the cover has more strands than the word count specified in the puzzle, try concatenating adjacent strands to form the spangram.

   > [!TIP]
   > Words that appear in multiple places in the grid (duplicates) can never be part of the solution, unless they are part of the spangram (concatenated with other words). Therefore, if a cover contains such a duplicate, we force it to be part of the spangram. This optimization speeds up spangram finding by reducing the number of concatenation combinations to try.

4. [`SolutionRanker`](./src/strands_solver/solution_ranker.py) — Rank solutions found in phase 3 by semantic similarity between words in the solution and the theme. Compute [embeddings](https://en.wikipedia.org/wiki/Word_embedding) for all words and the theme, then score each solution by the average pairwise [cosine similarity](https://en.wikipedia.org/wiki/Cosine_similarity) between its words and the theme.

   > [!TIP]
   > Embeddings are cached on disk to reduce costs. Since we only embed single words from the dictionary and themes from puzzles, the total embedding cost is bounded (see [`embed`](#embed) usage).

The main orchestration logic is in [`Solver`](./src/strands_solver/solver.py).

## How It Was Made

I started this project to try out modern coding agents on a non-trivial but easy to validate problem. I expected a little vibe-coding would get me most of the way there, but the problem proved to be a lot more challenging than I thought! Along the way though, I learned to collaborate with my coding agent in a way that truly extended my abilities.

My first idea was simple. First, I'd find all words in the grid by looking at each cell and taking steps in all directions, stopping if it was not a valid prefix of a word in the dictionary. Then, to cover the grid I'd just try all combinations of found words, ignoring combinations where words overlap (which I assumed would often be the case). The word finding worked first try, but the covering was extremely slow. It just never completed.

To find out why, I asked my coding agent for help. I have some basic knowledge of complexity analysis, but I first wanted to refresh my memory. I prompted:

> how do i estimate the computational complexity of a backtracking algorithm?

After grasping the basics, I asked:

> how would you estimate my algo in @solver.py? start simple and add more nuance after

It explained that my algo had a worst-case complexity of $O(2^M)$ with $M$ being the number of candidate words (typically 1000-2000). This was completely infeasible!

So let's make it faster!

> The puzzles I want to solve have N = 48 and M ~= 2000. What are some ways I could improve my algorithm in @solver.py to make this tractable? Think about different angles, start with the simplest/closest to my current algo and give 2 better options if they exist.

It gave me three options for algorithms, none of which I had ever heard of. It explained that the worst-case complexity was still exponential (as the problem is NP-complete), but that we could massively speed things up by always picking the cell with the smallest number of strands covering it, and recurse from there (a heuristic called MRV).

Of course I asked it to implement the new algo, and it worked! I was now able to cover the grid in just a few minutes for most puzzles. (I did lose the chat history for this step, unfortunately.)

I was really happy with this workflow. My coding agent could look at my code, suggest improvements I never would have thought of, implement them and make huge performance gains. I did end up rewriting some of the code to better fit my mental model and to fully understand it, as I found this was necessary to keep making improvements. But here too the agent was invaluable in helping me understand the existing code.

> [!TIP]
> I've added an [export of my chat](./assets/cursor_algo_analysis.md) where I asked for analysis and algo suggestions.

## Development

### Running locally

Clone the repository and run:

```bash
uv run strands-solver
```

> [!NOTE]
> `uvx` runs the latest _published_ version, which doesn't include your local changes.

### Tests

```bash
uv run pytest         # unit + integration tests
uv run pytest -m e2e  # end-to-end tests
```

We have three types of tests:

- **Unit tests** (`tests/unit/`) are fast and reliable because they test individual components.
- **Integration tests** (`tests/integration/`) test multiple components together but have no external dependencies.
- **End-to-end tests** (`tests/e2e/`) run the full application through the CLI, relying on external APIs.

By default, end-to-end tests are skipped because they are slower and could fail if an external API changes/fails.

### Type Checking

```bash
uv run pyright
```

### Formatting

```bash
uv run ruff format
```

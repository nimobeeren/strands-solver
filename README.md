# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Installation

Install the [uv](https://docs.astral.sh/uv/) package manager.

The dictionary will be automatically downloaded on first use.

## Usage

To solve today's puzzle:

```bash
uv run strands-solver today
```

To solve a puzzle from a given date:

```bash
uv run strands-solver 2025-11-30
```

To solve a puzzle from a JSON file:

```bash
uv run strands-solver path_to_puzzle.json
```

See `puzzles/` for the expected structure of the puzzle JSON file.

## Limitations

- Some puzzles take a very long time to solve (see [notes.md](./puzzles/notes.md)).
- The solver usually finds multiple solutions but it can't determine which one fits the theme best.
- The solver will only find a solution if the spangram is a single word or a concatenation of words which are each 4 letters or longer. In reality, the words in the spangram may be shorter than 4 letters.
- The solver will not find solutions where the spangram contains a contraction (like YOURE), which does appear in real solutions.
- The dictionary (`dictionary.py`) uses the [ENABLE1](https://rressler.quarto.pub/i_data_sets/data_word_lists.html) word list, which is comprehensive but may occasionally miss some valid words or include uncommon ones. This may cause the solver to fail to find a valid solution.

## Development

### Tests

```bash
uv run pytest
```

### Type checking

```bash
uv run pyright
```

### Formatting

```bash
uv run ruff format
```

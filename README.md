# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Installation

Install the [uv](https://docs.astral.sh/uv/) package manager.

The dictionary will be automatically downloaded on first use.

## Usage

1. Take a screenshot of the puzzle.

2. Recognize the puzzle grid and theme and save them to a JSON file:

```bash
uv run strands-ocr path_to_puzzle.jpeg path_to_puzzle.json
```

Note: the defaults are tuned for iPhone 15 screenshots. All spatial parameters are relative to image height (0.0=top, 1.0=bottom), making them resolution-independent. For other devices or layouts, you may need to adjust the `--tile-size`, `--origin-x`, and `--origin-y` parameters. Run `uv run strands-ocr --help` for more information.

3. Run the solver:

```bash
uv run strands-solver path_to_puzzle.json
```

## Limitations

- The solver may find multiple solutions but it can't determine which one fits the theme best.
- The solver will only find a solution if the spangram is a single word or a concatenation of words which are each 4 letters or longer. In reality, the words in the spangram may be shorter than 4 letters.
- The solver will not find solutions where the spangram contains a contraction (like YOURE), which does appear in real solutions.
- The dictionary (`dictionary.py`) uses the [ENABLE1](https://rressler.quarto.pub/i_data_sets/data_word_lists.html) word list, which is comprehensive but may occasionally miss some valid words or include uncommon ones. This may cause the solver to fail to find a valid solution.

## Development

### Running the tests

```bash
uv run pytest
```

The OCR tests are a bit slow so you if you don't need it you can skip it with `--ignore ocr_test.py`

### Running the type checker

```bash
uv run pyright
```

### Formatting the code

```bash
uv run ruff format
```

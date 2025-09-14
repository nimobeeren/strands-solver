# Strands Solver

A solver for Strands, the New York Times puzzle game.

## Installation

Install the [uv](https://docs.astral.sh/uv/) package manager.

## Usage

1. Take a screenshot of the puzzle.

2. Recognize the characters of the puzzle grid and save them to a CSV file:

```bash
uv run ocr.py <path_to_image.jpeg> <path_to_data.csv>
```

Note: the defaults are tuned for iPhone 15 screenshots; for other devices, you may need to adjust parameters. Run `uv run ocr.py --help` for more information.

3. TODO

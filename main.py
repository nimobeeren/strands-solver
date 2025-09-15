import argparse

from ocr import load_grid_from_csv
from solver import Solver


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("grid", type=str)
    args = parser.parse_args()

    grid = load_grid_from_csv(args.grid)

    print(grid)

    solver = Solver(grid)

    # Find all words in the grid, allowing overlap between different words
    cols = len(grid)
    rows = len(grid[0])
    words = set()
    for x in range(cols):
        for y in range(rows):
            words |= solver.find_words(current_pos=(x, y))
    print(words)

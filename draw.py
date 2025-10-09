from dataclasses import dataclass

from rich.console import Console
from rich.text import Text

from common import Strand


@dataclass
class RenderCell:
    """Represents a cell in the render grid."""

    content: str
    """The character to display."""
    covered: bool = False
    """Whether this cell is part of a strand."""


def get_letter_cell(
    r: int, c: int, grid: list[list[str]], pos_to_strand: dict[tuple[int, int], int]
) -> RenderCell:
    """Gets a letter cell from the original grid.

    Args:
        r: Row index in the original grid
        c: Column index in the original grid
        grid: The original letter grid
        pos_to_strand: Mapping from position to strand index

    Returns:
        A RenderCell containing the letter with appropriate type
    """
    pos = (r, c)
    letter = grid[r][c]
    is_covered = pos in pos_to_strand

    return RenderCell(content=letter, covered=is_covered)


def get_connector_cell(
    render_row: int,
    render_col: int,
    connections: dict[tuple[tuple[int, int], tuple[int, int]], list[int]],
) -> RenderCell:
    """Determines the connector type for a space between letters.

    Args:
        render_row: Row index in the render grid
        render_col: Column index in the render grid
        connections: Mapping from sorted position pairs to strand indices

    Returns:
        A RenderCell containing the appropriate connector or empty
    """
    # Even row, odd col: horizontal connector
    if render_row % 2 == 0 and render_col % 2 == 1:
        grid_row = render_row // 2
        grid_col_left = render_col // 2
        grid_col_right = grid_col_left + 1

        pos_left = (grid_row, grid_col_left)
        pos_right = (grid_row, grid_col_right)
        conn_key = tuple(sorted([pos_left, pos_right]))

        if conn_key in connections:
            return RenderCell(content="─")
        else:
            return RenderCell(content=" ")

    # Odd row, even col: vertical connector
    elif render_row % 2 == 1 and render_col % 2 == 0:
        grid_row_top = render_row // 2
        grid_row_bottom = grid_row_top + 1
        grid_col = render_col // 2

        pos_top = (grid_row_top, grid_col)
        pos_bottom = (grid_row_bottom, grid_col)
        conn_key = tuple(sorted([pos_top, pos_bottom]))

        if conn_key in connections:
            return RenderCell(content="│")
        else:
            return RenderCell(content=" ")

    # Odd row, odd col: diagonal connectors (may cross)
    elif render_row % 2 == 1 and render_col % 2 == 1:
        grid_row_top = render_row // 2
        grid_row_bottom = grid_row_top + 1
        grid_col_left = render_col // 2
        grid_col_right = grid_col_left + 1

        # Check for down-right diagonal: top-left to bottom-right
        pos_top_left = (grid_row_top, grid_col_left)
        pos_bottom_right = (grid_row_bottom, grid_col_right)
        conn_key_down_right = tuple(sorted([pos_top_left, pos_bottom_right]))
        has_down_right = conn_key_down_right in connections

        # Check for down-left diagonal: top-right to bottom-left
        pos_top_right = (grid_row_top, grid_col_right)
        pos_bottom_left = (grid_row_bottom, grid_col_left)
        conn_key_down_left = tuple(sorted([pos_top_right, pos_bottom_left]))
        has_down_left = conn_key_down_left in connections

        if has_down_right and has_down_left:
            # Both diagonals cross
            return RenderCell(content="╳")
        elif has_down_right:
            # Down-right diagonal
            return RenderCell(content="╲")
        elif has_down_left:
            # Down-left diagonal
            return RenderCell(content="╱")
        else:
            return RenderCell(content=" ")

    # Should not reach here
    raise ValueError(f"Invalid render row {render_row} and column {render_col}")


def build_render_grid(
    grid: list[list[str]], strands: list[Strand]
) -> list[list[RenderCell]]:
    """Builds the render grid containing both letters and connectors.

    The render grid has dimensions (2*rows-1) x (2*cols-1) where:
    - Even row, even col: Letter from original grid
    - Even row, odd col: Horizontal connector
    - Odd row, even col: Vertical connector
    - Odd row, odd col: Diagonal connector

    Args:
        grid: The original letter grid
        strands: List of strands to display

    Returns:
        The render grid as a 2D list of RenderCell objects
    """
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0

    # Create a mapping from position to strand index
    pos_to_strand = {}
    for idx, strand in enumerate(strands):
        for pos in strand.positions:
            pos_to_strand[pos] = idx

    # Create a mapping for connections between positions
    # Key: ((r1,c1), (r2,c2)) tuple with sorted positions
    # Value: list of strand indices that use this connection
    connections = {}
    for idx, strand in enumerate(strands):
        for i in range(len(strand.positions) - 1):
            pos1 = strand.positions[i]
            pos2 = strand.positions[i + 1]
            # Sort positions to normalize the connection key
            key = tuple(sorted([pos1, pos2]))
            if key not in connections:
                connections[key] = []
            connections[key].append(idx)

    # Build the render grid
    render_rows = 2 * rows - 1
    render_cols = 2 * cols - 1
    render_grid = []

    for render_row in range(render_rows):
        row_cells = []
        for render_col in range(render_cols):
            # Even row, even col: letter cell
            if render_row % 2 == 0 and render_col % 2 == 0:
                grid_row = render_row // 2
                grid_col = render_col // 2
                cell = get_letter_cell(grid_row, grid_col, grid, pos_to_strand)
            # Any other position: connector cell
            else:
                cell = get_connector_cell(render_row, render_col, connections)

            row_cells.append(cell)
        render_grid.append(row_cells)

    return render_grid


def render_grid(data: list[list[RenderCell]]) -> None:
    """Renders the render grid to the console.

    Args:
        render_grid: The render grid to display
    """
    console = Console()
    for row in data:
        line = Text()
        for cell in row:
            if cell.content.isalpha():
                if cell.covered:
                    style = "bold cyan on cyan"
                else:
                    style = "white"
            else:
                style = "cyan"
            line.append(f"{cell.content:^3}", style=style)
        console.print(line)


def draw(grid: list[list[str]], strands: list[Strand] = []) -> None:
    """Draws a puzzle nicely in the console."""
    render_grid_data = build_render_grid(grid, strands)
    render_grid(render_grid_data)


if __name__ == "__main__":
    grid = [
        ["A", "B", "C", "D"],
        ["E", "F", "G", "H"],
        ["I", "J", "K", "L"],
        ["M", "N", "O", "P"],
    ]
    print("Test 1: Crossing diagonals")
    strands1 = [
        Strand(positions=((0, 0), (1, 1), (2, 2), (3, 3)), string="AFKP"),
        Strand(positions=((0, 3), (1, 2), (2, 1), (3, 0)), string="DGJM"),
    ]
    draw(grid, strands1)

    print("\nTest 2: Horizontal and vertical paths")
    strands2 = [
        Strand(positions=((0, 0), (0, 1), (0, 2), (0, 3)), string="ABCD"),
        Strand(positions=((3, 2), (2, 2), (2, 3), (3, 3)), string="OKLP"),
    ]
    draw(grid, strands2)

    print("\nTest 3: Mixed directions")
    strands3 = [
        Strand(positions=((0, 0), (1, 0), (2, 1), (2, 2)), string="AEJK"),
        Strand(positions=((0, 3), (0, 2), (1, 2), (1, 3)), string="DCGH"),
        Strand(positions=((3, 0), (3, 1), (3, 2), (3, 3)), string="MNOP"),
    ]
    draw(grid, strands3)

from collections.abc import Iterable
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
    strand_indices: list[int] | None = None
    """The indices of strands that use this cell (for letters or connectors)."""


def _get_letter_cell(
    x: int, y: int, grid: list[list[str]], pos_to_strand: dict[tuple[int, int], int]
) -> RenderCell:
    """Gets a letter cell from the original grid.

    Args:
        x: Column index in the original grid
        y: Row index in the original grid
        grid: The original letter grid
        pos_to_strand: Mapping from position to strand index

    Returns:
        A RenderCell containing the letter with appropriate type
    """
    pos = (x, y)
    letter = grid[y][x]
    strand_idx = pos_to_strand.get(pos)
    is_covered = strand_idx is not None

    return RenderCell(
        content=letter,
        covered=is_covered,
        strand_indices=[strand_idx] if strand_idx is not None else None,
    )


def _get_connector_cell(
    render_x: int,
    render_y: int,
    connections: dict[tuple[tuple[int, int], ...], list[int]],
) -> RenderCell:
    """Determines the connector type for a space between letters.

    Args:
        render_x: Column index in the render grid
        render_y: Row index in the render grid
        connections: Mapping from sorted position pairs to strand indices

    Returns:
        A RenderCell containing the appropriate connector or empty
    """
    # Even row, odd col: horizontal connector
    if render_y % 2 == 0 and render_x % 2 == 1:
        grid_y = render_y // 2
        grid_x_left = render_x // 2
        grid_x_right = grid_x_left + 1

        pos_left = (grid_x_left, grid_y)
        pos_right = (grid_x_right, grid_y)
        conn_key = tuple(sorted([pos_left, pos_right]))

        if conn_key in connections:
            return RenderCell(content="─", strand_indices=connections[conn_key])
        else:
            return RenderCell(content=" ")

    # Odd row, even col: vertical connector
    elif render_y % 2 == 1 and render_x % 2 == 0:
        grid_y_top = render_y // 2
        grid_y_bottom = grid_y_top + 1
        grid_x = render_x // 2

        pos_top = (grid_x, grid_y_top)
        pos_bottom = (grid_x, grid_y_bottom)
        conn_key = tuple(sorted([pos_top, pos_bottom]))

        if conn_key in connections:
            return RenderCell(content="│", strand_indices=connections[conn_key])
        else:
            return RenderCell(content=" ")

    # Odd row, odd col: diagonal connectors (may cross)
    elif render_y % 2 == 1 and render_x % 2 == 1:
        grid_y_top = render_y // 2
        grid_y_bottom = grid_y_top + 1
        grid_x_left = render_x // 2
        grid_x_right = grid_x_left + 1

        # Check for down-right diagonal: top-left to bottom-right
        pos_top_left = (grid_x_left, grid_y_top)
        pos_bottom_right = (grid_x_right, grid_y_bottom)
        conn_key_down_right = tuple(sorted([pos_top_left, pos_bottom_right]))
        has_down_right = conn_key_down_right in connections

        # Check for down-left diagonal: top-right to bottom-left
        pos_top_right = (grid_x_right, grid_y_top)
        pos_bottom_left = (grid_x_left, grid_y_bottom)
        conn_key_down_left = tuple(sorted([pos_top_right, pos_bottom_left]))
        has_down_left = conn_key_down_left in connections

        if has_down_right and has_down_left:
            # Both diagonals cross
            all_strands = (
                connections[conn_key_down_right] + connections[conn_key_down_left]
            )
            return RenderCell(content="╳", strand_indices=all_strands)
        elif has_down_right:
            # Down-right diagonal
            return RenderCell(
                content="╲", strand_indices=connections[conn_key_down_right]
            )
        elif has_down_left:
            # Down-left diagonal
            return RenderCell(
                content="╱", strand_indices=connections[conn_key_down_left]
            )
        else:
            return RenderCell(content=" ")

    # Should not reach here
    raise ValueError(f"Invalid render x {render_x} and y {render_y}")


def _build_render_grid(
    grid: list[list[str]], strands: Iterable[Strand]
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
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Create a mapping from position to strand index
    pos_to_strand = {}
    for idx, strand in enumerate(strands):
        for pos in strand.positions:
            pos_to_strand[pos] = idx

    # Create a mapping for connections between positions
    # Key: ((x1,y1), (x2,y2)) tuple with sorted positions
    # Value: list of strand indices that use this connection
    connections: dict[tuple[tuple[int, int], ...], list[int]] = {}
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
    render_height = 2 * height - 1
    render_width = 2 * width - 1
    render_grid = []

    for render_y in range(render_height):
        row_cells = []
        for render_x in range(render_width):
            # Even row, even col: letter cell
            if render_y % 2 == 0 and render_x % 2 == 0:
                grid_x = render_x // 2
                grid_y = render_y // 2
                cell = _get_letter_cell(grid_x, grid_y, grid, pos_to_strand)
            # Any other position: connector cell
            else:
                cell = _get_connector_cell(render_x, render_y, connections)

            row_cells.append(cell)
        render_grid.append(row_cells)

    return render_grid


def _render_grid(data: list[list[RenderCell]]) -> None:
    """Renders the render grid to the console.

    Args:
        render_grid: The render grid to display
    """
    # Define colors for strands (cycling through if more strands than colors)
    colors = ["cyan", "magenta", "yellow", "green", "blue", "red"]

    console = Console()
    for row in data:
        line = Text()
        for cell in row:
            if cell.content.isalpha():
                if cell.covered and cell.strand_indices:
                    # Use the color for this strand
                    color = colors[cell.strand_indices[0] % len(colors)]
                    style = f"bold on {color}"
                else:
                    style = "white"
            else:
                # Connector
                if cell.content == "╳":
                    # X connector is always white
                    style = "white"
                elif cell.strand_indices:
                    # Use the color of the strand
                    color = colors[cell.strand_indices[0] % len(colors)]
                    style = color
                else:
                    # Empty space
                    style = "white"
            line.append(f"{cell.content:^3}", style=style)
        console.print(line)


def draw(grid: list[list[str]], strands: Iterable[Strand] = []) -> None:
    """Draws a puzzle nicely in the console."""
    render_grid_data = _build_render_grid(grid, strands)
    _render_grid(render_grid_data)


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

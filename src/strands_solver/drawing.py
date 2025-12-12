from dataclasses import dataclass
from typing import Literal

from rich.console import Console
from rich.text import Text

from .common import Solution, Strand

StrandType = Literal["spangram", "other"]


@dataclass
class RenderCell:
    """Represents a cell in the render grid."""

    content: str
    """The character to display."""
    covered: bool = False
    """Whether this cell is part of a strand."""
    strand_type: StrandType = "other"
    """The type of strand that uses this cell."""


def _get_letter_cell(
    x: int,
    y: int,
    grid: list[list[str]],
    pos_to_type: dict[tuple[int, int], StrandType],
) -> RenderCell:
    """Gets a letter cell from the original grid.

    Args:
        x: Column index in the original grid
        y: Row index in the original grid
        grid: The original letter grid
        pos_to_type: Mapping from position to strand type

    Returns:
        A RenderCell containing the letter with appropriate type
    """
    pos = (x, y)
    letter = grid[y][x]
    strand_type = pos_to_type.get(pos, "other")
    is_covered = pos in pos_to_type

    return RenderCell(
        content=letter,
        covered=is_covered,
        strand_type=strand_type,
    )


def _get_connector_cell(
    render_x: int,
    render_y: int,
    connections: dict[tuple[tuple[int, int], ...], StrandType],
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
            return RenderCell(
                content="───",
                covered=True,
                strand_type=connections[conn_key],
            )
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
            return RenderCell(
                content="│",
                covered=True,
                strand_type=connections[conn_key],
            )
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
            strand_type = (
                "spangram"
                if connections[conn_key_down_right] == "spangram"
                or connections[conn_key_down_left] == "spangram"
                else "other"
            )
            return RenderCell(content="╳", covered=True, strand_type=strand_type)
        elif has_down_right:
            # Down-right diagonal
            return RenderCell(
                content="▔╲▁",
                covered=True,
                strand_type=connections[conn_key_down_right],
            )
        elif has_down_left:
            # Down-left diagonal
            return RenderCell(
                content="▁╱▔",
                covered=True,
                strand_type=connections[conn_key_down_left],
            )
        else:
            return RenderCell(content=" ")

    # Should not reach here
    raise ValueError(f"Invalid render x {render_x} and y {render_y}")


def _build_render_grid(
    grid: list[list[str]], solution: Solution | None
) -> list[list[RenderCell]]:
    """Builds the render grid containing both letters and connectors.

    The render grid has dimensions (2*rows-1) x (2*cols-1) where:
    - Even row, even col: Letter from original grid
    - Even row, odd col: Horizontal connector
    - Odd row, even col: Vertical connector
    - Odd row, odd col: Diagonal connector

    Args:
        grid: The original letter grid
        solution: The solution to render, if any

    Returns:
        The render grid as a 2D list of RenderCell objects
    """
    height = len(grid)
    width = len(grid[0]) if height > 0 else 0

    # Create mappings from positions/connections to strand types
    pos_to_type: dict[tuple[int, int], StrandType] = {}
    connections: dict[tuple[tuple[int, int], ...], StrandType] = {}

    if solution:
        spangram_strands: tuple[Strand, ...] = ()
        if solution.spangram:
            spangram_strand = solution.spangram[0]
            if len(solution.spangram) > 1:
                spangram_strand = spangram_strand.concatenate(*solution.spangram[1:])
            spangram_strands = (spangram_strand,)
        other_strands = tuple(solution.non_spangram_strands)

        def _record_strands(
            strands: tuple[Strand, ...], strand_type: StrandType
        ) -> None:
            for strand in strands:
                for pos in strand.positions:
                    pos_to_type[pos] = strand_type
                for i in range(len(strand.positions) - 1):
                    pos1 = strand.positions[i]
                    pos2 = strand.positions[i + 1]
                    key = tuple(sorted([pos1, pos2]))
                    connections[key] = strand_type

        _record_strands(spangram_strands, "spangram")
        _record_strands(other_strands, "other")

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
                cell = _get_letter_cell(grid_x, grid_y, grid, pos_to_type)
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
    console = Console()
    for row in data:
        line = Text()
        for cell in row:
            if cell.content.isalpha():
                if cell.covered:
                    if cell.strand_type == "spangram":
                        style = "bold on yellow"
                    else:
                        style = "bold on cyan"
                else:
                    style = "white"
            else:
                # Connector
                if cell.covered and cell.content.strip():
                    if cell.strand_type == "spangram":
                        style = "yellow"
                    else:
                        style = "cyan"
                else:
                    # Empty space
                    style = "white"
            # Pad cell content to 3 characters (centered)
            line.append(f"{cell.content:^3}", style=style)
        console.print(line)


def draw(grid: list[list[str]], solution: Solution | None = None) -> None:
    """Draws a puzzle and optionally overlays a solution."""
    render_grid_data = _build_render_grid(grid, solution)
    _render_grid(render_grid_data)


if __name__ == "__main__":
    grid = [
        ["A", "B", "C", "D"],
        ["E", "F", "G", "H"],
        ["I", "J", "K", "L"],
        ["M", "N", "O", "P"],
    ]
    print("Test 1: Crossing diagonals")
    solution1 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 1), (2, 2), (3, 3)), string="AFKP"),),
        non_spangram_strands=frozenset(
            (Strand(positions=((0, 3), (1, 2), (2, 1), (3, 0)), string="DGJM"),)
        ),
    )
    draw(grid, solution1)

    print("\nTest 2: Horizontal and vertical paths")

    solution2 = Solution(
        spangram=(Strand(positions=((0, 0), (0, 1), (0, 2), (0, 3)), string="ABCD"),),
        non_spangram_strands=frozenset(
            (Strand(positions=((3, 2), (2, 2), (2, 3), (3, 3)), string="OKLP"),)
        ),
    )
    draw(grid, solution2)

    print("\nTest 3: Mixed directions")
    solution3 = Solution(
        spangram=(Strand(positions=((0, 0), (1, 0), (2, 1), (2, 2)), string="AEJK"),),
        non_spangram_strands=frozenset(
            (
                Strand(positions=((0, 3), (0, 2), (1, 2), (1, 3)), string="DCGH"),
                Strand(positions=((3, 0), (3, 1), (3, 2), (3, 3)), string="MNOP"),
            )
        ),
    )
    draw(grid, solution3)

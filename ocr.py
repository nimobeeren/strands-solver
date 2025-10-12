"""Wonky AI-generated code to extract the puzzle grid from a screenshot."""

import argparse
import json
import logging
import sys
from collections import deque
from pathlib import Path
from typing import Sequence

import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from pytesseract import Output

logger = logging.getLogger(__name__)


def _maybe_set_tesseract_path() -> None:
    """Point pytesseract to a likely tesseract binary if not on PATH.

    This helps local runs on macOS/Homebrew and common Linux locations without
    requiring users to export environment variables.
    """
    common_paths = [
        "/opt/homebrew/bin/tesseract",  # Apple Silicon Homebrew
        "/usr/local/bin/tesseract",  # Intel macOS Homebrew
        "/usr/bin/tesseract",  # Linux
    ]
    for candidate in common_paths:
        if Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            break


def _generate_variants(tile: Image.Image) -> list[Image.Image]:
    """Produce a handful of preprocessing variants for robust OCR."""
    variants: list[Image.Image] = []

    def prep(
        trim_frac: float, contrast: float, threshold: bool, invert: bool
    ) -> Image.Image:
        w, h = tile.size
        trim = int(min(w, h) * trim_frac)
        img = tile.crop((trim, trim, w - trim, h - trim))
        img = ImageOps.grayscale(img)
        img = ImageEnhance.Contrast(img).enhance(contrast)
        img = ImageOps.autocontrast(img, cutoff=0)
        img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)  # pyright: ignore[reportAttributeAccessIssue]
        if threshold:
            img = img.point(lambda p: 255 if p > 128 else 0, mode="1")  # pyright: ignore[reportOperatorIssue]
        if invert:
            img = ImageOps.invert(img.convert("L"))
        return img

    # Balanced
    variants.append(prep(0.12, 2.0, True, False))
    variants.append(prep(0.12, 2.0, True, True))
    # No threshold
    variants.append(prep(0.12, 2.2, False, False))
    variants.append(prep(0.12, 2.2, False, True))
    # Smaller crop
    variants.append(prep(0.08, 2.0, True, False))
    # Higher contrast without threshold
    variants.append(prep(0.10, 3.0, False, False))
    return variants


def _ocr_letter(tile: Image.Image) -> str:
    _maybe_set_tesseract_path()
    config = "--psm 10 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ"

    best_char = ""
    best_conf = -1

    for variant in _generate_variants(tile):
        try:
            data = pytesseract.image_to_data(
                variant, config=config, output_type=Output.DICT
            )
            for txt, conf in zip(data.get("text", []), data.get("conf", [])):
                if not txt:
                    continue
                # Some conf values can be strings like "-1"
                try:
                    conf_int = int(float(conf))
                except Exception:
                    conf_int = -1
                letters = [c for c in txt.strip().upper() if "A" <= c <= "Z"]
                if not letters:
                    continue
                c = letters[0]
                if conf_int > best_conf:
                    best_conf = conf_int
                    best_char = c
        except Exception:
            # Fall back to simple recognition for this variant
            txt = pytesseract.image_to_string(variant, config=config).strip().upper()
            letters = [c for c in txt if "A" <= c <= "Z"]
            if letters and best_conf < 0:
                best_char = letters[0]
                best_conf = 0

    return best_char


def _to_binary(tile: Image.Image) -> Image.Image:
    """Return a binarized, cropped, standardized tile (L mode 0/255)."""
    # Mirror first variant in _generate_variants for determinism
    w, h = tile.size
    trim = int(min(w, h) * 0.10)
    img = tile.crop((trim, trim, w - trim, h - trim))
    img = ImageOps.grayscale(img)
    img = ImageEnhance.Contrast(img).enhance(2.2)
    img = ImageOps.autocontrast(img, cutoff=0)
    img = img.resize((img.width * 2, img.height * 2), Image.BICUBIC)  # pyright: ignore[reportAttributeAccessIssue]
    img = img.point(lambda p: 255 if p > 128 else 0, mode="L")  # pyright: ignore[reportOperatorIssue]
    return img


def _count_holes(binary_img: Image.Image) -> int:
    """Count internal black regions (holes) not touching the border.

    Expects binary 0/255 image where letters are white (255) on black (0)
    background. We count black components enclosed by white strokes.
    """
    w, h = binary_img.size
    px = binary_img.load()
    assert px is not None

    visited = [[False] * w for _ in range(h)]

    def neighbors(x: int, y: int):
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < w and 0 <= ny < h:
                yield nx, ny

    # Mark border-connected black as background
    dq = deque()
    for x in range(w):
        if px[x, 0] == 0:
            dq.append((x, 0))
        if px[x, h - 1] == 0:
            dq.append((x, h - 1))
    for y in range(h):
        if px[0, y] == 0:
            dq.append((0, y))
        if px[w - 1, y] == 0:
            dq.append((w - 1, y))

    while dq:
        x, y = dq.popleft()
        if visited[y][x] or px[x, y] != 0:
            continue
        visited[y][x] = True
        for nx, ny in neighbors(x, y):
            if not visited[ny][nx] and px[nx, ny] == 0:
                dq.append((nx, ny))

    # Remaining unvisited black components are holes; ignore tiny specks
    min_area = max(20, int(w * h * 0.002))
    holes = 0
    for y in range(h):
        for x in range(w):
            if px[x, y] == 0 and not visited[y][x]:
                dq.append((x, y))
                visited[y][x] = True
                area = 0
                while dq:
                    cx, cy = dq.popleft()
                    area += 1
                    for nx, ny in neighbors(cx, cy):
                        if (
                            0 <= nx < w
                            and 0 <= ny < h
                            and px[nx, ny] == 0
                            and not visited[ny][nx]
                        ):
                            visited[ny][nx] = True
                            dq.append((nx, ny))
                if area >= min_area:
                    holes += 1
    return holes


def _looks_like_I(binary_img: Image.Image) -> bool:
    """Heuristic to detect an 'I' glyph when OCR is uncertain.

    Works on binary tiles where the letter is white (255) on black (0).
    We look for a tall, thin white column near the center.
    """
    w, h = binary_img.size
    px = binary_img.load()
    assert px is not None

    # Bounding box of white pixels
    min_x, min_y, max_x, max_y = w, h, -1, -1
    white = 0
    for y in range(h):
        for x in range(w):
            if px[x, y] == 255:
                white += 1
                if x < min_x:
                    min_x = x
                if y < min_y:
                    min_y = y
                if x > max_x:
                    max_x = x
                if y > max_y:
                    max_y = y
    if white == 0 or max_x < 0:
        return False

    bb_w = max_x - min_x + 1
    bb_h = max_y - min_y + 1
    fill_ratio = white / float(w * h)

    # 'I' is tall and relatively narrow
    aspect = bb_h / max(1, bb_w)

    # Scan columns within the bounding box for strongest vertical stroke
    max_col_ratio = 0.0
    for cx in range(min_x, max_x + 1):
        col_white = sum(1 for y in range(min_y, max_y + 1) if px[cx, y] == 255) / max(
            1, bb_h
        )
        if col_white > max_col_ratio:
            max_col_ratio = col_white

    # Heuristics tuned for this font: tall, narrow, sparse fill, strong single column
    if (
        aspect > 3.0
        and (bb_w / w) < 0.25
        and fill_ratio < 0.30
        and max_col_ratio > 0.60
    ):
        return True
    return False


def extract_theme(
    image: Image.Image,
    *,
    theme_top_left_x: float = 0.0492957746,
    theme_top_left_y: float = 0.2093114241,
    theme_bottom_right_x: float = 0.4123630673,
    theme_bottom_right_y: float = 0.2488262911,
) -> str:
    """Extracts the theme text from an iPhone screenshot.

    All spatial parameters are relative to image height:
    - theme_top_left_x: left edge of theme region (default ~0.0493)
    - theme_top_left_y: top edge of theme region (default ~0.2093)
    - theme_bottom_right_x: right edge of theme region (default ~0.4124)
    - theme_bottom_right_y: bottom edge of theme region (default ~0.2488)

    Other devices may need adjustments to these parameters.
    """
    _maybe_set_tesseract_path()

    img_width, img_height = image.size
    top_left_x_px = int(theme_top_left_x * img_height)
    top_left_y_px = int(theme_top_left_y * img_height)
    bottom_right_x_px = int(theme_bottom_right_x * img_height)
    bottom_right_y_px = int(theme_bottom_right_y * img_height)

    # Crop the theme region
    theme_region = image.crop(
        (top_left_x_px, top_left_y_px, bottom_right_x_px, bottom_right_y_px)
    )

    # Preprocess the theme region for better OCR results
    theme_region = ImageOps.grayscale(theme_region)
    theme_region = ImageEnhance.Contrast(theme_region).enhance(2.0)
    theme_region = ImageOps.autocontrast(theme_region, cutoff=0)
    theme_region = theme_region.resize(
        (theme_region.width * 2, theme_region.height * 2),
        Image.BICUBIC,  # pyright: ignore[reportAttributeAccessIssue]
    )

    # Use PSM 7 for single line text
    config = "--psm 7"
    theme_text = pytesseract.image_to_string(theme_region, config=config).strip()

    return theme_text


def extract_num_words(
    image: Image.Image,
    *,
    num_words_top_left_x: float = 0.147,
    num_words_top_left_y: float = 0.92,
    num_words_bottom_right_x: float = 0.920,
    num_words_bottom_right_y: float = 0.959,
) -> int | None:
    """Extracts the number of theme words from text like '0 of 7 theme words found.'

    All spatial parameters are relative to image height:
    - num_words_top_left_x: left edge of region (default ~0.147)
    - num_words_top_left_y: top edge of region (default ~0.92)
    - num_words_bottom_right_x: right edge of region (default ~0.920)
    - num_words_bottom_right_y: bottom edge of region (default ~0.959)

    Returns the number N from "0 of N theme words found." or None if not found.
    """
    _maybe_set_tesseract_path()

    img_width, img_height = image.size
    top_left_x_px = int(num_words_top_left_x * img_height)
    top_left_y_px = int(num_words_top_left_y * img_height)
    bottom_right_x_px = int(num_words_bottom_right_x * img_height)
    bottom_right_y_px = int(num_words_bottom_right_y * img_height)

    # Crop the region
    num_words_region = image.crop(
        (top_left_x_px, top_left_y_px, bottom_right_x_px, bottom_right_y_px)
    )

    # Preprocess for better OCR results
    num_words_region = ImageOps.grayscale(num_words_region)
    num_words_region = ImageEnhance.Contrast(num_words_region).enhance(2.0)
    num_words_region = ImageOps.autocontrast(num_words_region, cutoff=0)
    num_words_region = num_words_region.resize(
        (num_words_region.width * 2, num_words_region.height * 2),
        Image.BICUBIC,  # pyright: ignore[reportAttributeAccessIssue]
    )

    # Use PSM 7 for single line text
    config = "--psm 7"
    text = pytesseract.image_to_string(num_words_region, config=config).strip()

    # Parse "0 of N theme words found." to extract N
    import re

    match = re.search(r"of\s+(\d+)\s+theme", text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def extract_grid(
    image: Image.Image,
    *,
    rows: int = 8,
    cols: int = 6,
    tile_size: float = 0.0665,
    origin_x: float = 0.0274,
    origin_y: float = 0.3521,
) -> list[list[str]]:
    """Extracts a grid of characters from an iPhone screenshot.

    All spatial parameters are relative to image height:
    - tile_size: size of each tile (default ~0.0665)
    - origin_x: left edge of grid (default ~0.0274)
    - origin_y: top edge of grid, where 0.0=top and 1.0=bottom (default ~0.3521)

    Other devices may need adjustments to these parameters.
    """
    img_width, img_height = image.size
    tile_size_px = int(tile_size * img_height)
    origin_x_px = int(origin_x * img_height)
    origin_y_px = int(origin_y * img_height)

    grid: list[list[str]] = []
    for r in range(rows):
        row_letters: list[str] = []
        for c in range(cols):
            left = origin_x_px + c * tile_size_px
            top = origin_y_px + r * tile_size_px
            right = left + tile_size_px
            bottom = top + tile_size_px
            tile = image.crop((left, top, right, bottom))
            bin_img = _to_binary(tile)
            holes = _count_holes(bin_img)
            letter = _ocr_letter(tile)
            # Disambiguate B vs P using hole count
            if letter in {"B", "P"}:
                letter = "B" if holes >= 2 else "P"
            elif not letter:
                # Rescue uncertain cases
                if _looks_like_I(bin_img):
                    letter = "I"
            row_letters.append(letter)
        grid.append(row_letters)
    return grid


def load_image(image_path: str | Path) -> Image.Image:
    """Load an image from disk and return a PIL Image in RGB mode.

    Raises FileNotFoundError if the path does not exist.
    """
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image not found: {path}")
    img = Image.open(path)
    # Normalize to RGB to avoid alpha-channel surprises during processing
    return img.convert("RGB")


def save_grid_to_json(
    grid: Sequence[Sequence[str]],
    json_path: str | Path,
    *,
    theme: str | None = None,
    num_words: int | None = None,
) -> None:
    """Save a 2D grid of letters to a JSON file with basic validation.

    Validation rules:
    - Grid must be non-empty and rectangular (all rows same length)
    - Each cell must be a single uppercase A-Z letter or empty string
    - Theme (if provided) is saved as a string field
    - num_words (if provided) is saved as an integer field
    """
    # Basic structure checks
    if not grid or not grid[0]:
        raise ValueError("Grid must be non-empty")
    expected_cols = len(grid[0])
    for r_idx, row in enumerate(grid):
        if len(row) != expected_cols:
            raise ValueError(
                f"Grid is not rectangular: row 0 has {expected_cols} cols, row {r_idx} has {len(row)}"
            )
        for c_idx, cell in enumerate(row):
            if not isinstance(cell, str):
                raise ValueError(f"Grid cell at ({r_idx},{c_idx}) must be a string")
            value = cell.strip().upper()
            if value not in {""} | {chr(ord("A") + i) for i in range(26)}:
                raise ValueError(
                    f"Invalid cell at ({r_idx},{c_idx}): '{cell}'. Must be '', or A-Z."
                )

    out_path = Path(json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    normalized_grid = [[cell.strip().upper() for cell in row] for row in grid]
    with out_path.open("w", encoding="utf-8") as f:
        f.write("{\n")
        if theme is not None:
            f.write(f'  "theme": {json.dumps(theme)},\n')
        f.write('  "grid": [\n')
        for i, row in enumerate(normalized_grid):
            row_json = json.dumps(row)
            if i < len(normalized_grid) - 1:
                f.write("    " + row_json + ",\n")
            else:
                f.write("    " + row_json + "\n")
        f.write("  ]")
        if num_words is not None:
            f.write(",\n")
            f.write(f'  "numWords": {num_words}\n')
        else:
            f.write("\n")
        f.write("}\n")


def load_grid_from_json(
    json_path: str | Path,
    *,
    expected_rows: int | None = None,
    expected_cols: int | None = None,
    allow_blank: bool = True,
) -> list[list[str]]:
    """Load a grid from JSON and return a 2D list of strings with validation.

    - Validates rectangular shape
    - Optionally validates row/column count
    - Validates each cell is a single A-Z letter; blanks optionally allowed
    """
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict) or "grid" not in data:
        raise ValueError("JSON must contain a 'grid' key")

    raw_grid = data["grid"]
    if not isinstance(raw_grid, list):
        raise ValueError("grid data must be a list")

    rows: list[list[str]] = []
    for raw_row in raw_grid:
        if not isinstance(raw_row, list):
            raise ValueError("Each row in grid must be a list")
        # Normalize each cell: strip and uppercase
        normalized = [str(cell).strip().upper() for cell in raw_row]
        rows.append(normalized)

    if not rows:
        raise ValueError("JSON grid is empty; expected at least one row")

    # Rectangular validation
    num_cols = len(rows[0])
    for r_idx, row in enumerate(rows):
        if len(row) != num_cols:
            raise ValueError(
                f"JSON grid is not rectangular: row 0 has {num_cols} cols, row {r_idx} has {len(row)}"
            )

    if expected_rows is not None and len(rows) != expected_rows:
        raise ValueError(
            f"Unexpected row count: got {len(rows)}, expected {expected_rows}"
        )
    if expected_cols is not None and num_cols != expected_cols:
        raise ValueError(
            f"Unexpected column count: got {num_cols}, expected {expected_cols}"
        )

    # Cell validation
    valid_letters = {chr(ord("A") + i) for i in range(26)}
    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row):
            if cell == "":
                if not allow_blank:
                    raise ValueError(f"Blank cell not allowed at ({r_idx},{c_idx})")
                continue
            if cell not in valid_letters:
                raise ValueError(
                    f"Invalid cell at ({r_idx},{c_idx}): '{cell}'. Must be A-Z."
                )

    return rows


def process_image_to_json(
    image_path: str | Path,
    json_path: str | Path,
    *,
    rows: int = 8,
    cols: int = 6,
    tile_size: float = 0.0665,
    origin_x: float = 0.0274,
    origin_y: float = 0.3521,
    extract_theme_flag: bool = True,
    extract_num_words_flag: bool = True,
) -> None:
    """High-level helper: load image, extract grid, save as JSON.

    All spatial parameters are relative to image height (0.0=top, 1.0=bottom).
    """
    image = load_image(image_path)

    theme = None
    if extract_theme_flag:
        theme = extract_theme(image)

    num_words = None
    if extract_num_words_flag:
        num_words = extract_num_words(image)

    grid = extract_grid(
        image,
        rows=rows,
        cols=cols,
        tile_size=tile_size,
        origin_x=origin_x,
        origin_y=origin_y,
    )
    save_grid_to_json(grid, json_path, theme=theme, num_words=num_words)


def _cli_parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract Strands grid from screenshot and save as JSON"
    )
    parser.add_argument("image", help="Path to screenshot image")
    parser.add_argument("json", help="Path to output JSON")
    parser.add_argument(
        "--rows", type=int, default=8, help="Number of grid rows (default: 8)"
    )
    parser.add_argument(
        "--cols", type=int, default=6, help="Number of grid columns (default: 6)"
    )
    parser.add_argument(
        "--tile-size",
        type=float,
        default=0.0665,
        help="Tile size relative to image height (default: 0.0665)",
    )
    parser.add_argument(
        "--origin-x",
        type=float,
        default=0.0274,
        help="Left origin relative to image height (default: 0.0274)",
    )
    parser.add_argument(
        "--origin-y",
        type=float,
        default=0.3521,
        help="Top origin relative to image height, 0.0=top 1.0=bottom (default: 0.3521)",
    )
    parser.add_argument(
        "--print", action="store_true", help="Print the extracted grid to stdout"
    )
    return parser.parse_args(argv)


def cli_main(argv: list[str] | None = None) -> int:
    args = _cli_parse_args(list(argv) if argv is not None else sys.argv[1:])
    try:
        process_image_to_json(
            args.image,
            args.json,
            rows=args.rows,
            cols=args.cols,
            tile_size=args.tile_size,
            origin_x=args.origin_x,
            origin_y=args.origin_y,
        )
        if args.print:
            grid = load_grid_from_json(
                args.json, expected_rows=args.rows, expected_cols=args.cols
            )
            for row in grid:
                logger.info(",".join(row))
        return 0
    except Exception as e:
        logger.error(f"Error: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(cli_main())

"""Wonky AI-generated code to extract the puzzle grid from a screenshot."""

from collections import deque
from pathlib import Path

import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from pytesseract import Output


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


def extract_grid(
    image: Image.Image,
    *,
    rows: int = 8,
    cols: int = 6,
    tile_size: int = 170,
    origin_x: int = 70,
    origin_y: int = 900,
) -> list[list[str]]:
    """Extracts a grid of characters from an iPhone screenshot. Other devices may need
    adjustments to tile_size and origin parameters."""
    grid: list[list[str]] = []
    for r in range(rows):
        row_letters: list[str] = []
        for c in range(cols):
            left = origin_x + c * tile_size
            top = origin_y + r * tile_size
            right = left + tile_size
            bottom = top + tile_size
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

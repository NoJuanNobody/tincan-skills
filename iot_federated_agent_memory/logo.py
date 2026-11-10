"""THE AI MESSIAH logo: pixel asset loading, resampling, glow animation and title font.

The pixel asset (assets/ai_messiah_logo.hex) is generated from the original
artwork by scripts/build_logo_asset.py, so the TUI renders the real image
(two pixels per terminal cell via half-blocks) instead of hand-drawn ASCII.
"""

from __future__ import annotations

import math
import os
from typing import List, Optional, Tuple

from .ansi import RGB, Canvas

ASSET_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "ai_messiah_logo.hex")

GLOW_NONE, GLOW_HALO, GLOW_EYE, GLOW_BRAIN = 0, 1, 2, 3

_ASSET_CACHE: Optional[List[List[RGB]]] = None


def load_logo(path: str = ASSET_PATH) -> List[List[RGB]]:
    global _ASSET_CACHE
    if path == ASSET_PATH and _ASSET_CACHE is not None:
        return _ASSET_CACHE
    with open(path) as f:
        w, h = (int(v) for v in f.readline().split())
        pixels = []
        for _ in range(h):
            line = f.readline().strip()
            pixels.append([(int(line[i:i + 2], 16), int(line[i + 2:i + 4], 16), int(line[i + 4:i + 6], 16))
                           for i in range(0, w * 6, 6)])
    if path == ASSET_PATH:
        _ASSET_CACHE = pixels
    return pixels


def resample(pixels: List[List[RGB]], tw: int, th: int) -> List[List[RGB]]:
    """Area-average downsample (nearest-neighbour when enlarging)."""
    sh, sw = len(pixels), len(pixels[0])
    tw, th = max(1, tw), max(1, th)
    out = []
    for ty in range(th):
        y0 = int(ty * sh / th)
        y1 = max(y0 + 1, int(math.ceil((ty + 1) * sh / th)))
        row = []
        for tx in range(tw):
            x0 = int(tx * sw / tw)
            x1 = max(x0 + 1, int(math.ceil((tx + 1) * sw / tw)))
            r = g = b = n = 0
            for yy in range(y0, min(y1, sh)):
                src = pixels[yy]
                for xx in range(x0, min(x1, sw)):
                    p = src[xx]
                    r += p[0]
                    g += p[1]
                    b += p[2]
                    n += 1
            row.append((r // n, g // n, b // n))
        out.append(row)
    return out


class LogoImage:
    """A resampled logo plus per-pixel glow classes used for animation."""

    def __init__(self, width: int, height: int) -> None:
        src = load_logo()
        self.width = max(1, width)
        self.height = max(2, height + (height % 2))  # even: two pixel rows per cell
        self.pixels = resample(src, self.width, self.height)
        self.glow: List[List[int]] = []
        self.phase: List[List[float]] = []
        cx, cy = self.width * 0.5, self.height * 0.54   # head centre
        rx, ry = self.width * 0.35, self.height * 0.38  # head ellipse
        bx, by = self.width * 0.5, self.height * 0.25   # brain centre
        for y, row in enumerate(self.pixels):
            g_row, p_row = [], []
            for x, (r, g, b) in enumerate(row):
                inside_head = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.0
                if g > 140 and g > r + 40 and g > b + 30:
                    kind = GLOW_EYE
                elif r > 200 and g > 170 and b < 110 and not inside_head:
                    kind = GLOW_HALO
                elif inside_head and y < self.height * 0.40 and r > 110 and g > 80 and b < 90 and r >= g:
                    kind = GLOW_BRAIN
                else:
                    kind = GLOW_NONE
                g_row.append(kind)
                # Ripple phase: distance from the brain, normalised to the logo size.
                p_row.append(math.hypot((x - bx) / self.width, (y - by) / self.height))
            self.glow.append(g_row)
            self.phase.append(p_row)

    @classmethod
    def fit(cls, max_cols: int, max_rows: int) -> "LogoImage":
        src = load_logo()
        sw, sh = len(src[0]), len(src)
        scale = min(max_cols / sw, (max_rows * 2) / sh, 1.0)
        return cls(int(sw * scale), int(sh * scale))

    @property
    def cell_rows(self) -> int:
        return self.height // 2

    def color_at(self, x: int, y: int, t: Optional[float]) -> RGB:
        r, g, b = self.pixels[y][x]
        if t is None:
            return (r, g, b)
        kind = self.glow[y][x]
        if kind == GLOW_NONE:
            return (r, g, b)
        if kind == GLOW_EYE:
            f = 1.0 + 0.30 * math.sin(t * 3.4)
        elif kind == GLOW_HALO:
            f = 1.0 + 0.22 * math.sin(t * 3.0 - self.phase[y][x] * 18.0)  # energy wave rippling outward
        else:
            f = 1.0 + 0.45 * max(0.0, math.sin(t * 5.0 - self.phase[y][x] * 40.0)) ** 6  # neurons firing
        return (min(255, int(r * f)), min(255, int(g * f)), min(255, int(b * f)))

    def draw(self, canvas: Canvas, x0: int, y0: int, t: Optional[float] = None) -> None:
        for cy in range(self.cell_rows):
            top_y, bot_y = cy * 2, cy * 2 + 1
            for cx in range(self.width):
                canvas.put(x0 + cx, y0 + cy, "\u2580", self.color_at(cx, top_y, t), self.color_at(cx, bot_y, t))


# --- Block title font ("THE AI MESSIAH" / "CONSULTING") --------------------------------

_FONT = {
    "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "E": ["###", "#..", "##.", "#..", "###"],
    "A": [".#.", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"],
    "S": ["###", "#..", "###", "..#", "###"],
    "C": ["###", "#..", "#..", "#..", "###"],
    "O": ["###", "#.#", "#.#", "#.#", "###"],
    "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"],
    "L": ["#..", "#..", "#..", "#..", "###"],
    "G": ["###", "#..", "#.#", "#.#", "###"],
    " ": ["..", "..", "..", "..", ".."],
}

# Yellow -> orange -> pink, like the lettering on the artwork.
TITLE_GRADIENT: List[RGB] = [(255, 236, 90), (255, 208, 64), (255, 172, 52), (252, 138, 62), (238, 108, 92), (222, 92, 112)]


def title_width(text: str) -> int:
    glyphs = [_FONT.get(c, _FONT[" "]) for c in text.upper()]
    return sum(len(g[0]) for g in glyphs) + max(0, len(glyphs) - 1)


def draw_title(canvas: Canvas, x0: int, y0: int, text: str, gradient: List[RGB] = TITLE_GRADIENT) -> None:
    """Draw text in the 5px block font using half-blocks (occupies 3 terminal rows)."""
    columns: List[str] = []  # each entry: 5-char vertical bit column
    for i, c in enumerate(text.upper()):
        glyph = _FONT.get(c, _FONT[" "])
        for gx in range(len(glyph[0])):
            columns.append("".join(glyph[gy][gx] for gy in range(5)))
        if i < len(text) - 1:
            columns.append(".....")
    for x, col in enumerate(columns):
        bits = col + "."  # pad to 6 pixel rows -> 3 cells
        for cy in range(3):
            top, bot = bits[cy * 2] == "#", bits[cy * 2 + 1] == "#"
            ct, cb = gradient[cy * 2], gradient[cy * 2 + 1]
            if top and bot:
                canvas.put(x0 + x, y0 + cy, "\u2580", ct, cb)
            elif top:
                canvas.put(x0 + x, y0 + cy, "\u2580", ct, None, keep_bg=True)
            elif bot:
                canvas.put(x0 + x, y0 + cy, "\u2584", cb, None, keep_bg=True)

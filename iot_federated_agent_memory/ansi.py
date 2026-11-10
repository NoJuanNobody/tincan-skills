"""Minimal cell-based ANSI canvas with truecolor / 256-color output (no dependencies)."""

from __future__ import annotations

import os
from typing import Dict, List, Optional, Tuple

RGB = Tuple[int, int, int]


def detect_color_mode() -> str:
    """Return "truecolor" or "256" based on the terminal environment."""
    if os.environ.get("COLORTERM", "").lower() in ("truecolor", "24bit"):
        return "truecolor"
    if os.environ.get("TERM_PROGRAM", "") in ("iTerm.app", "WezTerm", "ghostty", "vscode", "Hyper"):
        return "truecolor"
    return "256"


_CACHE_256: Dict[RGB, int] = {}


def rgb_to_256(c: RGB) -> int:
    hit = _CACHE_256.get(c)
    if hit is not None:
        return hit
    r, g, b = c
    if abs(r - g) < 12 and abs(g - b) < 12:
        if r < 8:
            idx = 16
        elif r > 246:
            idx = 231
        else:
            idx = 232 + round((r - 8) / 238 * 23)
    else:
        def q(v: int) -> int:
            return 0 if v < 48 else 1 if v < 115 else min(5, (v - 35) // 40)
        idx = 16 + 36 * q(r) + 6 * q(g) + q(b)
    if len(_CACHE_256) > 65536:
        _CACHE_256.clear()
    _CACHE_256[c] = idx
    return idx


def _sgr(fg: Optional[RGB], bg: Optional[RGB], mode: str) -> str:
    parts = ["0"]
    if fg is not None:
        parts.append("38;2;%d;%d;%d" % fg if mode == "truecolor" else "38;5;%d" % rgb_to_256(fg))
    if bg is not None:
        parts.append("48;2;%d;%d;%d" % bg if mode == "truecolor" else "48;5;%d" % rgb_to_256(bg))
    return "\x1b[" + ";".join(parts) + "m"


class Canvas:
    """A grid of (char, fg, bg) cells that serializes to one ANSI frame."""

    def __init__(self, cols: int, rows: int, bg: Optional[RGB] = None) -> None:
        self.cols = max(1, cols)
        self.rows = max(1, rows)
        self.ch: List[List[str]] = [[" "] * self.cols for _ in range(self.rows)]
        self.fg: List[List[Optional[RGB]]] = [[None] * self.cols for _ in range(self.rows)]
        self.bg: List[List[Optional[RGB]]] = [[bg] * self.cols for _ in range(self.rows)]

    def put(self, x: int, y: int, ch: str, fg: Optional[RGB] = None, bg: Optional[RGB] = None, keep_bg: bool = False) -> None:
        if 0 <= x < self.cols and 0 <= y < self.rows:
            self.ch[y][x] = ch
            self.fg[y][x] = fg
            if not keep_bg:
                self.bg[y][x] = bg

    def text(self, x: int, y: int, s: str, fg: Optional[RGB] = None, bg: Optional[RGB] = None, keep_bg: bool = True) -> int:
        """Write a string (clipped to the canvas). Returns the x after the last char."""
        for i, c in enumerate(s):
            self.put(x + i, y, c, fg, bg, keep_bg=keep_bg and bg is None)
        return x + len(s)

    def fill(self, x0: int, y0: int, x1: int, y1: int, bg: Optional[RGB]) -> None:
        for y in range(max(0, y0), min(self.rows, y1)):
            for x in range(max(0, x0), min(self.cols, x1)):
                self.ch[y][x] = " "
                self.fg[y][x] = None
                self.bg[y][x] = bg

    def render(self, mode: str = "truecolor", home: bool = True) -> str:
        out: List[str] = []
        for y in range(self.rows):
            out.append("\x1b[%d;1H" % (y + 1) if home else ("\n" if y else ""))
            last = None
            chars, fgs, bgs = self.ch[y], self.fg[y], self.bg[y]
            # Leave the bottom-right cell empty so the terminal never scrolls.
            width = self.cols - 1 if (home and y == self.rows - 1) else self.cols
            for x in range(width):
                key = (fgs[x], bgs[x])
                if key != last:
                    out.append(_sgr(fgs[x], bgs[x], mode))
                    last = key
                out.append(chars[x])
            out.append("\x1b[0m")
        return "".join(out)

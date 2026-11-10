"""AI MESSIAH terminal app for iot-federated-agent-memory.

Two views that share one live status feed from the mesh relay:

* dashboard   - relay health, readiness tier, peers and AI credit pools
* screensaver - the AI Messiah logo rendered from the real artwork, with
                glowing eyes/halo/brain animation and circuit rain

The dashboard drops into the screensaver after an idle timeout; any key
returns. Pure standard library (termios/select), macOS + Linux.

    python3 tui.py                      # dashboard (idle -> screensaver)
    python3 tui.py --screensaver        # start in the screensaver
    python3 tui.py --relay http://10.0.0.40:8085
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
import select
import shutil
import signal
import sys
import threading
import time
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from .ansi import RGB, Canvas, detect_color_mode
from .logo import LogoImage, draw_title, title_width

DEFAULT_RELAY = os.environ.get("IOT_MESH_RELAY", "https://iot-federated-agent-memory-production.up.railway.app")

# Palette sampled from the artwork.
BG_DEEP: RGB = (14, 6, 24)
PURPLE: RGB = (150, 70, 200)
PURPLE_DIM: RGB = (70, 30, 100)
GOLD: RGB = (255, 214, 90)
GOLD_DIM: RGB = (170, 130, 60)
GREEN: RGB = (110, 255, 120)
RED: RGB = (255, 95, 95)
WHITE: RGB = (235, 230, 240)
GREY: RGB = (150, 140, 160)
HEADER_BG: RGB = (40, 16, 60)


# --------------------------------------------------------------------------- status

class StatusPoller(threading.Thread):
    """Polls <relay>/api/status in the background so the UI never blocks."""

    def __init__(self, relay: str, interval: float = 10.0) -> None:
        super().__init__(daemon=True)
        self.relay = relay.rstrip("/")
        self.interval = interval
        self._lock = threading.Lock()
        self._wake = threading.Event()
        self._state: Dict[str, Any] = {"data": None, "error": None, "updated_at": None, "fetching": True}

    def run(self) -> None:
        while True:
            self._fetch()
            self._wake.wait(self.interval)
            self._wake.clear()

    def refresh(self) -> None:
        self._wake.set()

    def _fetch(self) -> None:
        with self._lock:
            self._state["fetching"] = True
        try:
            req = urllib.request.Request(self.relay + "/api/status", headers={"User-Agent": "ai-messiah-tui/1.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            with self._lock:
                self._state.update(data=data, error=None, updated_at=time.time(), fetching=False)
        except Exception as exc:  # network errors, bad JSON, HTTP errors
            with self._lock:
                self._state.update(error=str(exc)[:160], updated_at=time.time(), fetching=False)

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)


def status_summary(snap: Dict[str, Any]) -> Tuple[str, RGB]:
    if snap.get("data") and not snap.get("error"):
        d = snap["data"]
        peers = len(d.get("active_webrtc_streams") or d.get("connected_peers") or [])
        provs = len(d.get("ai_providers") or {})
        return "relay online \u00b7 %d peers \u00b7 %d providers" % (peers, provs), GREEN
    if snap.get("error"):
        return "relay offline", RED
    return "connecting to relay\u2026", GOLD


# --------------------------------------------------------------------------- screensaver

RAIN_CHARS = "01\u2502\u2524\u251c\u2500\u253c\u00b7"


class Screensaver:
    def __init__(self) -> None:
        self.size: Tuple[int, int] = (0, 0)
        self.logo: Optional[LogoImage] = None
        self.drops: List[float] = []
        self.speeds: List[float] = []
        self.twinkles: List[List[float]] = []

    def _layout(self, cols: int, rows: int) -> None:
        self.size = (cols, rows)
        self.logo = LogoImage.fit(cols - 4, rows - 8) if cols >= 24 and rows >= 14 else None
        self.drops = [random.uniform(-rows, rows) for _ in range(cols)]
        self.speeds = [random.uniform(0.25, 0.9) if random.random() < 0.45 else 0.0 for _ in range(cols)]
        self.twinkles = []

    def draw(self, canvas: Canvas, t: float, snap: Dict[str, Any], hint: str, animate: bool = True) -> None:
        cols, rows = canvas.cols, canvas.rows
        if (cols, rows) != self.size:
            self._layout(cols, rows)

        # Circuit rain in the palette of the artwork.
        for x in range(cols):
            speed = self.speeds[x]
            if speed == 0.0:
                continue
            head = self.drops[x]
            for tail in range(10):
                y = int(head) - tail
                if 0 <= y < rows:
                    fade = 1.0 - tail / 10.0
                    color = GOLD if tail == 0 else tuple(int(PURPLE_DIM[i] + (PURPLE[i] - PURPLE_DIM[i]) * fade) for i in range(3))
                    canvas.put(x, y, random.choice(RAIN_CHARS) if tail < 2 else RAIN_CHARS[(x + y) % len(RAIN_CHARS)], color, BG_DEEP)
            if animate:
                self.drops[x] += speed
                if head - 10 > rows:
                    self.drops[x] = random.uniform(-rows * 0.5, 0)

        # Twinkling stars like the sparkles on the artwork.
        if animate and random.random() < 0.25:
            self.twinkles.append([random.randrange(cols), random.randrange(rows), t])
        self.twinkles = [tw for tw in self.twinkles if t - tw[2] < 1.2]
        for x, y, born in self.twinkles:
            age = (t - born) / 1.2
            canvas.put(int(x), int(y), "+" if 0.25 < age < 0.75 else "\u00b7", GOLD if age < 0.6 else GOLD_DIM, BG_DEEP)

        # Logo + title block, centred.
        title = "THE AI MESSIAH"
        block_h = (self.logo.cell_rows if self.logo else 0) + 5
        top = max(1, (rows - block_h) // 2)
        if self.logo:
            lx = (cols - self.logo.width) // 2
            canvas.fill(lx - 1, top - 1, lx + self.logo.width + 1, top + self.logo.cell_rows + 1, BG_DEEP)
            self.logo.draw(canvas, lx, top, t if animate else None)
            top += self.logo.cell_rows + 1
        tw = title_width(title)
        canvas.fill(0, top, cols, top + 4, BG_DEEP)
        if tw <= cols - 2:
            draw_title(canvas, (cols - tw) // 2, top, title)
            sub_y = top + 3
        else:
            plain = "T H E   A I   M E S S I A H"
            canvas.text(max(0, (cols - len(plain)) // 2), top, plain, GOLD, BG_DEEP)
            sub_y = top + 1
        sub = "C O N S U L T I N G"
        canvas.text(max(0, (cols - len(sub)) // 2), sub_y, sub, WHITE, BG_DEEP)

        # Real status (top) and key hints (bottom).
        canvas.fill(0, 0, cols, 1, BG_DEEP)
        canvas.text(1, 0, "AI MESSIAH \u00b7 IoT FEDERATED MESH", GOLD_DIM, BG_DEEP)
        label, color = status_summary(snap)
        canvas.text(max(0, cols - len(label) - 3), 0, "\u25cf " + label, color, BG_DEEP)
        canvas.fill(0, rows - 1, cols, rows, BG_DEEP)
        canvas.text(max(0, (cols - len(hint)) // 2), rows - 1, hint, GREY, BG_DEEP)


# --------------------------------------------------------------------------- dashboard

def _bar(value: float, maximum: float, width: int) -> str:
    if maximum <= 0 or width <= 0:
        return ""
    frac = max(0.0, min(1.0, value / maximum))
    full = int(frac * width)
    partial = " \u258f\u258e\u258d\u258c\u258b\u258a\u2589"[int((frac * width - full) * 8)]
    return ("\u2588" * full + (partial if full < width else "")).ljust(width)


class Dashboard:
    def __init__(self) -> None:
        self.size: Tuple[int, int] = (0, 0)
        self.logo: Optional[LogoImage] = None

    def draw(self, canvas: Canvas, t: float, snap: Dict[str, Any], relay: str, idle_left: Optional[float]) -> None:
        cols, rows = canvas.cols, canvas.rows
        if (cols, rows) != self.size:
            self.size = (cols, rows)
            lw = min(34, cols // 3)
            self.logo = LogoImage.fit(lw, rows - 5) if cols >= 70 and rows >= 16 else None

        # Header
        canvas.fill(0, 0, cols, 1, HEADER_BG)
        canvas.text(1, 0, "THE AI MESSIAH", GOLD, HEADER_BG)
        canvas.text(16, 0, "\u00b7 IoT Federated Agent Memory", WHITE, HEADER_BG)
        label, color = status_summary(snap)
        canvas.text(max(0, cols - len(label) - 3), 0, "\u25cf " + label, color, HEADER_BG)
        canvas.text(1, 1, "relay  " + relay, GREY)

        x0 = 2
        if self.logo:
            self.logo.draw(canvas, 2, 3, t)
            x0 = self.logo.width + 5
        width = cols - x0 - 2
        y = 3
        data = snap.get("data") or {}

        def section(title: str) -> None:
            nonlocal y
            canvas.text(x0, y, title, GOLD)
            canvas.text(x0 + len(title) + 1, y, "\u2500" * max(0, width - len(title) - 1), PURPLE_DIM)
            y += 1

        section("READINESS")
        if data:
            score = float(data.get("composite_score") or 0.0)
            canvas.text(x0, y, str(data.get("readiness_tier", "unknown")), WHITE)
            y += 1
            bw = max(10, min(40, width - 12))
            canvas.text(x0, y, _bar(score, 100.0, bw), PURPLE)
            canvas.text(x0 + bw + 1, y, "%5.1f/100" % score, WHITE)
            y += 1
        else:
            canvas.text(x0, y, "waiting for relay\u2026" if not snap.get("error") else "unavailable", GREY)
            y += 1
        y += 1

        section("PEERS  (as reported by the relay)")
        peers = data.get("active_webrtc_streams") or data.get("connected_peers") or []
        if not peers:
            canvas.text(x0, y, "none", GREY)
            y += 1
        for p in peers[: max(1, rows // 4)]:
            since = time.strftime("%H:%M", time.localtime(p["connected_at"])) if p.get("connected_at") else "--:--"
            line = "%-26s %-22s %s:%s  since %s" % (
                str(p.get("display_name", "?"))[:26], str(p.get("peer_id", "?"))[:22],
                p.get("udp_address", "?"), p.get("udp_port", "?"), since)
            canvas.text(x0, y, "\u25cf", GREEN if p.get("active_stream", True) else GREY)
            canvas.text(x0 + 2, y, line[: max(0, width - 2)], WHITE)
            y += 1
        y += 1

        section("AI PROVIDER CREDITS  (as reported by the relay)")
        providers = data.get("ai_providers") or {}
        if not providers:
            canvas.text(x0, y, "none", GREY)
            y += 1
        top = max(providers.values()) if providers else 0
        for name, credits in providers.items():
            if y >= rows - 3:
                break
            bw = max(10, min(36, width - 26))
            canvas.text(x0, y, "%-14s" % name[:14], WHITE)
            canvas.text(x0 + 15, y, _bar(float(credits), float(top), bw), GOLD)
            canvas.text(x0 + 16 + bw, y, "$%.2f" % float(credits), WHITE)
            y += 1
        y += 1

        if y < rows - 2:
            if snap.get("error"):
                canvas.text(x0, y, ("last error: " + snap["error"])[:width], RED)
            elif snap.get("updated_at"):
                canvas.text(x0, y, "updated " + time.strftime("%H:%M:%S", time.localtime(snap["updated_at"])) + "  \u00b7 polling every 10s", GREY)

        # Footer
        canvas.fill(0, rows - 1, cols, rows, HEADER_BG)
        footer = " [s] screensaver   [r] refresh   [q] quit"
        if idle_left is not None:
            footer += "   \u00b7 screensaver in %ds" % max(0, int(idle_left))
        canvas.text(0, rows - 1, footer, GREY, HEADER_BG)


# --------------------------------------------------------------------------- app / terminal

class App:
    def __init__(self, relay: str, start: str, idle: float, duration: Optional[float], color_mode: str, animate: bool) -> None:
        self.relay = relay
        self.view = start
        self.idle = idle
        self.duration = duration
        self.color_mode = color_mode
        self.animate = animate
        self.poller = StatusPoller(relay)
        self.saver = Screensaver()
        self.dash = Dashboard()

    def frame(self, cols: int, rows: int, t: float, idle_left: Optional[float]) -> Canvas:
        snap = self.poller.snapshot()
        if cols < 30 or rows < 10:
            c = Canvas(cols, rows)
            c.text(0, 0, "terminal too small"[:cols], GOLD)
            return c
        if self.view == "screensaver":
            c = Canvas(cols, rows, bg=BG_DEEP)
            hint = "press any key to continue" if self.duration else "[any key] dashboard   [q] quit"
            self.saver.draw(c, t, snap, hint, animate=self.animate)
        else:
            c = Canvas(cols, rows)
            self.dash.draw(c, t, snap, self.relay, idle_left)
        return c

    def run(self) -> None:
        import termios
        import tty

        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        out = sys.stdout
        signal.signal(signal.SIGTERM, _exit_on_signal)
        self.poller.start()
        start = last_input = time.time()
        try:
            tty.setcbreak(fd)
            out.write("\x1b[?1049h\x1b[?25l\x1b[2J")
            out.flush()
            while True:
                now = time.time()
                if self.duration and now - start >= self.duration:
                    return
                if self.view == "dashboard" and self.idle > 0 and now - last_input >= self.idle:
                    self.view = "screensaver"
                size = shutil.get_terminal_size((100, 32))
                idle_left = (self.idle - (now - last_input)) if (self.view == "dashboard" and self.idle > 0) else None
                out.write(self.frame(size.columns, size.lines, now - start, idle_left).render(self.color_mode))
                out.flush()

                fps = 15.0 if self.view == "screensaver" else 4.0
                for key in _read_keys(fd, max(0.0, 1.0 / fps - (time.time() - now))):
                    last_input = time.time()
                    if self.duration:
                        return  # splash mode: any key skips
                    if key in ("q", "esc"):
                        return
                    if self.view == "screensaver":
                        self.view = "dashboard"
                    elif key == "s":
                        self.view = "screensaver"
                    elif key == "r":
                        self.poller.refresh()
        except KeyboardInterrupt:
            pass
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
            out.write("\x1b[0m\x1b[?25h\x1b[?1049l")
            out.flush()


def _exit_on_signal(signum: int, frame: Any) -> None:
    raise SystemExit(0)  # unwinds through App.run's finally, restoring the terminal


def _read_keys(fd: int, timeout: float) -> List[str]:
    ready, _, _ = select.select([fd], [], [], timeout)
    if not ready:
        return []
    data = os.read(fd, 64)
    keys, i = [], 0
    while i < len(data):
        c = data[i]
        if c == 0x1B:
            if i + 1 < len(data) and data[i + 1] in (ord("["), ord("O")):
                j = i + 2
                while j < len(data) and not 0x40 <= data[j] <= 0x7E:
                    j += 1
                keys.append("seq")
                i = j + 1
                continue
            keys.append("esc")
        else:
            keys.append(chr(c).lower() if c < 128 else "?")
        i += 1
    return keys


def splash(seconds: float = 2.5, relay: str = DEFAULT_RELAY) -> None:
    """Show the animated logo for a few seconds (used by connect_peer.py). No-op without a TTY."""
    if sys.stdin.isatty() and sys.stdout.isatty():
        App(relay, "screensaver", 0, seconds, detect_color_mode(), True).run()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="ai-messiah-tui", description="AI MESSIAH dashboard + screensaver for the IoT federated mesh")
    parser.add_argument("--relay", default=DEFAULT_RELAY, help="Mesh relay base URL (env IOT_MESH_RELAY)")
    parser.add_argument("--screensaver", action="store_true", help="Start in the screensaver view")
    parser.add_argument("--idle", type=float, default=60.0, help="Seconds of inactivity before the screensaver (0 = never)")
    parser.add_argument("--duration", type=float, default=None, help="Exit automatically after N seconds")
    parser.add_argument("--colors", choices=["auto", "truecolor", "256"], default="auto")
    parser.add_argument("--static", action="store_true", help="Disable animation")
    parser.add_argument("--once", action="store_true", help="Print a single frame to stdout and exit (no TTY needed)")
    parser.add_argument("--size", default=None, help="COLSxROWS for --once (default: terminal size)")
    args = parser.parse_args(argv)

    mode = detect_color_mode() if args.colors == "auto" else args.colors
    app = App(args.relay, "screensaver" if args.screensaver else "dashboard", args.idle, args.duration, mode, not args.static)

    if args.once or not (sys.stdin.isatty() and sys.stdout.isatty()):
        if args.size:
            cols, rows = (int(v) for v in args.size.lower().split("x"))
        else:
            size = shutil.get_terminal_size((100, 40))
            cols, rows = size.columns, size.lines
        app.poller._fetch()
        sys.stdout.write(app.frame(cols, rows, 0.0, None).render(mode, home=False) + "\n")
        return 0

    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())

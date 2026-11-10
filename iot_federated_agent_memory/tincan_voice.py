"""Local & Remote Voice (TTS) Integration for TinCan (`kokoro-say` & macOS `say`)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from typing import Any, Dict, List, Optional


def find_tts_binary() -> Optional[str]:
    """Locate kokoro-say or platform fallback TTS binary."""
    kokoro_default = os.path.expanduser("~/.local/bin/kokoro-say")
    if os.path.isfile(kokoro_default) and os.access(kokoro_default, os.X_OK):
        return kokoro_default

    which_kokoro = shutil.which("kokoro-say")
    if which_kokoro:
        return which_kokoro

    if sys.platform == "darwin" and os.path.isfile("/usr/bin/say"):
        return "/usr/bin/say"

    which_espeak = shutil.which("espeak")
    if which_espeak:
        return which_espeak

    return None


def speak_text(
    text: str,
    voice: Optional[str] = None,
    background: bool = True,
) -> Dict[str, Any]:
    """Vocalize text aloud using local Kokoro-82M (`kokoro-say`) or system TTS fallback."""
    clean_text = (text or "").strip()
    if not clean_text:
        return {"status": "skipped", "engine": "none", "reason": "empty_text"}

    binary = find_tts_binary()
    if not binary:
        return {"status": "unavailable", "engine": "none", "text": clean_text}

    engine_name = "kokoro-say" if "kokoro-say" in os.path.basename(binary) else os.path.basename(binary)
    cmd: List[str] = [binary]

    if engine_name == "kokoro-say":
        if background:
            cmd.append("--bg")
        if voice:
            cmd.extend(["-v", voice])
        cmd.append(clean_text)
    elif binary == "/usr/bin/say":
        if voice:
            cmd.extend(["-v", voice])
        cmd.append(clean_text)
    else:
        cmd.append(clean_text)

    try:
        if binary == "/usr/bin/say" and background:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=15)
        return {
            "status": "spoken",
            "engine": engine_name,
            "binary": binary,
            "voice": voice,
            "background": background,
            "text": clean_text,
        }
    except Exception as exc:
        return {
            "status": "error",
            "engine": engine_name,
            "error": str(exc),
            "text": clean_text,
        }

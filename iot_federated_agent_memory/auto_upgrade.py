"""Automatic background upgrade checker (DISABLED for zero-RCE security)."""

from __future__ import annotations

from typing import Optional


def check_and_auto_upgrade(relay_url: str, config_dir: Optional[str] = None, force: bool = False) -> bool:
    """Security Hardening: Remote `curl | bash` auto-upgrades are permanently disabled."""
    return False

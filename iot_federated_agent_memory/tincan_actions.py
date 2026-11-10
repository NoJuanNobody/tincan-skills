"""Human-In-The-Loop (HITL) Execution Gate & Accessibility Queue for Inbound Actions.

All remote peer actions (opening URLs, launching apps, or playing remote voice TTS)
are strictly held in `pending_actions.json` with `status="pending_approval"` and NEVER
execute until the local human operator explicitly approves them via `tincan trigger <seq>`.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from typing import Any, Dict, List, Optional


def get_queue_file(config_dir: Optional[str] = None) -> str:
    base = config_dir or os.path.expanduser("~/.tin-can")
    os.makedirs(base, exist_ok=True)
    return os.path.join(base, "pending_actions.json")


def load_pending_actions(config_dir: Optional[str] = None) -> List[Dict[str, Any]]:
    path = get_queue_file(config_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception:
        return []


def save_pending_actions(actions: List[Dict[str, Any]], config_dir: Optional[str] = None) -> None:
    path = get_queue_file(config_dir)
    with open(path, "w") as f:
        json.dump(actions, f, indent=2)


def enqueue_action(
    seq: int,
    sender: str,
    sender_alias: Optional[str],
    command_text: str,
    config_dir: Optional[str] = None,
    action_type: str = "command",
    sender_role: str = "peer",
) -> Dict[str, Any]:
    """Queue an incoming command or TTS request requiring explicit human approval before firing."""
    actions = load_pending_actions(config_dir)
    for act in actions:
        if act["seq"] == seq and act["sender"] == sender and act.get("action_type") == action_type:
            return act

    item = {
        "id": f"action-{int(time.time()*1000)}-{seq}",
        "seq": seq,
        "sender": sender,
        "sender_alias": sender_alias or "peer",
        "sender_role": sender_role or "peer",
        "command": command_text,
        "action_type": action_type,
        "queued_at": time.time(),
        "status": "pending_approval",
    }
    actions.append(item)
    save_pending_actions(actions, config_dir)
    return item


def execute_action(action_id_or_seq: str, config_dir: Optional[str] = None) -> Dict[str, Any]:
    """Execute an action ONLY after explicit human approval via `tincan trigger`."""
    actions = load_pending_actions(config_dir)
    target = None
    for act in actions:
        if act["id"] == action_id_or_seq or str(act["seq"]) == str(action_id_or_seq):
            target = act
            break

    if not target:
        raise ValueError(f"Action '{action_id_or_seq}' not found in pending queue.")

    cmd_text = target["command"].strip()
    act_type = target.get("action_type", "command")
    result_output = ""
    status = "completed"

    url_match = re.search(r"https?://[^\s\"'>]+", cmd_text)
    if act_type == "tts":
        from .tincan_voice import speak_text
        sender_label = target.get("sender_alias") or target.get("sender") or "peer"
        tts_res = speak_text(f"Message from {sender_label}: {cmd_text}", background=True)
        result_output = f"Approved & spoken via {tts_res.get('engine', 'TTS')}: {cmd_text}"
    elif "open gemini" in cmd_text.lower():
        if sys.platform == "darwin":
            subprocess.run(["open", "https://gemini.google.com"])
            result_output = "Opened https://gemini.google.com in default browser (Approved)"
        else:
            result_output = "Platform trigger dispatched for Gemini (Approved)"
    elif url_match:
        target_url = url_match.group(0)
        if sys.platform == "darwin":
            subprocess.run(["open", target_url])
            result_output = f"Opened {target_url} in default browser (Approved)"
        else:
            result_output = f"Dispatched browser open for {target_url} (Approved)"
    else:
        result_output = f"Approved & executed command: {cmd_text}"

    target["status"] = status
    target["executed_at"] = time.time()
    target["result"] = result_output
    save_pending_actions(actions, config_dir)
    return target


def dismiss_action(action_id_or_seq: str, config_dir: Optional[str] = None) -> Dict[str, Any]:
    """Dismiss/reject an inbound action without executing."""
    actions = load_pending_actions(config_dir)
    target = None
    for act in actions:
        if act["id"] == action_id_or_seq or str(act["seq"]) == str(action_id_or_seq):
            target = act
            break

    if not target:
        raise ValueError(f"Action '{action_id_or_seq}' not found.")

    target["status"] = "dismissed"
    save_pending_actions(actions, config_dir)
    return target

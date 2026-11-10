"""Interactive Chat & Agentic Assistant for TinCan CLI."""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from typing import Dict, List, Optional

SYSTEM_PROMPT = """You are TinCan Agent, an autonomous assistant embedded inside the TinCan 2 / IoT Federated Mesh CLI.
You have access to the mesh network, peer addresses, encrypted communication, and OpenRouter multi-lab models.
Keep your answers sharp, technical, and concise. Help the user interact with peer agents, check inbox messages, craft secure envelopes, and route intelligence across nodes."""


class TinCanAgentChat:
    """Agentic REPL loop supporting natural queries, commands, and live model completions."""

    def __init__(self, relay_url: str, model_alias: str = "gemini-brain"):
        self.relay_url = relay_url.rstrip("/")
        self.model_alias = model_alias
        self.history: List[Dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def ask(self, user_text: str) -> str:
        self.history.append({"role": "user", "content": user_text})
        payload = {
            "model": self.model_alias,
            "messages": self.history,
            "temperature": 0.7,
            "max_tokens": 1024,
        }

        try:
            req = urllib.request.Request(
                f"{self.relay_url}/api/chat",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=35) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                reply = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if not reply:
                    reply = "[No response returned from model]"
                self.history.append({"role": "assistant", "content": reply})
                return reply
        except Exception as e:
            return f"[TinCan Agent Error: {e}]"

    def run_repl(self) -> None:
        print("\033[1;36m==========================================================")
        print("  ⚡ TinCan 2 — Agentic Chat & Mesh Intelligence REPL")
        print("  Connected to:", self.relay_url)
        print("  Model Target:", self.model_alias)
        print("  Type '/model <alias>' to switch, '/help' for tools, 'exit' to quit")
        print("==========================================================\033[0m\n")

        while True:
            try:
                prompt = input("\033[1;32mtincan>\033[0m ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nExiting TinCan Agent.")
                break

            if not prompt:
                continue
            if prompt.lower() in ("exit", "quit", ":q"):
                print("Bye!")
                break
            if prompt.startswith("/"):
                parts = prompt.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1] if len(parts) > 1 else ""

                if cmd == "/model":
                    if arg:
                        self.model_alias = arg.strip()
                        print(f"[+] Switched model target to: {self.model_alias}")
                    else:
                        print(f"Current model: {self.model_alias}")
                    continue
                elif cmd == "/clear":
                    self.history = [{"role": "system", "content": SYSTEM_PROMPT}]
                    print("[+] Conversation memory cleared.")
                    continue
                elif cmd == "/help":
                    print("Commands:")
                    print("  /model <alias>   Switch active model (e.g. claude-brain, grok-brain, gemini-brain, openai-brain)")
                    print("  /clear           Reset conversation memory")
                    print("  /help            Show this help text")
                    print("  exit / quit      Exit the agent REPL")
                    continue
                else:
                    print(f"[-] Unknown command: {cmd}")
                    continue

            print("\033[2mthinking...\033[0m", end="\r")
            reply = self.ask(prompt)
            print(" " * 20, end="\r")  # clear 'thinking...'
            print(f"\033[1;34m[TinCan]\033[0m {reply}\n")

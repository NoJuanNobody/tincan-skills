"""
TinCan Client & Relay CLI Interface.

Supports:
  whoami                    Inspect local cryptographic identity and address
  send <recipient> <msg>    Encrypt, sign, and post sealed ciphertext to relay
  read [--since <seq>]      Fetch inbox, decrypt using private key, verify signatures
  contacts                  List pinned contacts (TOFU)
  add-contact <alias> <tc>  Pin a trusted contact address
  mcp                       Run standard MCP stdio server
  serve [--port 8080]       Run standalone TinCan Blind Relay server
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import List, Optional

from .tincan_mcp import TinCanMCPClient, run_stdio_server
from .tincan_relay import TinCanBlindRelay


def main(argv: Optional[List[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        prog="tincan",
        description="TinCan Agent-to-Agent Encrypted Messaging & Blind Relay CLI",
    )
    parser.add_argument("--dir", default=None, help="Directory for identities & contacts (~/.tin-can)")
    parser.add_argument(
        "--relay",
        default=os.environ.get("TINCAN_RELAY", "https://iot-federated-agent-memory-production.up.railway.app"),
        help="Relay server URL (default: live Railway production relay)",
    )
    parser.add_argument("--as", dest="alias", default="default", help="Identity alias to use (default: 'default')")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    subparsers = parser.add_subparsers(dest="command", help="TinCan commands")

    # whoami
    who_p = subparsers.add_parser("whoami", help="Display current local identity and TinCan address")
    who_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # register
    reg_p = subparsers.add_parser("register", help="Register a username and create an account to receive token credits")
    reg_p.add_argument("--username", "-u", help="Desired username / display name")
    reg_p.add_argument("--email", "-e", help="Account email address for billing receipts")
    reg_p.add_argument("--phone", "-p", default="", help="Contact phone number (optional)")
    reg_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # send
    send_parser = subparsers.add_parser("send", help="Send sealed message to a recipient address or contact alias")
    send_parser.add_argument("recipient", help="Recipient TinCan address (tc:...) or contact alias")
    send_parser.add_argument("message", help="Message text to send")
    send_parser.add_argument("--speak", action="store_true", help="Request vocalization via TTS")
    send_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # read
    read_parser = subparsers.add_parser("read", help="Fetch and decrypt inbox messages")
    read_parser.add_argument("--since", type=int, default=0, help="Fetch messages after this sequence number")
    read_parser.add_argument("--timeout", type=float, default=0.0, help="Long-poll timeout in seconds")
    read_parser.add_argument("--speak", action="store_true", help="Speak all unread messages aloud via TTS")
    read_parser.add_argument("--no-speak", action="store_true", help="Disable automatic TTS vocalization")
    read_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # say (local + remote voice TTS)
    say_p = subparsers.add_parser("say", help="Speak text aloud via Kokoro TTS and optionally send spoken message to a peer")
    say_p.add_argument("text", help="Text to vocalize")
    say_p.add_argument("--voice", default=None, help="Optional voice name (e.g. bella, michael)")
    say_p.add_argument("--to", default=None, help="Optional recipient alias or tc: address to also send spoken message")
    say_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # call / video (live WebRTC video, voice & screenshare room)
    for call_cmd in ("call", "video"):
        call_p = subparsers.add_parser(call_cmd, help="Launch live WebRTC Video, Voice & Screenshare call room")
        call_p.add_argument("recipient", nargs="?", default=None, help="Optional contact alias or tc: address to invite")
        call_p.add_argument("--room", default="main", help="WebRTC room name (default: main)")
        call_p.add_argument("--voice-only", action="store_true", help="Start in voice-only microphone mode")
        call_p.add_argument("--screen", action="store_true", help="Start with desktop screenshare enabled")
        call_p.add_argument("--no-browser", action="store_true", help="Do not automatically open local browser")
        call_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # contacts
    contacts_p = subparsers.add_parser("contacts", help="List pinned contacts")
    contacts_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # add-contact
    add_parser = subparsers.add_parser("add-contact", help="Pin a contact's public key (TOFU) with optional Mentor/Mentee role")
    add_parser.add_argument("alias", help="Human-readable alias name")
    add_parser.add_argument("address", help="TinCan address (tc:<52 base32 chars>)")
    add_parser.add_argument("--role", default="peer", choices=["admin", "moderator", "mentor", "mentee", "peer"], help="Relationship role (admin, moderator, mentor, mentee, peer)")
    add_parser.add_argument("--allow-voice", action="store_true", help="Pre-approve live TTS voice coaching from this Mentor")
    add_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # mentor (Mentor-Mentee coaching, guidance & hand-raise protocol)
    mentor_p = subparsers.add_parser("mentor", help="Manage Mentor-Mentee relationships, guided walkthroughs, and hand-raises")
    mentor_p.add_argument("action", nargs="?", default="status", choices=["status", "set", "guide", "hand"], help="Action (status, set, guide, hand)")
    mentor_p.add_argument("target", nargs="?", default=None, help="Contact alias (for 'set'/'guide') or topic (for 'hand')")
    mentor_p.add_argument("message", nargs="?", default=None, help="Guidance instruction or URL (for 'guide')")
    mentor_p.add_argument("--role", default="mentor", choices=["mentor", "mentee", "peer"], help="Role to assign when using 'set'")
    mentor_p.add_argument("--allow-voice", action="store_true", help="Allow trusted Mentor voice coaching to play without gating")
    mentor_p.add_argument("--gate-voice", action="store_true", help="Require explicit approval gate for Mentor voice coaching")
    mentor_p.add_argument("--speak", action="store_true", help="Attach spoken TTS coaching flag when sending 'guide'")
    mentor_p.add_argument("--mentor", default=None, help="Specific Mentor alias to notify when raising 'hand'")
    mentor_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # mcp
    subparsers.add_parser("mcp", help="Start MCP server over stdio")

    # screensaver / start
    start_p = subparsers.add_parser("start", help="Launch the full terminal screensaver and live mesh dashboard")
    start_p.add_argument("--duration", type=float, default=None, help="Exit after N seconds")

    ss_p = subparsers.add_parser("screensaver", help="Alias for 'start'")
    ss_p.add_argument("--duration", type=float, default=None, help="Exit after N seconds")

    # chat / agent
    chat_p = subparsers.add_parser("chat", help="Start interactive agentic chat REPL with the live OpenRouter models")
    chat_p.add_argument("prompt", nargs="?", default=None, help="Single-shot prompt to send to the agent")
    chat_p.add_argument("--model", default="gemini-brain", help="Model alias to use (default: gemini-brain)")

    agent_p = subparsers.add_parser("ask", help="Single-shot query to the TinCan Agent")
    agent_p.add_argument("prompt", help="Prompt question for the agent")
    agent_p.add_argument("--model", default="gemini-brain", help="Model alias to use")

    # actions / accessibility queue
    act_p = subparsers.add_parser("actions", help="List and review incoming actions queued for approval (Accessibility Gate)")
    act_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    run_act_p = subparsers.add_parser("trigger", help="Approve and trigger an incoming queued action (e.g. 'tincan trigger 1')")
    run_act_p.add_argument("action", help="Sequence number or action ID to execute")
    run_act_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    dismiss_act_p = subparsers.add_parser("dismiss", help="Dismiss a queued action without executing")
    dismiss_act_p.add_argument("action", help="Sequence number or action ID to dismiss")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Run local standalone TinCan Blind Relay")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    serve_parser.add_argument("--db", default=":memory:", help="SQLite database path (default: :memory:)")

    # playlist
    pl_parser = subparsers.add_parser("playlist", help="Manage the Relay Video Channel & Collection Playlist")
    pl_parser.add_argument("action", nargs="?", default="list", choices=["list", "add", "remove"], help="Action (list, add, remove)")
    pl_parser.add_argument("target", nargs="?", default=None, help="TikTok URL, video ID, embed snippet, or item ID")
    pl_parser.add_argument("--title", default=None, help="Optional title for the video")
    pl_parser.add_argument("--category", default="spotlight", help="Category tag (instruction, ad, spotlight)")
    pl_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # status / ping (check if a peer is on their computer)
    for st_cmd in ("status", "ping"):
        st_parser = subparsers.add_parser(st_cmd, help="Check if a peer is online / on their computer and inspect read receipts")
        st_parser.add_argument("peer", nargs="?", default="harper", help="Contact alias or tc: address (default: harper)")
        st_parser.add_argument("--mesh", action="store_true", help="Display all live website visitors and mesh nodes")
        st_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # who / peers / mesh / roster (inspect who is on the website and connected to the mesh)
    for who_cmd in ("who", "peers", "mesh", "roster"):
        who_p = subparsers.add_parser(who_cmd, help="List who is currently on the relay website and connected to the mesh")
        who_p.add_argument("--room", default="main", help="Filter by room name (default: main)")
        who_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # admin (admin moderator commands)
    admin_p = subparsers.add_parser("admin", help="Admin moderator tools for TinCan mesh & relay")
    admin_sub = admin_p.add_subparsers(dest="admin_action", help="Admin actions")

    admin_who = admin_sub.add_parser("who", help="Inspect all website visitors and connected mesh peers")
    admin_who.add_argument("--room", default="main", help="Filter by room name (default: main)")
    admin_who.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    admin_kick = admin_sub.add_parser("kick", help="Kick / disconnect a peer or web client from the mesh")
    admin_kick.add_argument("peer", help="Peer ID to disconnect")
    admin_kick.add_argument("--room", default="main", help="Room name (default: main)")
    admin_kick.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    admin_bc = admin_sub.add_parser("broadcast", help="Broadcast a system-wide high-priority moderator announcement")
    admin_bc.add_argument("text", help="Announcement message")
    admin_bc.add_argument("--room", default="main", help="Room name (default: main)")
    admin_bc.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    admin_role = admin_sub.add_parser("role", help="Set role for self or a contact (admin, moderator, mentor, mentee, peer)")
    admin_role.add_argument("target", nargs="?", default="self", help="Contact alias or 'self' (default: self)")
    admin_role.add_argument("role_val", nargs="?", default="admin", help="Role (admin, moderator, mentor, mentee, peer)")
    admin_role.add_argument("--role", default=None, choices=["admin", "moderator", "mentor", "mentee", "peer"], help="Role to assign")
    admin_role.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # credits / cost (live OpenRouter cost & credit dashboard)
    for cr_cmd in ("credits", "cost"):
        cr_parser = subparsers.add_parser(cr_cmd, help="Display live OpenRouter account credits, spend, and per-model cost rates")
        cr_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # disconnect / leave / close
    for disc_cmd in ("disconnect", "leave", "close"):
        disc_parser = subparsers.add_parser(disc_cmd, help="Disconnect a peer node or close connection to WebRTC mesh room")
        disc_parser.add_argument("peer", nargs="?", help="Peer ID to disconnect (e.g. peer-2i6pm0, or default current identity)")
        disc_parser.add_argument("--room", default="main", help="WebRTC room name (default: main)")
        disc_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # msg / broadcast (live room chat)
    for msg_cmd in ("msg", "broadcast"):
        msg_parser = subparsers.add_parser(msg_cmd, help="Broadcast a real-time message to all peers in a WebRTC room")
        msg_parser.add_argument("text", help="Message text to broadcast to peers")
        msg_parser.add_argument("--room", default="main", help="WebRTC room name (default: main)")
        msg_parser.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # upgrade
    upg_p = subparsers.add_parser("upgrade", help="Upgrade TinCan CLI and mesh bundles to the latest production release (Approval-Gated)")
    upg_p.add_argument("--yes", "-y", action="store_true", help="Approve upgrade non-interactively")

    # board (Cyberspace Discussion Board · GraphRAG + BM25)
    board_p = subparsers.add_parser("board", help="Cyberspace Discussion Board (Topics, @username/@agent tags, GraphRAG + BM25 search)")
    board_p.add_argument("board_action", nargs="?", default="list", choices=["list", "new", "reply", "search", "graph"], help="Board action")
    board_p.add_argument("target", nargs="?", default=None, help="Search query, Topic Title (for 'new'), or Topic ID (for 'reply')")
    board_p.add_argument("body", nargs="?", default=None, help="Topic body (for 'new') or reply text (for 'reply')")
    board_p.add_argument("--category", default="cyberspace", help="Topic category (default: cyberspace)")
    board_p.add_argument("--mode", default="hybrid", choices=["hybrid", "graphrag", "bm25"], help="Search retrieval mode (hybrid, graphrag, bm25)")
    board_p.add_argument("--username", "-u", default=None, help="Author @username handle")
    board_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # verify (Identity Verification Agent @verifier-agent)
    verify_p = subparsers.add_parser("verify", help="Identity Verification Agent (@verifier-agent) form dispatch and attestation")
    verify_p.add_argument("verify_action", nargs="?", default="status", choices=["status", "send-form", "submit"], help="Verification action")
    verify_p.add_argument("--peer", default=None, help="Target peer ID")
    verify_p.add_argument("--name", default=None, help="Full Legal Name (for 'submit')")
    verify_p.add_argument("--username", "-u", default=None, help="Cyberspace @username (for 'send-form' or 'submit')")
    verify_p.add_argument("--email", "-e", default=None, help="Contact Email (for 'submit')")
    verify_p.add_argument("--phone", "-p", default=None, help="Phone Number (for 'submit')")
    verify_p.add_argument("--role", default="FAU Graduate School / Academic", help="Affiliation / Role")
    verify_p.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    args = parser.parse_args(argv)

    # Privacy & Consent Guard: Automatic background `curl | bash` upgrades are disabled.
    # Upgrades only run when the operator explicitly invokes `tincan upgrade`.

    if not args.command:
        # Default bare command: launch the interactive screensaver / live mesh TUI
        from .tui import main as tui_main
        return tui_main(["--screensaver", "--relay", args.relay])

    if args.command == "upgrade":
        import subprocess
        print(f"[*] Checking release status on {args.relay}/api/version...")
        approved = getattr(args, "yes", False)
        if not approved and sys.stdin.isatty():
            ans = input(f"Approve upgrading TinCan CLI & skills from {args.relay}? [y/N]: ").strip().lower()
            approved = ans in ("y", "yes")
        if not approved:
            print("[!] Upgrade cancelled (requires explicit approval or `tincan upgrade --yes`).")
            return 0
        cmd = f"curl -sSL {args.relay}/install.sh | bash"
        res = subprocess.run(cmd, shell=True)
        return res.returncode

    if args.command == "mcp":
        client = TinCanMCPClient(relay_url=args.relay, config_dir=args.dir, alias=args.alias)
        run_stdio_server(client)
        return 0

    if args.command == "serve":
        from http.server import ThreadingHTTPServer
        from .tincan_relay import TinCanBlindRelay

        relay_instance = TinCanBlindRelay(db_path=args.db)
        from ..server import MeshGatewayHandler
        print(f"[*] Starting TinCan Blind Relay on 127.0.0.1:{args.port} (db: {args.db})...")
        server = ThreadingHTTPServer(("127.0.0.1", args.port), MeshGatewayHandler)
        server.serve_forever()
        return 0

    client = TinCanMCPClient(relay_url=args.relay, config_dir=args.dir, alias=args.alias)

    if args.command == "whoami":
        info = client.tincan_whoami()
        if args.json:
            print(json.dumps(info, indent=2))
        else:
            role_str = str(info.get("role", "peer")).upper()
            if role_str in ("ADMIN", "MODERATOR"):
                role_badge = "\033[1;33m🛡️ ADMIN MODERATOR\033[0m"
            elif role_str == "MENTOR":
                role_badge = "\033[1;32m🎓 MENTOR\033[0m"
            elif role_str == "MENTEE":
                role_badge = "\033[1;36m🌱 MENTEE\033[0m"
            else:
                role_badge = "🤝 PEER"
            print(f"TinCan Identity: {info['alias']}")
            print(f"Role:            {role_badge}")
            print(f"Address:         {info['address']}")
            print(f"Public Key (hex): {info['public_key']}")
            print(f"Relay:           {info['relay_url']}")
            print(f"Pinned Contacts: {info['contacts_count']}")

            # Check for registered billing account
            try:
                from .account_registry import PeerAccountRegistry
                acc = PeerAccountRegistry().get_account_by_peer(info['address'])
                if acc:
                    print(f"Account:         \033[1;32m@{acc['full_name']}\033[0m ({acc['email']})")
                    print(f"Token Balance:   \033[1;33m{acc['token_balance']:,} Tokens\033[0m (\033[1;36m${acc['credit_balance_usd']:.2f} USD\033[0m)")
                else:
                    print("Account:         \033[0;33mUnregistered\033[0m (Run `tincan register` to claim 50,000 starter tokens)")
            except Exception:
                pass
        return 0

    if args.command == "register":
        username = getattr(args, "username", None)
        if not username:
            try:
                username = input("Enter username / display name: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[!] Registration cancelled.")
                return 1
        if not username:
            print("[!] Username cannot be empty.")
            return 1

        email = getattr(args, "email", None)
        if not email:
            try:
                email = input("Enter email address: ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\n[!] Registration cancelled.")
                return 1
        if not email or "@" not in email:
            print("[!] Valid email is required for billing and token receipts.")
            return 1

        phone = getattr(args, "phone", None) or "+10000000000"

        info = client.tincan_whoami()
        peer_id = info.get("address") or info.get("identity") or client.alias

        from .account_registry import PeerAccountRegistry
        registry = PeerAccountRegistry()
        try:
            acc = registry.register_account(
                peer_id=peer_id,
                full_name=username,
                phone_number=phone,
                email=email,
            )
            acc_file = os.path.join(client.config_dir, "account.json")
            try:
                with open(acc_file, "w") as f:
                    json.dump(acc, f, indent=2)
            except Exception:
                pass

            if getattr(args, "json", False):
                print(json.dumps(acc, indent=2))
            else:
                print("\n\033[1;32m═══════════════════════════════════════════════════════════════\033[0m")
                print(f"\033[1;32m🎉 Account Successfully Created for @{username}!\033[0m")
                print(f"  • Peer Address:   {acc['peer_id']}")
                print(f"  • Email:          {acc['email']}")
                print(f"  • Token Balance:  \033[1;33m{acc['token_balance']:,} Tokens\033[0m")
                print(f"  • Credit Balance: \033[1;36m${acc['credit_balance_usd']:.2f} USD\033[0m")
                print("\033[1;32m═══════════════════════════════════════════════════════════════\033[0m\n")
            return 0
        except Exception as e:
            if getattr(args, "json", False):
                print(json.dumps({"error": str(e)}, indent=2))
            else:
                print(f"[!] Registration failed: {e}")
            return 1

    if args.command == "send":
        try:
            res = client.tincan_send(recipient_address=args.recipient, message=args.message, speak=args.speak)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"[+] Message sent! Seq: {res.get('seq')}, Envelope ID: {res.get('envelope_id')}")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Send failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "read":
        try:
            from .tincan_actions import enqueue_action
            from .tincan_voice import speak_text
            msgs = client.tincan_read(since_seq=args.since, timeout=args.timeout)
            if args.json:
                print(json.dumps(msgs, indent=2))
            else:
                if not msgs:
                    print("Inbox empty (no new messages).")
                for m in msgs:
                    sender_label = m.get("sender_alias") or m.get("sender")
                    sender_role = str(m.get("sender_role", "peer")).lower()
                    if sender_role in ("admin", "moderator"):
                        role_badge = " \033[1;33m[🛡️ ADMIN MODERATOR]\033[0m"
                    elif sender_role == "mentor":
                        role_badge = " \033[1;32m[🎓 MENTOR]\033[0m"
                    elif sender_role == "mentee":
                        role_badge = " \033[1;36m[🌱 MENTEE]\033[0m"
                    else:
                        role_badge = ""
                    ver_badge = "✓ verified" if m.get("verified") else "✗ unverified"
                    # Approval Gate for Speaker Peripheral: Play immediately if user passed --speak OR
                    # if sender is a pinned Mentor with explicit `trust_mentor_tts` enabled by the Mentee;
                    # otherwise queue in the Accessibility Gate!
                    mentor_trusted_tts = (sender_role == "mentor") and bool(m.get("sender_trust_mentor_tts"))
                    should_speak_now = (bool(args.speak) or (bool(m.get("speak")) and mentor_trusted_tts)) and not bool(args.no_speak)
                    speak_badge = (
                        " [🔊 TTS spoken]"
                        if should_speak_now
                        else (" [🔒 TTS queued for approval]" if m.get("speak") else "")
                    )
                    print(f"[{m.get('seq')}] From: {sender_label}{role_badge} ({ver_badge}){speak_badge}")
                    print(f"    {m.get('message')}")

                    msg_txt = m.get("message", "")
                    if should_speak_now and msg_txt:
                        speak_text(f"Message from {sender_label}: {msg_txt}", background=True)
                    elif m.get("speak") and msg_txt and not bool(args.no_speak):
                        enqueue_action(
                            seq=m.get("seq", 0),
                            sender=m.get("sender", ""),
                            sender_alias=m.get("sender_alias"),
                            command_text=msg_txt,
                            config_dir=args.dir,
                            action_type="tts",
                            sender_role=sender_role,
                        )
                        gate_label = "🎓 Mentor Voice Coaching" if sender_role == "mentor" else "🔊 Voice playback"
                        print(f"    \033[33m{gate_label} gated [seq {m.get('seq')}]. Run 'tincan trigger {m.get('seq')}' to approve & play aloud.\033[0m")

                    # Automatically enqueue actionable requests into the Accessibility Gate
                    if any(keyword in msg_txt.lower() for keyword in ["open", "run", "launch", "execute", "start", "call", "join", "[mentor guidance]", "[mentee hand raise]"]):
                        act = enqueue_action(
                            seq=m.get("seq", 0),
                            sender=m.get("sender", ""),
                            sender_alias=m.get("sender_alias"),
                            command_text=msg_txt,
                            config_dir=args.dir,
                            action_type="command",
                            sender_role=sender_role,
                        )
                        q_label = "🎓 Mentor Guidance Step" if sender_role == "mentor" else ("✋ Mentee Review Request" if sender_role == "mentee" else "⚡ Action")
                        print(f"    \033[33m{q_label} queued in Accessibility Gate [seq {m.get('seq')}]. Run 'tincan trigger {m.get('seq')}' to approve & execute.\033[0m")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Read failed: {exc}", file=sys.stderr)
            return 1

    if args.command == "say":
        from .tincan_voice import speak_text
        tts_res = speak_text(args.text, voice=args.voice, background=True)
        send_res = None
        if args.to:
            try:
                send_res = client.tincan_send(recipient_address=args.to, message=args.text, speak=True)
            except Exception as exc:
                send_res = {"error": str(exc)}
        out = {"tts": tts_res, "sent": send_res}
        if args.json:
            print(json.dumps(out, indent=2))
        else:
            print(f"\033[1;32m🔊 Spoken via {tts_res.get('engine')}:\033[0m \"{args.text}\"")
            if send_res:
                if "error" in send_res:
                    print(f"[-] Remote send failed: {send_res['error']}", file=sys.stderr)
                else:
                    print(f"[+] Sent vocalized envelope to {args.to} (seq {send_res.get('seq')})")
        return 0

    if args.command in ("call", "video"):
        import subprocess
        import urllib.parse
        import urllib.request

        room = args.room or "main"
        mode = "screen" if args.screen else ("voice" if args.voice_only else "video")
        # Privacy Guard: Use registered operator identity when available instead of anonymous default-*
        anon_id = client.public_key_hex[:8]
        peer_id = f"{args.alias}-{anon_id}"
        display_name = f"{args.alias} ({anon_id})"
        acc_file = os.path.join(client.config_dir, "account.json")
        if os.path.isfile(acc_file):
            try:
                with open(acc_file, "r") as f:
                    acc_data = json.load(f)
                fn = (acc_data.get("full_name") or "").strip()
                un = (acc_data.get("username") or "").strip()
                if fn and un:
                    display_name = f"{fn} (@{un})"
                elif fn:
                    display_name = fn
            except Exception:
                pass
        relay_base = args.relay.rstrip("/")
        call_url = f"{relay_base}/?room={urllib.parse.quote(room)}&peer={urllib.parse.quote(peer_id)}&mode={mode}#call"

        # Register peer session on relay WebRTC room (peripherals default to False until browser consent)
        reg_payload = {
            "peer_id": peer_id,
            "display_name": display_name,
            "room": room,
            "has_video": False,
            "has_audio": False,
            "has_screen": False,
        }
        try:
            req = urllib.request.Request(
                f"{relay_base}/api/webrtc/register",
                data=json.dumps(reg_payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                json.loads(resp.read().decode("utf-8"))
        except Exception:
            pass

        invite_res = None
        if args.recipient:
            try:
                invite_msg = f"Incoming TinCan {mode.upper()} Call in room '{room}'! Open {call_url} to join."
                invite_res = client.tincan_send(
                    recipient_address=args.recipient,
                    message=invite_msg,
                    speak=True,
                )
            except Exception as exc:
                invite_res = {"error": str(exc)}

        # When the local user explicitly runs `tincan call`, open the call studio unless --no-browser is set.
        if not args.no_browser and sys.platform == "darwin":
            try:
                subprocess.run(["open", call_url], check=False)
            except Exception:
                pass

        result_info = {
            "status": "call_ready",
            "room": room,
            "mode": mode,
            "peer_id": peer_id,
            "call_url": call_url,
            "invite": invite_res,
        }
        if args.json:
            print(json.dumps(result_info, indent=2))
        else:
            print(f"\033[1;36m📹 TinCan Live WebRTC {mode.upper()} Room Ready:\033[0m")
            print(f"  Room:     {room}")
            print(f"  Join URL: {call_url}")
            if invite_res:
                if "error" in invite_res:
                    print(f"  Invite:   [-] Failed to notify {args.recipient}: {invite_res['error']}")
                else:
                    print(f"  Invite:   ✓ Sent encrypted + spoken call invite to {args.recipient} (seq {invite_res.get('seq')})")
        return 0

    if args.command == "actions":
        from .tincan_actions import load_pending_actions
        actions = load_pending_actions(args.dir)
        if args.json:
            print(json.dumps(actions, indent=2))
        else:
            pending = [a for a in actions if a.get("status") == "pending_approval"]
            if not pending:
                print("No pending actions awaiting approval.")
            else:
                print("\033[1;36m=== Pending Inbound Actions (Mentor & Peer Accessibility Gate) ===\033[0m")
                for a in pending:
                    s_role = a.get("sender_role", "peer")
                    r_tag = "🎓 MENTOR" if s_role == "mentor" else ("🌱 MENTEE" if s_role == "mentee" else "PEER")
                    a_type = "🔊 TTS" if a.get("action_type") == "tts" else "⚡ CMD"
                    print(f"[{a['seq']}] [{r_tag} · {a_type}] From {a['sender_alias']}: \"{a['command']}\"")
                    print(f"    -> Run: \033[1;32mtincan trigger {a['seq']}\033[0m to approve & execute (or 'tincan dismiss {a['seq']}')")
        return 0

    if args.command == "trigger":
        from .tincan_actions import execute_action
        try:
            res = execute_action(args.action, args.dir)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\033[1;32m✓ Action triggered:\033[0m {res['command']}")
                print(f"  Result: {res.get('result')}")
            return 0
        except Exception as exc:
            print(f"[-] Trigger error: {exc}", file=sys.stderr)
            return 1

    if args.command == "dismiss":
        from .tincan_actions import dismiss_action
        try:
            res = dismiss_action(args.action, args.dir)
            print(f"[+] Dismissed action {res['seq']}")
            return 0
        except Exception as exc:
            print(f"[-] Error: {exc}", file=sys.stderr)
            return 1

    if args.command in ("start", "screensaver"):
        from .tui import main as tui_main
        tui_args = ["--screensaver", "--relay", args.relay]
        if args.duration is not None:
            tui_args.extend(["--duration", str(args.duration)])
        return tui_main(tui_args)

    if args.command in ("chat", "ask"):
        from .tincan_agent import TinCanAgentChat
        agent = TinCanAgentChat(relay_url=args.relay, model_alias=args.model)
        if hasattr(args, "prompt") and args.prompt:
            reply = agent.ask(args.prompt)
            print(reply)
            return 0
        agent.run_repl()
        return 0

    if args.command == "contacts":
        contacts = client.tincan_list_contacts()
        if args.json:
            print(json.dumps(contacts, indent=2))
        else:
            if not contacts:
                print("No pinned contacts.")
            for c in contacts:
                role = str(c.get("role", "peer")).lower()
                role_badge = "🛡️ ADMIN" if role in ("admin", "moderator") else ("🎓 MENTOR" if role == "mentor" else ("🌱 MENTEE" if role == "mentee" else "🤝 PEER"))
                voice_policy = "🔊 live-voice" if c.get("trust_mentor_tts") else "🔒 approval-gated"
                print(f"- {c['alias']} [{role_badge} · {voice_policy}]: {c['address']}")
        return 0

    if args.command == "add-contact":
        try:
            res = client.tincan_add_contact(
                args.alias,
                args.address,
                role=getattr(args, "role", "peer"),
                trust_mentor_tts=bool(getattr(args, "allow_voice", False)),
            )
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"[+] Pinned contact '{res['alias']}' ({res.get('role', 'peer').upper()}) -> {res['address']}")
            return 0
        except Exception as exc:
            if args.json:
                print(json.dumps({"error": str(exc)}, indent=2))
            else:
                print(f"[-] Failed to pin contact: {exc}", file=sys.stderr)
            return 1

    if args.command == "mentor":
        from .tincan_actions import load_pending_actions
        import urllib.parse
        import urllib.request

        contacts = client.tincan_list_contacts()
        mentors = [c for c in contacts if c.get("role") == "mentor"]
        mentees = [c for c in contacts if c.get("role") == "mentee"]

        if args.action == "status":
            pending = [a for a in load_pending_actions(args.dir) if a.get("status") == "pending_approval"]
            status_payload = {
                "identity": client.alias,
                "address": client.address,
                "mentors": mentors,
                "mentees": mentees,
                "pending_guidance_count": len(pending),
                "pending_guidance": pending,
            }
            if args.json:
                print(json.dumps(status_payload, indent=2))
            else:
                print("\033[1;33m=== 🎓 TinCan Mentor–Mentee Studio Status ===\033[0m")
                print(f"  Local Identity: {client.alias} ({client.address[:20]}...)")
                print(f"  Pinned Mentors ({len(mentors)}):")
                if not mentors:
                    print("    • None yet (Run: tincan mentor set <alias> --role mentor)")
                for m in mentors:
                    vp = "🔊 Live Voice Coaching ON" if m.get("trust_mentor_tts") else "🔒 Approval-Gated (Safe Default)"
                    print(f"    • {m['alias']} ({vp}) -> {m['address'][:22]}...")
                print(f"  Pinned Mentees ({len(mentees)}):")
                if not mentees:
                    print("    • None yet (Run: tincan mentor set <alias> --role mentee)")
                for mt in mentees:
                    print(f"    • {mt['alias']} -> {mt['address'][:22]}...")
                print(f"  Pending Guidance Queue: {len(pending)} item(s) awaiting 'tincan trigger <seq>'")
            return 0

        if args.action == "set":
            if not args.target:
                print("[-] Usage: tincan mentor set <contact_alias> [--role mentor|mentee|peer] [--allow-voice | --gate-voice]", file=sys.stderr)
                return 1
            trust_tts = None
            if args.allow_voice:
                trust_tts = True
            elif args.gate_voice:
                trust_tts = False
            try:
                updated = client.set_contact_role(args.target, role=args.role, trust_mentor_tts=trust_tts)
                if args.json:
                    print(json.dumps(updated, indent=2))
                else:
                    vp = "Live Voice Coaching ON" if updated["trust_mentor_tts"] else "Approval-Gated (Default)"
                    print(f"\033[1;32m[+] Updated '{updated['alias']}' -> Role: {updated['role'].upper()} ({vp})\033[0m")
                return 0
            except Exception as exc:
                if args.json:
                    print(json.dumps({"error": str(exc)}, indent=2))
                else:
                    print(f"[-] Mentor set failed: {exc}", file=sys.stderr)
                return 1

        if args.action == "guide":
            if not args.target or not args.message:
                print("[-] Usage: tincan mentor guide <mentee_alias> \"<instruction_or_url>\" [--speak]", file=sys.stderr)
                return 1
            guided_msg = f"[MENTOR GUIDANCE] {args.message}"
            try:
                res = client.tincan_send(recipient_address=args.target, message=guided_msg, speak=bool(args.speak))
                # Award Mentor Guidance XP on relay
                try:
                    relay_base = args.relay.rstrip("/")
                    q_req = urllib.request.Request(
                        f"{relay_base}/api/mesh/quest",
                        data=json.dumps({
                            "peer_id": f"{client.alias}-{client.public_key_hex[:8]}",
                            "action_key": "mentor_guidance",
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(q_req, timeout=4.0).read()
                except Exception:
                    pass
                out = {"status": "guidance_sent", "mentee": args.target, "message": guided_msg, "envelope": res}
                if args.json:
                    print(json.dumps(out, indent=2))
                else:
                    print(f"\033[1;33m🎓 Mentor Guidance dispatched to '{args.target}' (seq {res.get('seq')})!\033[0m")
                    print(f"   Step: {args.message}")
                    print("   (Queued in Mentee's Accessibility Gate for approval + execution)")
                return 0
            except Exception as exc:
                if args.json:
                    print(json.dumps({"error": str(exc)}, indent=2))
                else:
                    print(f"[-] Guidance send failed: {exc}", file=sys.stderr)
                return 1

        if args.action == "hand":
            topic = args.target or "Requesting live Mentor code review & walkthrough"
            target_mentor = args.mentor or (mentors[0]["alias"] if mentors else None)
            if not target_mentor:
                print("[-] No Mentor pinned yet. Pin a Mentor first with 'tincan mentor set <alias> --role mentor' or pass --mentor <alias>.", file=sys.stderr)
                return 1
            anon_id = client.public_key_hex[:8]
            room = f"mentor-{anon_id}"
            relay_base = args.relay.rstrip("/")
            call_url = f"{relay_base}/?room={urllib.parse.quote(room)}&mode=screen#call"
            hand_msg = f"[MENTEE HAND RAISE] {topic} — Join Mentor Pair Room: {call_url}"
            try:
                res = client.tincan_send(recipient_address=target_mentor, message=hand_msg, speak=True)
                try:
                    q_req = urllib.request.Request(
                        f"{relay_base}/api/mesh/quest",
                        data=json.dumps({
                            "peer_id": f"{client.alias}-{anon_id}",
                            "action_key": "mentee_hand_raise",
                        }).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    )
                    urllib.request.urlopen(q_req, timeout=4.0).read()
                except Exception:
                    pass
                out = {
                    "status": "hand_raised",
                    "mentor": target_mentor,
                    "topic": topic,
                    "pair_room": room,
                    "call_url": call_url,
                    "envelope": res,
                }
                if args.json:
                    print(json.dumps(out, indent=2))
                else:
                    print(f"\033[1;36m✋ Hand Raised to Mentor '{target_mentor}' (seq {res.get('seq')})!\033[0m")
                    print(f"   Topic:     {topic}")
                    print(f"   Pair Room: {call_url}")
                return 0
            except Exception as exc:
                if args.json:
                    print(json.dumps({"error": str(exc)}, indent=2))
                else:
                    print(f"[-] Hand raise failed: {exc}", file=sys.stderr)
                return 1

    if args.command == "playlist":
        import urllib.request
        relay_base = args.relay.rstrip("/")
        try:
            if args.action == "list":
                req = urllib.request.Request(f"{relay_base}/api/playlist", method="GET")
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"\033[1;35m📺 Relay Video Collection ({data.get('total', 0)} videos):\033[0m")
                    for idx, v in enumerate(data.get("videos", []), 1):
                        print(f"  {idx}. [{v.get('category', '').upper()}] {v.get('title')} ({v.get('creator')}) -> {v.get('cite_url')}")
                return 0
            elif args.action == "add":
                if not args.target:
                    print("[-] Please provide a TikTok URL, video ID, or embed snippet.", file=sys.stderr)
                    return 1
                payload = {"input": args.target, "title": args.title, "category": args.category}
                req = urllib.request.Request(
                    f"{relay_base}/api/playlist/add",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    it = data.get("item", {})
                    print(f"\033[1;32m[+] Added to Relay Collection:\033[0m {it.get('title')} ({it.get('cite_url')})")
                    print(f"    Total videos in rotation: {data.get('playlist', {}).get('total')}")
                return 0
            elif args.action == "remove":
                if not args.target:
                    print("[-] Please provide a video_id to remove.", file=sys.stderr)
                    return 1
                payload = {"video_id": args.target}
                req = urllib.request.Request(
                    f"{relay_base}/api/playlist/remove",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"[+] Status: {data.get('status')} (Remaining: {data.get('playlist', {}).get('total')})")
                return 0
        except Exception as exc:
            print(f"[-] Playlist error: {exc}", file=sys.stderr)
            return 1

    if args.command in ("status", "ping"):
        import urllib.parse
        import urllib.request

        if getattr(args, "mesh", False) or args.peer in ("all", "mesh"):
            # Redirect to who roster
            args.command = "who"
        else:
            target_peer = args.peer or "harper"
            resolved_addr = target_peer
            if client.contact_book.has_alias(target_peer):
                resolved_addr = client.contact_book.get_address(target_peer)
            relay_base = args.relay.rstrip("/")
            try:
                url = f"{relay_base}/api/tincan/whoami?address={urllib.parse.quote(resolved_addr)}"
                with urllib.request.urlopen(url, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    mb = data.get("mailbox_stats") or {}
                    pres = data.get("presence") or mb.get("presence") or {}
                    state = pres.get("state", "offline").upper()
                    badge_color = "\033[1;32m● ONLINE" if state == "ONLINE" else ("\033[1;33m◐ IDLE" if state == "IDLE" else "\033[1;31m○ OFFLINE / AWAY")
                    print(f"Peer Presence for '{target_peer}' ({resolved_addr}):")
                    print(f"  Status:          {badge_color}\033[0m")
                    print(f"  On Computer:     {'YES' if pres.get('is_on_computer') else 'NO (has not polled relay recently)'}")
                    if pres.get("seconds_since_active") is not None:
                        print(f"  Last Activity:   {pres.get('seconds_since_active')}s ago ({pres.get('last_event')})")
                    else:
                        print("  Last Activity:   No active CLI/TUI poll recorded since last relay boot")
                    print(f"  Mailbox Queue:   {mb.get('count', 0)} total envelopes ({pres.get('unread_count', mb.get('count', 0))} unread, last read seq: {pres.get('last_read_seq', 0)})")
                return 0
            except Exception as exc:
                print(f"[-] Status check failed: {exc}", file=sys.stderr)
                return 1

    if args.command in ("who", "peers", "mesh", "roster") or (args.command == "admin" and getattr(args, "admin_action", None) in ("who", "users", "peers", "list", None)):
        import time
        import urllib.parse
        import urllib.request

        relay_base = args.relay.rstrip("/")
        room = getattr(args, "room", "main") or "main"
        try:
            state_url = f"{relay_base}/api/mesh/state?room={urllib.parse.quote(room)}"
            req = urllib.request.Request(state_url, headers={"User-Agent": "TinCanCLI/2.2-Admin"})
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                mesh_state = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"[-] Failed to fetch mesh state from {relay_base}: {e}", file=sys.stderr)
            return 1

        cursors = mesh_state.get("cursors", [])
        streams = mesh_state.get("active_webrtc_streams", [])
        leaderboard = mesh_state.get("leaderboard", [])
        tier = mesh_state.get("tier", {})
        now = time.time()

        if args.json:
            out = {
                "relay": relay_base,
                "room": room,
                "tier": tier,
                "counts": {
                    "website_visitors": len(cursors),
                    "mesh_nodes": len(streams),
                    "total_active": len(cursors) + len(streams),
                },
                "website_visitors": cursors,
                "mesh_nodes": streams,
                "leaderboard": leaderboard,
            }
            print(json.dumps(out, indent=2))
            return 0

        print("\033[1;36m=======================================================================\033[0m")
        print("\033[1;36m       🥫 TINCAN MESH & RELAY WEBSITE ROSTER (ADMIN TELEMETRY)\033[0m")
        print(f"\033[1;30m       Relay: {relay_base} | Room: {room} | Tier: {tier.get('tier_code', 'L4')}\033[0m")
        print("\033[1;36m=======================================================================\033[0m\n")

        # 1. Website Visitors (Active browser sessions / cursors)
        print(f"\033[1;32m🌐 RELAY WEBSITE VISITORS ({len(cursors)} Active Browser Sessions)\033[0m")
        print("\033[1;30m" + "-" * 71 + "\033[0m")
        if not cursors:
            print("  (No website visitors currently active on the retro desktop)")
        else:
            for c in cursors:
                p_id = c.get("peer_id", "unknown")
                name = c.get("display_name") or p_id
                x = int(c.get("x", 0))
                y = int(c.get("y", 0))
                win = c.get("window_id", "desktop")
                upd = c.get("updated_at", 0)
                diff = int(now - upd) if upd else 0
                if diff <= 15:
                    status_badge = "\033[1;32m● ACTIVE NOW\033[0m"
                elif diff <= 60:
                    status_badge = f"\033[1;33m◐ IDLE ({diff}s ago)\033[0m"
                else:
                    status_badge = f"\033[1;30m○ AWAY ({diff}s ago)\033[0m"

                label_str = f"{p_id} ({name})" if name != p_id else p_id
                print(f"  • \033[1;37m{label_str:22s}\033[0m {status_badge:28s} Window: {win:10s} Pos: ({x:4d}, {y:4d})")

        print()
        # 2. Connected Mesh Nodes (Live WebRTC Streams & Workstations)
        print(f"\033[1;34m📡 CONNECTED MESH NODES ({len(streams)} Active WebRTC / Workstation Streams)\033[0m")
        print("\033[1;30m" + "-" * 71 + "\033[0m")
        if not streams:
            print("  (No WebRTC streaming nodes active in this room)")
        else:
            for s in streams:
                p_id = s.get("peer_id", "unknown")
                d_name = s.get("display_name") or p_id
                r = s.get("room", room)
                port = s.get("udp_port", "auto")
                caps = []
                if s.get("has_video"):
                    caps.append("📹 Video")
                if s.get("has_audio"):
                    caps.append("🎙️ Voice")
                if s.get("has_screen"):
                    caps.append("🖥️ Screen")
                if not caps:
                    caps.append("⚡ Workstation Signaling")
                caps_str = ", ".join(caps)
                print(f"  • \033[1;37m{p_id:22s}\033[0m [{d_name}]")
                print(f"    Room: {r:10s} | Port: UDP/{port} | Media: {caps_str}")

        print()
        # 3. Top Active Mesh Operators (Leaderboard)
        if leaderboard:
            print(f"\033[1;35m🏆 TOP MESH OPERATORS ({len(leaderboard)} Registered Peers)\033[0m")
            print("\033[1;30m" + "-" * 71 + "\033[0m")
            for idx, p in enumerate(leaderboard[:5]):
                badges_str = " ".join(p.get("badges", []))
                print(f"  #{idx+1} \033[1;37m{p.get('peer_id'):18s}\033[0m | XP: \033[1;33m{p.get('xp', 0):4d}\033[0m | Envelopes: {p.get('envelopes_sealed', 0)} | {badges_str}")

        print("\n\033[1;30m" + "=" * 71 + "\033[0m")
        print(f"\033[1;32mTotal Online: {len(cursors)} on Web, {len(streams)} on Mesh\033[0m | Mod Action: \033[1;33mtincan admin kick <peer_id>\033[0m")
        return 0

    if args.command == "admin":
        action = getattr(args, "admin_action", "who")
        if action == "kick":
            import urllib.request
            relay_base = args.relay.rstrip("/")
            room = getattr(args, "room", "main") or "main"
            target_peer = args.peer
            try:
                req = urllib.request.Request(
                    f"{relay_base}/api/webrtc/leave",
                    data=json.dumps({"peer_id": target_peer, "room": room}).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "TinCanCLI/2.2-Admin"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    if data.get("removed"):
                        print(f"\033[1;32m[🛡️ ADMIN MODERATOR] Successfully kicked '{target_peer}' from mesh room '{room}'.\033[0m")
                    else:
                        print(f"[*] Node '{target_peer}' was not active in room '{room}'.")
                return 0
            except Exception as exc:
                print(f"[-] Admin kick error: {exc}", file=sys.stderr)
                return 1

        elif action == "broadcast":
            import time
            import urllib.request
            relay_base = args.relay.rstrip("/")
            room = getattr(args, "room", "main") or "main"
            pub_hex = client.identity.verify_key.encode().hex()[:8]
            sender_id = f"admin-{args.alias}-{pub_hex}"
            payload_data = {
                "from": sender_id,
                "to": "*",
                "type": "admin_broadcast",
                "room": room,
                "payload": {
                    "text": args.text,
                    "sender": sender_id,
                    "role": "admin",
                    "timestamp": time.time(),
                    "priority": "emergency",
                },
            }
            try:
                req = urllib.request.Request(
                    f"{relay_base}/api/webrtc/signal",
                    data=json.dumps(payload_data).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "TinCanCLI/2.2-Admin"},
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=8.0) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                if args.json:
                    print(json.dumps(data, indent=2))
                else:
                    print(f"\033[1;32m[🛡️ ADMIN MODERATOR] System-wide announcement broadcast to room '{room}':\033[0m")
                    print(f"  \033[1;33m\"{args.text}\"\033[0m")
                return 0
            except Exception as exc:
                print(f"[-] Admin broadcast error: {exc}", file=sys.stderr)
                return 1

        elif action == "role":
            target = args.target or "self"
            role_choice = (getattr(args, "role", None) or getattr(args, "role_val", "admin") or "admin").strip().lower()
            if target in ("self", "me", args.alias):
                client.set_my_role(role_choice)
                if args.json:
                    print(json.dumps({"status": "updated", "target": "self", "role": role_choice}, indent=2))
                else:
                    print(f"\033[1;32m[🛡️ ADMIN MODERATOR] Successfully set local identity role to: {role_choice.upper()}\033[0m")
                return 0
            else:
                updated = client.set_contact_role(target, role=role_choice)
                if args.json:
                    print(json.dumps(updated, indent=2))
                else:
                    print(f"\033[1;32m[🛡️ ADMIN MODERATOR] Successfully set role for contact '{target}' to: {role_choice.upper()}\033[0m")
                return 0

    if args.command in ("credits", "cost"):
        from .ai_gateway import DynamicAIGatewayRouter

        router_inst = DynamicAIGatewayRouter()
        analytics = router_inst.get_analytics(include_live_billing=True)
        if args.json:
            print(json.dumps(analytics, indent=2))
        else:
            or_info = analytics.get("openrouter") or {}
            print("\033[1;36m=== 💳 OpenRouter Live Cost & Credit Dashboard ===\033[0m")
            if or_info.get("connected"):
                print(f"  Remaining Balance:   \033[1;32m${or_info.get('account_remaining_balance_usd', 0):.4f}\033[0m (of ${or_info.get('account_total_credits_usd', 0):.2f} total credits)")
                print(f"  Total Account Spend: \033[1;33m${or_info.get('account_total_usage_usd', 0):.4f}\033[0m")
                print(f"  Active Key ({or_info.get('key_label')}):")
                print(f"    • Key Spend Total: ${or_info.get('key_usage_total_usd', 0):.6f} (Today: ${or_info.get('key_usage_daily_usd', 0):.6f} | Month: ${or_info.get('key_usage_monthly_usd', 0):.6f})")
                if or_info.get("key_remaining_usd") is not None:
                    print(f"    • Key Budget Left: ${or_info.get('key_remaining_usd', 0):.4f} (of ${or_info.get('key_limit_usd')} limit)")
            else:
                print("  Status:              OpenRouter key not found in local environment")
            print("\n\033[1;35m--- Per-Model Token Pricing & Cost ---\033[0m")
            for alias, p in (analytics.get("providers") or {}).items():
                print(
                    f"  • {alias:13s} ({p['model']:28s}) -> "
                    f"In: ${p['input_cost_per_1m_usd']:.2f}/1M | Out: ${p['output_cost_per_1m_usd']:.2f}/1M | "
                    f"~1K Call: ${p['est_cost_per_1k_prompt_usd']:.5f}"
                )
        return 0

    if args.command in ("disconnect", "leave", "close"):
        import urllib.request

        pub_hex = client.identity.verify_key.encode().hex()[:8]
        target_peer = args.peer or f"{args.alias}-{pub_hex}"
        relay_base = args.relay.rstrip("/")
        try:
            req = urllib.request.Request(
                f"{relay_base}/api/webrtc/leave",
                data=json.dumps({"peer_id": target_peer, "room": args.room}).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TinCanCLI/2.2"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                if data.get("removed"):
                    print(f"\033[1;32m[+] Successfully disconnected '{target_peer}' from room '{args.room}'.\033[0m")
                else:
                    print(f"[*] Node '{target_peer}' was not active in room '{args.room}' (already disconnected).")
            return 0
        except Exception as exc:
            print(f"[-] Disconnect error: {exc}", file=sys.stderr)
            return 1

    if args.command in ("msg", "broadcast"):
        import time
        import urllib.request

        pub_hex = client.identity.verify_key.encode().hex()[:8]
        sender_id = f"{args.alias}-{pub_hex}"
        relay_base = args.relay.rstrip("/")
        payload_data = {
            "from": sender_id,
            "to": "*",
            "type": "chat",
            "room": args.room,
            "payload": {
                "text": args.text,
                "sender": args.alias or sender_id,
                "timestamp": time.time(),
            },
        }
        try:
            req = urllib.request.Request(
                f"{relay_base}/api/webrtc/signal",
                data=json.dumps(payload_data).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "TinCanCLI/2.2"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=8.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print(f"\033[1;32m[+] Message broadcast to room '{args.room}'!\033[0m")
                print(f"    From: {sender_id}")
                print(f"    Text: {args.text}")
            return 0
        except Exception as exc:
            print(f"[-] Broadcast error: {exc}", file=sys.stderr)
            return 1

    if args.command == "board":
        from .cyberspace_board import CyberspaceBoardEngine
        from .account_registry import PeerAccountRegistry

        reg = PeerAccountRegistry()
        engine = CyberspaceBoardEngine(account_registry=reg)
        pub_hex = client.identity.verify_key.encode().hex()[:8]
        peer_id = f"{args.alias}-{pub_hex}"
        act = args.board_action or "list"

        if act == "list":
            res = engine.list_topics(limit=25)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\033[1;36m=== 🌐 TinCan Cyberspace Discussion Board ({res['total_topics']} topics) ===\033[0m")
                for t in res["topics"]:
                    tags_s = " ".join(f"#{x}" for x in t.get("tags", [])[:5])
                    print(f"  • [{t['topic_id']}] \033[1;37m{t['title']}\033[0m (by @{t['author_username']}) — {t['reply_count']} replies | {tags_s}")
            return 0
        elif act == "new":
            if not args.target or not args.body:
                print("[-] Usage: tincan board new \"<Title>\" \"<Body with @username and @agent tags>\"", file=sys.stderr)
                return 1
            topic = engine.create_topic(
                peer_id=peer_id,
                title=args.target,
                body=args.body,
                category=args.category,
                author_username=args.username or args.alias,
            )
            if args.json:
                print(json.dumps(topic, indent=2))
            else:
                print(f"\033[1;32m[+] Created Cyberspace Topic [{topic['topic_id']}]: {topic['title']}\033[0m")
                print(f"    Mentions: users={topic['user_mentions']} | agents={topic['agent_mentions']} | replies={topic['reply_count']}")
            return 0
        elif act == "reply":
            if not args.target or not args.body:
                print("[-] Usage: tincan board reply <topic_id> \"<Reply body with @username or @agent>\"", file=sys.stderr)
                return 1
            rep = engine.create_post(
                topic_id=args.target,
                peer_id=peer_id,
                body=args.body,
                author_username=args.username or args.alias,
            )
            if args.json:
                print(json.dumps(rep, indent=2))
            else:
                print(f"\033[1;32m[+] Posted reply [{rep['post_id']}] in {args.target}\033[0m")
            return 0
        elif act == "search":
            res = engine.search(query=args.target or "", mode=args.mode, top_k=10)
            if args.json:
                print(json.dumps(res, indent=2))
            else:
                print(f"\033[1;35m=== 🔍 Cyberspace Search ({res['mode'].upper()}): \"{res['query']}\" ===\033[0m")
                print(f"  {res['synthesis']}")
                for r in res["results"]:
                    print(
                        f"  • [{r['topic_id']}] \033[1;37m{r['title']}\033[0m "
                        f"(Score: {r['score']:.3f} | BM25: {r['bm25_score']:.3f} | GraphRAG: {r['graphrag_score']:.3f})"
                    )
            return 0
        elif act == "graph":
            snap = engine.graphrag.get_full_graph_snapshot()
            if args.json:
                print(json.dumps(snap, indent=2))
            else:
                print(f"\033[1;36m=== 🕸️ Cyberspace Knowledge Graph ===\033[0m")
                print(f"  Nodes: {snap['stats']['total_nodes']} | Edges: {snap['stats']['total_edges']} | Types: {snap['stats']['by_type']}")
            return 0

    if args.command == "verify":
        from .cyberspace_board import CyberspaceBoardEngine
        from .account_registry import PeerAccountRegistry

        reg = PeerAccountRegistry()
        engine = CyberspaceBoardEngine(account_registry=reg)
        pub_hex = client.identity.verify_key.encode().hex()[:8]
        peer_id = args.peer or f"{args.alias}-{pub_hex}"
        v_act = args.verify_action or "status"

        if v_act == "status":
            st = engine.get_verification_status(peer_id)
            if args.json:
                print(json.dumps(st, indent=2))
            else:
                badge = "✅ VERIFIED" if st["verified"] else "⚠️ UNVERIFIED"
                print(f"[🛡️ @verifier-agent] Peer {peer_id}: {badge} (Pending forms: {len(st['pending_forms'])})")
            return 0
        elif v_act == "send-form":
            disp = engine.dispatch_verification_form(peer_id=peer_id, target_username=args.username or "")
            if args.json:
                print(json.dumps(disp, indent=2))
            else:
                print(f"\033[1;33m[🛡️ @verifier-agent] Dispatched Verification Form [{disp['request_id']}] to {peer_id}\033[0m")
            return 0
        elif v_act == "submit":
            if not (args.name and args.username and args.email and args.phone):
                print("[-] Usage: tincan verify submit --name \"Full Name\" --username handle --email a@b.com --phone +15615550199", file=sys.stderr)
                return 1
            sub = engine.submit_verification_form(
                peer_id=peer_id,
                full_name=args.name,
                username=args.username,
                email=args.email,
                phone_number=args.phone,
                role=args.role,
                consent_pii=True,
            )
            if args.json:
                print(json.dumps(sub, indent=2))
            else:
                print(f"\033[1;32m[✅ @verifier-agent] Verified {sub['username']} ({sub['full_name']})! Attestation: {sub['attestation_hash']}\033[0m")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

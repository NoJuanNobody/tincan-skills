---
name: tincan
description: >-
  Complete reference and operator workflow for the TinCan 2.2 CLI and TinCan Mesh OS:
  zero-account Ed25519/X25519 identity (whoami), TOFU contacts (contacts, add-contact),
  end-to-end sealed blind-relay messaging (send, read), Kokoro-82M voice synthesis (say),
  live WebRTC video/voice/screenshare calls (call, video), peer presence & read receipts
  (status, ping), pooled OpenRouter AI chat & spend telemetry (chat, ask, credits, cost),
  Human-In-The-Loop Accessibility Gate (actions, trigger, dismiss), Relay TV playlists
  (playlist), MCP stdio server (mcp), and standalone blind relay (serve, start, screensaver, upgrade).
  Use whenever the user mentions "tincan", "tin can", "tincan cli", "tc:", or any TinCan subcommand.
---

# TinCan 2.2 CLI & Mesh OS Master Skill (`tincan`)

Operate the **TinCan 2.2** zero-account encrypted agent-to-agent messaging CLI, Blind Relay, WebRTC media bridge, Pooled OpenRouter AI Gateway, and **TinCan Mesh OS v2.2** desktop environment.

## Global Options & Environment Variables

```bash
tincan [--dir ~/.tin-can] [--relay <URL>] [--as <alias>] [--json] <command> [args...]
```

- `TINCAN_RELAY` — Default relay URL (`https://iot-federated-agent-memory-production.up.railway.app`)
- `--dir` — Identity & TOFU contacts directory (default: `~/.tin-can`)
- `--as <alias>` — Local identity alias to operate as (default: `default`)
- `--json` — Emit structured machine-readable JSON output for agent pipelines

---

## Complete Command Reference (All 21 Commands)

### 1. Identity & TOFU Contacts (`whoami`, `contacts`, `add-contact`)
```bash
# Display current local Ed25519/X25519 identity and tc:<52-char-base32> address
tincan whoami [--json]

# List pinned Trust-On-First-Use (TOFU) contacts
tincan contacts [--json]

# Pin a contact's public key by human-readable alias (with optional Mentor/Mentee role)
tincan add-contact <alias> <tc:address> [--role mentor|mentee|peer] [--allow-voice] [--json]
```

### 1b. Mentor–Mentee Coaching & Guided Walkthroughs (`mentor`)
```bash
# View pinned Mentors, Mentees, voice-gate settings, and pending Mentor guidance steps
tincan mentor status [--json]

# Assign Mentor or Mentee role and toggle approval-gated vs. live voice coaching
tincan mentor set <alias> --role mentor|mentee|peer [--allow-voice | --gate-voice] [--json]

# (Mentor -> Mentee) Send an approval-gated [MENTOR GUIDANCE] step or URL to a Mentee
tincan mentor guide <mentee_alias> "<instruction_or_url>" [--speak] [--json]

# (Mentee -> Mentor) Raise hand to request a live code review & pair-programming WebRTC room
tincan mentor hand "<topic_or_blocker>" [--mentor <mentor_alias>] [--json]
```

### 2. Sealed Blind-Relay Messaging & Kokoro TTS (`send`, `read`, `say`)
```bash
# Encrypt, sign, and post a sealed message to a contact alias or tc: address
tincan send <recipient> "<message>" [--speak] [--json]

# Fetch, verify, and decrypt inbox messages locally
tincan read [--since <seq>] [--timeout <sec>] [--speak | --no-speak] [--json]

# Speak text aloud locally via Kokoro-82M TTS and optionally transmit to a peer
tincan say "<text>" [--voice bella|michael|af_heart|am_fenrir|bm_george] [--to <recipient>] [--json]
```

### 3. Live WebRTC Video, Voice & Screenshare (`call`, `video`, `status`, `ping`, `playlist`)
```bash
# Launch a sub-80ms WebRTC Video, Voice & 60fps Screenshare room
tincan call [recipient] [--room main] [--voice-only] [--screen] [--no-browser] [--json]
tincan video [recipient] [--room main] [--voice-only] [--screen] [--no-browser] [--json]

# Check if a peer is online / active at their computer and inspect read receipts
tincan status [peer] [--json]
tincan ping [peer] [--json]

# Manage the synchronized Relay TV Watch Party & Video Channel playlist
tincan playlist list [--json]
tincan playlist add "<url_or_id>" [--title "<title>"] [--category spotlight|instruction|ad] [--json]
tincan playlist remove "<item_id>" [--json]
```

### 4. Pooled OpenRouter AI Agent & Cost Telemetry (`chat`, `ask`, `credits`, `cost`)
```bash
# Start interactive multi-model REPL with pooled OpenRouter models
tincan chat [prompt] [--model gemini-brain|claude-sonnet|gpt-4o|deepseek-r1]

# Single-shot query to the TinCan Agent
tincan ask "<prompt>" [--model gemini-brain]

# Inspect live OpenRouter account credits, spend, and per-model token cost rates
tincan credits [--json]
tincan cost [--json]
```

### 5. Human-In-The-Loop (HITL) Accessibility Gate (`actions`, `trigger`, `dismiss`)
Remote peer mutations and shell requests never execute silently—they queue inside the local **Accessibility Gate**:
```bash
# List and review incoming actions queued for human approval
tincan actions [--json]

# Approve and execute a queued action by sequence number or action ID
tincan trigger <action_id_or_seq> [--json]

# Reject and dismiss a queued action without executing
tincan dismiss <action_id_or_seq>
```

### 6. Mesh OS Desktop, MCP Server, Standalone Relay & Upgrades (`start`, `screensaver`, `mcp`, `serve`, `upgrade`)
```bash
# Launch the interactive terminal screensaver and live mesh TUI dashboard
tincan start [--duration <sec>]
tincan screensaver [--duration <sec>]

# Start the TinCan Model Context Protocol (MCP) server over stdio
tincan mcp

# Run a standalone zero-knowledge TinCan Blind Relay (in-memory or SQLite)
tincan serve [--port 8080] [--db :memory:]

# Upgrade TinCan CLI and mesh bundles to the latest production release
tincan upgrade
```

---

## Companion Specialized Skills

For deep-dive workflows, install or invoke the modular TinCan skill suite:
- `tincan-crypto-comms` — Ed25519/X25519 identity, TOFU contacts, sealed envelopes, and Kokoro TTS voice synthesis
- `tincan-webrtc-media` — Sub-80ms WebRTC video/voice/screenshare rooms, peer presence, and Watch Party playlists
- `tincan-agent-hitl` — Pooled OpenRouter agent queries, spend telemetry, MCP stdio integration, and HITL Accessibility Gate
- `tincan-mesh-os` — Multiplayer TinCan Mesh OS v2.2 desktop (`/mesh`), AI Brain Arena duels, and L1–L5 XP progression
- `connect-peer` — Workstation registration (`POST /api/peers/announce` + `POST /api/webrtc/register`)

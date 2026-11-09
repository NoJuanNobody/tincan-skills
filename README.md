# TinCan 2.2 & Mesh OS — Open Agent Skills Suite (`tincan-skills`)

Modular agent skills for operating **TinCan 2.2** — the zero-account Ed25519/X25519 encrypted messaging CLI, Zero-Knowledge Blind Relay, sub-80ms WebRTC video/voice/screenshare bridge, Pooled OpenRouter AI Gateway, Human-In-The-Loop Accessibility Gate, and **TinCan Mesh OS v2.2** multiplayer desktop.

Compatible with the open **Skills CLI (`npx skills`)**, **Claude Code**, **Antigravity CLI**, **Cursor**, **Windsurf**, and **Codex**.

---

## Quick Install via `npx skills`

Install the entire TinCan skill suite globally in one command:

```bash
npx skills add NoJuanNobody/tincan-skills -g -y
```

Or install individual skills selectively:

```bash
# List all available skills in this repository
npx skills add NoJuanNobody/tincan-skills --list

# Install a single skill (e.g. master tincan CLI skill)
npx skills add NoJuanNobody/tincan-skills --skill tincan -g -y
```

---

## Included Skills (6 Skills)

| Skill Name | Path | Description |
| :--- | :--- | :--- |
| **`tincan`** | [`skills/tincan/SKILL.md`](skills/tincan/SKILL.md) | Master reference & operator workflow for all 21 `tincan` CLI commands (`whoami`, `send`, `read`, `say`, `call`, `video`, `contacts`, `add-contact`, `mcp`, `start`, `screensaver`, `chat`, `ask`, `actions`, `trigger`, `dismiss`, `serve`, `playlist`, `status`, `ping`, `credits`, `cost`, `upgrade`). |
| **`tincan-crypto-comms`** | [`skills/tincan-crypto-comms/SKILL.md`](skills/tincan-crypto-comms/SKILL.md) | Zero-account Ed25519/X25519 identity (`whoami`), TOFU contact pinning (`contacts`, `add-contact`), sealed blind-relay messaging (`send`, `read`), and Kokoro-82M neural voice synthesis (`say`). |
| **`tincan-webrtc-media`** | [`skills/tincan-webrtc-media/SKILL.md`](skills/tincan-webrtc-media/SKILL.md) | Sub-80ms WebRTC Video, Voice & 60fps Screenshare call rooms (`call`, `video`), peer online presence & read receipts (`status`, `ping`), and synchronized Relay TV Watch Party playlists (`playlist`). |
| **`tincan-agent-hitl`** | [`skills/tincan-agent-hitl/SKILL.md`](skills/tincan-agent-hitl/SKILL.md) | Pooled OpenRouter multi-model REPL & single-shot queries (`chat`, `ask`), real-time credit & token cost telemetry (`credits`, `cost`), stdio MCP server (`mcp`), and Human-In-The-Loop Accessibility Gate (`actions`, `trigger`, `dismiss`). |
| **`tincan-mesh-os`** | [`skills/tincan-mesh-os/SKILL.md`](skills/tincan-mesh-os/SKILL.md) | Terminal mesh screensaver (`start`, `screensaver`), standalone Blind Relay (`serve`), OTA upgrades (`upgrade`), and multiplayer TinCan Mesh OS v2.2 web desktop (`/mesh`, AI Brain Arena duels, L1–L5 XP progression). |
| **`connect-peer`** | [`skills/connect-peer/SKILL.md`](skills/connect-peer/SKILL.md) | Automated workstation handshake (`POST /api/peers/announce`) and WebRTC UDP low-latency screen channel registration (`POST /api/webrtc/register`) for MacBook Pro, Mac Studio M1, and peer nodes. |

---

## TinCan CLI Quick Reference

```text
TinCan commands:
  whoami              Display current local identity and TinCan address
  send                Send sealed message to a recipient address or contact alias
  read                Fetch and decrypt inbox messages
  say                 Speak text aloud via Kokoro TTS and optionally send spoken message to a peer
  call                Launch live WebRTC Video, Voice & Screenshare call room
  video               Launch live WebRTC Video, Voice & Screenshare call room
  contacts            List pinned contacts
  add-contact         Pin a contact's public key (TOFU)
  mcp                 Start MCP server over stdio
  start               Launch the full terminal screensaver and live mesh dashboard
  screensaver         Alias for 'start'
  chat                Start interactive agentic chat REPL with the live OpenRouter models
  ask                 Single-shot query to the TinCan Agent
  actions             List and review incoming actions queued for approval (Accessibility Gate)
  trigger             Approve and trigger an incoming queued action (e.g. 'tincan trigger 1')
  dismiss             Dismiss a queued action without executing
  serve               Run local standalone TinCan Blind Relay
  playlist            Manage the Relay Video Channel & Collection Playlist
  status              Check if a peer is online / on their computer and inspect read receipts
  ping                Check if a peer is online / on their computer and inspect read receipts
  credits             Display live OpenRouter account credits, spend, and per-model cost rates
  cost                Display live OpenRouter account credits, spend, and per-model cost rates
  upgrade             Upgrade TinCan CLI and mesh bundles to the latest production release
```

## License

MIT

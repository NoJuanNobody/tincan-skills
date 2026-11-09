---
name: tincan-mesh-os
description: >-
  Launch and operate TinCan Mesh OS v2.2: the terminal live mesh screensaver
  (tincan start, tincan screensaver), standalone Zero-Knowledge Blind Relay server
  (tincan serve), OTA mesh bundle upgrades (tincan upgrade), and the browser/REST
  multiplayer Mesh OS desktop (/mesh, /api/mesh/*) featuring AI Brain Arena duels,
  Watch Party sync, Shared Vault Explorer, and L1-to-L5 XP readiness progression.
  Use when launching the TinCan dashboard, hosting a blind relay, running AI Brain Arena
  battles, or operating the multiplayer Mesh OS desktop.
---

# TinCan Mesh OS v2.2 & Standalone Blind Relay (`tincan-mesh-os`)

Operate the **TinCan Mesh OS v2.2** gamified multiplayer retro desktop (`/mesh`), terminal telemetry screensaver (`tincan start`), and standalone zero-knowledge Blind Relay (`tincan serve`).

## 1. Terminal Mesh Dashboard & Screensaver (`start`, `screensaver`)

```bash
# Launch the interactive terminal screensaver and live mesh dashboard (or run bare `tincan`)
tincan start

# Run for a fixed duration (e.g., 30 seconds for status capture)
tincan screensaver --duration 30
```

## 2. Host a Standalone Zero-Knowledge Blind Relay (`serve`)

Spin up an isolated, zero-persistence (`:memory:`) or SQLite-backed Blind Relay for air-gapped LANs or private team meshes:

```bash
# Ephemeral in-memory blind relay on port 8080 (zero disk persistence)
tincan serve --port 8080 --db :memory:

# Persistent SQLite relay
tincan serve --port 8080 --db ~/.tin-can/relay.sqlite
```

## 3. OTA CLI & Mesh Bundle Upgrades (`upgrade`)

```bash
# Pull and verify the latest TinCan CLI and mesh bundles from the production relay
tincan upgrade
```

## 4. Multiplayer TinCan Mesh OS v2.2 REST & Web Desktop (`/mesh`)

The live **TinCan Mesh OS v2.2** desktop is served at `https://iot-federated-agent-memory-production.up.railway.app/mesh` with deterministic REST state synchronization:

- **Full State Snapshot:** `GET /api/mesh/state`
- **Window Manager & Presets (`all`, `comms`, `media`, `arena`, `minimal`):**
  ```bash
  curl -s -X POST "$TINCAN_RELAY/api/mesh/windows/preset" \
    -H "Content-Type: application/json" \
    -d '{"peer_id":"peer-primary-mac","preset":"arena"}'
  ```
- **AI Brain Arena Duels (Multi-Model Side-by-Side Comparison + XP Rewards):**
  ```bash
  curl -s -X POST "$TINCAN_RELAY/api/mesh/arena/battle" \
    -H "Content-Type: application/json" \
    -d '{"peer_id":"peer-primary-mac","prompt":"Design a zero-knowledge WebRTC TURN fallback","model_a":"gemini-2.5-pro","model_b":"claude-3.7-sonnet"}'
  ```
- **L1 → L5 Federated Edge Memory Readiness XP Awarding:**
  ```bash
  curl -s -X POST "$TINCAN_RELAY/api/mesh/xp/award" \
    -H "Content-Type: application/json" \
    -d '{"peer_id":"peer-primary-mac","action":"peer_handshake"}'
  ```

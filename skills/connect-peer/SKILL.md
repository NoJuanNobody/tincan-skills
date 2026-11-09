---
name: connect-peer
description: >-
  Connect this computer or a named hardware workstation (e.g., MacBook Pro, Mac Studio M1)
  to the live IoT Federated Agent Mesh, WebRTC UDP screensharing relay, shared Obsidian
  brain, and dynamic AI token gateway on Railway. Trigger with natural phrases like
  "connect peer", "connect peer mac studio", "join mesh", "link to friend",
  "start screen share", or "/connect-peer".
---

# Connect Peer Skill (`connect-peer`)

Seamlessly handshakes with the live Railway mesh relay (`https://iot-federated-agent-memory-production.up.railway.app`), announces this machine's presence (`POST /api/peers/announce`), registers WebRTC UDP low-latency screen channels (`POST /api/webrtc/register`), and synchronizes shared skills and AI token pools.

## Quick Trigger Phrases
- "connect peer"
- "connect peer mac studio m1 chip"
- "connect to friend's computer"
- "join mesh"
- "start peer screen share"
- "/connect-peer"

## Execution Runbook

### 1. Connect Current Workstation (Anonymous ID, All Peripherals OFF by Default)
```bash
python3 "$HOME/dev/iot-federated-agent-memory/connect_peer.py" \
  --peer-id "peer-workstation-node" \
  --display-name "Workstation Node"
```

### 2. Connect a Specific Hardware Node (e.g., Mac Studio M1 Chip)
```bash
python3 "$HOME/dev/iot-federated-agent-memory/connect_peer.py" \
  --peer-id "peer-primary-mac" \
  --display-name "Mac Studio (M1 Chip)" \
  --capabilities "antigravity_cli,claude_code,obsidian_vault,webrtc_udp_screen,kokoro_tts,apple_silicon_m1_max"
```

### 3. Verify Live Mesh & WebRTC Status
```bash
curl -s https://iot-federated-agent-memory-production.up.railway.app/api/status | python3 -m json.tool
```

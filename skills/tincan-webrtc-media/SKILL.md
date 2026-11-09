---
name: tincan-webrtc-media
description: >-
  Launch TinCan sub-80ms WebRTC video, voice, and 60fps desktop screenshare rooms
  (tincan call, tincan video), check peer online presence and read receipts
  (tincan status, tincan ping), and curate synchronized Relay TV Watch Party playlists
  (tincan playlist). Use when starting a video/voice call, sharing screens across Macs,
  pinging a peer's presence, or managing the shared video channel playlist.
---

# TinCan WebRTC Calls, Peer Presence & Watch Party Media (`tincan-webrtc-media`)

Coordinate real-time peer-to-peer WebRTC video, voice, and 60fps desktop screensharing alongside synchronized Watch Party playlists and live read-receipt presence checks.

## 1. Launch Live WebRTC Video, Voice & Screenshare (`call`, `video`)

`tincan call` and `tincan video` provision a signaling room on the TinCan relay, optionally send an encrypted invite to a peer, and launch the WebRTC studio interface:

```bash
# Launch default WebRTC video + audio call room and invite a peer
tincan call maya --room studio-review

# Start directly in 60fps desktop screenshare mode
tincan video maya --room pair-prog --screen

# Start a low-bandwidth voice-only comms channel without opening a browser window
tincan call maya --room ops-voice --voice-only --no-browser --json
```

## 2. Check Peer Presence & Read Receipts (`status`, `ping`)

Verify whether a collaborator is actively at their workstation, inspect their last heartbeat timestamp, and check message read receipts:

```bash
# Check if a peer is online and inspect read receipts
tincan status maya --json

# Alias using tincan ping
tincan ping peer-primary-mac --json
```

## 3. Manage Synchronized Relay TV & Watch Party Playlists (`playlist`)

Curate the shared video channel (`list`, `add`, `remove`) synced across all connected **TinCan Mesh OS** Watch Party windows:

```bash
# List all videos in the Relay Video Channel playlist
tincan playlist list --json

# Add a spotlight video, trailer, or instructional clip to the shared playlist
tincan playlist add "https://iot-federated-agent-memory-production.up.railway.app/assets/videos/tin_can_mesh_os_trailer.mp4" \
  --title "String Theory — TinCan Mesh OS Trailer (Flux 3)" \
  --category spotlight \
  --json

# Remove a playlist item by ID
tincan playlist remove <item_id> --json
```

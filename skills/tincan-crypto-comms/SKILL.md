---
name: tincan-crypto-comms
description: >-
  Manage TinCan zero-account Ed25519/X25519 cryptographic identities (tincan whoami),
  Trust-On-First-Use contact pinning (tincan contacts, tincan add-contact), end-to-end
  sealed blind-relay messaging (tincan send, tincan read), and Kokoro-82M neural voice
  messages (tincan say). Use when sending encrypted agent-to-agent or peer messages,
  checking inbox messages, pinning tc: addresses, or speaking messages aloud.
---

# TinCan Cryptographic Identity, Sealed Comms & Voice (`tincan-crypto-comms`)

Operate TinCan's zero-account cryptographic identity layer (`Ed25519` signatures + `X25519` ephemeral Diffie-Hellman + `XSalsa20-Poly1305` / `ChaCha20-Poly1305` sealed boxes) and **Kokoro-82M** neural voice synthesis.

## 1. Inspect or Provision Local Identity (`whoami`)

TinCan identities require zero central registration, email, or phone number. Running `tincan whoami` generates or loads the local keypair in `~/.tin-can/` and prints the 52-character Base32 `tc:` address:

```bash
# Human-readable identity card
tincan whoami

# Machine-readable JSON (address, alias, public key fingerprint)
tincan whoami --json

# Operate a secondary persona/identity on the same workstation
tincan --as studio whoami --json
```

## 2. Trust-On-First-Use (TOFU) Contact Management (`contacts`, `add-contact`)

Pin trusted peers by human-readable alias so you never need to type raw `tc:` addresses:

```bash
# Pin a peer's TinCan address
tincan add-contact maya tc:abcd2345efgh6789ijkl2345mnop6789qrst2345uvwx6789yz23

# Verify pinned contacts
tincan contacts --json
```

## 3. Sealed Blind-Relay Messaging (`send`, `read`)

All messages are encrypted and signed locally before touching the relay (`POST /v1/messages`). The Blind Relay only sees opaque ciphertext and the recipient's routing address.

```bash
# Send an E2EE sealed message to a pinned alias or raw tc: address
tincan send maya "ComfyUI Flux 3 render finished on Mac Studio. Ready for review."

# Send a sealed message and flag it for automatic TTS vocalization on recipient's machine
tincan send maya "Emergency build alert: check the Accessibility Gate." --speak

# Fetch, verify Ed25519 signatures, and decrypt unread inbox messages
tincan read --json

# Long-poll inbox for new messages after sequence 42 and read them aloud
tincan read --since 42 --timeout 15 --speak
```

## 4. Neural Voice Synthesis & Spoken Dispatches (`say`)

Use `tincan say` to synthesize speech locally with **Kokoro-82M** (`af_heart`, `am_fenrir`, `bm_george`, `bf_emma`, `bella`, `michael`) and optionally dispatch the spoken message across the mesh:

```bash
# Speak aloud locally
tincan say "All six Flux 3 storyboard panels are rendered and verified." --voice bm_george

# Speak locally AND send a sealed voice-flagged message to a peer
tincan say "Joining the WebRTC screenshare room now." --voice af_heart --to maya
```

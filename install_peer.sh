#!/usr/bin/env bash
# ==============================================================================
# TinCan 2.2 CLI & Skills Installer (Public GitHub Clone + Verified Binary Gate)
# Usage: curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash
# ==============================================================================
set -e

REPO_URL="https://github.com/NoJuanNobody/iot-federated-agent-memory.git"
MIRROR_REPO_URL="https://github.com/NoJuanNobody/tincan-skills.git"
INSTALL_DIR="$HOME/dev/iot-federated-agent-memory"
SKILLS_DIR="$HOME/.gemini/config/skills/connect-peer"
AGENTS_SKILLS_DIR="$HOME/.agents/skills/connect-peer"

echo "=========================================================="
echo "[*] Installing TinCan 2.2 Mesh OS & Peer Connector"
echo "=========================================================="

# 1. Ensure dev directory exists
mkdir -p "$HOME/dev"

# 2. Clone or update repository from GitHub (with mirror fallback)
if [ -d "$INSTALL_DIR/.git" ]; then
    echo "[+] Updating existing repository in $INSTALL_DIR..."
    git -C "$INSTALL_DIR" pull --rebase origin main || true
elif [ ! -d "$INSTALL_DIR" ]; then
    echo "[+] Cloning repository to $INSTALL_DIR..."
    if ! git clone "$REPO_URL" "$INSTALL_DIR"; then
        echo "[!] Primary repo clone failed; falling back to public mirror $MIRROR_REPO_URL..."
        git clone "$MIRROR_REPO_URL" "$INSTALL_DIR"
    fi
fi

# 3. Ensure PyNaCl dependency is installed for Ed25519/X25519 cryptography
if command -v python3 >/dev/null 2>&1; then
    python3 -c "import nacl" 2>/dev/null || python3 -m pip install --user --quiet PyNaCl 2>/dev/null || python3 -m pip install --break-system-packages --quiet PyNaCl 2>/dev/null || true
fi

# 4. Link global 'tincan' executable to ~/.local/bin (and /usr/local/bin if writable)
mkdir -p "$HOME/.local/bin"
export PATH="$HOME/.local/bin:$PATH"

if [ ! -f "$INSTALL_DIR/tincan_cli.py" ]; then
    echo "[!] ERROR: $INSTALL_DIR/tincan_cli.py not found after clone. Aborting before installing skills."
    exit 1
fi

chmod +x "$INSTALL_DIR/tincan_cli.py"
ln -sf "$INSTALL_DIR/tincan_cli.py" "$HOME/.local/bin/tincan"
chmod +x "$HOME/.local/bin/tincan"
echo "[+] Linked global 'tincan' command -> $HOME/.local/bin/tincan"

if [ -d "/usr/local/bin" ] && [ -w "/usr/local/bin" ]; then
    ln -sf "$INSTALL_DIR/tincan_cli.py" "/usr/local/bin/tincan" 2>/dev/null || true
fi

# Ensure ~/.local/bin is persisted in shell RC files so 'which tincan' works in new terminals
for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
    if [ -f "$rc" ] && ! grep -q '\.local/bin' "$rc" 2>/dev/null; then
        printf '\n# TinCan CLI PATH\nexport PATH="$HOME/.local/bin:$PATH"\n' >> "$rc"
    fi
done

# Verify the CLI binary executes cleanly BEFORE installing agent skills
if ! "$HOME/.local/bin/tincan" --help >/dev/null 2>&1; then
    echo "[!] ERROR: 'tincan --help' verification failed. Aborting skill registration so skills are never orphaned."
    exit 1
fi
echo "[+] Verified 'tincan' CLI binary is executable and operational."

# 5. Install official TinCan Agent Skills via npx skills (only after CLI is verified)
if command -v npx >/dev/null 2>&1; then
    echo "[*] Installing TinCan agent skills via npx skills..."
    npx -y skills add NoJuanNobody/tincan-skills -g -y
else
    echo "[!] Warning: 'npx' not found. Please install Node.js to use agent skills."
fi

# 6. Register connect-peer natural language skill
mkdir -p "$SKILLS_DIR"
mkdir -p "$AGENTS_SKILLS_DIR"
cat << 'EOF' > "$SKILLS_DIR/SKILL.md"
---
name: connect-peer
description: >-
  Connect this computer to the live IoT Federated Agent Mesh, WebRTC UDP screensharing relay,
  shared Obsidian brain, and dynamic AI token gateway on Railway. Trigger with natural phrases
  like "connect peer", "join mesh", "link to friend", "start screen share", or "/connect-peer".
---

# Connect Peer Skill (`connect-peer`)

Seamlessly handshakes with the live Railway mesh relay (`https://iot-federated-agent-memory-production.up.railway.app`), announces this machine's presence, registers WebRTC UDP low-latency screen channels, and synchronizes shared skills and AI token pools.
EOF
cp "$SKILLS_DIR/SKILL.md" "$AGENTS_SKILLS_DIR/SKILL.md"

echo ""
echo "=========================================================="
echo "✓ TinCan 2.2 Installation Complete!"
echo "  • Binary verified at: $(command -v tincan || echo "$HOME/.local/bin/tincan")"
echo "  • Run 'tincan' or 'tincan --help' in your terminal."
echo "  • Skills installed: tincan, tincan-agent-hitl, tincan-crypto-comms, tincan-mesh-os, tincan-webrtc-media, connect-peer"
echo "  • All peripherals (camera, microphone, screen) remain OFF by default."
echo "=========================================================="

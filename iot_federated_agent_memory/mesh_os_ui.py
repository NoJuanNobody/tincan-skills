"""TinCan Mesh OS — Multi-Window, Multiplayer & Gamified UI Specification.

Provides MESH_OS_HTML_UI with retro-futuristic spatial window manager,
top gamified telemetry HUD, interactive packet-flight background canvas,
multiplayer cursor layer, and multi-monitor pop-out window capabilities.
"""

MESH_OS_HTML_UI = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>TinCan Mesh OS 2.1 — Multi-Window, Multiplayer &amp; AI Mesh Gateway</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    :root {
      --bg-color: #020617;
      --panel-bg: rgba(15, 23, 42, 0.92);
      --border-color: rgba(51, 65, 85, 0.7);
      --accent-color: #38bdf8;
    }

    body.theme-slate {
      --bg-color: #020617;
      --panel-bg: rgba(15, 23, 42, 0.92);
      --border-color: rgba(51, 65, 85, 0.7);
      --accent-color: #38bdf8;
    }

    body.theme-amber-crt {
      --bg-color: #120900;
      --panel-bg: rgba(26, 16, 3, 0.94);
      --border-color: rgba(245, 158, 11, 0.7);
      --accent-color: #f59e0b;
    }
    body.theme-amber-crt::after {
      content: " ";
      position: fixed;
      inset: 0;
      background: linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.28) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03));
      background-size: 100% 3px, 6px 100%;
      pointer-events: none;
      z-index: 9999;
    }

    body.theme-crypto-emerald {
      --bg-color: #021a0f;
      --panel-bg: rgba(2, 36, 20, 0.93);
      --border-color: rgba(16, 185, 129, 0.75);
      --accent-color: #10b981;
    }

    body.theme-webrtc-cyan {
      --bg-color: #031726;
      --panel-bg: rgba(6, 30, 48, 0.92);
      --border-color: rgba(6, 182, 212, 0.8);
      --accent-color: #06b6d4;
    }

    body.theme-messiah-gold {
      --bg-color: #1a1403;
      --panel-bg: rgba(38, 28, 5, 0.95);
      --border-color: rgba(234, 179, 8, 0.85);
      --accent-color: #eab308;
    }

    /* Spatial Draggable & Resizable Windows */
    .mesh-window {
      position: absolute;
      background: var(--panel-bg);
      border: 1px solid var(--border-color);
      border-radius: 12px;
      box-shadow: 0 20px 45px -10px rgba(0, 0, 0, 0.7);
      transition: box-shadow 0.2s ease, opacity 0.2s ease;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 320px;
      min-height: 180px;
      resize: both;
    }

    .window-resize-handle {
      position: absolute;
      bottom: 0;
      right: 0;
      width: 18px;
      height: 18px;
      cursor: nwse-resize;
      z-index: 50;
      display: flex;
      align-items: flex-end;
      justify-content: flex-end;
      padding: 3px;
      user-select: none;
    }
    .window-resize-handle::after {
      content: "";
      width: 8px;
      height: 8px;
      border-right: 2px solid rgba(255, 255, 255, 0.4);
      border-bottom: 2px solid rgba(255, 255, 255, 0.4);
      border-bottom-right-radius: 2px;
    }
    .window-resize-handle:hover::after {
      border-color: var(--accent-color);
    }

    .mesh-window.window-focused {
      border-color: var(--accent-color);
      box-shadow: 0 0 25px -4px var(--accent-color), 0 25px 50px -12px rgba(0, 0, 0, 0.85);
    }

    .mesh-window.maximized {
      top: 64px !important;
      left: 16px !important;
      right: 16px !important;
      bottom: 76px !important;
      width: calc(100vw - 32px) !important;
      height: calc(100vh - 140px) !important;
      z-index: 100 !important;
    }

    .mesh-window.popout-fullscreen {
      position: fixed !important;
      top: 56px !important;
      left: 8px !important;
      right: 8px !important;
      bottom: 8px !important;
      width: calc(100vw - 16px) !important;
      height: calc(100vh - 64px) !important;
      min-height: calc(100vh - 64px) !important;
      max-height: calc(100vh - 64px) !important;
      z-index: 100 !important;
      border-radius: 12px !important;
      background: #020617 !important;
      box-shadow: 0 0 50px rgba(0, 0, 0, 0.9) !important;
    }

    .mesh-window.popout-fullscreen .window-body {
      max-height: calc(100vh - 110px) !important;
      height: calc(100vh - 110px) !important;
      overflow-y: auto !important;
    }

    .mesh-window.popout-fullscreen .window-resize-handle {
      display: none !important;
    }

    .mesh-window.minimized {
      min-height: 0 !important;
      height: auto !important;
    }

    .mesh-window.minimized .window-body,
    .mesh-window.minimized .window-resize-handle {
      display: none !important;
    }

    .window-header {
      cursor: grab;
      user-select: none;
    }
    .window-header:active {
      cursor: grabbing;
    }

    /* Floating Reactions */
    @keyframes floatUpFade {
      0% {
        opacity: 1;
        transform: translateY(0) scale(0.8) rotate(0deg);
      }
      50% {
        opacity: 0.9;
        transform: translateY(-80px) scale(1.3) rotate(-10deg);
      }
      100% {
        opacity: 0;
        transform: translateY(-160px) scale(1.6) rotate(15deg);
      }
    }
    .reaction-particle {
      position: absolute;
      pointer-events: none;
      animation: floatUpFade 2s ease-out forwards;
      font-size: 2rem;
      z-index: 50;
    }

    /* Multiplayer Cursors */
    .remote-cursor {
      position: absolute;
      pointer-events: none;
      transition: transform 0.12s linear;
      z-index: 999;
    }

    /* Custom Scrollbar */
    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(148, 163, 184, 0.3);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(148, 163, 184, 0.5);
    }
  </style>
</head>
<body class="theme-slate bg-slate-950 text-slate-100 min-h-screen overflow-x-hidden font-sans select-none">

  <!-- Interactive Background Canvas: Peer Topology & Flying Packets -->
  <canvas id="meshTopologyCanvas" class="fixed inset-0 pointer-events-none z-0"></canvas>

  <!-- Multiplayer Peer Cursors Layer -->
  <div id="multiplayerCursorsLayer" class="fixed inset-0 pointer-events-none z-40 overflow-hidden"></div>

  <!-- High-Priority Admin Moderator Broadcast Banner -->
  <div id="adminBroadcastBanner" class="hidden fixed top-0 left-0 right-0 z-[100] bg-gradient-to-r from-amber-600 via-red-600 to-amber-600 text-white font-mono text-xs py-2 px-4 shadow-2xl flex items-center justify-between border-b-2 border-yellow-300 animate-pulse">
    <div class="flex items-center gap-2 max-w-5xl mx-auto">
      <span class="text-base">🚨</span>
      <span class="font-bold tracking-wider">[ADMIN MODERATOR ANNOUNCEMENT]:</span>
      <span id="adminBroadcastText" class="font-semibold text-amber-100"></span>
    </div>
    <button onclick="dismissAdminBanner()" class="px-2 py-0.5 rounded bg-black/40 hover:bg-black/70 text-white text-[11px] font-bold border border-white/30">✕ Dismiss</button>
  </div>

  <!-- ===================================================================== -->
  <!-- Non-Negotiable Account Registration & Identity Gate Modal -->
  <!-- ===================================================================== -->
  <div id="accountSetupModal" class="hidden fixed inset-0 z-[9999] bg-slate-950/95 backdrop-blur-xl flex items-center justify-center p-4 pointer-events-auto select-none">
    <div class="bg-slate-900 border-2 border-emerald-500/80 rounded-2xl max-w-lg w-full shadow-[0_0_80px_rgba(16,185,129,0.35)] overflow-hidden p-6 space-y-4">
      <div class="flex items-center justify-between border-b border-slate-800 pb-3">
        <div class="flex items-center gap-3">
          <span class="text-3xl">🛡️</span>
          <div>
            <h3 class="text-sm font-bold text-white font-mono flex items-center gap-2">
              <span>Mandatory Operator Registration</span>
              <span class="px-2 py-0.5 rounded-full bg-red-950 border border-red-500 text-red-300 text-[9px] uppercase font-bold tracking-wider">Non-Negotiable</span>
            </h3>
            <p class="text-[11px] text-slate-400">Mesh security protocol requires verified identity &amp; PII consent before entry</p>
          </div>
        </div>
      </div>

      <!-- Starter Perks Banner -->
      <div class="p-3 bg-gradient-to-r from-emerald-950/60 to-cyan-950/60 border border-emerald-500/40 rounded-xl space-y-1.5 font-mono text-[11px]">
        <div class="text-emerald-300 font-bold flex items-center gap-1.5">
          <span>🎁</span> <span>Claim Verified Mesh Operator Credentials:</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Complimentary Tokens:</span>
          <span class="font-bold text-emerald-400">50,000 🪙</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Sandbox API Credit:</span>
          <span class="font-bold text-cyan-400">$1.00 USD</span>
        </div>
        <div class="flex justify-between text-slate-300 pl-4">
          <span>• Hardware Node Peer ID:</span>
          <span id="modalPeerIdLabel" class="text-slate-400 truncate max-w-[160px]">...</span>
        </div>
      </div>

      <!-- Registration Form -->
      <form id="accountSetupForm" onsubmit="handleAccountFormSubmit(event)" class="space-y-3 font-mono text-xs">
        <div>
          <label class="block text-slate-300 font-semibold mb-1">Full Legal / Real Name <span class="text-red-400">*</span></label>
          <input id="accInputFullName" type="text" required minlength="2" placeholder="e.g. Jane Doe" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
        </div>

        <div>
          <label class="block text-slate-300 font-semibold mb-1">Username / Mesh Call-Sign <span class="text-red-400">*</span></label>
          <div class="relative">
            <span class="absolute left-3 top-2 text-slate-500">@</span>
            <input id="accInputUsername" type="text" required minlength="3" placeholder="handle_or_callsign" class="w-full pl-7 pr-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label class="block text-slate-300 font-semibold mb-1">Contact Email <span class="text-red-400">*</span></label>
            <input id="accInputEmail" type="email" required placeholder="you@fau.edu or email" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
          <div>
            <label class="block text-slate-300 font-semibold mb-1">Phone Number (SMS/2FA) <span class="text-red-400">*</span></label>
            <input id="accInputPhone" type="tel" required minlength="10" placeholder="+1 561 555 0199" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white placeholder-slate-600 focus:border-emerald-500 focus:outline-none" />
          </div>
        </div>

        <div>
          <label class="block text-slate-300 font-semibold mb-1">Affiliation / Purpose</label>
          <select id="accInputRole" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white focus:border-emerald-500 focus:outline-none">
            <option value="FAU Graduate School / Academic">FAU Graduate School / Academic Research</option>
            <option value="AI Systems Engineer">AI Systems Engineer / Developer</option>
            <option value="Mesh Operator">Decentralized Mesh Operator</option>
            <option value="Security Auditor">Security Auditor / Observer</option>
          </select>
        </div>

        <!-- Non-Negotiable PII Consent Accordion/Box -->
        <div class="p-3 bg-slate-950 rounded-xl border border-amber-500/40 space-y-2">
          <label class="flex items-start gap-2.5 cursor-pointer text-slate-200">
            <input id="accInputConsentPii" type="checkbox" required class="mt-0.5 w-4 h-4 rounded bg-slate-900 border-amber-500 text-emerald-500 focus:ring-0 focus:outline-none shrink-0" />
            <span class="text-[11px] leading-relaxed">
              <strong class="text-amber-300">Mandatory PII &amp; Operator Consent:</strong> I explicitly consent to the collection, cryptographic attestation, and federated storage of my Name, Email, Phone Number, Node IP, and AI usage telemetry for operator moderation and billing auditing.
            </span>
          </label>
        </div>

        <div id="accFormError" class="hidden text-red-400 text-[11px] p-2 bg-red-950/40 border border-red-800 rounded"></div>

        <div class="pt-2">
          <button type="submit" id="accSubmitBtn" class="w-full py-2.5 bg-gradient-to-r from-emerald-600 via-teal-600 to-cyan-600 hover:brightness-110 text-white font-bold rounded-lg shadow-lg transition active:scale-95 flex items-center justify-center gap-1.5 text-xs">
            <span>🛡️</span> <span>Sign Identity &amp; Unlock TinCan Mesh OS</span>
          </button>
          <p class="text-[10px] text-center text-slate-400 mt-2">
            ⚠️ This step is mandatory. Desktop and agent windows remain locked until verified.
          </p>
        </div>
      </form>
    </div>
  </div>

  <!-- Top Gamified Mesh OS HUD Bar -->
  <header id="meshOsHud" class="fixed top-0 left-0 right-0 h-14 bg-slate-950/90 border-b border-slate-800/80 backdrop-blur-md z-50 flex items-center justify-between px-3 sm:px-6 select-none">
    <div class="flex items-center gap-3">
      <div class="flex items-center gap-2">
        <span class="text-xl">🥫</span>
        <div>
          <span class="font-bold text-sm tracking-wide bg-gradient-to-r from-emerald-400 via-teal-300 to-cyan-400 bg-clip-text text-transparent">
            TinCan Mesh OS
          </span>
          <span class="hidden sm:inline-block text-[10px] text-slate-400 font-mono ml-1.5 px-1.5 py-0.5 rounded bg-slate-900 border border-slate-800">v2.1</span>
          <span id="osAdminBadge" class="hidden text-[10px] font-mono ml-1.5 px-2 py-0.5 rounded-full bg-amber-950/90 text-amber-300 border border-amber-500 font-bold tracking-wider shadow-[0_0_10px_rgba(245,158,11,0.4)]">🛡️ ADMIN MOD</span>
        </div>
      </div>

      <!-- Readiness Tier Badge -->
      <div id="osTierBadge" class="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 shadow-sm flex items-center gap-1.5">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>L5: Autonomous Mesh (94.5%)</span>
      </div>

      <!-- Live Squad XP Progress Bar -->
      <div class="hidden lg:flex items-center gap-2 font-mono text-xs">
        <div class="w-40 bg-slate-900 border border-slate-700/80 rounded-full h-2.5 overflow-hidden p-0.5">
          <div id="osXpBar" class="bg-gradient-to-r from-emerald-500 via-cyan-400 to-indigo-500 h-full rounded-full transition-all duration-500" style="width: 72%;"></div>
        </div>
        <span id="osXpText" class="text-cyan-300 text-[11px]">1,450 / 2,000 XP</span>
      </div>
    </div>

    <!-- HUD Right Controls -->
    <div class="flex items-center gap-2">
      <!-- User Account & Token Chip -->
      <button id="hudAccountBtn" onclick="openAccountModal()" class="text-xs font-mono px-2.5 py-1 rounded border border-emerald-600/70 bg-emerald-950/80 text-emerald-300 hover:bg-emerald-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-semibold" title="View or manage your mesh account & token billing balance">
        <span>👤</span> <span id="hudAccountName">Set Username</span> <span id="hudTokenPill" class="px-1.5 py-0.2 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-bold">50k 🪙</span>
      </button>

      <!-- Admin Mode Toggle & Mod Panel -->
      <button id="osAdminToggleBtn" onclick="toggleAdminMode()" class="text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:text-amber-400 hover:border-amber-600 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-semibold">
        <span>🛡️</span> <span id="osAdminToggleText">Admin Mode</span>
      </button>
      <button id="osModPanelBtn" onclick="toggleWindow('win-moderator')" class="hidden text-xs font-mono px-2.5 py-1 rounded border border-amber-500 bg-amber-950 text-amber-300 hover:bg-amber-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm font-bold">
        <span>🛡️</span> <span>Mod Panel</span>
      </button>

      <!-- Direct Live Chat Toggle -->
      <button onclick="focusChatWindow()" class="text-xs font-mono px-2.5 py-1 rounded border border-cyan-700 bg-cyan-950 text-cyan-300 hover:bg-cyan-900 transition flex items-center gap-1.5 active:scale-95 shadow-sm">
        <span>💬</span> <span class="font-bold">Chat</span> <span id="hudChatBadge" class="px-1.5 py-0.2 rounded-full bg-cyan-400 text-black text-[10px] font-bold">Live</span>
      </button>

      <!-- Active Peer & Network Pop-Out Launcher ("2 active") -->
      <button id="osPeerCount" onclick="toggleWindow('win-network')" class="text-xs font-mono px-2.5 py-1 rounded bg-emerald-950/90 border border-emerald-600/90 text-emerald-300 hover:bg-emerald-900 transition flex items-center gap-1.5 shadow-sm active:scale-95 cursor-pointer font-bold" title="Click to open Active Network Roster, Live Visitors & Leaderboard">
        <span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
        <span>👥 <span id="osPeerCountNum">2</span> Active ↗</span>
      </button>

      <!-- Layout Tiling Mode Switcher -->
      <div class="hidden md:flex items-center bg-slate-900 border border-slate-700/80 rounded-lg p-0.5 font-mono text-[11px] shadow-sm">
        <button id="btnLayoutTile2x2" onclick="setDesktopLayout('tile2x2')" class="px-2 py-0.5 rounded text-slate-300 hover:text-white transition flex items-center gap-1" title="Tile 2x2 Grid (4 Quadrants)">
          <span>🪟</span> <span>2x2 Grid</span>
        </button>
        <button id="btnLayoutSplit" onclick="setDesktopLayout('split2col')" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1" title="Split 2-Column Side-by-Side">
          <span>📑</span> <span>Split</span>
        </button>
        <button id="btnLayoutFree" onclick="setDesktopLayout('free')" class="px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1" title="Free Draggable Mode">
          <span>🗔</span> <span>Free</span>
        </button>
      </div>

      <!-- Unlockable Theme Selector -->
      <select id="osThemeSelect" onchange="changeTheme(this.value)" class="text-xs bg-slate-900 border border-slate-700 rounded px-2 py-1 text-slate-200 font-mono cursor-pointer hover:border-slate-500 transition">
        <option value="slate">Theme: Slate Standard (L1)</option>
        <option value="amber-crt">Theme: Amber Phosphor CRT (L2)</option>
        <option value="crypto-emerald">Theme: Cryptographic Emerald (L3)</option>
        <option value="webrtc-cyan">Theme: WebRTC Cyan Pulse (L4)</option>
        <option value="messiah-gold">Theme: AI Messiah Cyber Gold (L5)</option>
      </select>

      <!-- Audio Chimes SFX Toggle -->
      <button id="osSfxBtn" onclick="toggleSfx()" class="text-xs font-mono px-2.5 py-1 rounded border border-emerald-800 bg-emerald-950 text-emerald-300 hover:brightness-110 transition active:scale-95">
        🔔 SFX: ON
      </button>

      <!-- Pop Out Mode Guide -->
      <button onclick="togglePopoutGuide()" class="text-xs font-mono px-2 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:bg-slate-800 transition">
        ↗ Pop Out Guide
      </button>
    </div>
  </header>

  <!-- Desktop Spatial Workspace (Houses Draggable .mesh-window Containers) -->
  <main id="desktopWorkspace" class="relative w-full min-h-screen pt-16 pb-24 px-3 sm:px-6 z-10 select-text">

    <!-- ===================================================================== -->
    <!-- Window 1: Terminal & Quickstart.exe -->
    <!-- ===================================================================== -->
    <div id="win-terminal" class="mesh-window w-[540px]" data-window-id="win-terminal" style="top: 72px; left: 24px; z-index: 20;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">⚡</span>
          <span class="text-xs font-bold text-white font-mono">Terminal &amp; Quickstart.exe</span>
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-terminal')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[620px] overflow-y-auto">
        <div class="flex items-center justify-between">
          <h2 class="font-bold text-white text-sm">Quickstart &amp; One-Line Curl Commands</h2>
          <span class="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded font-mono">Instant Terminal Access</span>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-1.5">1. One-Line Terminal Installer (Installs TinCan CLI &amp; Skills):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between font-mono text-xs">
            <code id="curlInstallCmd" class="text-emerald-400 select-all overflow-x-auto">curl -sSL https://iot-federated-agent-memory-production.up.railway.app/install.sh | bash</code>
            <button onclick="copyCommand('curlInstallCmd')" class="ml-3 px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[11px] font-sans font-semibold transition shrink-0 active:scale-95">
              Copy Curl
            </button>
          </div>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-1.5">2. Or Install TinCan Skills Directly via npx skills:</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between font-mono text-xs">
            <code id="installCmd" class="text-indigo-300 select-all overflow-x-auto">npx skills add NoJuanNobody/tincan-skills -g -y</code>
            <button onclick="copyCommand('installCmd')" class="ml-3 px-2.5 py-1 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-[11px] font-sans font-semibold transition shrink-0 active:scale-95">
              Copy Command
            </button>
          </div>
        </div>

        <div>
          <p class="text-xs text-slate-400 mb-1.5">3. Live AI Model Prompt over OpenRouter Gateway (Gemini 2.5, Claude, Grok, GPT-4o):</p>
          <div class="bg-black/80 border border-slate-800 rounded-lg p-2.5 flex items-center justify-between font-mono text-xs">
            <code id="chatCmd" class="text-cyan-400 select-all overflow-x-auto">curl -s -X POST https://iot-federated-agent-memory-production.up.railway.app/api/chat -H "Content-Type: application/json" -d '{"prompt":"Hello world!"}'</code>
            <button onclick="copyCommand('chatCmd')" class="ml-3 px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-[11px] font-sans font-semibold transition shrink-0 active:scale-95">
              Copy Curl
            </button>
          </div>
        </div>

        <!-- Live Chat Quick Launcher -->
        <div class="p-3 bg-cyan-950/40 border border-cyan-800/80 rounded-lg flex items-center justify-between">
          <div class="space-y-0.5">
            <div class="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
              <span>💬</span> Live Mesh &amp; Peer Chat
            </div>
            <p class="text-[11px] text-slate-400">Broadcast messages in real time across all connected browsers and phones.</p>
          </div>
          <button onclick="focusChatWindow()" class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-bold font-mono transition shrink-0 active:scale-95 shadow">
            Open Chat →
          </button>
        </div>

        <div class="bg-slate-950/80 border border-slate-800 rounded-lg p-3 space-y-2">
          <div class="flex items-center justify-between">
            <h3 class="text-xs font-bold uppercase tracking-wider text-amber-400">TinCan Voice, Video &amp; Mesh Cheat Sheet</h3>
            <span class="text-[10px] font-mono text-slate-400">Watch the @nojuannobody walkthrough →</span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 font-mono text-xs">
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Speak + Send Remote TTS</div>
              <div class="text-emerald-300 mt-0.5">tincan say "Hey!" --to peer1</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live 2-Way Voice Call</div>
              <div class="text-cyan-300 mt-0.5">tincan call peer1 --voice-only</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Live Video / Screenshare</div>
              <div class="text-indigo-300 mt-0.5">tincan call peer1 --screen</div>
            </div>
            <div class="p-2 bg-slate-900 rounded border border-slate-800">
              <div class="text-slate-400 text-[10px]">Approve Queued Peer Action</div>
              <div class="text-amber-300 mt-0.5">tincan trigger 1</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 2: Relay TV Watch Party.app -->
    <!-- ===================================================================== -->
    <div id="win-tv" class="mesh-window w-[520px]" data-window-id="win-tv" style="top: 72px; right: 24px; z-index: 21;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">📺</span>
          <span class="text-xs font-bold text-white font-mono">Relay TV Watch Party.app</span>
          <span class="w-2 h-2 rounded-full bg-pink-500"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-tv')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div id="tv" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="w-full flex items-center justify-between">
          <div>
            <h2 class="font-bold text-white text-sm">Relay Video Channel &amp; Collection</h2>
            <p id="nowPlayingTitle" class="text-[11px] text-slate-400">Self-hosted Native MP4 · <span class="text-pink-400 font-mono">@nojuannobody</span></p>
          </div>
          <span id="playlistCounterBadge" class="text-[10px] bg-pink-950 text-pink-300 border border-pink-800 px-2.5 py-0.5 rounded-full font-mono uppercase">1 / 1 · Loop</span>
        </div>

        <!-- Video Player with Overlay for Multiplayer Floating Reactions -->
        <div class="relative w-full flex flex-col items-center justify-center overflow-hidden rounded-lg bg-black border border-slate-800 h-[380px]">
          <video
            id="relayNativeVideo"
            src="/videos/7705677376465767711.mp4"
            autoplay
            loop
            muted
            playsinline
            controls
            class="w-full h-full object-contain bg-black"
          ></video>
          <!-- Floating Reaction Particles Spawn In This Overlay -->
          <div id="reactionOverlay" class="absolute inset-0 pointer-events-none overflow-hidden"></div>
        </div>

        <!-- Watch Party Reactions Bar & Room Sync -->
        <div class="p-2.5 bg-slate-950/80 border border-pink-900/50 rounded-lg flex items-center justify-between gap-2">
          <div class="flex items-center gap-1.5 text-sm">
            <span class="text-[11px] font-mono text-slate-400 mr-1">React:</span>
            <button onclick="sendReaction('🔥')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🔥</button>
            <button onclick="sendReaction('🥫')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🥫</button>
            <button onclick="sendReaction('⚡')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">⚡</button>
            <button onclick="sendReaction('🧠')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🧠</button>
            <button onclick="sendReaction('🚀')" class="px-2 py-1 bg-slate-900 hover:bg-pink-950 rounded border border-slate-700 hover:border-pink-600 transition active:scale-125">🚀</button>
          </div>
          <button onclick="syncWatchParty()" class="px-3 py-1 bg-pink-900/70 hover:bg-pink-800 border border-pink-700 text-pink-200 rounded text-xs font-mono transition active:scale-95 shrink-0 flex items-center gap-1">
            <span>🔗</span> <span>Sync Party</span>
          </button>
        </div>

        <!-- Playlist Controls -->
        <div class="flex items-center justify-between gap-2 text-xs font-mono">
          <div class="flex items-center gap-1.5">
            <button onclick="prevPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">⏮ Prev</button>
            <button onclick="nextPlaylistVideo()" class="px-2.5 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded border border-slate-700 transition">Next ⏭</button>
            <button id="autoRotateBtn" onclick="toggleAutoRotate()" class="px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition">🔁 Auto-Loop: ON</button>
          </div>
          <button id="soundToggleBtn" onclick="toggleVideoSound()" class="px-2.5 py-1 bg-pink-950 hover:bg-pink-900 text-pink-300 rounded border border-pink-800 transition">
            🔊 Tap to Unmute
          </button>
        </div>

        <!-- Collection Queue List -->
        <div id="playlistQueue" class="space-y-1 max-h-24 overflow-y-auto pr-1 text-xs font-mono">
          <!-- Populated dynamically from /api/playlist -->
        </div>

        <!-- Add Video Form -->
        <div class="pt-2 border-t border-slate-800 flex gap-1.5 text-xs">
          <input id="newVideoInput" type="text" placeholder="Paste video URL or ID to ingest MP4 into relay collection..." class="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white font-mono placeholder:text-slate-600">
          <button onclick="addVideoToPlaylist()" class="px-3 py-1.5 bg-pink-600 hover:bg-pink-500 text-white font-semibold rounded transition shrink-0 active:scale-95">
            + Ingest MP4
          </button>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 3: AI Brain Router & Model Arena.app -->
    <!-- ===================================================================== -->
    <div id="win-arena" class="mesh-window w-[560px]" data-window-id="win-arena" style="top: 720px; left: 24px; z-index: 22;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">🧠</span>
          <span class="text-xs font-bold text-white font-mono">AI Brain Router &amp; Arena.app</span>
          <span class="w-2 h-2 rounded-full bg-indigo-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-arena')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[620px] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-sm font-bold text-white flex items-center gap-2">
              <span>💳</span> OpenRouter Cost, Spend &amp; Credit Dashboard
            </h2>
            <p class="text-[11px] text-slate-400">Live account credits, lifetime spend, key usage, and per-model token pricing</p>
          </div>
          <div id="analyticsHeader" class="text-right text-[11px] font-mono text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2.5 py-1 rounded-md">
            Fetching live OpenRouter billing...
          </div>
        </div>

        <div class="grid grid-cols-2 gap-2 text-xs font-mono">
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">OpenRouter Remaining Balance</div>
            <div id="orRemaining" class="text-base font-bold text-emerald-400 mt-0.5">--</div>
            <div id="orCreditsTotal" class="text-[10px] text-slate-500">of -- credits</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Total Lifetime Spend</div>
            <div id="orTotalUsage" class="text-base font-bold text-amber-400 mt-0.5">--</div>
            <div class="text-[10px] text-slate-500">Account aggregate</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Active Key Usage</div>
            <div id="orKeyUsage" class="text-base font-bold text-cyan-400 mt-0.5">--</div>
            <div id="orKeyToday" class="text-[10px] text-slate-500">Today: --</div>
          </div>
          <div class="p-2.5 bg-slate-950/80 border border-slate-800 rounded-lg">
            <div class="text-slate-400 text-[10px]">Key Budget Cap</div>
            <div id="orKeyLimitRem" class="text-base font-bold text-indigo-400 mt-0.5">--</div>
            <div id="orKeyLabel" class="text-[10px] text-slate-500 truncate">Key: --</div>
          </div>
        </div>

        <!-- Hidden elements to preserve backward compatibility for top cards -->
        <div class="hidden">
          <div id="topBalanceValue">Loading...</div>
          <div id="topBalanceSub">Live OpenRouter Credit Pool</div>
        </div>

        <!-- Live Provider & Cost Cards Grid -->
        <div id="providerCards" class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <!-- Injected via JavaScript -->
        </div>

        <!-- Configure / Swap Model Form -->
        <div class="bg-slate-950/70 border border-slate-800 rounded-lg p-3 space-y-2.5">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-xs font-semibold text-slate-200">Configure / Swap Model Target</h3>
            <span id="currentTargetModelBadge" class="text-[10px] font-mono bg-indigo-950/80 text-indigo-300 border border-indigo-800 px-2 py-0.5 rounded">
              Active: gemini-brain → google/gemini-2.5-flash
            </span>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-4 gap-2 text-xs">
            <div>
              <label class="block text-slate-400 mb-1 text-[11px]">Target Alias</label>
              <select id="aliasSelect" onchange="syncSelectedAliasModel(true)" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono">
                <option value="gemini-brain">gemini-brain → google/gemini-2.5-flash</option>
                <option value="claude-brain">claude-brain → anthropic/claude-sonnet-5.5</option>
                <option value="grok-brain">grok-brain → x-ai/grok-4.7</option>
                <option value="openai-brain">openai-brain → openai/gpt-4o</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="block text-slate-400 mb-1 text-[11px]">OpenRouter Model ID</label>
              <input type="text" id="modelInput" placeholder="e.g. meta-llama/llama-3.3-70b-instruct" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white font-mono placeholder:text-slate-600">
            </div>
            <div class="flex items-end">
              <button onclick="updateModel()" class="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-semibold rounded px-2.5 py-1.5 transition active:scale-95 text-xs">
                Update Model
              </button>
            </div>
          </div>
          <div class="flex flex-wrap items-center gap-1 pt-1 text-[10px] font-mono">
            <span class="text-slate-500 mr-1">Quick Swap:</span>
            <button type="button" onclick="quickPickModel('google/gemini-2.5-pro')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">gemini-2.5-pro</button>
            <button type="button" onclick="quickPickModel('anthropic/claude-3.7-sonnet')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">claude-3.7-sonnet</button>
            <button type="button" onclick="quickPickModel('x-ai/grok-3')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">x-ai/grok-3</button>
            <button type="button" onclick="quickPickModel('openai/gpt-4o')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">openai/gpt-4o</button>
            <button type="button" onclick="quickPickModel('meta-llama/llama-3.3-70b-instruct')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">llama-3.3-70b</button>
            <button type="button" onclick="quickPickModel('deepseek/deepseek-r1')" class="px-1.5 py-0.5 rounded bg-slate-900 hover:bg-indigo-950 text-slate-300 border border-slate-700">deepseek-r1</button>
          </div>
          <p id="updateFeedback" class="text-xs mt-2 font-mono hidden"></p>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 4: WebRTC Comms & Screenshare Studio.app -->
    <!-- ===================================================================== -->
    <div id="win-comms" class="mesh-window w-[540px]" data-window-id="win-comms" style="top: 720px; right: 24px; z-index: 23;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">📹</span>
          <span class="text-xs font-bold text-white font-mono">WebRTC Comms Studio.app</span>
          <span class="w-2 h-2 rounded-full bg-cyan-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-comms')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div id="call" class="window-body p-4 space-y-3 max-h-[620px] overflow-y-auto">
        <div class="flex flex-wrap justify-between items-center gap-2">
          <div>
            <h2 class="text-xs font-bold text-white uppercase tracking-wider">P2P Encrypted Mesh Comms</h2>
            <p class="text-[11px] text-slate-400">Multi-peer voice calling, H.264 video &amp; desktop screenshare</p>
          </div>
          <div class="flex items-center gap-1.5 text-xs font-mono">
            <span class="text-slate-400 text-[11px]">Room:</span>
            <input id="roomInput" type="text" value="main" class="bg-slate-950 border border-slate-700 rounded px-2 py-0.5 text-cyan-300 w-20 text-xs">
            <button onclick="copyInviteLink()" class="px-2 py-0.5 bg-slate-800 hover:bg-slate-700 border border-slate-600 rounded text-slate-200 transition text-[11px]">
              Copy Link
            </button>
            <span id="callStatusBadge" class="px-2 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700 text-[11px]">Idle</span>
          </div>
        </div>

        <!-- Call Action Buttons -->
        <div class="flex flex-wrap gap-1.5 text-xs font-mono">
          <button onclick="startCall('video')" class="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold rounded transition active:scale-95">
            🎥 Video + Voice
          </button>
          <button onclick="startCall('voice')" class="px-2.5 py-1 bg-teal-600 hover:bg-teal-500 text-white font-semibold rounded transition active:scale-95">
            🎙️ Voice Call
          </button>
          <button onclick="startScreenShare()" class="px-2.5 py-1 bg-cyan-600 hover:bg-cyan-500 text-white font-semibold rounded transition active:scale-95">
            🖥️ Screen Share
          </button>
          <button id="muteBtn" onclick="toggleMute()" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded border border-slate-700 transition">
            🔇 Mute Mic
          </button>
          <button id="camBtn" onclick="toggleCamera()" class="px-2 py-1 bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold rounded border border-slate-700 transition">
            📷 Toggle Cam
          </button>
          <button onclick="hangupCall()" class="px-2.5 py-1 bg-rose-700 hover:bg-rose-600 text-white font-semibold rounded transition ml-auto active:scale-95">
            ⏹ End
          </button>
        </div>

        <!-- Video Viewports -->
        <div class="grid grid-cols-1 sm:grid-cols-2 gap-2">
          <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
            <video id="localVideo" autoplay playsinline muted class="w-full h-full object-cover"></video>
            <div class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 bg-black/75 rounded text-[10px] font-mono text-emerald-300 border border-emerald-900">
              Local (<span id="localPeerLabel">you</span>)
            </div>
          </div>
          <div class="relative bg-black rounded-lg border border-slate-800 overflow-hidden aspect-video flex items-center justify-center">
            <video id="remoteVideo" autoplay playsinline class="w-full h-full object-cover"></video>
            <div class="absolute bottom-1.5 left-1.5 px-1.5 py-0.5 bg-black/75 rounded text-[10px] font-mono text-cyan-300 border border-cyan-900">
              Remote (<span id="remotePeerLabel">waiting for peer...</span>)
            </div>
          </div>
        </div>

        <!-- Active UDP Streams -->
        <div class="pt-2 border-t border-slate-800">
          <div class="text-[11px] font-semibold text-slate-400 mb-1.5">Active Room &amp; UDP Streams</div>
          <div id="roomPeersGrid" class="space-y-1.5 text-xs font-mono">
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center">
              <span class="text-white">Mac Studio (M1 Max)</span>
              <span class="bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">UDP: 50004</span>
            </div>
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center">
              <span class="text-white">Collaborator MacBook</span>
              <span class="bg-cyan-900 text-cyan-300 px-1.5 py-0.5 rounded text-[10px]">UDP: 50006</span>
            </div>
          </div>
        </div>

        <!-- Live Room & Peer Chat Messaging -->
        <div class="pt-3 border-t border-slate-800 space-y-2">
          <div class="flex items-center justify-between">
            <span class="text-[11px] font-bold text-cyan-400 uppercase tracking-wider flex items-center gap-1.5">
              <span>💬</span> Live Mesh &amp; Peer Chat
            </span>
            <span id="chatCounterBadge" class="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">0 messages</span>
          </div>

          <!-- Message stream -->
          <div id="chatMessagesList" class="h-44 overflow-y-auto p-2.5 bg-slate-950/90 border border-slate-800 rounded-lg space-y-2 text-xs font-mono">
            <div class="text-slate-500 text-[11px] italic">No messages yet. Send a broadcast to all active room peers below.</div>
          </div>

          <!-- Message input -->
          <div class="flex gap-1.5">
            <input id="chatInput" type="text" placeholder="Type a message to room peers..." class="flex-1 bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-white font-mono placeholder:text-slate-600 focus:border-cyan-400 focus:outline-none" onkeydown="if(event.key==='Enter') sendChatMessage()">
            <button onclick="sendChatMessage()" class="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-bold font-mono transition active:scale-95 shrink-0 flex items-center gap-1">
              <span>Send</span>
              <span>↵</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 5: Quests, Arena & Operator Leaderboard.app -->
    <!-- ===================================================================== -->
    <div id="win-quests" class="mesh-window w-[1100px] max-w-full" data-window-id="win-quests" style="top: 1380px; left: 24px; z-index: 24;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-slate-900/90 border-b border-slate-800">
        <div class="flex items-center gap-2">
          <span class="text-base">🎯</span>
          <span class="text-xs font-bold text-white font-mono">Quests, Arena &amp; Operator Leaderboard.app</span>
          <span class="w-2 h-2 rounded-full bg-amber-400"></span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-quests')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-6 max-h-[750px] overflow-y-auto">

        <!-- Top Section: Cooperative Quest Deck -->
        <div>
          <div class="flex items-center justify-between mb-3">
            <div>
              <h2 class="text-sm font-bold text-white flex items-center gap-2">
                <span>⚔️</span> Cooperative Quest Deck &amp; L1 $\rightarrow$ L5 Ascension Loop
              </h2>
              <p class="text-xs text-slate-400">Complete peer actions to award Squad XP, unlock desktop themes, and level up the mesh.</p>
            </div>
            <span class="text-xs font-mono text-amber-400 bg-amber-950/60 border border-amber-800 px-2.5 py-1 rounded">
              Active Squad Quests
            </span>
          </div>

          <div id="questDeckGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            <!-- Dynamically populated or rendered via JS from /api/mesh/state -->
            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-emerald-400 font-mono">L1 Sealed Courier</span>
                  <span class="text-[10px] bg-emerald-950 text-emerald-300 border border-emerald-800 px-1.5 py-0.5 rounded font-mono">+100 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Dispatch an Ed25519 sealed envelope through TinCan Blind Relay.</p>
              </div>
              <button onclick="triggerQuestAction('sealed_courier')" class="w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                🥫 Dispatch Sealed Ping (+100 XP)
              </button>
            </div>

            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-indigo-400 font-mono">L4 Synapse Battle</span>
                  <span class="text-[10px] bg-indigo-950 text-indigo-300 border border-indigo-800 px-1.5 py-0.5 rounded font-mono">+150 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Run dual completion duel and vote for winning AI brain.</p>
              </div>
              <button onclick="triggerQuestAction('arena_vote')" class="w-full py-1.5 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                🧠 Run Blind Arena Battle (+150 XP)
              </button>
            </div>

            <div class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div>
                <div class="flex justify-between items-center">
                  <span class="font-bold text-xs text-amber-400 font-mono">L5 HITL Trigger</span>
                  <span class="text-[10px] bg-amber-950 text-amber-300 border border-amber-800 px-1.5 py-0.5 rounded font-mono">+200 XP</span>
                </div>
                <p class="text-xs text-slate-300 mt-1">Execute human-in-the-loop approved peer command.</p>
              </div>
              <button onclick="triggerQuestAction('coop_action')" class="w-full py-1.5 bg-amber-600 hover:bg-amber-500 text-white rounded text-xs font-mono font-semibold transition active:scale-95">
                ⚡ Trigger Co-Op Action (+200 XP)
              </button>
            </div>
          </div>
        </div>

        <!-- Middle Section: Side-by-Side AI Brain Arena -->
        <div id="arenaBattleBox" class="bg-slate-950/90 border border-indigo-900/60 rounded-xl p-4 space-y-3">
          <div class="flex flex-wrap items-center justify-between gap-2">
            <div>
              <h3 class="text-xs font-bold uppercase tracking-wider text-indigo-300 flex items-center gap-1.5">
                <span>⚔️</span> Side-by-Side AI Brain Arena Duel
              </h3>
              <p class="text-[11px] text-slate-400">Dispatch dual completion to Gemini 2.5 vs Claude 3.7 and vote for the best response (+150 XP).</p>
            </div>
            <span class="text-[11px] font-mono text-cyan-400 bg-cyan-950/60 border border-cyan-800 px-2 py-0.5 rounded">
              Blind Duel Protocol
            </span>
          </div>

          <div class="flex gap-2">
            <input id="arenaPromptInput" type="text" value="Explain zero-knowledge proofs and federated CRDT meshes in two concise sentences." class="flex-1 bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-600">
            <button onclick="runArenaBattle()" class="px-4 py-1.5 bg-gradient-to-r from-indigo-600 to-cyan-600 hover:brightness-110 text-white font-semibold rounded text-xs transition active:scale-95 shrink-0 flex items-center gap-1.5">
              <span>⚔️</span> <span>Battle 2 Brains</span>
            </button>
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-3 pt-2">
            <!-- Brain A: Gemini -->
            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div class="flex justify-between items-center pb-1.5 border-b border-slate-800">
                <span class="font-bold text-xs text-emerald-300 font-mono">Brain A (gemini-brain)</span>
                <span class="text-[10px] text-slate-400 font-mono">Gemini 2.5 Flash</span>
              </div>
              <div id="arenaResultA" class="text-xs font-mono text-slate-200 min-h-[90px] max-h-[160px] overflow-y-auto whitespace-pre-wrap bg-black/40 p-2.5 rounded">
                Click "Battle 2 Brains" above to dispatch simultaneous prompts...
              </div>
              <button onclick="voteArenaWinner('gemini-brain')" class="w-full py-1.5 bg-emerald-700/80 hover:bg-emerald-600 text-white font-semibold rounded text-xs transition active:scale-95 font-mono">
                🏆 Vote Brain A (+150 XP)
              </button>
            </div>

            <!-- Brain B: Claude -->
            <div class="p-3 bg-slate-900/90 rounded-lg border border-slate-800 flex flex-col justify-between space-y-2">
              <div class="flex justify-between items-center pb-1.5 border-b border-slate-800">
                <span class="font-bold text-xs text-cyan-300 font-mono">Brain B (claude-brain)</span>
                <span class="text-[10px] text-slate-400 font-mono">Claude 3.7 Sonnet</span>
              </div>
              <div id="arenaResultB" class="text-xs font-mono text-slate-200 min-h-[90px] max-h-[160px] overflow-y-auto whitespace-pre-wrap bg-black/40 p-2.5 rounded">
                Click "Battle 2 Brains" above to dispatch simultaneous prompts...
              </div>
              <button onclick="voteArenaWinner('claude-brain')" class="w-full py-1.5 bg-cyan-700/80 hover:bg-cyan-600 text-white font-semibold rounded text-xs transition active:scale-95 font-mono">
                🏆 Vote Brain B (+150 XP)
              </button>
            </div>
          </div>
        </div>

        <!-- Bottom Section: Live Operator Leaderboard -->
        <div>
          <div class="flex items-center justify-between mb-2">
            <h3 class="text-xs font-bold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
              <span>🏆</span> Live Mesh Operator Leaderboard
            </h3>
            <div class="flex items-center gap-2">
              <span class="text-[11px] font-mono text-slate-400">Ranked by Lifetime XP</span>
              <button onclick="toggleWindow('win-network')" class="text-[10px] font-mono text-emerald-400 hover:text-emerald-300 bg-emerald-950/80 border border-emerald-700/80 px-2 py-0.5 rounded transition flex items-center gap-1 active:scale-95" title="Open standalone window with 2 Active Peers and Live Visitors">
                <span>👥</span> <span>Standalone 2-Active Window ↗</span>
              </button>
            </div>
          </div>

          <div class="bg-slate-950/80 border border-slate-800 rounded-lg overflow-hidden">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-900 text-slate-400 border-b border-slate-800">
                <tr>
                  <th class="px-3 py-2">Rank</th>
                  <th class="px-3 py-2">Operator Peer</th>
                  <th class="px-3 py-2">Readiness Tier</th>
                  <th class="px-3 py-2">Badges</th>
                  <th class="px-3 py-2 text-right">Squad XP</th>
                </tr>
              </thead>
              <tbody id="operatorLeaderboard" class="divide-y divide-slate-800/60">
                <tr>
                  <td class="px-3 py-2 text-amber-400 font-bold">#1</td>
                  <td class="px-3 py-2 text-white font-bold">Mac Studio (M1 Max)</td>
                  <td class="px-3 py-2 text-emerald-400">L5: Autonomous Mesh</td>
                  <td class="px-3 py-2">
                    <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">🟢 Initiate</span>
                    <span class="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px]">🥫 Postmaster</span>
                  </td>
                  <td class="px-3 py-2 text-right text-cyan-300 font-bold">850 XP</td>
                </tr>
                <tr>
                  <td class="px-3 py-2 text-slate-400 font-bold">#2</td>
                  <td class="px-3 py-2 text-slate-200">Collaborator MacBook</td>
                  <td class="px-3 py-2 text-emerald-400">L4: CRDT Gossip</td>
                  <td class="px-3 py-2">
                    <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px]">🟢 Initiate</span>
                  </td>
                  <td class="px-3 py-2 text-right text-cyan-300 font-bold">600 XP</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 6: Admin Moderator Control Panel -->
    <!-- ===================================================================== -->
    <div id="win-moderator" class="mesh-window w-[680px] hidden" data-window-id="win-moderator" style="top: 84px; left: 180px; z-index: 25;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-gradient-to-r from-amber-950/90 via-slate-900/90 to-amber-950/90 border-b border-amber-600/50">
        <div class="flex items-center gap-2">
          <span class="text-base">🛡️</span>
          <span class="text-xs font-bold text-amber-300 font-mono tracking-wide">Admin Moderator Control Panel</span>
          <span class="px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/50">AUTHORITY LEVEL: HIGH</span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-moderator')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-moderator')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-moderator')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
          <button onclick="toggleWindow('win-moderator')" class="px-1.5 py-0.5 rounded bg-amber-950 hover:bg-amber-900 text-amber-300 text-[11px] border border-amber-800">✕</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[660px] overflow-y-auto">

        <!-- Moderator KPI Cards -->
        <div class="grid grid-cols-3 gap-2 font-mono">
          <div class="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Web Visitors</div>
            <div id="modWebCount" class="text-xl font-bold text-emerald-400 mt-0.5">0</div>
            <div class="text-[9px] text-emerald-500/80">Active Browser Tabs</div>
          </div>
          <div class="bg-slate-900/90 border border-slate-800 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-slate-400 uppercase tracking-wider">Mesh Streams</div>
            <div id="modMeshCount" class="text-xl font-bold text-cyan-400 mt-0.5">0</div>
            <div class="text-[9px] text-cyan-500/80">WebRTC / Workstations</div>
          </div>
          <div class="bg-slate-900/90 border border-amber-900/40 rounded-lg p-2.5 text-center">
            <div class="text-[10px] text-amber-400/90 uppercase tracking-wider">Admin Status</div>
            <div class="text-sm font-bold text-amber-300 mt-1 flex items-center justify-center gap-1">
              <span class="w-2 h-2 rounded-full bg-amber-400 animate-pulse"></span>
              <span>ACTIVE 🛡️</span>
            </div>
            <div class="text-[9px] text-slate-400">Total Mesh Authority</div>
          </div>
        </div>

        <!-- Emergency Moderator Broadcast -->
        <div class="bg-slate-900/90 border border-amber-700/60 rounded-xl p-3.5 space-y-2">
          <div class="flex items-center justify-between">
            <div class="text-xs font-bold text-amber-300 font-mono flex items-center gap-1.5">
              <span>📢</span>
              <span>System-Wide Moderator Announcement</span>
            </div>
            <span class="text-[10px] text-slate-400 font-mono">Pushes banner to all web &amp; mesh clients</span>
          </div>
          <div class="flex gap-2">
            <input type="text" id="adminAnnouncementInput" placeholder="Enter high-priority announcement (e.g., 'Scheduled maintenance in 10 mins' or 'Welcome to the lab')..." class="flex-1 bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono placeholder:text-slate-600 focus:outline-none focus:border-amber-500">
            <button onclick="sendAdminBroadcast()" class="px-3 py-1.5 bg-gradient-to-r from-amber-600 to-yellow-600 hover:brightness-110 text-slate-950 font-bold rounded-lg text-xs font-mono transition active:scale-95 shadow flex items-center gap-1">
              <span>⚡</span> <span>Broadcast</span>
            </button>
          </div>
        </div>

        <!-- Section 1: Relay Website Visitors -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1.5">
              <span>🌐</span>
              <span>Relay Website Visitors (Active Browser Cursors)</span>
            </div>
            <span id="modWebVisitorsCountTag" class="text-[11px] font-mono text-slate-400">0 connected</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Peer ID</th>
                  <th class="px-2.5 py-1.5">Room</th>
                  <th class="px-2.5 py-1.5">Focus Window</th>
                  <th class="px-2.5 py-1.5">Cursor Pos</th>
                  <th class="px-2.5 py-1.5">Last Seen</th>
                  <th class="px-2.5 py-1.5 text-right">Moderator Action</th>
                </tr>
              </thead>
              <tbody id="modWebVisitorsTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Polling live website cursors...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 2: Connected Mesh Nodes -->
        <div class="bg-slate-900/80 border border-slate-800 rounded-xl p-3.5 space-y-2.5">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-cyan-400 font-mono flex items-center gap-1.5">
              <span>📡</span>
              <span>Connected Mesh Nodes (Live WebRTC Streams &amp; Workstations)</span>
            </div>
            <span id="modMeshNodesCountTag" class="text-[11px] font-mono text-slate-400">0 streams</span>
          </div>
          <div class="overflow-x-auto">
            <table class="w-full text-left font-mono text-xs">
              <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                <tr>
                  <th class="px-2.5 py-1.5">Peer / Node ID</th>
                  <th class="px-2.5 py-1.5">Display Name</th>
                  <th class="px-2.5 py-1.5">Room</th>
                  <th class="px-2.5 py-1.5">Media Capabilities</th>
                  <th class="px-2.5 py-1.5">UDP Port</th>
                  <th class="px-2.5 py-1.5 text-right">Moderator Action</th>
                </tr>
              </thead>
              <tbody id="modMeshNodesTable" class="divide-y divide-slate-800/50">
                <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Polling active WebRTC streams...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Section 3: Video & Sponsored Ad Fleet Studio (Admin CRUD) -->
        <div class="bg-slate-900/80 border border-pink-900/50 rounded-xl p-3.5 space-y-3">
          <div class="flex items-center justify-between border-b border-slate-800/80 pb-2">
            <div class="text-xs font-bold text-pink-400 font-mono flex items-center gap-1.5">
              <span>🎬</span>
              <span>Video &amp; Sponsored Ad Fleet Studio (Admin CRUD)</span>
            </div>
            <div class="flex items-center gap-1.5">
              <button onclick="toggleAdminTab('videos')" id="adminTabBtnVideos" class="px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-700 text-[10px] font-mono font-bold">Videos (<span id="adminVideosCount">0</span>)</button>
              <button onclick="toggleAdminTab('sponsors')" id="adminTabBtnSponsors" class="px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono">Sponsor Ads (<span id="adminSponsorsCount">0</span>)</button>
            </div>
          </div>

          <!-- Sub-Panel A: Videos CRUD -->
          <div id="adminVideosPanel" class="space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-300 font-mono">Relay Watch Party Collection (S3 Backed)</span>
              <button onclick="toggleAddVideoDrawer()" class="px-2.5 py-1 bg-pink-600 hover:bg-pink-500 text-white font-mono text-[10px] rounded font-bold transition flex items-center gap-1 active:scale-95">
                <span>+</span> <span>Add Video / Ingest MP4</span>
              </button>
            </div>

            <!-- Add Video Drawer -->
            <div id="adminAddVideoDrawer" class="hidden p-2.5 bg-slate-950 border border-pink-800/60 rounded-lg space-y-2 text-xs font-mono">
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Video URL or TikTok ID *</label>
                  <input id="adminNewVideoUrl" type="text" placeholder="https://www.tiktok.com/@creator/video/123... or ID" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Display Title</label>
                  <input id="adminNewVideoTitle" type="text" placeholder="Video Title" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Creator Handle</label>
                  <input id="adminNewVideoCreator" type="text" placeholder="@creator" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Category</label>
                  <select id="adminNewVideoCategory" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                    <option value="spotlight">spotlight</option>
                    <option value="instruction">instruction</option>
                    <option value="ad">ad (sponsored)</option>
                  </select>
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Duration (Seconds)</label>
                  <input id="adminNewVideoDuration" type="number" value="35" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex justify-end gap-1.5 pt-1">
                <button onclick="toggleAddVideoDrawer()" class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded text-[10px]">Cancel</button>
                <button onclick="adminSubmitAddVideo()" class="px-3 py-1 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded text-[10px] active:scale-95">Save &amp; Ingest to S3</button>
              </div>
            </div>

            <!-- Videos Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-left font-mono text-xs">
                <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                  <tr>
                    <th class="px-2.5 py-1.5">ID / Stream</th>
                    <th class="px-2.5 py-1.5">Title</th>
                    <th class="px-2.5 py-1.5">Creator</th>
                    <th class="px-2.5 py-1.5">Category</th>
                    <th class="px-2.5 py-1.5">Dur</th>
                    <th class="px-2.5 py-1.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody id="adminVideosTableBody" class="divide-y divide-slate-800/50">
                  <tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">Loading video collection...</td></tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- Sub-Panel B: Sponsor Ads CRUD -->
          <div id="adminSponsorsPanel" class="hidden space-y-2.5">
            <div class="flex items-center justify-between">
              <span class="text-[11px] text-slate-300 font-mono">Sponsor Creatives &amp; Ad Subsidies</span>
              <button onclick="toggleAddSponsorDrawer()" class="px-2.5 py-1 bg-amber-600 hover:bg-amber-500 text-slate-950 font-mono text-[10px] rounded font-bold transition flex items-center gap-1 active:scale-95">
                <span>+</span> <span>Add Sponsor Creative</span>
              </button>
            </div>

            <!-- Add Sponsor Drawer -->
            <div id="adminAddSponsorDrawer" class="hidden p-2.5 bg-slate-950 border border-amber-800/60 rounded-lg space-y-2 text-xs font-mono">
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Sponsor Name *</label>
                  <input id="adminNewSponsorName" type="text" placeholder="e.g. Anthropic Claude" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Icon / Emoji</label>
                  <input id="adminNewSponsorIcon" type="text" value="🌟" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Badge Text</label>
                  <input id="adminNewSponsorBadge" type="text" value="Partner" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-2 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Tagline</label>
                  <input id="adminNewSponsorTagline" type="text" placeholder="Tagline description" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Destination URL</label>
                  <input id="adminNewSponsorUrl" type="text" placeholder="https://..." class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="grid grid-cols-3 gap-2">
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">CTA Button</label>
                  <input id="adminNewSponsorCta" type="text" value="Visit Partner ↗" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Reward Tokens</label>
                  <input id="adminNewSponsorRewardTokens" type="number" value="5000" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
                <div>
                  <label class="text-[10px] text-slate-400 block mb-0.5">Reward USD</label>
                  <input id="adminNewSponsorRewardUsd" type="number" step="0.01" value="0.05" class="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-white text-xs">
                </div>
              </div>
              <div class="flex justify-end gap-1.5 pt-1">
                <button onclick="toggleAddSponsorDrawer()" class="px-2.5 py-1 bg-slate-800 text-slate-300 rounded text-[10px]">Cancel</button>
                <button onclick="adminSubmitAddSponsor()" class="px-3 py-1 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded text-[10px] active:scale-95">Save Sponsor Ad</button>
              </div>
            </div>

            <!-- Sponsors Table -->
            <div class="overflow-x-auto">
              <table class="w-full text-left font-mono text-xs">
                <thead class="text-slate-400 bg-slate-950/60 border-b border-slate-800 text-[11px]">
                  <tr>
                    <th class="px-2.5 py-1.5">Sponsor</th>
                    <th class="px-2.5 py-1.5">Badge</th>
                    <th class="px-2.5 py-1.5">Reward</th>
                    <th class="px-2.5 py-1.5">Telemetry (Imp/Clk/Comp)</th>
                    <th class="px-2.5 py-1.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody id="adminSponsorsTableBody" class="divide-y divide-slate-800/50">
                  <tr><td colspan="5" class="px-3 py-3 text-center text-slate-500 text-[11px]">Loading sponsor creatives...</td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 7: Token Billing, Top-Up & Sponsored Ads.app -->
    <!-- ===================================================================== -->
    <div id="win-billing" class="mesh-window w-[620px]" data-window-id="win-billing" style="top: 140px; left: 120px; z-index: 26;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-gradient-to-r from-emerald-950/90 via-slate-900/90 to-cyan-950/90 border-b border-emerald-500/40">
        <div class="flex items-center gap-2">
          <span class="text-base">💳</span>
          <span class="text-xs font-bold text-emerald-300 font-mono tracking-wide">Token Store &amp; Sponsor Ads.app</span>
          <span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-mono border border-emerald-500/40 font-semibold">COST SUBSIDY</span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-billing')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-billing')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-billing')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">⤢</button>
          <button onclick="toggleWindow('win-billing')" class="px-1.5 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 text-[11px]">✕</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[720px] overflow-y-auto text-xs font-sans">
        <!-- Live Balance Banner -->
        <div class="p-3 bg-slate-900/80 rounded-xl border border-emerald-500/40 flex items-center justify-between">
          <div>
            <div class="text-[11px] text-slate-400 font-mono">Connected Peer Token Balance</div>
            <div class="flex items-baseline gap-2 mt-0.5">
              <span id="billingWindowTokens" class="text-2xl font-bold font-mono text-emerald-400">50,000</span>
              <span class="text-slate-400 text-xs font-mono">tokens</span>
              <span class="text-slate-600">|</span>
              <span id="billingWindowCredits" class="text-sm font-mono text-cyan-300 font-bold">$1.00 USD</span>
            </div>
          </div>
          <button onclick="refreshBillingWindow()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 text-xs font-mono flex items-center gap-1 active:scale-95">
            🔄 Refresh
          </button>
        </div>

        <!-- Section 1: Sponsored Ads (Subsidize Costs with Ads) -->
        <div class="p-3 bg-gradient-to-r from-amber-950/40 to-slate-900/80 rounded-xl border border-amber-600/40 space-y-3">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="text-amber-400 text-sm">📺</span>
              <span class="font-bold text-amber-300 font-mono">Watch Sponsored Ads (Earn Free Tokens)</span>
            </div>
            <div class="flex items-center gap-1.5">
              <button type="button" onclick="fetchNextSponsor()" title="Rotate to next sponsor" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[10px] font-mono border border-slate-700 active:scale-95 transition">⟳ Next Sponsor</button>
              <span class="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-mono border border-amber-500/30 font-bold">+5,000 TOKENS</span>
            </div>
          </div>
          <p class="text-[11px] text-slate-300">
            Advertisers fund your AI compute! Watch an interactive 10-second sponsor video or visit our developer partners to cover API token costs without paying out-of-pocket.
          </p>

          <!-- Interactive Sponsor Ad Card -->
          <div id="sponsorAdContainer" class="p-3 bg-slate-950/80 rounded-lg border border-slate-800 flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
            <div class="flex items-center gap-3 min-w-0 flex-1">
              <div id="adSponsorIcon" class="w-12 h-12 rounded-lg bg-gradient-to-br from-indigo-500 to-pink-500 flex items-center justify-center text-white text-xl shrink-0 shadow-md">
                ⚡
              </div>
              <div class="flex-1 min-w-0">
                <div class="flex items-center gap-2">
                  <span id="adSponsorName" class="font-bold text-white text-xs truncate">Vercel AI SDK &amp; MicroVMs</span>
                  <span id="adSponsorBadge" class="text-[9px] px-1 rounded bg-slate-800 text-slate-400 border border-slate-700 uppercase">Sponsored</span>
                </div>
                <div id="adSponsorTagline" class="text-[11px] text-slate-400 truncate">Deploy durable agent sandboxes and AI gateways with zero server management.</div>
              </div>
            </div>
            <div class="flex items-center gap-2 shrink-0 w-full md:w-auto justify-end">
              <a id="adSponsorCtaBtn" href="https://sdk.vercel.ai?utm_source=tincan-mesh" target="_blank" rel="noopener noreferrer" onclick="trackSponsorClick()" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 text-xs font-mono rounded border border-slate-700 transition">
                Visit Partner ↗
              </a>
              <button id="watchAdBtn" onclick="watchSponsoredAd()" class="px-3 py-1.5 bg-gradient-to-r from-amber-500 to-amber-600 hover:brightness-110 text-slate-950 font-bold font-mono text-xs rounded-lg transition active:scale-95 shadow-md">
                ▶ Watch Video (10s)
              </button>
            </div>
          </div>

          <!-- Video Player Container (Active when watching) -->
          <div id="adVideoContainer" class="hidden space-y-2 p-2.5 bg-slate-950 rounded-lg border border-amber-500/40">
            <div class="relative bg-black rounded overflow-hidden aspect-video flex items-center justify-center">
              <video id="adVideoPlayer" playsinline preload="auto" class="w-full h-full object-contain"></video>
              <div id="adVideoOverlay" class="absolute top-2 left-2 px-2 py-0.5 bg-black/80 rounded border border-slate-700 text-[10px] font-mono text-amber-300">
                Sponsor Clip: <span id="adVideoTitle">Partner Ad</span>
              </div>
            </div>
            <div id="adProgressWrap" class="space-y-1">
              <div class="flex justify-between text-[10px] font-mono text-amber-300">
                <span id="adProgressText">Streaming verified sponsor video...</span>
                <span id="adTimerText">10s remaining</span>
              </div>
              <div class="w-full bg-slate-800 h-1.5 rounded-full overflow-hidden">
                <div id="adProgressBar" class="bg-amber-400 h-full w-0 transition-all duration-300 ease-linear"></div>
              </div>
            </div>
          </div>

          <!-- Advertising Network & Community Partner Info -->
          <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono px-1">
            <span>Direct Partner Ads • EthicalAds • Google AdSense • Community Ads</span>
            <div class="flex items-center gap-2">
              <button type="button" onclick="openSponsorInfoModal()" class="text-amber-400 hover:underline">How to Advertise ℹ</button>
              <button type="button" id="billingAdminSponsorBtn" onclick="openAdminSponsorStudio()" class="hidden px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-600 hover:bg-amber-900 transition">🛡️ Admin Studio</button>
            </div>
          </div>
        </div>

        <!-- Section 2: Direct Token Top-Up Packages -->
        <div class="space-y-2">
          <div class="flex items-center justify-between">
            <span class="font-bold text-white font-mono">💳 Or Buy Token Credits Directly</span>
            <span class="text-[10px] text-slate-400 font-mono">Instant mesh deposit</span>
          </div>
          <div class="grid grid-cols-3 gap-2.5">
            <div class="p-3 bg-slate-900/90 rounded-xl border border-slate-800 hover:border-emerald-500/60 transition flex flex-col justify-between">
              <div>
                <div class="text-xs font-bold text-white">Starter Pack</div>
                <div class="text-lg font-bold font-mono text-emerald-400 mt-1">$1.00</div>
                <div class="text-[11px] text-slate-400 mt-0.5">50,000 Tokens</div>
              </div>
              <button onclick="buyTokens(1.00, 50000)" class="mt-3 w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-semibold rounded-lg transition active:scale-95">
                Pay $1
              </button>
            </div>
            <div class="p-3 bg-slate-900/90 rounded-xl border border-emerald-500/80 shadow-md hover:border-emerald-400 transition flex flex-col justify-between relative overflow-hidden">
              <div class="absolute top-0 right-0 bg-emerald-500 text-slate-950 font-bold text-[9px] px-1.5 py-0.2 rounded-bl uppercase">Popular</div>
              <div>
                <div class="text-xs font-bold text-white">Developer Pack</div>
                <div class="text-lg font-bold font-mono text-emerald-400 mt-1">$5.00</div>
                <div class="text-[11px] text-slate-400 mt-0.5">275,000 Tokens <span class="text-emerald-400 font-semibold">(+10%)</span></div>
              </div>
              <button onclick="buyTokens(5.00, 275000)" class="mt-3 w-full py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white font-mono text-xs font-semibold rounded-lg transition active:scale-95">
                Pay $5
              </button>
            </div>
            <div class="p-3 bg-slate-900/90 rounded-xl border border-slate-800 hover:border-cyan-500/60 transition flex flex-col justify-between">
              <div>
                <div class="text-xs font-bold text-white">Fleet Pro Pack</div>
                <div class="text-lg font-bold font-mono text-cyan-400 mt-1">$20.00</div>
                <div class="text-[11px] text-slate-400 mt-0.5">1,200,000 Tokens <span class="text-cyan-400 font-semibold">(+20%)</span></div>
              </div>
              <button onclick="buyTokens(20.00, 1200000)" class="mt-3 w-full py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white font-mono text-xs font-semibold rounded-lg transition active:scale-95">
                Pay $20
              </button>
            </div>
          </div>
        </div>

        <!-- Section 3: Recent Invoices & Consumption -->
        <div class="space-y-1.5">
          <div class="flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Recent Token Invoices &amp; Deductions</span>
            <span id="billingTotalUsedText" class="text-slate-300">Total used: 0 tokens</span>
          </div>
          <div class="bg-slate-950 rounded-lg border border-slate-800 p-2 max-h-36 overflow-y-auto font-mono text-[10px]">
            <table class="w-full text-left">
              <thead>
                <tr class="text-slate-500 border-b border-slate-800 pb-1">
                  <th>Model</th>
                  <th>Tokens</th>
                  <th>Cost (USD)</th>
                  <th class="text-right">Time</th>
                </tr>
              </thead>
              <tbody id="billingLedgerRows" class="divide-y divide-slate-800/40 text-slate-300">
                <tr><td colspan="4" class="py-2 text-center text-slate-500">No token deductions recorded yet.</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 8: Cyberspace Discussion Board · GraphRAG + BM25 + @verifier-agent -->
    <!-- ===================================================================== -->
    <div id="win-board" class="mesh-window w-[940px] max-w-full" data-window-id="win-board" style="top: 84px; left: 130px; z-index: 27;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-gradient-to-r from-indigo-950/95 via-slate-900/95 to-cyan-950/95 border-b border-indigo-500/50">
        <div class="flex items-center gap-2">
          <span class="text-base">🌐</span>
          <span class="text-xs font-bold text-indigo-300 font-mono tracking-wide">Cyberspace Discussion Board &amp; Knowledge Base.app</span>
          <span class="px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 text-[10px] font-mono border border-indigo-500/40 font-semibold">PPR GraphRAG + Okapi BM25 + @verifier-agent</span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-board')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Pop out into separate monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-board')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-board')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">⤢</button>
          <button onclick="toggleWindow('win-board')" class="px-1.5 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 text-[11px]">✕</button>
        </div>
      </div>

      <div id="board" class="window-body p-4 space-y-3.5 max-h-[780px] overflow-y-auto text-xs font-sans">
        <!-- Identity Verification Agent (@verifier-agent) Status & Form Dispatch Banner -->
        <div id="boardVerifierBanner" class="p-3 bg-gradient-to-r from-emerald-950/60 via-slate-900/90 to-indigo-950/60 rounded-xl border border-emerald-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
          <div class="flex items-center gap-2.5">
            <span class="text-xl">🛡️</span>
            <div>
              <div class="font-mono font-bold text-emerald-300 text-xs flex flex-wrap items-center gap-2">
                <span>Identity Agent: <span class="text-cyan-300">@verifier-agent</span></span>
                <span id="boardVerifiedBadge" class="px-2 py-0.5 rounded-full bg-emerald-900/80 text-emerald-300 border border-emerald-600 text-[10px]">Checking...</span>
                <span id="boardAttestationBadge" class="hidden px-2 py-0.5 rounded bg-slate-950 text-cyan-300 border border-cyan-800 text-[10px] font-mono"></span>
              </div>
              <p id="boardVerifierSubtext" class="text-[11px] text-slate-300 mt-0.5">
                Verify your identity to tag @usernames, summon @ai-agents, vote on threads, and build the Cyberspace Knowledge Graph.
              </p>
            </div>
          </div>
          <div class="flex items-center gap-1.5 shrink-0">
            <button type="button" onclick="requestAgentVerificationForm()" class="px-2.5 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-mono font-bold text-[11px] transition active:scale-95 shadow">
              📨 Have @verifier-agent Send Form
            </button>
            <button type="button" onclick="switchBoardTab('verify')" class="px-2.5 py-1.5 rounded-lg bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-600 font-mono font-bold text-[11px] transition">
              🛡️ Open Verification Form
            </button>
          </div>
        </div>

        <!-- Navigation Tabs + Graph Telemetry Pill -->
        <div class="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800 pb-2 font-mono">
          <div class="flex flex-wrap items-center gap-1.5">
            <button id="boardTabBtn-discussions" type="button" onclick="switchBoardTab('discussions')" class="px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-xs transition">
              💬 Discussions &amp; Threads
            </button>
            <button id="boardTabBtn-search" type="button" onclick="switchBoardTab('search')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
              🔍 GraphRAG + BM25 IR Lab
            </button>
            <button id="boardTabBtn-graph" type="button" onclick="switchBoardTab('graph')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition">
              🕸️ Knowledge Graph Explorer
            </button>
            <button id="boardTabBtn-verify" type="button" onclick="switchBoardTab('verify')" class="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition flex items-center gap-1">
              <span>🛡️ @verifier-agent Center</span>
              <span id="boardPendingVerifyCount" class="px-1.5 py-0.2 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px]">0</span>
            </button>
          </div>
          <div class="flex items-center gap-2">
            <span id="boardGraphStatsBadge" class="text-[10px] font-mono text-cyan-300 bg-slate-950 px-2.5 py-1 rounded border border-slate-800">Graph: loading...</span>
            <button type="button" onclick="loadCyberspaceBoard()" class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-[10px]" title="Refresh Board & S3 Sync">🔄 Sync</button>
          </div>
        </div>

        <!-- Citizen Profile & Attestation Inspector Drawer (Hidden until a @username is clicked) -->
        <div id="boardProfileDrawer" class="hidden p-3 bg-slate-950/95 rounded-xl border border-cyan-500/50 space-y-2 font-mono text-xs shadow-xl">
          <div class="flex items-center justify-between border-b border-slate-800 pb-1.5">
            <div class="flex items-center gap-2">
              <span class="text-base">🪪</span>
              <span id="boardProfileName" class="font-bold text-white text-sm">@username</span>
              <span id="boardProfileVerifiedPill" class="px-2 py-0.5 rounded-full text-[10px]"></span>
            </div>
            <button type="button" onclick="document.getElementById('boardProfileDrawer').classList.add('hidden')" class="text-slate-400 hover:text-white px-1.5">✕</button>
          </div>
          <div id="boardProfileMeta" class="text-[11px] text-slate-300 grid grid-cols-1 sm:grid-cols-3 gap-2"></div>
          <div id="boardProfileTopics" class="text-[10px] text-slate-400 space-y-1 pt-1 border-t border-slate-900"></div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 1: DISCUSSIONS & THREADS -->
        <!-- =============================================================== -->
        <div id="boardTab-discussions" class="space-y-3.5">
          <!-- Quick Hybrid Search + Category Filter + Sort Bar -->
          <div class="p-3 bg-slate-900/90 rounded-xl border border-indigo-500/40 space-y-2.5">
            <div class="flex flex-col sm:flex-row gap-2">
              <input id="boardSearchInput" type="text" placeholder="Search discussions, @username, @gemini-brain, @verifier-agent, #graphrag, #bm25..." onkeydown="if(event.key==='Enter') searchCyberspaceBoard()" class="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:border-indigo-400 focus:outline-none" />
              <select id="boardSearchMode" onchange="if(document.getElementById('boardSearchInput').value.trim()) searchCyberspaceBoard()" class="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-cyan-300 font-mono text-xs">
                <option value="hybrid">⚡ Hybrid (GraphRAG + BM25)</option>
                <option value="graphrag">🕸️ GraphRAG (PPR + 2-Hop)</option>
                <option value="bm25">📚 Okapi BM25 (Lexical IR)</option>
              </select>
              <button type="button" onclick="searchCyberspaceBoard()" class="px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-indigo-600 to-cyan-600 hover:brightness-110 text-white font-mono font-bold text-xs transition active:scale-95">
                Search
              </button>
              <button type="button" onclick="resetCyberspaceSearch()" class="px-2.5 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-xs border border-slate-700">
                Reset
              </button>
            </div>

            <!-- Category Pills + Sort Selector -->
            <div class="flex flex-wrap items-center justify-between gap-2 pt-1 font-mono text-[10px]">
              <div id="boardCategoryBar" class="flex flex-wrap items-center gap-1">
                <button type="button" onclick="setBoardCategoryFilter('')" data-cat="" class="board-cat-btn px-2 py-0.5 rounded bg-indigo-600 text-white font-bold">All Topics</button>
                <button type="button" onclick="setBoardCategoryFilter('cyberspace')" data-cat="cyberspace" class="board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">#cyberspace</button>
                <button type="button" onclick="setBoardCategoryFilter('ai')" data-cat="ai" class="board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">#ai-agents</button>
                <button type="button" onclick="setBoardCategoryFilter('architecture')" data-cat="architecture" class="board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">#architecture</button>
                <button type="button" onclick="setBoardCategoryFilter('security')" data-cat="security" class="board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">#security</button>
                <button type="button" onclick="setBoardCategoryFilter('qa')" data-cat="qa" class="board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300">#q&amp;a</button>
              </div>
              <div class="flex items-center gap-1.5">
                <label class="flex items-center gap-1 text-emerald-300 cursor-pointer">
                  <input id="boardVerifiedOnlyToggle" type="checkbox" onchange="loadCyberspaceBoard()" class="rounded border-slate-700 bg-slate-950" />
                  <span>✅ Verified Only</span>
                </label>
                <select id="boardSortSelect" onchange="loadCyberspaceBoard()" class="px-2 py-0.5 rounded bg-slate-950 border border-slate-700 text-slate-200 text-[10px]">
                  <option value="hot">🔥 Hot / Pinned</option>
                  <option value="new">🆕 Newest</option>
                  <option value="top">⬆️ Top Voted</option>
                  <option value="discussed">💬 Most Discussed</option>
                </select>
              </div>
            </div>

            <!-- Inline GraphRAG + BM25 Search Synthesis Box -->
            <div id="boardSynthesisBox" class="hidden p-2.5 bg-indigo-950/60 border border-indigo-500/50 rounded-lg space-y-2 font-mono text-[11px]">
              <div class="flex items-center justify-between">
                <span class="text-[10px] uppercase tracking-wider text-cyan-300 font-bold">🧠 Hybrid GraphRAG + Okapi BM25 Synthesis</span>
                <button type="button" onclick="switchBoardTab('search')" class="text-[10px] text-indigo-300 underline hover:text-white">Open Full IR Diagnostics ↗</button>
              </div>
              <div id="boardSynthesisText" class="text-indigo-100 leading-relaxed"></div>
              <div id="boardSubgraphEntities" class="flex flex-wrap gap-1.5 pt-1"></div>
            </div>
          </div>

          <!-- Create New Cyberspace Topic + Dynamic @User / @Agent Roster Bar -->
          <details id="boardComposerDetails" class="bg-slate-900/80 rounded-xl border border-slate-800 p-3" open>
            <summary class="cursor-pointer font-mono font-bold text-cyan-300 text-xs flex items-center justify-between select-none">
              <span>➕ Start a New Cyberspace Topic (Tag @yourself, @usernames, @ai-agents &amp; #tags)</span>
              <span class="text-[10px] text-slate-400">Click to expand/collapse</span>
            </summary>
            <div class="mt-3 space-y-2.5 font-mono">
              <div class="grid grid-cols-1 sm:grid-cols-4 gap-2">
                <input id="boardTopicTitle" type="text" placeholder="Topic Title (e.g. Hybrid GraphRAG + BM25 Indexing with @gemini-brain)" class="sm:col-span-2 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:border-cyan-400 focus:outline-none" />
                <select id="boardTopicCategory" class="px-2.5 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-emerald-300 text-xs focus:border-cyan-400 focus:outline-none">
                  <option value="cyberspace">#cyberspace (General)</option>
                  <option value="ai">#ai (AI Agents &amp; Models)</option>
                  <option value="architecture">#architecture (Mesh &amp; GraphRAG)</option>
                  <option value="security">#security (Zero-Trust &amp; Verification)</option>
                  <option value="qa">#qa (Q&amp;A / Troubleshooting)</option>
                </select>
                <input id="boardTopicTags" type="text" placeholder="Extra tags: graphrag, bm25" class="px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-pink-300 text-xs focus:border-cyan-400 focus:outline-none" />
              </div>

              <!-- Dynamic Quick-Tagging Chips (@Me, Registered @Users, @AI-Agents, #Tags) -->
              <div class="space-y-1.5 p-2 bg-slate-950/80 rounded-lg border border-slate-800/80 text-[10px]">
                <div class="flex flex-wrap items-center gap-1">
                  <span class="text-slate-400 mr-1">Peers:</span>
                  <button type="button" onclick="insertBoardSelfTag('boardTopicBody')" class="px-2 py-0.5 rounded bg-emerald-950 hover:bg-emerald-900 text-emerald-300 border border-emerald-700 font-bold">🙋 @Me (Tag Yourself)</button>
                  <div id="boardDynamicUserChips" class="flex flex-wrap items-center gap-1"></div>
                </div>
                <div class="flex flex-wrap items-center gap-1">
                  <span class="text-slate-400 mr-1">AI Agents:</span>
                  <div id="boardDynamicAgentChips" class="flex flex-wrap items-center gap-1">
                    <button type="button" onclick="insertBoardTag('@gemini-brain', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700">🤖 @gemini-brain</button>
                    <button type="button" onclick="insertBoardTag('@claude-brain', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700">🤖 @claude-brain</button>
                    <button type="button" onclick="insertBoardTag('@openai-brain', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700">🤖 @openai-brain</button>
                    <button type="button" onclick="insertBoardTag('@grok-brain', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700">🤖 @grok-brain</button>
                    <button type="button" onclick="insertBoardTag('@deepseek-r1', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700">🤖 @deepseek-r1</button>
                    <button type="button" onclick="insertBoardTag('@verifier-agent', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-amber-950 hover:bg-amber-900 text-amber-300 border border-amber-700">🛡️ @verifier-agent</button>
                    <button type="button" onclick="insertBoardTag('@tincan-agent', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-teal-950 hover:bg-teal-900 text-teal-300 border border-teal-700">🥫 @tincan-agent</button>
                  </div>
                </div>
                <div class="flex flex-wrap items-center gap-1">
                  <span class="text-slate-400 mr-1">Topics:</span>
                  <button type="button" onclick="insertBoardTag('#graphrag', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-pink-300 border border-slate-700">#graphrag</button>
                  <button type="button" onclick="insertBoardTag('#bm25', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-pink-300 border border-slate-700">#bm25</button>
                  <button type="button" onclick="insertBoardTag('#cyberspace', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-pink-300 border border-slate-700">#cyberspace</button>
                  <button type="button" onclick="insertBoardTag('#verification', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-pink-300 border border-slate-700">#verification</button>
                  <button type="button" onclick="insertBoardTag('#webrtc', 'boardTopicBody')" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-pink-300 border border-slate-700">#webrtc</button>
                </div>
              </div>

              <textarea id="boardTopicBody" rows="3" placeholder="Write your discussion post... Tag yourself (@username), peers (@harper), AI agents (@gemini-brain @verifier-agent), and #topics!" class="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:border-cyan-400 focus:outline-none"></textarea>

              <div class="flex flex-wrap items-center justify-between gap-2">
                <span class="text-[10px] text-slate-400">Tagged @ai-agents automatically synthesize a grounded reply using GraphRAG + BM25 context!</span>
                <button type="button" onclick="createCyberspaceTopic()" class="px-4 py-1.5 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 hover:brightness-110 text-white font-bold text-xs transition active:scale-95 shadow">
                  🚀 Post Topic to Cyberspace
                </button>
              </div>
            </div>
          </details>

          <!-- Topics Feed & Active Thread View -->
          <div id="boardTopicsFeed" class="space-y-3"></div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 2: GRAPHRAG + OKAPI BM25 INFORMATION RETRIEVAL LAB -->
        <!-- =============================================================== -->
        <div id="boardTab-search" class="hidden space-y-3.5 font-mono">
          <div class="p-3.5 bg-slate-900/90 rounded-xl border border-indigo-500/50 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-indigo-300 uppercase tracking-wider">🔬 Hybrid GraphRAG (Personalized PageRank) + Okapi BM25 IR Workbench</h3>
                <p class="text-[11px] text-slate-400 font-sans">Inspect lexical BM25 term IDF weights ($k_1=1.5, b=0.75$), Personalized PageRank ($\alpha=0.85$) scores, and multi-hop GraphRAG relational paths.</p>
              </div>
              <span class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 text-[10px]">Reciprocal Rank Fusion</span>
            </div>

            <div class="flex flex-col sm:flex-row gap-2">
              <input id="boardLabSearchInput" type="text" value="graphrag bm25 @gemini-brain @verifier-agent" placeholder="Enter query terms, @username, @agent, or #tag..." onkeydown="if(event.key==='Enter') runIrLabSearch()" class="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:border-indigo-400 focus:outline-none" />
              <select id="boardLabSearchMode" onchange="runIrLabSearch()" class="px-2.5 py-2 rounded-lg bg-slate-950 border border-slate-700 text-cyan-300 text-xs">
                <option value="hybrid">⚡ Hybrid (0.52 BM25 + 0.48 GraphRAG)</option>
                <option value="bm25">📚 Okapi BM25 Only</option>
                <option value="graphrag">🕸️ GraphRAG PPR Only</option>
              </select>
              <button type="button" onclick="runIrLabSearch()" class="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs transition active:scale-95">
                Run IR Query
              </button>
            </div>

            <!-- BM25 Corpus & Term IDF Diagnostics -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div class="p-3 bg-slate-950/90 rounded-lg border border-emerald-800/60 space-y-2">
                <div class="flex items-center justify-between text-[11px]">
                  <span class="font-bold text-emerald-300">📚 Okapi BM25 Lexical Index Diagnostics</span>
                  <span id="bm25CorpusParams" class="text-[10px] text-slate-400">k1=1.5, b=0.75</span>
                </div>
                <table class="w-full text-left text-[10px]">
                  <thead class="text-slate-400 border-b border-slate-800">
                    <tr>
                      <th class="py-1">Query Token</th>
                      <th class="py-1">Doc Freq (df)</th>
                      <th class="py-1 text-right">BM25 IDF Weight</th>
                    </tr>
                  </thead>
                  <tbody id="bm25TermTableBody" class="divide-y divide-slate-900 text-slate-200">
                    <tr><td colspan="3" class="py-2 text-slate-500 text-center">Run a query above to inspect BM25 IDF weights.</td></tr>
                  </tbody>
                </table>
              </div>

              <div class="p-3 bg-slate-950/90 rounded-lg border border-cyan-800/60 space-y-2">
                <div class="flex items-center justify-between text-[11px]">
                  <span class="font-bold text-cyan-300">🕸️ GraphRAG Subgraph &amp; Seed Activation</span>
                  <span id="graphragSubgraphStats" class="text-[10px] text-slate-400">PPR α=0.85</span>
                </div>
                <div id="irLabSynthesisBox" class="text-[11px] text-indigo-200 leading-relaxed bg-indigo-950/40 p-2 rounded border border-indigo-900/50">
                  Run a query to synthesize knowledge across topics, @users, @agents, and #tags.
                </div>
                <div id="irLabSeedBadges" class="flex flex-wrap gap-1 pt-1"></div>
              </div>
            </div>

            <!-- Detailed Ranked Retrieval Table -->
            <div id="irLabResultsList" class="space-y-2 pt-1"></div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 3: INTERACTIVE KNOWLEDGE GRAPH EXPLORER & PATH FINDER -->
        <!-- =============================================================== -->
        <div id="boardTab-graph" class="hidden space-y-3.5 font-mono">
          <div class="p-3.5 bg-slate-900/90 rounded-xl border border-cyan-500/40 space-y-3">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-cyan-300 uppercase tracking-wider">🕸️ Cyberspace Multi-Relational Knowledge Graph</h3>
                <p class="text-[11px] text-slate-400 font-sans">Click any node on the canvas to inspect its neighborhood, or compute the shortest relational path between any two Cyberspace entities.</p>
              </div>
              <div class="flex items-center gap-2 text-[10px]">
                <span class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700">● Topic</span>
                <span class="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">● @User</span>
                <span class="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700">● @Agent</span>
                <span class="px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-700">● #Tag</span>
                <button type="button" onclick="loadAndDrawBoardGraph()" class="px-2.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-white border border-slate-700">⟳ Re-Layout</button>
              </div>
            </div>

            <!-- Shortest-Path Entity Finder -->
            <div class="p-2.5 bg-slate-950/90 rounded-lg border border-slate-800 flex flex-col sm:flex-row items-stretch sm:items-center gap-2 text-xs">
              <span class="text-slate-400 text-[11px] shrink-0">Shortest Path:</span>
              <input id="graphPathSource" type="text" value="@alejandro" placeholder="From (e.g. @alejandro, #bm25)" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-cyan-300 text-xs flex-1" />
              <span class="text-slate-500 text-center">⟶</span>
              <input id="graphPathTarget" type="text" value="@verifier-agent" placeholder="To (e.g. @verifier-agent, #graphrag)" class="px-2.5 py-1 rounded bg-slate-900 border border-slate-700 text-indigo-300 text-xs flex-1" />
              <button type="button" onclick="findCyberspaceEntityPath()" class="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs shrink-0">
                Find Relational Path
              </button>
            </div>
            <div id="graphPathOutput" class="hidden p-2.5 bg-cyan-950/50 border border-cyan-600/50 rounded-lg text-[11px] text-cyan-200"></div>

            <!-- Interactive HTML5 Canvas -->
            <div class="relative bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
              <canvas id="boardGraphCanvas" width="860" height="380" class="w-full h-[380px] cursor-grab active:cursor-grabbing"></canvas>
              <div id="boardGraphNodeInspector" class="absolute bottom-2 left-2 right-2 p-2 bg-slate-900/95 border border-slate-700 rounded-lg text-[10px] text-slate-300 flex items-center justify-between">
                <span>Click any node on the graph canvas to inspect its connections and filter topics.</span>
              </div>
            </div>
          </div>
        </div>

        <!-- =============================================================== -->
        <!-- TAB 4: @VERIFIER-AGENT IDENTITY VERIFICATION CENTER & FORM -->
        <!-- =============================================================== -->
        <div id="boardTab-verify" class="hidden space-y-4 font-mono">
          <!-- Step 1: @verifier-agent Dispatch Console -->
          <div class="p-3.5 bg-gradient-to-r from-amber-950/40 via-slate-900/95 to-indigo-950/40 rounded-xl border border-amber-500/50 space-y-2.5">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <div>
                <h3 class="text-xs font-bold text-amber-300 uppercase tracking-wider flex items-center gap-1.5">
                  <span>🛡️</span> <span>@verifier-agent Automated Form Dispatcher</span>
                </h3>
                <p class="text-[11px] text-slate-300 font-sans">
                  Have <code class="text-cyan-300">@verifier-agent</code> send a cryptographic verification form + challenge code (<code class="text-amber-300">CYBER-XXXXXX</code>) to yourself or any unverified peer in the mesh.
                </p>
              </div>
              <span class="px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 text-[10px] font-bold">Ed25519 + SHA-256 Attestation</span>
            </div>
            <div class="flex flex-col sm:flex-row gap-2">
              <input id="verifyDispatchTargetUser" type="text" placeholder="Target @username or peer_id (leave blank to send to yourself)" class="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs" />
              <input id="verifyDispatchReason" type="text" value="Cyberspace Discussion Board Identity Verification" placeholder="Reason for verification" class="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-slate-300 text-xs" />
              <button type="button" onclick="dispatchVerifierAgentFormFromCenter()" class="px-4 py-1.5 rounded-lg bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs transition active:scale-95 shrink-0">
                📨 Dispatch Form via @verifier-agent
              </button>
            </div>
            <div id="verifyDispatchFeedback" class="hidden p-2.5 rounded-lg bg-emerald-950/70 border border-emerald-500/60 text-emerald-200 text-[11px]"></div>
          </div>

          <!-- Step 2: Dedicated Cyberspace Identity Verification Form -->
          <div class="p-4 bg-slate-900/95 rounded-xl border border-emerald-500/50 space-y-3">
            <div class="flex items-center justify-between border-b border-slate-800 pb-2">
              <div>
                <h3 class="text-sm font-bold text-emerald-300 flex items-center gap-2">
                  <span>✍️</span> <span>Official Cyberspace Identity Verification Form</span>
                </h3>
                <p class="text-[11px] text-slate-400 font-sans">Fill out and submit this form to <code class="text-cyan-300">@verifier-agent</code> to receive your <code class="text-emerald-300">✅ Verified Cyberspace Citizen</code> badge and SHA-256 attestation hash.</p>
              </div>
              <span id="verifyFormRequestIdBadge" class="px-2 py-0.5 rounded bg-slate-950 text-cyan-300 border border-slate-700 text-[10px]">Ready</span>
            </div>

            <input type="hidden" id="verifyFormRequestId" value="" />

            <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">Full Legal / Real Name *</label>
                <input id="verifyFormFullName" type="text" placeholder="e.g. Alejandro Londono" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:border-emerald-400 focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">Cyberspace @username Handle *</label>
                <input id="verifyFormUsername" type="text" placeholder="e.g. alejandro" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-cyan-300 focus:border-emerald-400 focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">Verified Contact Email *</label>
                <input id="verifyFormEmail" type="email" placeholder="e.g. operator@fau.edu" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:border-emerald-400 focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">2FA Contact Phone Number *</label>
                <input id="verifyFormPhone" type="tel" placeholder="e.g. +15615550199" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white focus:border-emerald-400 focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">Role / Institution / Affiliation</label>
                <input id="verifyFormRole" type="text" value="Graduate Researcher / Mesh Engineer" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-emerald-300 focus:border-emerald-400 focus:outline-none" />
              </div>
              <div>
                <label class="block text-[10px] text-slate-400 mb-1">@verifier-agent Challenge Code</label>
                <input id="verifyFormChallengeCode" type="text" placeholder="e.g. CYBER-A1B2C3 (auto-filled on dispatch)" class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-amber-700/70 text-amber-300 focus:border-amber-400 focus:outline-none" />
              </div>
            </div>

            <div>
              <label class="block text-[10px] text-slate-400 mb-1">Cyberspace Bio &amp; Knowledge Domains (Indexed in GraphRAG)</label>
              <textarea id="verifyFormBio" rows="2" placeholder="e.g. Building federated GraphRAG + BM25 knowledge bases, WebRTC mesh systems, and autonomous agents." class="w-full px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white text-xs focus:border-emerald-400 focus:outline-none"></textarea>
            </div>

            <label class="flex items-start gap-2 text-[11px] text-slate-300 font-sans cursor-pointer">
              <input id="verifyFormConsent" type="checkbox" checked class="mt-0.5 rounded border-slate-700 bg-slate-950" />
              <span>I attest that this identity information is accurate and consent to cryptographic SHA-256 identity attestation by <code class="text-cyan-300">@verifier-agent</code> for the TinCan Cyberspace Knowledge Base.</span>
            </label>

            <div id="verifyFormStatusMsg" class="hidden p-2.5 rounded-lg text-xs"></div>

            <div class="flex items-center justify-end gap-2 pt-1">
              <button type="button" onclick="submitCyberspaceVerificationForm()" class="px-5 py-2 rounded-lg bg-gradient-to-r from-emerald-600 to-cyan-600 hover:brightness-110 text-white font-bold text-xs transition active:scale-95 shadow-lg">
                ✅ Submit Verification Form &amp; Claim Citizen Badge
              </button>
            </div>
          </div>

          <!-- Step 3: Live Pending Requests & Verified Citizens Ledger -->
          <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div class="p-3 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-amber-300">📨 Pending @verifier-agent Forms</span>
                <button type="button" onclick="loadVerificationCenterData()" class="text-[10px] text-slate-400 hover:text-white">🔄 Refresh</button>
              </div>
              <div id="verifyPendingList" class="space-y-1.5 text-[11px] max-h-48 overflow-y-auto"></div>
            </div>

            <div class="p-3 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-emerald-300">🏛️ Verified Cyberspace Citizens</span>
                <span id="verifyCitizensCount" class="text-[10px] text-slate-400">0 verified</span>
              </div>
              <div id="verifyCitizensList" class="space-y-1.5 text-[11px] max-h-48 overflow-y-auto"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ===================================================================== -->
    <!-- Window 9: Network Roster & Operator Leaderboard.app -->
    <!-- ===================================================================== -->
    <div id="win-network" class="mesh-window w-[560px] max-w-full" data-window-id="win-network" style="top: 72px; right: 24px; z-index: 28;">
      <div class="window-header flex items-center justify-between px-3 py-2 bg-gradient-to-r from-emerald-950/95 via-slate-900/95 to-slate-900/95 border-b border-emerald-500/50">
        <div class="flex items-center gap-2">
          <span class="text-base">👥</span>
          <span class="text-xs font-bold text-emerald-300 font-mono tracking-wide">Network Presence &amp; Standalone Leaderboard.app</span>
          <span id="netWinActiveBadge" class="px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-600 text-[10px] font-bold">🟢 <span id="netWinActiveNum">2</span> active</span>
        </div>
        <div class="window-controls flex items-center gap-1.5 font-mono text-xs">
          <button onclick="openPopoutWindow('win-network')" class="px-1.5 py-0.5 rounded bg-emerald-900/90 hover:bg-emerald-800 text-emerald-200 border border-emerald-600 text-[10px] font-bold transition active:scale-95" title="Pop out into separate window or secondary monitor">↗ Pop Out</button>
          <button onclick="minimizeWindow('win-network')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">—</button>
          <button onclick="maximizeWindow('win-network')" class="px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px]">□</button>
          <button onclick="toggleWindow('win-network')" class="px-1.5 py-0.5 rounded bg-red-950/80 hover:bg-red-900 text-red-300 text-[11px]">✕</button>
        </div>
      </div>
      <div class="window-body p-4 space-y-4 max-h-[680px] overflow-y-auto">
        <!-- Top Metrics Cards -->
        <div class="grid grid-cols-3 gap-2 text-center font-mono">
          <div class="p-2.5 bg-slate-950/90 border border-slate-800 rounded-lg">
            <div class="text-xs font-bold text-emerald-400 flex items-center justify-center gap-1">
              <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              <span id="netMetricPeers">2</span>
            </div>
            <div class="text-[10px] text-slate-400">Mesh Peers</div>
          </div>
          <div class="p-2.5 bg-slate-950/90 border border-slate-800 rounded-lg">
            <div class="text-xs font-bold text-cyan-400" id="netMetricVisitors">14</div>
            <div class="text-[10px] text-slate-400">Web Cursors</div>
          </div>
          <div class="p-2.5 bg-slate-950/90 border border-slate-800 rounded-lg">
            <div class="text-xs font-bold text-amber-400" id="netMetricTopXp">850 XP</div>
            <div class="text-[10px] text-slate-400">Top Rank</div>
          </div>
        </div>

        <!-- Sub Tabs -->
        <div class="flex items-center bg-slate-950 border border-slate-800 rounded-lg p-1 text-xs font-mono">
          <button onclick="switchNetTab('peers')" id="btnNetTab-peers" class="flex-1 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold text-center transition">
            🟢 Active Peers (<span id="netTabPeersCount">2</span>)
          </button>
          <button onclick="switchNetTab('visitors')" id="btnNetTab-visitors" class="flex-1 py-1 rounded text-slate-400 hover:text-white text-center transition">
            🌐 Web Visitors (<span id="netTabVisitorsCount">1</span>)
          </button>
          <button onclick="switchNetTab('leaderboard')" id="btnNetTab-leaderboard" class="flex-1 py-1 rounded text-slate-400 hover:text-white text-center transition">
            🏆 Leaderboard
          </button>
        </div>

        <!-- Tab 1: Active Peers List -->
        <div id="netPanel-peers" class="space-y-2">
          <div id="netPeersList" class="space-y-2 font-mono">
            <!-- Dynamically populated via syncState -->
          </div>
        </div>

        <!-- Tab 2: Web Visitors List -->
        <div id="netPanel-visitors" class="space-y-2 hidden">
          <div class="text-[11px] text-slate-400 font-mono flex items-center justify-between">
            <span>Real-time Multiplayer WebKit Cursors &amp; Visitors</span>
            <span class="text-emerald-400 font-bold">● Live Sync</span>
          </div>
          <div id="netVisitorsList" class="space-y-1.5 font-mono text-xs max-h-72 overflow-y-auto">
            <!-- Dynamically populated via syncState -->
          </div>
        </div>

        <!-- Tab 3: Operator Leaderboard -->
        <div id="netPanel-leaderboard" class="space-y-2 hidden">
          <div class="flex items-center justify-between">
            <span class="text-xs font-bold uppercase tracking-wider text-slate-300 font-mono flex items-center gap-1.5">
              <span>🏆</span> Live Operator Leaderboard
            </span>
            <span class="text-[10px] font-mono text-slate-400">Ranked by Lifetime XP</span>
          </div>
          <div class="bg-slate-950/80 border border-slate-800 rounded-lg overflow-hidden">
            <table class="w-full text-left text-xs font-mono">
              <thead class="bg-slate-900 text-slate-400 border-b border-slate-800">
                <tr>
                  <th class="px-3 py-2">Rank</th>
                  <th class="px-3 py-2">Operator Peer</th>
                  <th class="px-3 py-2">Readiness Tier</th>
                  <th class="px-3 py-2">Badges</th>
                  <th class="px-3 py-2 text-right">Squad XP</th>
                </tr>
              </thead>
              <tbody id="operatorLeaderboardStandalone" class="divide-y divide-slate-800/60">
                <!-- Dynamically updated -->
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

  </main>

  <!-- Bottom OS Dock -->
  <footer id="meshOsDock" class="fixed bottom-3 left-1/2 -translate-x-1/2 z-50 bg-slate-900/90 border border-slate-700/80 rounded-2xl px-3 py-2 flex items-center gap-1.5 sm:gap-2.5 backdrop-blur-md shadow-2xl select-none font-sans">
    <button id="dockBtn-win-terminal" onclick="toggleWindow('win-terminal')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Terminal & Quickstart">
      <span>⚡</span> <span class="hidden md:inline">Terminal</span>
    </button>
    <button id="dockBtn-win-board" onclick="toggleWindow('win-board')" class="px-2.5 py-1.5 bg-indigo-950/90 hover:bg-indigo-900 border border-indigo-500/80 text-indigo-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-bold" title="Cyberspace Discussion Board · GraphRAG + BM25">
      <span>🌐</span> <span class="hidden md:inline">Cyberspace</span>
    </button>
    <button id="dockBtn-win-tv" onclick="toggleWindow('win-tv')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Relay Watch Party TV">
      <span>📺</span> <span class="hidden md:inline">Watch Party TV</span>
    </button>
    <button id="dockBtn-win-arena" onclick="toggleWindow('win-arena')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="AI Brain Router & Arena">
      <span>🧠</span> <span class="hidden md:inline">AI Arena</span>
    </button>
    <button id="dockBtn-win-network" onclick="toggleWindow('win-network')" class="px-2.5 py-1.5 bg-emerald-950/90 hover:bg-emerald-900 border border-emerald-500/80 text-emerald-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-bold" title="Active Network Roster, Live Visitors & Standalone Leaderboard">
      <span>👥</span> <span class="hidden md:inline">2 Active &amp; Ranks</span>
    </button>
    <button id="dockBtn-chat" onclick="focusChatWindow()" class="px-2.5 py-1.5 bg-cyan-950 hover:bg-cyan-900 border border-cyan-800 text-cyan-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Live Mesh Chat &amp; Comms">
      <span>💬</span> <span class="font-bold">Live Chat</span>
    </button>
    <button id="dockBtn-win-comms" onclick="toggleWindow('win-comms')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="WebRTC Video &amp; Voice Comms">
      <span>📹</span> <span class="hidden md:inline">Video/Voice</span>
    </button>
    <button id="dockBtn-win-quests" onclick="toggleWindow('win-quests')" class="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Quests, Arena & Leaderboard">
      <span>🎯</span> <span class="hidden md:inline">Quests &amp; Leaderboard</span>
    </button>
    <button id="dockBtn-win-billing" onclick="toggleWindow('win-billing')" class="px-2.5 py-1.5 bg-emerald-950/80 hover:bg-emerald-900 border border-emerald-600/80 text-emerald-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95 font-semibold" title="Token Billing, Store &amp; Sponsor Ads">
      <span>💳</span> <span class="hidden md:inline">Tokens &amp; Ads</span>
    </button>
    <button id="dockModBtn" onclick="toggleWindow('win-moderator')" class="hidden px-2.5 py-1.5 bg-amber-950/80 hover:bg-amber-900 border border-amber-600 text-amber-300 rounded-xl text-xs font-mono transition flex items-center gap-1 active:scale-95" title="Admin Moderator Control Panel">
      <span>🛡️</span> <span class="hidden md:inline font-bold">Mod Panel</span>
    </button>
    <div class="h-5 w-px bg-slate-700 mx-1"></div>
    <button onclick="fireTestPacket()" class="px-3 py-1.5 bg-gradient-to-r from-emerald-600 to-cyan-600 hover:brightness-110 text-white rounded-xl text-xs font-mono font-semibold transition active:scale-95 flex items-center gap-1 shadow-md" title="Launch animated test packet across mesh topology">
      <span>🥫</span> <span>Fire Test Packet</span>
    </button>
  </footer>

  <!-- ===================================================================== -->
  <!-- Master JavaScript Engine for TinCan Mesh OS -->
  <!-- ===================================================================== -->
  <script>
    // URL Params & Core Identity
    const urlParams = new URLSearchParams(window.location.search);
    const savedPeerId = localStorage.getItem('tincan_peer_id');
    const myPeerId = urlParams.get('peer') || savedPeerId || ('peer-' + Math.random().toString(36).substring(2, 8));
    localStorage.setItem('tincan_peer_id', myPeerId);
    const currentRoom = urlParams.get('room') || 'main';
    let singleWindowParam = urlParams.get('window');

    // Route alias normalization: support /tv, /call, or window=tv, window=call, etc.
    if (!singleWindowParam) {
      if (window.location.pathname === '/tv') singleWindowParam = 'win-tv';
      else if (window.location.pathname === '/call') singleWindowParam = 'win-comms';
      else if (window.location.pathname === '/arena') singleWindowParam = 'win-arena';
      else if (window.location.pathname === '/terminal') singleWindowParam = 'win-terminal';
      else if (window.location.pathname === '/billing' || window.location.pathname === '/tokens') singleWindowParam = 'win-billing';
      else if (window.location.pathname === '/board' || window.location.pathname === '/cyberspace') singleWindowParam = 'win-board';
    }
    if (singleWindowParam && !singleWindowParam.startsWith('win-')) {
      singleWindowParam = 'win-' + singleWindowParam;
    }

    if (document.getElementById('roomInput')) document.getElementById('roomInput').value = currentRoom;
    if (document.getElementById('localPeerLabel')) document.getElementById('localPeerLabel').innerText = myPeerId;

    // Admin Moderator State & Controls
    let isAdmin = (urlParams.get('role') === 'admin' || urlParams.get('admin') === 'true' || localStorage.getItem('tincan_admin') === 'true');

    function updateAdminUI() {
      const badge = document.getElementById('osAdminBadge');
      const modBtn = document.getElementById('osModPanelBtn');
      const dockBtn = document.getElementById('dockModBtn');
      const toggleText = document.getElementById('osAdminToggleText');
      const toggleBtn = document.getElementById('osAdminToggleBtn');
      if (isAdmin) {
        if (badge) badge.classList.remove('hidden');
        if (modBtn) modBtn.classList.remove('hidden');
        if (dockBtn && !(typeof poppedOutWindows !== 'undefined' && poppedOutWindows.has('win-moderator'))) {
          dockBtn.classList.remove('hidden');
          dockBtn.style.display = '';
        }
        if (toggleText) toggleText.innerText = 'Admin: ACTIVE 🛡️';
        if (toggleBtn) {
          toggleBtn.className = 'text-xs font-mono px-2.5 py-1 rounded border border-amber-500 bg-amber-950 text-amber-300 transition flex items-center gap-1.5 shadow-sm font-bold';
        }
      } else {
        if (badge) badge.classList.add('hidden');
        if (modBtn) modBtn.classList.add('hidden');
        if (dockBtn) dockBtn.classList.add('hidden');
        if (toggleText) toggleText.innerText = 'Admin Mode';
        if (toggleBtn) {
          toggleBtn.className = 'text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-300 hover:text-amber-400 hover:border-amber-600 transition flex items-center gap-1.5 shadow-sm font-semibold';
        }
      }
    }

    function toggleAdminMode() {
      isAdmin = !isAdmin;
      localStorage.setItem('tincan_admin', isAdmin ? 'true' : 'false');
      updateAdminUI();
      if (isAdmin) {
        toggleWindow('win-moderator');
        playXpChime();
      }
    }

    async function kickPeerNode(peerId, room = 'main') {
      if (!confirm(`Are you sure you want to disconnect / kick '${peerId}' from room '${room}'?`)) return;
      try {
        const res = await fetch('/api/webrtc/leave', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ peer_id: peerId, room })
        });
        if (res.ok) {
          playXpChime();
          await pollMeshState();
        }
      } catch (err) {
        alert('Kick request failed: ' + err);
      }
    }

    async function sendAdminBroadcast() {
      const input = document.getElementById('adminAnnouncementInput');
      const text = input ? input.value.trim() : '';
      if (!text) return;
      input.value = '';
      const room = document.getElementById('roomInput').value.trim() || 'main';
      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: '*',
            type: 'admin_broadcast',
            room,
            payload: {
              text,
              sender: myPeerId,
              role: 'admin',
              timestamp: Date.now()
            }
          })
        });
        showAdminBanner(text, myPeerId);
        playXpChime();
      } catch (err) {
        alert('Broadcast failed: ' + err);
      }
    }

    function showAdminBanner(text, sender) {
      const banner = document.getElementById('adminBroadcastBanner');
      const textEl = document.getElementById('adminBroadcastText');
      if (banner && textEl) {
        textEl.innerText = `${text} (by ${sender || 'Admin'})`;
        banner.classList.remove('hidden');
      }
    }

    function dismissAdminBanner() {
      const banner = document.getElementById('adminBroadcastBanner');
      if (banner) banner.classList.add('hidden');
    }

    // Cross-Window BroadcastChannel ('tincan-mesh-bus')
    const meshBus = new BroadcastChannel('tincan-mesh-bus');

    // WebAudio SFX Engine (Pentatonic Major Chords)
    let audioCtx = null;
    let sfxEnabled = true;

    function initAudio() {
      if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
      }
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    }

    function playXpChime() {
      if (!sfxEnabled) return;
      initAudio();
      if (!audioCtx) return;
      const now = audioCtx.currentTime;
      const notes = [523.25, 659.25, 783.99, 1046.50]; // C5, E5, G5, C6
      notes.forEach((freq, idx) => {
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq, now + idx * 0.07);
        gain.gain.setValueAtTime(0.08, now + idx * 0.07);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.07 + 0.32);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start(now + idx * 0.07);
        osc.stop(now + idx * 0.07 + 0.35);
      });
    }

    function toggleSfx() {
      sfxEnabled = !sfxEnabled;
      const btn = document.getElementById('osSfxBtn');
      btn.innerText = sfxEnabled ? '🔔 SFX: ON' : '🔕 SFX: OFF';
      btn.className = sfxEnabled
        ? 'text-xs font-mono px-2.5 py-1 rounded border border-emerald-800 bg-emerald-950 text-emerald-300 hover:brightness-110 transition active:scale-95'
        : 'text-xs font-mono px-2.5 py-1 rounded border border-slate-700 bg-slate-900 text-slate-400 hover:brightness-110 transition active:scale-95';
      if (sfxEnabled) playXpChime();
    }

    // Theme Switcher
    function changeTheme(themeName) {
      document.body.className = `theme-${themeName} bg-slate-950 text-slate-100 min-h-screen overflow-x-hidden font-sans select-none`;
      document.getElementById('osThemeSelect').value = themeName;
    }

    // Window Manager: Draggable, Resizable, Focus, Minimize, Maximize, Pop Out
    let highestZ = 30;
    const allWindows = ['win-terminal', 'win-tv', 'win-arena', 'win-comms', 'win-quests', 'win-moderator', 'win-billing', 'win-board', 'win-network'];
    const poppedOutWindows = new Set();

    function switchNetTab(tabName) {
      ['peers', 'visitors', 'leaderboard'].forEach(t => {
        const btn = document.getElementById(`btnNetTab-${t}`);
        const panel = document.getElementById(`netPanel-${t}`);
        if (btn) {
          if (t === tabName) {
            btn.className = 'flex-1 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-700 font-bold text-center transition';
          } else {
            btn.className = 'flex-1 py-1 rounded text-slate-400 hover:text-white text-center transition';
          }
        }
        if (panel) {
          panel.classList.toggle('hidden', t !== tabName);
        }
      });
    }

    function bringToFront(winEl) {
      highestZ += 1;
      winEl.style.zIndex = highestZ;
      document.querySelectorAll('.mesh-window').forEach(w => w.classList.remove('window-focused'));
      winEl.classList.add('window-focused');
      if (typeof syncDockIndicators === 'function') {
        syncDockIndicators();
      }
    }

    function makeWindowDraggable(winEl) {
      const header = winEl.querySelector('.window-header');
      if (!header) return;

      winEl.addEventListener('mousedown', () => bringToFront(winEl));

      header.addEventListener('mousedown', (e) => {
        if (e.target.tagName === 'BUTTON' || winEl.classList.contains('maximized') || winEl.classList.contains('popout-fullscreen')) {
          return;
        }
        bringToFront(winEl);
        let startX = e.clientX;
        let startY = e.clientY;
        const rect = winEl.getBoundingClientRect();
        let origLeft = rect.left;
        let origTop = rect.top;

        function onMouseMove(moveEvent) {
          const dx = moveEvent.clientX - startX;
          const dy = moveEvent.clientY - startY;
          winEl.style.left = `${Math.max(10, origLeft + dx)}px`;
          winEl.style.top = `${Math.max(60, origTop + dy)}px`;
          winEl.style.right = 'auto';
        }

        function onMouseUp() {
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      });
    }

    function makeWindowResizable(winEl) {
      let handle = winEl.querySelector('.window-resize-handle');
      if (!handle) {
        handle = document.createElement('div');
        handle.className = 'window-resize-handle';
        handle.title = 'Drag to resize window';
        winEl.appendChild(handle);
      }

      handle.addEventListener('mousedown', (e) => {
        if (winEl.classList.contains('maximized') || winEl.classList.contains('popout-fullscreen')) {
          return;
        }
        e.stopPropagation();
        e.preventDefault();
        bringToFront(winEl);

        const startX = e.clientX;
        const startY = e.clientY;
        const startW = winEl.offsetWidth;
        const startH = winEl.offsetHeight;

        function onMouseMove(moveEvent) {
          const newW = Math.max(320, startW + (moveEvent.clientX - startX));
          const newH = Math.max(180, startH + (moveEvent.clientY - startY));
          winEl.style.width = `${newW}px`;
          winEl.style.height = `${newH}px`;
        }

        function onMouseUp() {
          window.removeEventListener('mousemove', onMouseMove);
          window.removeEventListener('mouseup', onMouseUp);
        }

        window.addEventListener('mousemove', onMouseMove);
        window.addEventListener('mouseup', onMouseUp);
      });
    }

    function getDockButton(winId) {
      if (winId === 'win-moderator') {
        return document.getElementById('dockModBtn') || document.getElementById('dockBtn-win-moderator');
      }
      return document.getElementById(`dockBtn-${winId}`);
    }

    function setWindowPoppedOut(winId, isPoppedOut) {
      // In a pop-out standalone tab, never hide our own primary window!
      if (singleWindowParam && singleWindowParam === winId) {
        return;
      }

      const win = document.getElementById(winId);
      const dockBtn = getDockButton(winId);

      if (isPoppedOut) {
        poppedOutWindows.add(winId);
        if (win) {
          win.style.display = 'none';
          win.classList.add('hidden', 'popped-out');
        }
        if (dockBtn) {
          dockBtn.dataset.poppedOut = 'true';
          dockBtn.classList.add('ring-2', 'ring-indigo-400', 'bg-indigo-950/80', 'text-indigo-200');
          dockBtn.title = `${winId} is open in a pop-out window. Click to focus or redock.`;
        }
        if (winId === 'win-comms') {
          const chatDockBtn = document.getElementById('dockBtn-chat');
          if (chatDockBtn) {
            chatDockBtn.classList.add('ring-2', 'ring-indigo-400');
            chatDockBtn.title = 'Live Chat is open in pop-out window.';
          }
        }
      } else {
        poppedOutWindows.delete(winId);
        if (dockBtn) {
          delete dockBtn.dataset.poppedOut;
          dockBtn.classList.remove('ring-2', 'ring-indigo-400', 'bg-indigo-950/80', 'text-indigo-200');
          dockBtn.title = '';
          if (winId === 'win-moderator') {
            if (isAdmin) {
              dockBtn.style.display = '';
              dockBtn.classList.remove('hidden');
            }
          } else {
            dockBtn.style.display = '';
            dockBtn.classList.remove('hidden');
          }
        }
        if (winId === 'win-comms') {
          const chatDockBtn = document.getElementById('dockBtn-chat');
          if (chatDockBtn) {
            chatDockBtn.classList.remove('ring-2', 'ring-indigo-400');
            chatDockBtn.title = 'Live Mesh Chat & Comms';
          }
        }
        if (win) {
          win.classList.remove('hidden', 'minimized', 'popped-out');
          win.style.display = 'flex';
          bringToFront(win);
        }
      }
      syncDockIndicators();
    }

    function syncDockIndicators() {
      allWindows.forEach(id => {
        const win = document.getElementById(id);
        const dockBtn = getDockButton(id);
        if (!win || !dockBtn) return;

        const isClosed = win.style.display === 'none' || win.classList.contains('hidden') || win.classList.contains('minimized');
        const isFocused = !isClosed && win.classList.contains('window-focused');

        if (isFocused) {
          dockBtn.classList.add('ring-2', 'ring-cyan-400');
          dockBtn.classList.remove('opacity-70');
        } else if (!isClosed) {
          dockBtn.classList.remove('ring-2', 'ring-cyan-400');
          dockBtn.classList.add('ring-1', 'ring-slate-500');
          dockBtn.classList.remove('opacity-70');
        } else {
          dockBtn.classList.remove('ring-1', 'ring-2', 'ring-cyan-400', 'ring-slate-500');
          dockBtn.classList.add('opacity-70');
        }
      });
    }

    function toggleWindow(winId) {
      if (poppedOutWindows.has(winId)) {
        const handle = popoutWindowHandles.get(winId);
        if (handle && !handle.closed) {
          try { handle.focus(); } catch (e) {}
          const shouldRedock = confirm(`Window '${winId}' is currently open in a pop-out window on your second screen.\n\nClick OK to pull it back and redock onto this main desktop, or Cancel to leave it open.`);
          if (shouldRedock) {
            try { handle.close(); } catch(e){}
            popoutWindowHandles.delete(winId);
            setWindowPoppedOut(winId, false);
          }
          return;
        } else {
          setWindowPoppedOut(winId, false);
          return;
        }
      }

      const win = document.getElementById(winId);
      if (!win) return;
      const isHidden = win.style.display === 'none' || win.classList.contains('hidden') || win.classList.contains('minimized');
      if (isHidden) {
        win.style.display = 'flex';
        win.classList.remove('hidden', 'minimized');
        bringToFront(win);
      } else {
        if (win.classList.contains('window-focused')) {
          minimizeWindow(winId);
          return;
        } else {
          bringToFront(win);
        }
      }
      syncDockIndicators();
    }

    function focusChatWindow() {
      const win = document.getElementById('win-comms');
      if (!win) return;
      win.style.display = 'flex';
      win.classList.remove('minimized', 'hidden');
      bringToFront(win);
      win.scrollIntoView({ behavior: 'smooth', block: 'center' });
      const inp = document.getElementById('chatInput');
      if (inp) inp.focus();
      syncDockIndicators();
    }

    function minimizeWindow(winId) {
      const win = document.getElementById(winId);
      if (!win) return;
      win.classList.add('minimized', 'hidden');
      win.style.display = 'none';
      win.classList.remove('window-focused');
      syncDockIndicators();
    }

    function maximizeWindow(winId) {
      const win = document.getElementById(winId);
      if (!win) return;
      win.classList.remove('minimized', 'hidden');
      win.style.display = 'flex';
      win.classList.toggle('maximized');
      bringToFront(win);
      syncDockIndicators();
    }

    const popoutWindowHandles = new Map();

    function openPopoutWindow(winId) {
      const targetUrl = `/?window=${encodeURIComponent(winId)}&room=${encodeURIComponent(currentRoom)}&peer=${encodeURIComponent(myPeerId)}`;
      const popWin = window.open(targetUrl, `_tincan_popout_${winId}`, 'width=1120,height=760,menubar=no,toolbar=no,location=no,status=no');

      if (!popWin || popWin.closed || typeof popWin.closed === 'undefined') {
        alert('⚠️ Pop-up was blocked by your browser!\n\nPlease click the pop-up icon in your address bar and select "Always allow pop-ups for this site" to open windows in separate monitors.');
        return;
      }

      popoutWindowHandles.set(winId, popWin);
      setWindowPoppedOut(winId, true);

      const timer = setInterval(() => {
        if (popWin.closed) {
          clearInterval(timer);
          popoutWindowHandles.delete(winId);
          setWindowPoppedOut(winId, false);
          meshBus.postMessage({ type: 'WINDOW_REDOCK', winId: winId });
        }
      }, 400);

      meshBus.postMessage({ type: 'WINDOW_POPOUT', winId: winId });
    }

    let currentDesktopLayout = localStorage.getItem('tincan_layout_mode') || 'free';

    function setDesktopLayout(mode) {
      currentDesktopLayout = mode;
      localStorage.setItem('tincan_layout_mode', mode);

      const btn2x2 = document.getElementById('btnLayoutTile2x2');
      const btnSplit = document.getElementById('btnLayoutSplit');
      const btnFree = document.getElementById('btnLayoutFree');

      if (btn2x2) btn2x2.className = (mode === 'tile2x2') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';
      if (btnSplit) btnSplit.className = (mode === 'split2col') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';
      if (btnFree) btnFree.className = (mode === 'free') ? 'px-2 py-0.5 rounded bg-indigo-600 text-white font-bold shadow transition flex items-center gap-1' : 'px-2 py-0.5 rounded text-slate-400 hover:text-white transition flex items-center gap-1';

      if (mode === 'free') {
        allWindows.forEach(id => {
          const w = document.getElementById(id);
          if (w) {
            w.style.height = '';
            const body = w.querySelector('.window-body');
            if (body) body.style.height = '';
          }
        });
        return;
      }

      const isMobile = window.innerWidth < 768;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      const topBarHeight = 56;
      const dockHeight = 64;
      const pad = 12;
      const availH = vh - topBarHeight - dockHeight - (pad * 2);

      if (isMobile) {
        let top = 70;
        ['win-tv', 'win-arena', 'win-board', 'win-network'].forEach(id => {
          const w = document.getElementById(id);
          if (!w) return;
          w.style.display = 'flex';
          w.classList.remove('maximized', 'minimized', 'hidden');
          w.style.left = '10px';
          w.style.right = '10px';
          w.style.top = `${top}px`;
          w.style.width = 'calc(100vw - 20px)';
          top += 580;
        });
        return;
      }

      if (mode === 'tile2x2') {
        const halfW = Math.floor((vw - (pad * 3)) / 2);
        const halfH = Math.max(340, Math.floor(availH / 2));

        const quadrants = [
          { id: 'win-tv', x: pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-arena', x: pad + halfW + pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-board', x: pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH },
          { id: 'win-network', x: pad + halfW + pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH }
        ];

        quadrants.forEach(q => {
          const w = document.getElementById(q.id);
          if (w) {
            w.style.display = 'flex';
            w.classList.remove('hidden', 'minimized', 'maximized');
            w.style.left = `${q.x}px`;
            w.style.top = `${q.y}px`;
            w.style.width = `${q.w}px`;
            w.style.height = `${q.h}px`;
            const body = w.querySelector('.window-body');
            if (body) {
              body.style.maxHeight = `${q.h - 44}px`;
              body.style.height = `${q.h - 44}px`;
            }
            bringToFront(w);
          }
        });
      } else if (mode === 'split2col') {
        const halfW = Math.floor((vw - (pad * 3)) / 2);
        const halfH = Math.max(340, Math.floor(availH / 2));

        const splits = [
          { id: 'win-tv', x: pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-board', x: pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH },
          { id: 'win-arena', x: pad + halfW + pad, y: topBarHeight + pad, w: halfW, h: halfH },
          { id: 'win-network', x: pad + halfW + pad, y: topBarHeight + pad + halfH + pad, w: halfW, h: halfH }
        ];

        splits.forEach(s => {
          const w = document.getElementById(s.id);
          if (w) {
            w.style.display = 'flex';
            w.classList.remove('hidden', 'minimized', 'maximized');
            w.style.left = `${s.x}px`;
            w.style.top = `${s.y}px`;
            w.style.width = `${s.w}px`;
            w.style.height = `${s.h}px`;
            const body = w.querySelector('.window-body');
            if (body) {
              body.style.maxHeight = `${s.h - 44}px`;
              body.style.height = `${s.h - 44}px`;
            }
            bringToFront(w);
          }
        });
      }
    }

    function tileWindows() {
      setDesktopLayout('tile2x2');
    }

    function togglePopoutGuide() {
      alert('TinCan Mesh OS Pop-Out Mode:\n\n1. Click [ ↗ Pop Out ] on any window titlebar.\n2. Move the pop-out window to your secondary monitor.\n3. Packet flights, watch-party playback, cursor telemetry, and XP sync across all windows in real time via BroadcastChannel!');
    }

    // Initialize Windows
    allWindows.forEach(id => {
      const w = document.getElementById(id);
      if (w) {
        makeWindowDraggable(w);
        makeWindowResizable(w);
      }
    });
    syncDockIndicators();

    // Handle Pop-Out Single-Window Viewport Optimization
    if (singleWindowParam && allWindows.includes(singleWindowParam)) {
      allWindows.forEach(id => {
        const w = document.getElementById(id);
        if (w) {
          if (id === singleWindowParam) {
            w.classList.remove('hidden', 'minimized');
            w.classList.add('popout-fullscreen');
            w.style.display = 'flex';
            bringToFront(w);

            // Transform the Pop Out button in header into a Redock button
            const popBtn = w.querySelector('button[onclick*="openPopoutWindow"]');
            if (popBtn) {
              popBtn.innerText = '↙ Redock';
              popBtn.onclick = () => window.close();
              popBtn.title = 'Close pop-out and return window to main desktop';
              popBtn.className = 'px-2 py-0.5 rounded bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-[10px] shadow transition active:scale-95';
            }

            // Hide the minimize button in popout window as it fills the window
            const minBtn = w.querySelector('button[onclick*="minimizeWindow"]');
            if (minBtn) minBtn.style.display = 'none';

            // Hide the maximize button in popout window
            const maxBtn = w.querySelector('button[onclick*="maximizeWindow"]');
            if (maxBtn) maxBtn.style.display = 'none';

            // If this is the TV watch party, ensure video starts playing
            if (id === 'win-tv') {
              const vid = document.getElementById('relayNativeVideo');
              if (vid) {
                vid.play().catch(e => console.warn('Pop-out video autoplay notice:', e));
              }
            }
          } else {
            w.style.display = 'none';
            w.classList.add('hidden');
          }
        }
      });

      // In pop-out mode, hide background topology canvas, cursors, and dock to maximize app workspace
      const bgCanvas = document.getElementById('meshTopologyCanvas');
      if (bgCanvas) bgCanvas.style.display = 'none';
      const cursors = document.getElementById('multiplayerCursorsLayer');
      if (cursors) cursors.style.display = 'none';
      const dock = document.getElementById('meshOsDock');
      if (dock) dock.style.display = 'none';

      document.title = `[Pop-Out] TinCan Mesh OS — ${singleWindowParam}`;

      window.addEventListener('beforeunload', () => {
        meshBus.postMessage({ type: 'WINDOW_REDOCK', winId: singleWindowParam });
      });
    }

    // =========================================================================
    // Account Setup, Username Prompt & Onboarding Engine (Mandatory Non-Negotiable Gate)
    // =========================================================================
    const REGISTRATION_EPOCH = 'epoch_20261109_v3_strict_pii';

    function isIdentityVerified() {
      return (
        localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH &&
        Boolean((localStorage.getItem('tincan_fullname') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_username') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_email') || '').trim()) &&
        Boolean((localStorage.getItem('tincan_phone') || '').trim()) &&
        localStorage.getItem('tincan_consent_pii') === 'true'
      );
    }

    function getVerifiedDisplayName() {
      const fn = (localStorage.getItem('tincan_fullname') || '').trim();
      const un = (localStorage.getItem('tincan_username') || '').trim();
      if (fn && un) return `${fn} (@${un})`;
      if (un) return `@${un}`;
      if (fn) return fn;
      return myPeerId;
    }

    function requireVerifiedIdentity(actionDescription = 'enter the room') {
      if (isIdentityVerified()) return true;
      openAccountModal(true);
      const errEl = document.getElementById('accFormError');
      if (errEl) {
        errEl.innerText = `Mandatory Identity Gate: You must identify yourself (Full Name, Username, Email, Phone & PII Consent) to ${actionDescription}.`;
        errEl.classList.remove('hidden');
      }
      return false;
    }

    function openAccountModal(isMandatory = false) {
      const modal = document.getElementById('accountSetupModal');
      const peerLabel = document.getElementById('modalPeerIdLabel');
      const nameInp = document.getElementById('accInputFullName');
      const userInp = document.getElementById('accInputUsername');
      const emailInp = document.getElementById('accInputEmail');
      const phoneInp = document.getElementById('accInputPhone');
      const errEl = document.getElementById('accFormError');
      if (errEl) errEl.classList.add('hidden');
      if (peerLabel) peerLabel.innerText = myPeerId;

      if (nameInp && localStorage.getItem('tincan_fullname')) nameInp.value = localStorage.getItem('tincan_fullname');
      if (userInp && localStorage.getItem('tincan_username')) userInp.value = localStorage.getItem('tincan_username');
      if (emailInp && localStorage.getItem('tincan_email')) emailInp.value = localStorage.getItem('tincan_email');
      if (phoneInp && localStorage.getItem('tincan_phone')) phoneInp.value = localStorage.getItem('tincan_phone');

      if (modal) {
        modal.classList.remove('hidden');
        if (nameInp && !nameInp.value) nameInp.focus();
        else if (userInp) userInp.focus();
      }
    }

    function closeAccountModal() {
      const isRegistered = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH 
        && localStorage.getItem('tincan_username') 
        && localStorage.getItem('tincan_consent_pii') === 'true';
      if (!isRegistered) {
        // Enforce non-negotiable mandatory registration: cannot close until identity & PII consent are confirmed!
        return;
      }
      const modal = document.getElementById('accountSetupModal');
      if (modal) modal.classList.add('hidden');
    }

    // Intercept Escape key to prevent modal bypass
    window.addEventListener('keydown', (e) => {
      const isRegistered = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH 
        && localStorage.getItem('tincan_username') 
        && localStorage.getItem('tincan_consent_pii') === 'true';
      if (!isRegistered && e.key === 'Escape') {
        e.preventDefault();
        e.stopPropagation();
      }
    }, true);

    function awardLocalXp(amount, reason) {
      try {
        if (sfxEnabled && typeof playXpChime === 'function') playXpChime();
        fetch('/api/mesh/quest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            action_key: 'workstation_handshake',
            display_name: localStorage.getItem('tincan_username') || myPeerId
          })
        }).catch(() => {});
      } catch (e) {
        console.warn('awardLocalXp caught error:', e);
      }
    }

    async function handleAccountFormSubmit(e) {
      e.preventDefault();
      const fullName = (document.getElementById('accInputFullName') ? document.getElementById('accInputFullName').value : '').trim();
      const username = (document.getElementById('accInputUsername') ? document.getElementById('accInputUsername').value : '').trim();
      const email = (document.getElementById('accInputEmail') ? document.getElementById('accInputEmail').value : '').trim();
      const phone = (document.getElementById('accInputPhone') ? document.getElementById('accInputPhone').value : '').trim();
      const role = document.getElementById('accInputRole') ? document.getElementById('accInputRole').value : 'Mesh Operator';
      const consentPii = document.getElementById('accInputConsentPii') ? document.getElementById('accInputConsentPii').checked : false;
      const submitBtn = document.getElementById('accSubmitBtn');
      const errEl = document.getElementById('accFormError');

      if (!fullName || fullName.length < 2) {
        if (errEl) {
          errEl.innerText = 'Full Legal / Real Name is non-negotiable (minimum 2 characters).';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!username || username.length < 2) {
        if (errEl) {
          errEl.innerText = 'Username / Mesh Call-Sign is non-negotiable (minimum 2 characters).';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!email || !email.includes('@')) {
        if (errEl) {
          errEl.innerText = 'A valid contact email address is required for operator records.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      const cleanPhone = phone.replace(/[^\d+]/g, '');
      if (!cleanPhone || cleanPhone.replace(/\D/g, '').length < 10) {
        if (errEl) {
          errEl.innerText = 'A valid phone number (minimum 10 digits) is non-negotiable for operator 2FA verification.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (!consentPii) {
        if (errEl) {
          errEl.innerText = 'You must explicitly consent to PII storage, node telemetry, and operator auditing.';
          errEl.classList.remove('hidden');
        }
        return;
      }

      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span>⏳</span> <span>Verifying &amp; Attesting Operator Identity...</span>';
      }

      try {
        const resp = await fetch('/api/account/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: fullName,
            name: fullName,
            username: username,
            email: email,
            phone: phone,
            phone_number: phone,
            role: role,
            consent_pii: true
          })
        });

        const data = await resp.json();
        if (resp.ok && data.status === 'success') {
          localStorage.setItem('tincan_registration_epoch', REGISTRATION_EPOCH);
          localStorage.setItem('tincan_fullname', fullName);
          localStorage.setItem('tincan_username', username);
          localStorage.setItem('tincan_email', email);
          localStorage.setItem('tincan_phone', phone);
          localStorage.setItem('tincan_role', role);
          localStorage.setItem('tincan_consent_pii', 'true');
          const hudName = document.getElementById('hudAccountName');
          if (hudName) hudName.innerText = '@' + username;
          const localLbl = document.getElementById('localPeerLabel');
          if (localLbl) localLbl.innerText = getVerifiedDisplayName();

          if (sfxEnabled) playXpChime();
          awardLocalXp(100, `Verified identity @${username}`);
          const modal = document.getElementById('accountSetupModal');
          if (modal) modal.classList.add('hidden');
          refreshBillingWindow();
          fetch('/api/mesh/cursor', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              peer_id: myPeerId,
              display_name: getVerifiedDisplayName(),
              x: 120,
              y: 120,
              room: currentRoom
            })
          }).catch(() => {});
          alert(`🎉 Identity Verified! Welcome Operator @${username}. 50,000 tokens have been credited to your account.`);
        } else {
          if (errEl) {
            errEl.innerText = data.error || 'Failed to verify account. Please check your contact information.';
            errEl.classList.remove('hidden');
          }
        }
      } catch (err) {
        if (errEl) {
          errEl.innerText = 'Connection error: ' + err.message;
          errEl.classList.remove('hidden');
        }
      } finally {
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerHTML = '<span>🛡️</span> <span>Sign Identity &amp; Unlock TinCan Mesh OS</span>';
        }
      }
    }

    async function initAccountState() {
      const epochValid = localStorage.getItem('tincan_registration_epoch') === REGISTRATION_EPOCH;
      const savedUser = localStorage.getItem('tincan_username');
      const savedConsent = localStorage.getItem('tincan_consent_pii') === 'true';
      const hudName = document.getElementById('hudAccountName');

      if (!epochValid || !savedUser || !savedConsent) {
        // Enforce mandatory non-negotiable registration for EVERYONE
        openAccountModal(true);
        return;
      }

      if (savedUser) {
        if (hudName) hudName.innerText = '@' + savedUser;
        const localLbl = document.getElementById('localPeerLabel');
        if (localLbl) localLbl.innerText = getVerifiedDisplayName();
        // Re-sync localStorage identity to server in case container restarted
        fetch('/api/account/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: localStorage.getItem('tincan_fullname') || savedUser,
            name: localStorage.getItem('tincan_fullname') || savedUser,
            username: savedUser,
            email: localStorage.getItem('tincan_email') || `${savedUser}@mesh.local`,
            phone: localStorage.getItem('tincan_phone') || '+10000000000',
            phone_number: localStorage.getItem('tincan_phone') || '+10000000000',
            role: localStorage.getItem('tincan_role') || 'Mesh Operator',
            consent_pii: true
          })
        }).then(() => refreshBillingWindow()).catch(() => {});
        return;
      }

      openAccountModal(true);
    }

    setTimeout(initAccountState, 250);

    // =========================================================================
    // Token Billing, Top-Up & Sponsored Ads Interaction Engine
    // =========================================================================
    let isWatchingAd = false;
    let currentSponsor = {
      id: "vercel-ai",
      name: "Vercel AI SDK & MicroVMs",
      tagline: "Deploy durable agent sandboxes and AI gateways with zero server management.",
      cta: "Visit Partner ↗",
      url: "https://sdk.vercel.ai?utm_source=tincan-mesh",
      icon: "⚡",
      badge: "Sponsored",
      video_url: "/videos/7705677376465767711.mp4",
      duration_seconds: 10,
      reward_tokens: 5000,
      reward_usd: 0.05
    };

    async function loadActiveSponsor(sponsorId) {
      try {
        const url = sponsorId ? `/api/ads/sponsor?id=${encodeURIComponent(sponsorId)}` : '/api/ads/sponsor';
        const resp = await fetch(url);
        if (resp.ok) {
          const data = await resp.json();
          if (data && data.sponsor) {
            currentSponsor = data.sponsor;
            renderSponsorCard();
          }
        }
      } catch (err) {
        console.warn('Failed to load active sponsor:', err);
      }
    }

    function renderSponsorCard() {
      const nameEl = document.getElementById('adSponsorName');
      const tagEl = document.getElementById('adSponsorTagline');
      const badgeEl = document.getElementById('adSponsorBadge');
      const iconEl = document.getElementById('adSponsorIcon');
      const ctaBtn = document.getElementById('adSponsorCtaBtn');
      const titleEl = document.getElementById('adVideoTitle');

      if (nameEl) nameEl.innerText = currentSponsor.name || 'Developer Sponsor';
      if (tagEl) tagEl.innerText = currentSponsor.tagline || 'Fund free mesh AI tokens.';
      if (badgeEl) badgeEl.innerText = currentSponsor.badge || 'Sponsored';
      if (iconEl) iconEl.innerText = currentSponsor.icon || '⚡';
      if (titleEl) titleEl.innerText = currentSponsor.name || 'Sponsor Ad';
      if (ctaBtn) {
        ctaBtn.href = currentSponsor.url || '#';
        ctaBtn.innerText = currentSponsor.cta || 'Visit Partner ↗';
      }
    }

    async function fetchNextSponsor() {
      await loadActiveSponsor();
    }

    async function trackSponsorClick() {
      if (!currentSponsor || !currentSponsor.id) return;
      try {
        await fetch('/api/ads/click', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sponsor_id: currentSponsor.id })
        });
      } catch (e) {}
    }

    function openSponsorInfoModal() {
      alert("📣 Real Ads & Direct Sponsorships on TinCan:\n\n1. Direct Partner Sponsorship: Real developer brands (Railway, Vercel, Supabase) sponsor AI compute via verified video ads & click-through links.\n2. Developer Ad Networks: Integration-ready for EthicalAds (ETHICALADS_PUBLISHER_ID) and Carbon Ads.\n3. Rewarded Video Ads: Configurable Google AdSense Rewarded Ads (ADSENSE_CLIENT_ID).\n4. Community Ad Slots: Any peer can feature an ad in rotation using:\n   tincan playlist add <mp4_or_tiktok_url> --category ad");
    }

    async function refreshBillingWindow() {
      try {
        loadActiveSponsor();
        const resp = await fetch(`/api/account/billing?peer_id=${encodeURIComponent(myPeerId)}`);
        if (resp.ok) {
          const data = await resp.json();
          const tokEl = document.getElementById('billingWindowTokens');
          const credEl = document.getElementById('billingWindowCredits');
          const totalUsedEl = document.getElementById('billingTotalUsedText');
          if (tokEl) tokEl.innerText = Number(data.token_balance || 0).toLocaleString();
          if (credEl) credEl.innerText = `$${Number(data.credit_balance_usd || 0).toFixed(2)} USD`;
          if (totalUsedEl) totalUsedEl.innerText = `Total used: ${Number(data.total_tokens_used || 0).toLocaleString()} tokens ($${Number(data.total_billed_usd || 0).toFixed(4)})`;

          const pill = document.getElementById('hudTokenPill');
          if (pill) {
            const toks = Number(data.token_balance || 0);
            pill.innerText = toks >= 1000 ? `${Math.round(toks / 1000)}k 🪙` : `${toks} 🪙`;
          }

          const rowsEl = document.getElementById('billingLedgerRows');
          if (rowsEl && data.recent_invoices && data.recent_invoices.length > 0) {
            rowsEl.innerHTML = data.recent_invoices.map(inv => {
              const d = new Date(inv.timestamp * 1000);
              const timeStr = `${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}:${d.getSeconds().toString().padStart(2, '0')}`;
              return `
                <tr class="hover:bg-slate-900/60 transition">
                  <td class="py-1 text-cyan-400 font-bold">${inv.model}</td>
                  <td class="py-1 text-slate-200">${Number(inv.total_tokens).toLocaleString()}</td>
                  <td class="py-1 text-emerald-400">$${Number(inv.cost_usd).toFixed(5)}</td>
                  <td class="py-1 text-right text-slate-500">${timeStr}</td>
                </tr>
              `;
            }).join('');
          }
        }
      } catch (err) {
        console.warn('Billing refresh failed:', err);
      }
    }

    function watchSponsoredAd() {
      if (isWatchingAd) return;
      isWatchingAd = true;
      const btn = document.getElementById('watchAdBtn');
      const videoBox = document.getElementById('adVideoContainer');
      const videoEl = document.getElementById('adVideoPlayer');
      const bar = document.getElementById('adProgressBar');
      const timerText = document.getElementById('adTimerText');
      const progressText = document.getElementById('adProgressText');

      if (btn) btn.disabled = true;
      if (videoBox) videoBox.classList.remove('hidden');
      if (bar) bar.style.width = '0%';

      const duration = currentSponsor.duration_seconds || 10;
      let secondsLeft = duration;
      if (timerText) timerText.innerText = `${secondsLeft}s remaining`;
      if (progressText) progressText.innerText = `Streaming ${currentSponsor.name || 'sponsor'} video...`;

      let adFinished = false;
      let interval = null;

      const completeAd = () => {
        if (adFinished) return;
        adFinished = true;
        if (interval) clearInterval(interval);
        finishSponsoredAd();
      };

      if (videoEl && currentSponsor.video_url) {
        videoEl.src = currentSponsor.video_url;
        videoEl.currentTime = 0;
        videoEl.muted = true;
        videoEl.play().catch(e => {
          console.warn('Ad video autoplay policy note:', e);
        });
        videoEl.onended = completeAd;
      }

      interval = setInterval(() => {
        secondsLeft -= 1;
        const progressPct = Math.min(100, ((duration - secondsLeft) / duration) * 100);
        if (bar) bar.style.width = `${progressPct}%`;
        if (timerText) timerText.innerText = `${Math.max(0, secondsLeft)}s remaining`;

        if (secondsLeft <= 0) {
          completeAd();
        }
      }, 1000);
    }

    async function finishSponsoredAd() {
      const videoBox = document.getElementById('adVideoContainer');
      const videoEl = document.getElementById('adVideoPlayer');
      const btn = document.getElementById('watchAdBtn');

      if (videoEl) {
        try { videoEl.pause(); } catch(e){}
      }
      if (videoBox) videoBox.classList.add('hidden');
      if (btn) btn.disabled = false;
      isWatchingAd = false;

      const sponsorId = (currentSponsor && currentSponsor.id) ? currentSponsor.id : 'sponsor-default';
      const rewardTokens = (currentSponsor && currentSponsor.reward_tokens) ? currentSponsor.reward_tokens : 5000;
      const rewardUsd = (currentSponsor && currentSponsor.reward_usd) ? currentSponsor.reward_usd : 0.05;

      try {
        const resp = await fetch('/api/account/billing/topup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            tokens: rewardTokens,
            amount_usd: rewardUsd,
            sponsor_id: sponsorId
          })
        });
        if (resp.ok) {
          if (sfxEnabled) playXpChime();
          awardLocalXp(50, `Sponsored Ad Watched (+${rewardTokens.toLocaleString()} Tokens)`);
          refreshBillingWindow();
          alert(`🎉 Sponsor video completed! +${rewardTokens.toLocaleString()} Free Tokens credited from ${currentSponsor.name || 'Sponsor'}.`);
        }
      } catch (e) {
        console.error('Failed to credit ad tokens:', e);
      }
    }

    async function buyTokens(amountUsd, tokens) {
      try {
        const resp = await fetch('/api/account/billing/topup', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            tokens: tokens,
            amount_usd: amountUsd
          })
        });
        if (resp.ok) {
          if (sfxEnabled) playXpChime();
          awardLocalXp(100, `Purchased ${tokens.toLocaleString()} Tokens`);
          refreshBillingWindow();
          alert(`💎 Deposit confirmed! +${tokens.toLocaleString()} tokens ($${amountUsd.toFixed(2)}) funded to ${myPeerId}.`);
        }
      } catch (e) {
        alert('Top-up request failed: ' + e);
      }
    }

    setTimeout(refreshBillingWindow, 1500);

    // Copy Command Helper
    function copyCommand(id) {
      const text = document.getElementById(id).innerText;
      navigator.clipboard.writeText(text);
      alert('Copied curl command to clipboard:\n' + text);
    }

    // =========================================================================
    // Background Canvas: Mesh Topology, Taut String Tethers & Packet Flights
    // =========================================================================
    const canvas = document.getElementById('meshTopologyCanvas');
    const ctx = canvas.getContext('2d');
    let activeFlights = [];

    function resizeCanvas() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();

    function spawnPacketFlight(fromNode, toNode, kind = 'envelope', label = 'Packet') {
      const flight = {
        id: 'fl-' + Math.random().toString(36).substring(2, 8),
        from: fromNode,
        to: toNode,
        kind,
        label,
        progress: 0,
        speed: 0.018 + Math.random() * 0.012
      };
      activeFlights.push(flight);
      meshBus.postMessage({ type: 'FLIGHT', flight });
    }

    function fireTestPacket() {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, 'relay', 'test', '🥫 Sealed Courier');
      fetch('/api/mesh/quest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          peer_id: myPeerId,
          action_key: 'test_packet',
          from_node: myPeerId,
          to_node: 'relay',
          room: currentRoom
        })
      }).catch(() => {});
    }

    function renderTopology() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      const w = canvas.width;
      const h = canvas.height;

      // Define Node Anchors
      const pMap = window.latestProvidersMap || {};
      const relayPos = { x: w * 0.5, y: h * 0.42, label: 'Central Railway Relay' };
      const brains = [
        { id: 'gemini-brain', label: pMap['gemini-brain']?.model || 'Gemini 2.5', x: w * 0.28, y: h * 0.22 },
        { id: 'claude-brain', label: pMap['claude-brain']?.model || 'Claude Sonnet', x: w * 0.42, y: h * 0.18 },
        { id: 'grok-brain', label: pMap['grok-brain']?.model || 'Grok', x: w * 0.58, y: h * 0.18 },
        { id: 'openai-brain', label: pMap['openai-brain']?.model || 'GPT-4o', x: w * 0.72, y: h * 0.22 },
      ];
      const peers = [
        { id: myPeerId, label: 'You (Local)', x: w * 0.32, y: h * 0.68 },
        { id: 'peer-primary-mac', label: 'Mac Studio (M1 Max)', x: w * 0.5, y: h * 0.74 },
        { id: 'peer-secondary-node', label: 'Collaborator MacBook', x: w * 0.68, y: h * 0.68 },
      ];

      function getNodePos(nodeId) {
        if (nodeId === 'relay' || nodeId === 'central-relay') return relayPos;
        const b = brains.find(x => x.id === nodeId || nodeId.includes(x.id));
        if (b) return b;
        const p = peers.find(x => x.id === nodeId || nodeId.includes(x.id));
        if (p) return p;
        return relayPos;
      }

      // Draw Taut "Tin-Can String" Tethers (with subtle acoustic vibration)
      const nowMs = Date.now() * 0.003;
      ctx.save();
      peers.forEach(peer => {
        ctx.beginPath();
        ctx.moveTo(peer.x, peer.y);
        const midX = (peer.x + relayPos.x) / 2;
        const midY = (peer.y + relayPos.y) / 2 + Math.sin(nowMs + peer.x) * 6;
        ctx.quadraticCurveTo(midX, midY, relayPos.x, relayPos.y);
        ctx.strokeStyle = 'rgba(56, 189, 248, 0.22)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.stroke();
      });

      brains.forEach(brain => {
        ctx.beginPath();
        ctx.moveTo(relayPos.x, relayPos.y);
        const midX = (relayPos.x + brain.x) / 2;
        const midY = (relayPos.y + brain.y) / 2 - Math.sin(nowMs + brain.x) * 4;
        ctx.quadraticCurveTo(midX, midY, brain.x, brain.y);
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.25)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([3, 5]);
        ctx.stroke();
      });
      ctx.restore();

      // Draw Relay Node
      ctx.beginPath();
      ctx.arc(relayPos.x, relayPos.y, 14, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(16, 185, 129, 0.35)';
      ctx.fill();
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.fillStyle = '#6ee7b7';
      ctx.font = '10px monospace';
      ctx.fillText(relayPos.label, relayPos.x - 55, relayPos.y + 26);

      // Draw Brain Nodes
      brains.forEach(b => {
        ctx.beginPath();
        ctx.arc(b.x, b.y, 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(99, 102, 241, 0.3)';
        ctx.fill();
        ctx.strokeStyle = '#818cf8';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = '#c7d2fe';
        ctx.font = '9px monospace';
        ctx.fillText(b.label, b.x - 25, b.y - 14);
      });

      // Draw Peer Nodes
      peers.forEach(p => {
        ctx.beginPath();
        ctx.arc(p.x, p.y, 10, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(14, 165, 233, 0.3)';
        ctx.fill();
        ctx.strokeStyle = '#38bdf8';
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = '#bae6fd';
        ctx.font = '9px monospace';
        ctx.fillText(p.label, p.x - 30, p.y + 22);
      });

      // Draw Active Packet Flights
      activeFlights.forEach((fl, idx) => {
        fl.progress += fl.speed;
        const p1 = getNodePos(fl.from);
        const p2 = getNodePos(fl.to);
        const t = Math.min(1.0, fl.progress);

        // Bezier trajectory
        const midX = (p1.x + p2.x) / 2;
        const midY = (p1.y + p2.y) / 2 + (p1.y > p2.y ? -20 : 20);
        const curX = (1 - t) * (1 - t) * p1.x + 2 * (1 - t) * t * midX + t * t * p2.x;
        const curY = (1 - t) * (1 - t) * p1.y + 2 * (1 - t) * t * midY + t * t * p2.y;

        // Glowing packet capsule
        ctx.beginPath();
        ctx.arc(curX, curY, 6, 0, Math.PI * 2);
        ctx.fillStyle = fl.kind === 'ai_prompt' ? '#ec4899' : '#38bdf8';
        ctx.shadowColor = fl.kind === 'ai_prompt' ? '#ec4899' : '#06b6d4';
        ctx.shadowBlur = 12;
        ctx.fill();
        ctx.shadowBlur = 0;

        ctx.fillStyle = '#ffffff';
        ctx.font = '9px monospace';
        ctx.fillText(fl.label || 'Packet', curX + 9, curY - 4);
      });

      // Clean up finished flights
      activeFlights = activeFlights.filter(fl => fl.progress < 1.0);

      requestAnimationFrame(renderTopology);
    }
    requestAnimationFrame(renderTopology);

    // =========================================================================
    // Watch Party Reactions Bar & Live Emoji Particle Engine
    // =========================================================================
    function spawnEmojiParticle(emoji) {
      const overlay = document.getElementById('reactionOverlay');
      if (!overlay) return;
      const span = document.createElement('span');
      span.className = 'reaction-particle';
      span.innerText = emoji;
      span.style.left = `${20 + Math.random() * 60}%`;
      span.style.bottom = `${10 + Math.random() * 20}%`;
      overlay.appendChild(span);
      setTimeout(() => span.remove(), 2100);
    }

    async function sendReaction(emoji) {
      initAudio();
      spawnEmojiParticle(emoji);
      meshBus.postMessage({ type: 'REACTION', emoji });
      try {
        await fetch('/api/mesh/react', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            emoji,
            display_name: myPeerId,
            room: currentRoom
          })
        });
      } catch (e) {}
    }

    async function syncWatchParty() {
      const vid = document.getElementById('relayNativeVideo');
      if (!vid) return;
      const isPlaying = !vid.paused;
      const currentTime = vid.currentTime;
      try {
        await fetch('/api/mesh/watchparty', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            video_idx: currentVideoIdx,
            is_playing: isPlaying,
            current_time: currentTime,
            room: currentRoom
          })
        });
        meshBus.postMessage({
          type: 'WATCH_PARTY_SYNC',
          video_idx: currentVideoIdx,
          is_playing: isPlaying,
          current_time: currentTime
        });
        alert('Synchronized Watch Party across room peers!');
      } catch (e) {
        alert('Sync error: ' + e.message);
      }
    }

    // =========================================================================
    // Multiplayer Cursor Telemetry (Throttled, Visibility & Identity-Gated)
    // =========================================================================
    let lastCursorSend = 0;
    let lastCursorX = -1;
    let lastCursorY = -1;
    window.addEventListener('mousemove', (e) => {
      if (document.hidden || !isIdentityVerified()) return;
      const now = Date.now();
      const dx = Math.abs(e.clientX - lastCursorX);
      const dy = Math.abs(e.clientY - lastCursorY);
      if (now - lastCursorSend > 280 && (dx >= 4 || dy >= 4)) {
        lastCursorSend = now;
        lastCursorX = e.clientX;
        lastCursorY = e.clientY;
        fetch('/api/mesh/cursor', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: getVerifiedDisplayName(),
            x: e.clientX,
            y: e.clientY,
            room: currentRoom
          })
        }).catch(() => {});
      }
    });

    function renderMultiplayerCursors(cursors) {
      const layer = document.getElementById('multiplayerCursorsLayer');
      if (!layer) return;

      Object.entries(cursors || {}).forEach(([peerId, c]) => {
        if (peerId === myPeerId) return;
        let el = document.getElementById('cur-' + peerId);
        if (!el) {
          el = document.createElement('div');
          el.id = 'cur-' + peerId;
          el.className = 'remote-cursor';
          el.innerHTML = `
            <svg class="w-4 h-4 text-cyan-400 drop-shadow" fill="currentColor" viewBox="0 0 24 24">
              <path d="M4 0l16 12-7 2-3 8z"/>
            </svg>
            <span class="text-[10px] bg-slate-900/90 text-cyan-300 border border-cyan-800 px-1.5 py-0.5 rounded font-mono ml-3 -mt-2 inline-block whitespace-nowrap">
              ${c.display_name || peerId}
            </span>
          `;
          layer.appendChild(el);
        }
        el.style.transform = `translate(${c.x}px, ${c.y}px)`;
      });
    }

    // =========================================================================
    // AI Brain Arena Battle Engine & Peer Voting
    // =========================================================================
    async function runArenaBattle() {
      initAudio();
      const prompt = document.getElementById('arenaPromptInput').value.trim();
      const resA = document.getElementById('arenaResultA');
      const resB = document.getElementById('arenaResultB');

      resA.innerText = 'Routing prompt to Gemini 2.5 Flash...';
      resB.innerText = 'Routing prompt to Claude 3.7 Sonnet...';

      spawnPacketFlight(myPeerId, 'gemini-brain', 'ai_prompt', 'gemini-brain');
      spawnPacketFlight(myPeerId, 'claude-brain', 'ai_prompt', 'claude-brain');

      try {
        const [respA, respB] = await Promise.all([
          fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'gemini-brain', prompt })
          }).then(r => r.json()),
          fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ model: 'claude-brain', prompt })
          }).then(r => r.json())
        ]);

        resA.innerText = respA.choices?.[0]?.message?.content || respA.text || JSON.stringify(respA, null, 2);
        resB.innerText = respB.choices?.[0]?.message?.content || respB.text || JSON.stringify(respB, null, 2);
      } catch (err) {
        resA.innerText = 'Battle error: ' + err.message;
        resB.innerText = 'Battle error: ' + err.message;
      }
    }

    async function voteArenaWinner(winnerAlias) {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, winnerAlias, 'ai_prompt', `Vote: ${winnerAlias}`);
      try {
        const res = await fetch('/api/mesh/arena/vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            winner_alias: winnerAlias,
            prompt_preview: document.getElementById('arenaPromptInput').value.substring(0, 40),
            display_name: myPeerId,
            room: currentRoom
          })
        });
        const data = await res.json();
        alert(`🏆 Vote recorded for ${winnerAlias}! +150 XP awarded to your squad.`);
        pollMeshState();
      } catch (err) {
        alert('Vote error: ' + err.message);
      }
    }

    async function triggerQuestAction(actionKey) {
      initAudio();
      playXpChime();
      spawnPacketFlight(myPeerId, 'relay', actionKey, actionKey);
      try {
        const res = await fetch('/api/mesh/quest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            action_key: actionKey,
            display_name: myPeerId,
            from_node: myPeerId,
            to_node: 'relay',
            room: currentRoom
          })
        });
        const data = await res.json();
        pollMeshState();
      } catch (e) {}
    }

    // =========================================================================
    // Polling Loop: State, Quests, Leaderboard & Readiness Progression
    // =========================================================================
    async function pollMeshState(force = false) {
      if (!force && document.hidden) return;
      try {
        const res = await fetch(`/api/mesh/state?room=${encodeURIComponent(currentRoom)}`);
        if (!res.ok) return;
        const state = await res.json();

        // Update Tier Badge
        if (state.tier) {
          const badge = document.getElementById('osTierBadge');
          const tierLabel = state.tier.tier_name || state.tier.tier || 'L3: Cryptographic Multi-Account Bridge';
          const tierPct = state.tier.progress_pct !== undefined ? state.tier.progress_pct : (state.tier.score || '94.5');
          badge.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span><span>${tierLabel} (${tierPct}%)</span>`;
        }

        // Update Squad XP Progress Bar
        const squadXp = state.xp !== undefined ? state.xp : (state.squad_xp || 550);
        const targetXp = state.tier?.next_tier_xp || state.tier?.target_xp || 1000;
        const pct = Math.min(100, Math.round((squadXp / targetXp) * 100));
        document.getElementById('osXpBar').style.width = `${pct}%`;
        document.getElementById('osXpText').innerText = `${squadXp.toLocaleString()} / ${targetXp.toLocaleString()} XP`;

        // Update Peer Count across Top HUD and win-network
        const count = state.peers_count || (state.active_webrtc_streams?.length || 2);
        const osCountEl = document.getElementById('osPeerCountNum');
        if (osCountEl) osCountEl.innerText = count;
        const netWinBadgeEl = document.getElementById('netWinActiveNum');
        if (netWinBadgeEl) netWinBadgeEl.innerText = count;
        const netMetricPeersEl = document.getElementById('netMetricPeers');
        if (netMetricPeersEl) netMetricPeersEl.innerText = count;
        const netTabPeersEl = document.getElementById('netTabPeersCount');
        if (netTabPeersEl) netTabPeersEl.innerText = count;

        // Render Multiplayer Cursors
        if (state.cursors) {
          const cursorMap = {};
          if (Array.isArray(state.cursors)) {
            state.cursors.forEach(c => { cursorMap[c.peer_id] = c; });
          } else {
            Object.assign(cursorMap, state.cursors);
          }
          renderMultiplayerCursors(cursorMap);
        }

        // Update Leaderboard in both win-quests and standalone win-network
        if (state.leaderboard && Array.isArray(state.leaderboard)) {
          const renderLdRows = (rows) => rows.map((p, idx) => `
            <tr>
              <td class="px-3 py-2 text-${idx === 0 ? 'amber-400' : 'slate-400'} font-bold">#${idx + 1}</td>
              <td class="px-3 py-2 text-white font-bold">${p.display_name || p.peer_id}</td>
              <td class="px-3 py-2 text-emerald-400">${p.tier || 'L3: Cryptographic Bridge'}</td>
              <td class="px-3 py-2">
                ${(p.badges || ['🟢 Initiate']).map(b => `<span class="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px] mr-1">${b}</span>`).join('')}
              </td>
              <td class="px-3 py-2 text-right text-cyan-300 font-bold">${(p.xp || 0).toLocaleString()} XP</td>
            </tr>
          `).join('');

          const tbody = document.getElementById('operatorLeaderboard');
          if (tbody) tbody.innerHTML = renderLdRows(state.leaderboard);

          const tbodyStandalone = document.getElementById('operatorLeaderboardStandalone');
          if (tbodyStandalone) tbodyStandalone.innerHTML = renderLdRows(state.leaderboard);

          const topRank = state.leaderboard[0];
          const topXpEl = document.getElementById('netMetricTopXp');
          if (topXpEl && topRank) {
            topXpEl.innerText = `${(topRank.xp || 850).toLocaleString()} XP`;
          }
        }

        // Update win-network Peers & Visitors Roster
        const activePeers = (state.active_webrtc_streams && state.active_webrtc_streams.length > 0)
          ? state.active_webrtc_streams
          : [
              { peer_id: 'Mac Studio (M1 Max)', handle: '@nojuannobody', tier: 'L5: Autonomous Mesh', rtt: 24, status: 'Streaming 1080p', mbps: '5.4' },
              { peer_id: 'MacBook Pro (M2)', handle: '@collaborator', tier: 'L4: CRDT Gossip', rtt: 38, status: 'Connected', mbps: '2.1' }
            ];

        const netPeersListEl = document.getElementById('netPeersList');
        if (netPeersListEl) {
          netPeersListEl.innerHTML = activePeers.map(p => `
            <div class="p-3 bg-slate-950/80 border border-slate-800 rounded-lg space-y-1.5 hover:border-slate-700 transition">
              <div class="flex items-center justify-between">
                <span class="text-xs font-bold text-white flex items-center gap-1.5">
                  <span>🖥️</span> <span>${escapeHtml(p.peer_id || p.handle || 'Peer Node')}</span>
                </span>
                <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-bold">
                  ${escapeHtml(p.tier || 'L4: CRDT Gossip')}
                </span>
              </div>
              <div class="flex items-center justify-between text-[11px] text-slate-400">
                <span class="text-emerald-400">● ${escapeHtml(p.status || 'Active WebRTC Stream')}</span>
                <span class="font-mono text-cyan-300">${p.rtt || 24}ms RTT · ${p.mbps || '3.2'} Mbps</span>
              </div>
              <div class="flex items-center gap-2 pt-1 border-t border-slate-800/80 text-[10px]">
                <button onclick="startDirectCall('${escapeHtml(p.peer_id || '')}')" class="px-2 py-0.5 rounded bg-emerald-900/80 hover:bg-emerald-800 text-emerald-200 border border-emerald-700 transition active:scale-95">📞 Call</button>
                <button onclick="toggleWindow('win-comms')" class="px-2 py-0.5 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 transition active:scale-95">📺 View Screen</button>
                <button onclick="fireTestPacket()" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition active:scale-95">💬 Ping</button>
              </div>
            </div>
          `).join('');
        }

        const cursorsArr = Array.isArray(state.cursors) ? state.cursors : Object.values(state.cursors || {});
        const visitorsCount = Math.max(cursorsArr.length, 1);
        const netMetricVisitorsEl = document.getElementById('netMetricVisitors');
        if (netMetricVisitorsEl) netMetricVisitorsEl.innerText = visitorsCount;
        const netTabVisitorsEl = document.getElementById('netTabVisitorsCount');
        if (netTabVisitorsEl) netTabVisitorsEl.innerText = visitorsCount;

        const netVisitorsListEl = document.getElementById('netVisitorsList');
        if (netVisitorsListEl) {
          if (cursorsArr.length === 0) {
            netVisitorsListEl.innerHTML = `
              <div class="p-2.5 bg-slate-950/60 border border-slate-800/80 rounded-lg text-slate-400 text-xs flex items-center justify-between">
                <span class="flex items-center gap-1.5"><span>🖱️</span> <span>Local Browser Session</span></span>
                <span class="px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 text-[10px]">Active Now</span>
              </div>
            `;
          } else {
            netVisitorsListEl.innerHTML = cursorsArr.map(c => `
              <div class="p-2 bg-slate-950/70 border border-slate-800 rounded-lg flex items-center justify-between text-[11px]">
                <div class="flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full" style="background-color: ${c.color || '#38bdf8'}"></span>
                  <span class="text-white font-bold">${escapeHtml(c.user || c.display_name || c.peer_id || 'Web Visitor')}</span>
                  <span class="text-slate-400 text-[10px]">(${escapeHtml(c.agent || 'Web Client')})</span>
                </div>
                <span class="text-emerald-400 font-mono text-[10px]">${escapeHtml(c.window_id || c.focused_window || 'Mesh Desktop')}</span>
              </div>
            `).join('');
          }
        }

        // Update Moderator Panel Rosters
        const streamsArr = state.active_webrtc_streams || [];

        const modWebCountEl = document.getElementById('modWebCount');
        const modMeshCountEl = document.getElementById('modMeshCount');
        const modWebTagEl = document.getElementById('modWebVisitorsCountTag');
        const modMeshTagEl = document.getElementById('modMeshNodesCountTag');

        if (modWebCountEl) modWebCountEl.innerText = cursorsArr.length;
        if (modMeshCountEl) modMeshCountEl.innerText = streamsArr.length;
        if (modWebTagEl) modWebTagEl.innerText = `${cursorsArr.length} connected`;
        if (modMeshTagEl) modMeshTagEl.innerText = `${streamsArr.length} active streams`;

        const webTbody = document.getElementById('modWebVisitorsTable');
        if (webTbody) {
          if (cursorsArr.length === 0) {
            webTbody.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">No active web cursors detected</td></tr>';
          } else {
            const now = Date.now() / 1000;
            webTbody.innerHTML = cursorsArr.map(c => {
              const diff = Math.max(0, Math.round(now - (c.updated_at || now)));
              const isLocal = c.peer_id === myPeerId;
              const badge = diff <= 15 ? '<span class="text-emerald-400 font-bold">● Active</span>' :
                            diff <= 60 ? `<span class="text-yellow-400">◐ ${diff}s ago</span>` :
                            `<span class="text-slate-500">○ ${diff}s ago</span>`;
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="px-2.5 py-1.5 text-white font-bold">${escapeHtml(c.display_name || c.peer_id)} <span class="text-[10px] text-slate-400 font-mono">(${escapeHtml(c.peer_id)})</span> ${isLocal ? '<span class="text-[10px] text-cyan-400">(you)</span>' : ''}</td>
                  <td class="px-2.5 py-1.5 text-slate-300">${c.room || 'main'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400">${c.window_id || 'desktop'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400 font-mono">(${Math.round(c.x || 0)}, ${Math.round(c.y || 0)})</td>
                  <td class="px-2.5 py-1.5">${badge}</td>
                  <td class="px-2.5 py-1.5 text-right">
                    ${!isLocal ? `<button onclick="kickPeerNode('${c.peer_id}', '${c.room || 'main'}')" class="px-2 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 border border-red-800 text-[10px] font-bold transition">⛔ Kick</button>` : '<span class="text-slate-600 text-[10px]">Host</span>'}
                  </td>
                </tr>
              `;
            }).join('');
          }
        }

        const meshTbody = document.getElementById('modMeshNodesTable');
        if (meshTbody) {
          if (streamsArr.length === 0) {
            meshTbody.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500 text-[11px]">No active WebRTC / workstation streams</td></tr>';
          } else {
            meshTbody.innerHTML = streamsArr.map(s => {
              const isLocal = s.peer_id === myPeerId;
              const caps = [];
              if (s.has_video) caps.push('📹 Video');
              if (s.has_audio) caps.push('🎙️ Voice');
              if (s.has_screen) caps.push('🖥️ Screen');
              if (caps.length === 0) caps.push('⚡ Signaling');
              return `
                <tr class="hover:bg-slate-800/40 transition">
                  <td class="px-2.5 py-1.5 text-cyan-300 font-bold">${s.peer_id} ${isLocal ? '<span class="text-[10px] text-cyan-400">(you)</span>' : ''}</td>
                  <td class="px-2.5 py-1.5 text-white">${s.display_name || s.peer_id}</td>
                  <td class="px-2.5 py-1.5 text-slate-300">${s.room || 'main'}</td>
                  <td class="px-2.5 py-1.5 text-slate-400">${caps.join(', ')}</td>
                  <td class="px-2.5 py-1.5 text-slate-400 font-mono">UDP/${s.udp_port || 'auto'}</td>
                  <td class="px-2.5 py-1.5 text-right">
                    ${!isLocal ? `<button onclick="kickPeerNode('${s.peer_id}', '${s.room || 'main'}')" class="px-2 py-0.5 rounded bg-red-950/80 hover:bg-red-800 text-red-300 border border-red-800 text-[10px] font-bold transition">⛔ Disconnect</button>` : '<span class="text-slate-600 text-[10px]">Host</span>'}
                  </td>
                </tr>
              `;
            }).join('');
          }
        }
      } catch (e) {}
    }

    setInterval(() => pollMeshState(false), 4000);
    pollMeshState(true);

    // BroadcastChannel Listener
    meshBus.onmessage = (ev) => {
      const msg = ev.data;
      if (!msg) return;
      if (msg.type === 'REACTION' && msg.emoji) {
        spawnEmojiParticle(msg.emoji);
      } else if (msg.type === 'FLIGHT' && msg.flight) {
        activeFlights.push(msg.flight);
      } else if (msg.type === 'MODEL_UPDATED') {
        loadAnalytics();
      } else if (msg.type === 'WINDOW_POPOUT' && msg.winId) {
        if (!singleWindowParam) {
          setWindowPoppedOut(msg.winId, true);
        }
      } else if (msg.type === 'WINDOW_REDOCK' && msg.winId) {
        if (!singleWindowParam) {
          setWindowPoppedOut(msg.winId, false);
        }
      }
    };

    // =========================================================================
    // Core WebRTC Signaling & Media Engine (Preserved)
    // =========================================================================
    let pc = null;
    let localStream = null;
    let lastSignalSeq = 0;
    let pollTimer = null;
    let isMuted = false;
    let isCamOff = false;

    const rtcConfig = {
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    };

    function setCallStatus(text, tone = 'slate') {
      const badge = document.getElementById('callStatusBadge');
      badge.innerText = text;
      badge.className = `px-2 py-0.5 rounded border text-[11px] font-mono bg-${tone}-950 text-${tone}-300 border-${tone}-800`;
    }

    function copyInviteLink() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      const inviteUrl = `${window.location.origin}/?room=${encodeURIComponent(room)}#call`;
      navigator.clipboard.writeText(inviteUrl);
      alert('Copied WebRTC room invite link:\n' + inviteUrl);
    }

    async function sendSignal(type, payload, to = '*') {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      await fetch('/api/webrtc/signal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from: myPeerId, to, room, type, payload })
      });
    }

    function ensurePeerConnection() {
      if (pc) return pc;
      pc = new RTCPeerConnection(rtcConfig);
      pc.onicecandidate = (ev) => {
        if (ev.candidate) {
          sendSignal('candidate', { candidate: ev.candidate });
        }
      };
      pc.ontrack = (ev) => {
        const remoteVideo = document.getElementById('remoteVideo');
        if (ev.streams && ev.streams[0]) {
          remoteVideo.srcObject = ev.streams[0];
          setCallStatus('Connected (Live Media)', 'emerald');
        }
      };
      if (localStream) {
        localStream.getTracks().forEach(track => pc.addTrack(track, localStream));
      }
      return pc;
    }

    function startDirectCall(peerId) {
      toggleWindow('win-comms');
      const roomEl = document.getElementById('roomInput');
      if (roomEl && peerId && !roomEl.value.trim()) {
        roomEl.value = 'main';
      }
      startCall('video');
    }

    async function startCall(mode = 'video') {
      if (!requireVerifiedIdentity('join a live WebRTC call')) return;
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        setCallStatus('Requesting mic/cam...', 'amber');
        localStream = await navigator.mediaDevices.getUserMedia({
          video: mode === 'video',
          audio: true
        });
        document.getElementById('localVideo').srcObject = localStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: getVerifiedDisplayName(),
            room,
            has_video: mode === 'video',
            has_audio: true,
            has_screen: false
          })
        });

        ensurePeerConnection();
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Calling room ' + room + '...', 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Media error: ' + err.message, 'rose');
      }
    }

    async function startScreenShare() {
      if (!requireVerifiedIdentity('share your screen in a room')) return;
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: true });
        localStream = screenStream;
        document.getElementById('localVideo').srcObject = screenStream;

        await fetch('/api/webrtc/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            display_name: getVerifiedDisplayName() + ' (Screen)',
            room,
            has_video: true,
            has_audio: true,
            has_screen: true
          })
        });

        ensurePeerConnection();
        const videoTrack = screenStream.getVideoTracks()[0];
        const sender = pc.getSenders().find(s => s.track && s.track.kind === 'video');
        if (sender && videoTrack) {
          await sender.replaceTrack(videoTrack);
        } else {
          screenStream.getTracks().forEach(t => pc.addTrack(t, screenStream));
        }
        const offer = await pc.createOffer();
        await pc.setLocalDescription(offer);
        await sendSignal('offer', { sdp: pc.localDescription });
        setCallStatus('Sharing Screen in ' + room, 'cyan');
        if (!pollTimer) pollTimer = setInterval(pollSignals, 1200);
      } catch (err) {
        setCallStatus('Screenshare error: ' + err.message, 'rose');
      }
    }

    function toggleMute() {
      if (!localStream) return;
      isMuted = !isMuted;
      localStream.getAudioTracks().forEach(t => { t.enabled = !isMuted; });
      document.getElementById('muteBtn').innerText = isMuted ? '🔊 Unmute Mic' : '🔇 Mute Mic';
    }

    function toggleCamera() {
      if (!localStream) return;
      isCamOff = !isCamOff;
      localStream.getVideoTracks().forEach(t => { t.enabled = !isCamOff; });
      document.getElementById('camBtn').innerText = isCamOff ? '📷 Cam On' : '📷 Toggle Cam';
    }

    async function hangupCall() {
      const room = document.getElementById('roomInput').value.trim() || 'main';
      if (localStream) {
        localStream.getTracks().forEach(t => t.stop());
        localStream = null;
      }
      if (pc) {
        pc.close();
        pc = null;
      }
      document.getElementById('localVideo').srcObject = null;
      document.getElementById('remoteVideo').srcObject = null;
      document.getElementById('remotePeerLabel').innerText = 'waiting for peer...';
      await fetch('/api/webrtc/leave', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ peer_id: myPeerId, room })
      });
      setCallStatus('Call Ended', 'slate');
    }

    async function pollSignals(force = false) {
      if (!force && document.hidden && !pc) return;
      try {
        const room = document.getElementById('roomInput').value.trim() || 'main';
        const res = await fetch(`/api/webrtc/signals?peer_id=${encodeURIComponent(myPeerId)}&room=${encodeURIComponent(room)}&since_seq=${lastSignalSeq}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.latest_seq && data.latest_seq > lastSignalSeq) {
          lastSignalSeq = data.latest_seq;
        }
        if (data.peers) {
          const grid = document.getElementById('roomPeersGrid');
          grid.innerHTML = data.peers.map(p => `
            <div class="p-2 bg-slate-800/60 rounded border border-slate-700 flex justify-between items-center text-xs font-mono">
              <span class="text-white">${p.display_name}</span>
              <span class="bg-emerald-900 text-emerald-300 px-1.5 py-0.5 rounded text-[10px]">${p.has_screen ? 'SCREEN' : (p.has_video ? 'VIDEO+VOICE' : 'VOICE')} · UDP:${p.udp_port}</span>
            </div>
          `).join('');
        }
        for (const sig of (data.signals || [])) {
          document.getElementById('remotePeerLabel').innerText = sig.from;
          if (sig.type === 'offer' && sig.payload && sig.payload.sdp) {
            // Peripheral & Connection Consent Guard: Never auto-answer an incoming WebRTC offer
            // without explicit human consent.
            const accepted = window.confirm(`Incoming WebRTC call offer from '${sig.from}'. Accept connection? (Your camera/mic remain OFF unless you explicitly enable them)`);
            if (!accepted) {
              setCallStatus('Declined offer from ' + sig.from, 'amber');
              continue;
            }
            ensurePeerConnection();
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            const answer = await pc.createAnswer();
            await pc.setLocalDescription(answer);
            await sendSignal('answer', { sdp: pc.localDescription }, sig.from);
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'answer' && sig.payload && sig.payload.sdp && pc) {
            await pc.setRemoteDescription(new RTCSessionDescription(sig.payload.sdp));
            setCallStatus('Connected with ' + sig.from, 'emerald');
          } else if (sig.type === 'candidate' && sig.payload && sig.payload.candidate && pc) {
            try {
              await pc.addIceCandidate(new RTCIceCandidate(sig.payload.candidate));
            } catch (e) {}
          } else if (sig.type === 'hangup') {
            document.getElementById('remoteVideo').srcObject = null;
            document.getElementById('remotePeerLabel').innerText = 'peer hung up';
            setCallStatus('Peer disconnected', 'amber');
          } else if (sig.type === 'chat' || sig.type === 'message') {
            const sigKey = `${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const txt = (sig.payload && (sig.payload.text || sig.payload.message)) || (typeof sig.payload === 'string' ? sig.payload : '');
              const sender = (sig.payload && sig.payload.sender) || sig.from || 'Peer';
              if (txt && sig.from !== myPeerId) {
                appendChatMessage(sender, txt, false, sig.timestamp ? sig.timestamp * 1000 : null);
                playXpChime();
              }
            }
          } else if (sig.type === 'admin_broadcast') {
            const sigKey = `admin-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              const txt = (sig.payload && (sig.payload.text || sig.payload.message)) || (typeof sig.payload === 'string' ? sig.payload : '');
              showAdminBanner(txt, sig.from);
              playXpChime();
            }
          } else if (sig.type === 'verification_form') {
            const sigKey = `verify-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              playXpChime();
              const winEl = document.getElementById('win-board');
              if (winEl && winEl.classList.contains('hidden')) {
                toggleWindow('win-board');
              }
              switchBoardTab('verify');
              if (sig.payload) {
                prefillVerificationFormFromSignal(sig.payload);
              }
            }
          } else if (sig.type === 'board_event') {
            const sigKey = `board-${sig.seq || ''}-${sig.from}-${sig.timestamp || ''}`;
            if (!seenChatIds.has(sigKey)) {
              seenChatIds.add(sigKey);
              loadCyberspaceBoard();
            }
          }
        }
      } catch (e) {}
    }
    pollTimer = setInterval(() => pollSignals(false), 3000);

    // =========================================================================
    // Live Mesh & Peer Chat Engine
    // =========================================================================
    let chatMsgCount = 0;
    const seenChatIds = new Set();

    function escapeHtml(str) {
      if (!str) return '';
      return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
    }

    function appendChatMessage(sender, text, isMe = false, timestamp = null) {
      const list = document.getElementById('chatMessagesList');
      if (!list) return;

      if (chatMsgCount === 0) {
        list.innerHTML = '';
      }
      chatMsgCount++;
      const counter = document.getElementById('chatCounterBadge');
      if (counter) counter.innerText = `${chatMsgCount} message${chatMsgCount === 1 ? '' : 's'}`;

      const timeStr = timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const row = document.createElement('div');
      row.className = `p-2 rounded text-xs font-mono border transition-all ${isMe ? 'bg-cyan-950/40 border-cyan-800/60 ml-4' : 'bg-slate-900/90 border-slate-800 mr-4'}`;
      row.innerHTML = `
        <div class="flex items-center justify-between text-[10px] text-slate-400 mb-0.5">
          <span class="font-bold ${isMe ? 'text-cyan-300' : 'text-emerald-400'}">${escapeHtml(sender)}${isMe ? ' (you)' : ''}</span>
          <span class="text-[9px] text-slate-500">${timeStr}</span>
        </div>
        <div class="text-slate-100 break-words leading-relaxed">${escapeHtml(text)}</div>
      `;
      list.appendChild(row);
      list.scrollTop = list.scrollHeight;
    }

    async function sendChatMessage() {
      if (!requireVerifiedIdentity('send messages in the room chat')) return;
      const input = document.getElementById('chatInput');
      if (!input) return;
      const text = input.value.trim();
      if (!text) return;
      input.value = '';
      const room = document.getElementById('roomInput').value.trim() || 'main';
      const senderLabel = getVerifiedDisplayName();

      appendChatMessage(senderLabel, text, true, Date.now());
      playXpChime();

      try {
        await fetch('/api/webrtc/signal', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            from: myPeerId,
            to: '*',
            type: 'chat',
            room: room,
            payload: {
              text: text,
              sender: senderLabel,
              timestamp: Date.now()
            }
          })
        });
      } catch (err) {
        console.error('Failed to send chat message:', err);
      }
    }

    // =========================================================================
    // OpenRouter Analytics & Model Configuration Engine (Preserved & Synced)
    // =========================================================================
    var latestProvidersMap = window.latestProvidersMap = {};

    function syncSelectedAliasModel(forcePopulateInput = false) {
      const sel = document.getElementById('aliasSelect');
      const inp = document.getElementById('modelInput');
      const badge = document.getElementById('currentTargetModelBadge');
      if (!sel) return;
      const alias = sel.value;
      const info = latestProvidersMap[alias];
      const currentModel = info ? info.model : '';
      if (badge && currentModel) {
        badge.innerText = `Active: ${alias} → ${currentModel}`;
      }
      if (inp && currentModel && (forcePopulateInput || document.activeElement !== inp)) {
        if (forcePopulateInput || !inp.dataset.userEdited) {
          inp.value = currentModel;
          delete inp.dataset.userEdited;
        }
      }
    }

    document.getElementById('modelInput').addEventListener('input', (ev) => {
      ev.target.dataset.userEdited = 'true';
    });

    function quickPickModel(modelId) {
      const inp = document.getElementById('modelInput');
      if (!inp) return;
      inp.value = modelId;
      inp.dataset.userEdited = 'true';
      updateModel();
    }

    function selectProviderCardForSwap(alias) {
      const sel = document.getElementById('aliasSelect');
      if (!sel) return;
      sel.value = alias;
      syncSelectedAliasModel(true);
      document.getElementById('modelInput')?.focus();
    }

    async function loadAnalytics(force = false) {
      if (!force && document.hidden) return;
      try {
        const res = await fetch('/api/models/analytics');
        const data = await res.json();
        const or = data.openrouter || {};

        if (or.connected) {
          document.getElementById('orRemaining').innerText = `$${Number(or.account_remaining_balance_usd).toFixed(4)}`;
          document.getElementById('orCreditsTotal').innerText = `of $${Number(or.account_total_credits_usd).toFixed(2)} total credits`;
          document.getElementById('orTotalUsage').innerText = `$${Number(or.account_total_usage_usd).toFixed(4)}`;
          document.getElementById('orKeyUsage').innerText = `$${Number(or.key_usage_total_usd).toFixed(6)}`;
          document.getElementById('orKeyToday').innerText = `Today: $${Number(or.key_usage_daily_usd).toFixed(6)}`;
          document.getElementById('orKeyLimitRem').innerText = or.key_remaining_usd != null ? `$${Number(or.key_remaining_usd).toFixed(4)}` : 'Unlimited';
          document.getElementById('orKeyLabel').innerText = `Key: ${or.key_label || '--'}`;
        }

        document.getElementById('analyticsHeader').innerText = 
          `Calls: ${data.total_calls} | Tokens: ${data.total_tokens} | Cost: $${Number(data.total_spend_usd).toFixed(6)}`;
        
        window.latestProvidersMap = latestProvidersMap = data.providers || {};
        const sel = document.getElementById('aliasSelect');
        const prevSelected = sel ? sel.value : 'gemini-brain';
        if (sel && Object.keys(latestProvidersMap).length > 0) {
          sel.innerHTML = Object.entries(latestProvidersMap).map(([alias, info]) =>
            `<option value="${alias}">${alias} → ${info.model}</option>`
          ).join('');
          if (latestProvidersMap[prevSelected]) {
            sel.value = prevSelected;
          }
          syncSelectedAliasModel(false);
        }

        const container = document.getElementById('providerCards');
        container.innerHTML = '';
        for (const [alias, info] of Object.entries(latestProvidersMap)) {
          const isSelected = sel && sel.value === alias;
          const card = document.createElement('div');
          card.onclick = () => selectProviderCardForSwap(alias);
          card.className = `cursor-pointer p-3 bg-slate-800/60 rounded-lg border ${isSelected ? 'border-indigo-500 ring-1 ring-indigo-500/40' : 'border-slate-700/80 hover:border-slate-600'} space-y-1.5 font-mono text-xs transition`;
          card.innerHTML = `
            <div class="flex justify-between items-center">
              <span class="font-bold text-white">${alias}</span>
              <span class="text-[10px] bg-indigo-950 text-indigo-300 px-1.5 py-0.5 rounded border border-indigo-800">${info.display_name}</span>
            </div>
            <div class="text-emerald-300 truncate text-[11px] font-semibold"><span class="text-slate-500 font-normal">Model:</span> ${info.model}</div>
            <div class="grid grid-cols-3 gap-1 pt-1 text-slate-300 border-t border-slate-700/50 text-[10px]">
              <div><span class="text-slate-500">In/1M:</span> <span class="text-amber-300">$${Number(info.input_cost_per_1m_usd || 0).toFixed(2)}</span></div>
              <div><span class="text-slate-500">Out/1M:</span> <span class="text-amber-300">$${Number(info.output_cost_per_1m_usd || 0).toFixed(2)}</span></div>
              <div><span class="text-slate-500">Calls:</span> <span class="text-cyan-300">${info.total_calls ?? info.call_count ?? 0}</span></div>
            </div>
          `;
          container.appendChild(card);
        }
      } catch (e) {}
    }

    async function updateModel() {
      const sel = document.getElementById('aliasSelect');
      const inp = document.getElementById('modelInput');
      const alias = sel.value;
      const model = inp.value.trim();
      const fb = document.getElementById('updateFeedback');
      if (!model) {
        fb.innerText = 'Please enter a valid model identifier';
        fb.className = 'text-xs mt-2 font-mono text-red-400 block';
        return;
      }
      try {
        const res = await fetch('/api/models/set', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({alias, model})
        });
        const resp = await res.json();
        if (res.ok) {
          if (!latestProvidersMap[resp.alias]) {
            latestProvidersMap[resp.alias] = { display_name: resp.display_name || resp.alias, model: resp.model };
          } else {
            latestProvidersMap[resp.alias].model = resp.model;
          }
          delete inp.dataset.userEdited;
          inp.value = resp.model;
          syncSelectedAliasModel(true);
          fb.innerText = `✓ Updated ${resp.alias} → ${resp.model}`;
          fb.className = 'text-xs mt-2 font-mono text-emerald-400 block';
          spawnPacketFlight(myPeerId, resp.alias, 'ai_prompt', `Swap: ${resp.model}`);
          meshBus.postMessage({ type: 'MODEL_UPDATED', alias: resp.alias, model: resp.model });
          await loadAnalytics();
        } else {
          fb.innerText = `Error: ${resp.error}`;
          fb.className = 'text-xs mt-2 font-mono text-red-400 block';
        }
      } catch (err) {
        fb.innerText = `Request failed: ${err.message}`;
        fb.className = 'text-xs mt-2 font-mono text-red-400 block';
      }
    }

    // =========================================================================
    // Relay Video Channel & Auto-Rotating Playlist Engine (Preserved)
    // =========================================================================
    let playlistVideos = [];
    let currentVideoIdx = 0;
    let autoRotateEnabled = true;
    let rotateTimer = null;

    async function loadPlaylist(preserveIndex = true) {
      try {
        const res = await fetch('/api/playlist');
        if (!res.ok) return;
        const data = await res.json();
        playlistVideos = data.videos || [];
        if (!preserveIndex || currentVideoIdx >= playlistVideos.length) {
          currentVideoIdx = 0;
        }
        renderPlaylistUI();
      } catch (e) {}
    }

    function renderPlaylistUI() {
      const total = playlistVideos.length;
      const badge = document.getElementById('playlistCounterBadge');
      const queue = document.getElementById('playlistQueue');
      if (!total) {
        badge.innerText = '0 / 0';
        queue.innerHTML = '<div class="text-slate-500">No videos in collection</div>';
        return;
      }

      const item = playlistVideos[currentVideoIdx];
      badge.innerText = `${currentVideoIdx + 1} / ${total} · ${autoRotateEnabled ? 'Loop' : 'Paused'}`;
      document.getElementById('nowPlayingTitle').innerHTML =
        `${item.title} · <span class="text-pink-400 font-mono">${item.creator}</span>`;

      const vidEl = document.getElementById('relayNativeVideo');
      const targetSrc = item.embed_url || `/videos/${item.video_id}.mp4`;
      if (vidEl) {
        vidEl.loop = (total === 1 && autoRotateEnabled);
        if (vidEl.getAttribute('data-vid') !== item.id) {
          vidEl.setAttribute('data-vid', item.id);
          vidEl.src = targetSrc;
          vidEl.play().catch(() => {});
        }
      }

      queue.innerHTML = playlistVideos.map((v, idx) => `
        <div onclick="selectPlaylistVideo(${idx})" class="cursor-pointer px-2.5 py-1 rounded border flex justify-between items-center transition ${idx === currentVideoIdx ? 'bg-pink-950/60 border-pink-700 text-white' : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:border-slate-700'}">
          <span class="truncate">${idx + 1}. ${v.title} (${v.creator})</span>
          <div class="flex items-center gap-1.5 ml-2 shrink-0">
            <span class="text-[10px] uppercase px-1.5 py-0.5 rounded bg-slate-900 text-slate-300">${v.category}</span>
            ${isAdmin ? `
              <button onclick="event.stopPropagation(); openEditVideoModal('${v.video_id}')" class="px-1.5 py-0.5 bg-slate-800 hover:bg-slate-700 text-cyan-300 rounded text-[10px] border border-slate-700" title="Edit Video">✏️</button>
              <button onclick="event.stopPropagation(); adminDeleteVideo('${v.video_id}')" class="px-1.5 py-0.5 bg-red-950 hover:bg-red-800 text-red-300 rounded text-[10px] border border-red-800" title="Delete Video">🗑️</button>
            ` : ''}
          </div>
        </div>
      `).join('');
    }

    function selectPlaylistVideo(idx) {
      if (idx < 0 || idx >= playlistVideos.length) return;
      currentVideoIdx = idx;
      renderPlaylistUI();
    }

    function nextPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx + 1) % playlistVideos.length;
      renderPlaylistUI();
    }

    function prevPlaylistVideo() {
      if (!playlistVideos.length) return;
      currentVideoIdx = (currentVideoIdx - 1 + playlistVideos.length) % playlistVideos.length;
      renderPlaylistUI();
    }

    function toggleAutoRotate() {
      autoRotateEnabled = !autoRotateEnabled;
      const btn = document.getElementById('autoRotateBtn');
      btn.innerText = autoRotateEnabled ? '🔁 Auto-Loop: ON' : '⏸ Auto-Loop: OFF';
      btn.className = autoRotateEnabled
        ? 'px-2.5 py-1 bg-emerald-950 text-emerald-300 rounded border border-emerald-800 transition'
        : 'px-2.5 py-1 bg-slate-800 text-slate-400 rounded border border-slate-700 transition';
      renderPlaylistUI();
    }

    function toggleVideoSound() {
      const vidEl = document.getElementById('relayNativeVideo');
      const btn = document.getElementById('soundToggleBtn');
      if (!vidEl) return;
      vidEl.muted = !vidEl.muted;
      btn.innerText = vidEl.muted ? '🔊 Tap to Unmute' : '🔇 Mute Audio';
      vidEl.play().catch(() => {});
    }

    document.getElementById('relayNativeVideo').addEventListener('ended', () => {
      if (autoRotateEnabled && playlistVideos.length > 1) {
        nextPlaylistVideo();
      } else if (autoRotateEnabled && playlistVideos.length === 1) {
        const vidEl = document.getElementById('relayNativeVideo');
        vidEl.currentTime = 0;
        vidEl.play().catch(() => {});
      }
    });

    async function addVideoToPlaylist() {
      const inp = document.getElementById('newVideoInput');
      const raw = inp.value.trim();
      if (!raw) return;
      try {
        const res = await fetch('/api/playlist/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: raw, category: 'spotlight', peer_id: myPeerId })
        });
        const data = await res.json();
        if (res.ok) {
          inp.value = '';
          playlistVideos = data.playlist.videos || [];
          currentVideoIdx = playlistVideos.length - 1;
          renderPlaylistUI();
          playXpChime();
        } else {
          alert('Could not add video: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to add video: ' + err.message);
      }
    }

    // =========================================================================
    // Admin Video & Sponsor CRUD Functions
    // =========================================================================
    let adminActiveTab = 'videos';
    let allSponsorsList = [];

    function toggleAdminTab(tab) {
      adminActiveTab = tab;
      const vPanel = document.getElementById('adminVideosPanel');
      const sPanel = document.getElementById('adminSponsorsPanel');
      const vBtn = document.getElementById('adminTabBtnVideos');
      const sBtn = document.getElementById('adminTabBtnSponsors');
      if (tab === 'videos') {
        if (vPanel) vPanel.classList.remove('hidden');
        if (sPanel) sPanel.classList.add('hidden');
        if (vBtn) vBtn.className = 'px-2 py-0.5 rounded bg-pink-950 text-pink-300 border border-pink-700 text-[10px] font-mono font-bold';
        if (sBtn) sBtn.className = 'px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono';
      } else {
        if (vPanel) vPanel.classList.add('hidden');
        if (sPanel) sPanel.classList.remove('hidden');
        if (vBtn) vBtn.className = 'px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 text-[10px] font-mono';
        if (sBtn) sBtn.className = 'px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 text-[10px] font-mono font-bold';
      }
      renderAdminCrudTables();
    }

    function toggleAddVideoDrawer() {
      const d = document.getElementById('adminAddVideoDrawer');
      if (d) d.classList.toggle('hidden');
    }

    function toggleAddSponsorDrawer() {
      const d = document.getElementById('adminAddSponsorDrawer');
      if (d) d.classList.toggle('hidden');
    }

    function openAdminSponsorStudio() {
      toggleWindow('win-moderator');
      toggleAdminTab('sponsors');
    }

    async function adminSubmitAddVideo() {
      const url = document.getElementById('adminNewVideoUrl').value.trim();
      const title = document.getElementById('adminNewVideoTitle').value.trim();
      const creator = document.getElementById('adminNewVideoCreator').value.trim();
      const category = document.getElementById('adminNewVideoCategory').value;
      const duration = parseInt(document.getElementById('adminNewVideoDuration').value) || 35;
      if (!url) {
        alert('Please enter a video URL or ID');
        return;
      }
      try {
        const res = await fetch('/api/playlist/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ input: url, title, creator, category, duration_seconds: duration, peer_id: myPeerId }),
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('adminNewVideoUrl').value = '';
          document.getElementById('adminNewVideoTitle').value = '';
          document.getElementById('adminNewVideoCreator').value = '';
          toggleAddVideoDrawer();
          await loadPlaylist(false);
          renderAdminCrudTables();
          playXpChime();
        } else {
          alert('Error adding video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Request failed: ' + e.message);
      }
    }

    function openEditVideoModal(vidId) {
      const v = playlistVideos.find(it => it.video_id === vidId || it.id === vidId);
      if (!v) return;
      document.getElementById('editVideoId').value = v.video_id;
      document.getElementById('editVideoTitle').value = v.title || '';
      document.getElementById('editVideoCreator').value = v.creator || '';
      document.getElementById('editVideoCategory').value = v.category || 'spotlight';
      document.getElementById('editVideoDuration').value = v.duration_seconds || 35;
      document.getElementById('editVideoEmbedUrl').value = v.embed_url || `/videos/${v.video_id}.mp4`;
      document.getElementById('adminEditVideoModal').classList.remove('hidden');
    }

    function closeEditVideoModal() {
      document.getElementById('adminEditVideoModal').classList.add('hidden');
    }

    async function adminSubmitSaveVideoEdit() {
      const vidId = document.getElementById('editVideoId').value;
      const title = document.getElementById('editVideoTitle').value.trim();
      const creator = document.getElementById('editVideoCreator').value.trim();
      const category = document.getElementById('editVideoCategory').value;
      const duration = parseInt(document.getElementById('editVideoDuration').value) || 35;
      const embed_url = document.getElementById('editVideoEmbedUrl').value.trim();

      try {
        const res = await fetch('/api/playlist/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: vidId, title, creator, category, duration_seconds: duration, embed_url }),
        });
        const data = await res.json();
        if (res.ok) {
          closeEditVideoModal();
          await loadPlaylist(false);
          renderAdminCrudTables();
        } else {
          alert('Error updating video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to update: ' + e.message);
      }
    }

    async function adminDeleteVideo(vidId) {
      if (!confirm(`Are you sure you want to remove video ${vidId} from the playlist and S3 manifest?`)) return;
      try {
        const res = await fetch('/api/playlist/remove', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: vidId }),
        });
        const data = await res.json();
        if (res.ok) {
          await loadPlaylist(false);
          renderAdminCrudTables();
        } else {
          alert('Error deleting video: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to delete: ' + e.message);
      }
    }

    async function loadSponsorsData() {
      try {
        const res = await fetch('/api/sponsors');
        if (!res.ok) return;
        const data = await res.json();
        allSponsorsList = data.all_sponsors || [];
        renderAdminCrudTables();
      } catch (e) {}
    }

    async function adminSubmitAddSponsor() {
      const name = document.getElementById('adminNewSponsorName').value.trim();
      const icon = document.getElementById('adminNewSponsorIcon').value.trim() || '🌟';
      const badge = document.getElementById('adminNewSponsorBadge').value.trim() || 'Partner';
      const tagline = document.getElementById('adminNewSponsorTagline').value.trim();
      const url = document.getElementById('adminNewSponsorUrl').value.trim() || '/';
      const cta = document.getElementById('adminNewSponsorCta').value.trim() || 'Visit Partner ↗';
      const rewardTokens = parseInt(document.getElementById('adminNewSponsorRewardTokens').value) || 5000;
      const rewardUsd = parseFloat(document.getElementById('adminNewSponsorRewardUsd').value) || 0.05;

      if (!name) {
        alert('Please enter sponsor name');
        return;
      }

      try {
        const res = await fetch('/api/sponsors/add', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ name, icon, badge, tagline, url, cta, reward_tokens: rewardTokens, reward_usd: rewardUsd }),
        });
        const data = await res.json();
        if (res.ok) {
          document.getElementById('adminNewSponsorName').value = '';
          document.getElementById('adminNewSponsorTagline').value = '';
          toggleAddSponsorDrawer();
          await loadSponsorsData();
        } else {
          alert('Error adding sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to add: ' + e.message);
      }
    }

    function openEditSponsorModal(sId) {
      const s = allSponsorsList.find(it => it.id === sId);
      if (!s) return;
      document.getElementById('editSponsorId').value = s.id;
      document.getElementById('editSponsorName').value = s.name || '';
      document.getElementById('editSponsorIcon').value = s.icon || '🌟';
      document.getElementById('editSponsorBadge').value = s.badge || 'Partner';
      document.getElementById('editSponsorTagline').value = s.tagline || '';
      document.getElementById('editSponsorCta').value = s.cta || 'Visit Partner ↗';
      document.getElementById('editSponsorUrl').value = s.url || '/';
      document.getElementById('editSponsorRewardTokens').value = s.reward_tokens || 5000;
      document.getElementById('editSponsorRewardUsd').value = s.reward_usd || 0.05;
      document.getElementById('adminEditSponsorModal').classList.remove('hidden');
    }

    function closeEditSponsorModal() {
      document.getElementById('adminEditSponsorModal').classList.add('hidden');
    }

    async function adminSubmitSaveSponsorEdit() {
      const sId = document.getElementById('editSponsorId').value;
      const name = document.getElementById('editSponsorName').value.trim();
      const icon = document.getElementById('editSponsorIcon').value.trim();
      const badge = document.getElementById('editSponsorBadge').value.trim();
      const tagline = document.getElementById('editSponsorTagline').value.trim();
      const cta = document.getElementById('editSponsorCta').value.trim();
      const url = document.getElementById('editSponsorUrl').value.trim();
      const rewardTokens = parseInt(document.getElementById('editSponsorRewardTokens').value) || 5000;
      const rewardUsd = parseFloat(document.getElementById('editSponsorRewardUsd').value) || 0.05;

      try {
        const res = await fetch('/api/sponsors/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: sId, name, icon, badge, tagline, cta, url, reward_tokens: rewardTokens, reward_usd: rewardUsd }),
        });
        const data = await res.json();
        if (res.ok) {
          closeEditSponsorModal();
          await loadSponsorsData();
        } else {
          alert('Error updating sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to update: ' + e.message);
      }
    }

    async function adminDeleteSponsor(sId) {
      if (!confirm(`Are you sure you want to remove sponsor '${sId}' from rotation?`)) return;
      try {
        const res = await fetch('/api/sponsors/remove', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ id: sId }),
        });
        const data = await res.json();
        if (res.ok) {
          await loadSponsorsData();
        } else {
          alert('Error deleting sponsor: ' + (data.error || 'Unknown error'));
        }
      } catch (e) {
        alert('Failed to delete: ' + e.message);
      }
    }

    function renderAdminCrudTables() {
      const vCount = document.getElementById('adminVideosCount');
      const sCount = document.getElementById('adminSponsorsCount');
      if (vCount) vCount.innerText = playlistVideos.length;
      if (sCount) sCount.innerText = allSponsorsList.length;

      const vTable = document.getElementById('adminVideosTableBody');
      if (vTable) {
        if (!playlistVideos.length) {
          vTable.innerHTML = '<tr><td colspan="6" class="px-3 py-3 text-center text-slate-500">No videos in playlist</td></tr>';
        } else {
          vTable.innerHTML = playlistVideos.map(v => `
            <tr class="hover:bg-slate-800/40">
              <td class="px-2.5 py-2 font-mono text-[11px] text-pink-300">
                <a href="${v.embed_url || `/videos/${v.video_id}.mp4`}" target="_blank" class="hover:underline">${v.video_id}</a>
              </td>
              <td class="px-2.5 py-2 font-semibold text-white max-w-[160px] truncate" title="${v.title}">${v.title}</td>
              <td class="px-2.5 py-2 text-slate-400 font-mono text-[11px]">${v.creator}</td>
              <td class="px-2.5 py-2">
                <span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono ${v.category === 'ad' ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'bg-slate-800 text-slate-300 border border-slate-700'}">${v.category}</span>
              </td>
              <td class="px-2.5 py-2 text-slate-400 font-mono text-[11px]">${v.duration_seconds || 35}s</td>
              <td class="px-2.5 py-2 text-right space-x-1 shrink-0">
                <button onclick="openEditVideoModal('${v.video_id}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[10px]">Edit</button>
                <button onclick="adminDeleteVideo('${v.video_id}')" class="px-2 py-0.5 rounded bg-red-950 hover:bg-red-800 text-red-300 border border-red-800 text-[10px]">Delete</button>
              </td>
            </tr>
          `).join('');
        }
      }

      const sTable = document.getElementById('adminSponsorsTableBody');
      if (sTable) {
        if (!allSponsorsList.length) {
          sTable.innerHTML = '<tr><td colspan="5" class="px-3 py-3 text-center text-slate-500">No active sponsors</td></tr>';
        } else {
          sTable.innerHTML = allSponsorsList.map(s => `
            <tr class="hover:bg-slate-800/40">
              <td class="px-2.5 py-2 font-mono text-[11px]">
                <div class="flex items-center gap-1.5">
                  <span>${s.icon || '🌟'}</span>
                  <span class="font-bold text-white">${s.name}</span>
                </div>
                <div class="text-[10px] text-slate-400 truncate max-w-[180px]">${s.tagline || ''}</div>
              </td>
              <td class="px-2.5 py-2">
                <span class="px-1.5 py-0.5 rounded text-[9px] uppercase font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">${s.badge || 'Partner'}</span>
              </td>
              <td class="px-2.5 py-2 font-mono text-emerald-400 text-[11px]">+${s.reward_tokens || 5000}</td>
              <td class="px-2.5 py-2 font-mono text-slate-400 text-[10px]">
                Imp: ${s.impressions || 0} / Clk: ${s.clicks || 0}
              </td>
              <td class="px-2.5 py-2 text-right space-x-1 shrink-0">
                <button onclick="openEditSponsorModal('${s.id}')" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-[10px]">Edit</button>
                <button onclick="adminDeleteSponsor('${s.id}')" class="px-2 py-0.5 rounded bg-red-950 hover:bg-red-800 text-red-300 border border-red-800 text-[10px]">Delete</button>
              </td>
            </tr>
          `).join('');
        }
      }
    }

    // =========================================================================
    // Cyberspace Discussion Board · GraphRAG + BM25 + @verifier-agent Engine
    // =========================================================================
    let activeBoardTopicId = null;
    let activeBoardTab = 'discussions';
    let activeBoardCategoryFilter = '';
    let activeReplyParentPostByTopic = {};
    let boardGraphSnapshot = { nodes: [], edges: [] };
    let boardGraphLayoutNodes = [];
    let selectedGraphNodeId = null;

    function switchBoardTab(tabName) {
      activeBoardTab = tabName;
      ['discussions', 'search', 'graph', 'verify'].forEach(t => {
        const panel = document.getElementById(`boardTab-${t}`);
        const btn = document.getElementById(`boardTabBtn-${t}`);
        if (panel) panel.classList.toggle('hidden', t !== tabName);
        if (btn) {
          if (t === tabName) {
            btn.className = 'px-3 py-1.5 rounded-lg bg-indigo-600 text-white font-bold text-xs transition flex items-center gap-1';
          } else {
            btn.className = 'px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs transition flex items-center gap-1';
          }
        }
      });
      if (tabName === 'search') {
        runIrLabSearch();
      } else if (tabName === 'graph') {
        loadAndDrawBoardGraph();
      } else if (tabName === 'verify') {
        prefillVerificationFormDefaults();
        loadVerificationCenterData();
      }
    }

    function setBoardCategoryFilter(cat) {
      activeBoardCategoryFilter = cat || '';
      document.querySelectorAll('.board-cat-btn').forEach(btn => {
        const c = btn.getAttribute('data-cat') || '';
        if (c === activeBoardCategoryFilter) {
          btn.className = 'board-cat-btn px-2 py-0.5 rounded bg-indigo-600 text-white font-bold';
        } else {
          btn.className = 'board-cat-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300';
        }
      });
      loadCyberspaceBoard();
    }

    function formatBoardMentions(text) {
      const safe = escapeHtml(text || '');
      return safe
        .replace(/(?<![\w.])@([a-zA-Z0-9_\-]+)/g, (m, handle) => {
          const low = handle.toLowerCase();
          const isAgent = low.endsWith('-brain') || low.endsWith('-agent') || low === 'claude-sonnet' || low === 'gpt-4o' || low === 'deepseek-r1';
          if (isAgent) {
            return `<span onclick="quickSearchBoardEntity('@${handle}')" title="Search @${handle} across Cyberspace" class="cursor-pointer px-1.5 py-0.2 rounded bg-indigo-950 hover:bg-indigo-900 text-indigo-300 border border-indigo-700 font-mono text-[11px] font-bold">🤖 @${handle}</span>`;
          }
          return `<span onclick="inspectCyberspaceUserProfile('${handle}')" title="Inspect @${handle}'s Cyberspace profile & attestation" class="cursor-pointer px-1.5 py-0.2 rounded bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-700/70 font-mono text-[11px] font-semibold">🪪 @${handle}</span>`;
        })
        .replace(/(?<![\w.])#([a-zA-Z0-9_\-]+)/g, (m, tag) => {
          return `<span onclick="quickSearchBoardEntity('#${tag}')" class="cursor-pointer px-1.5 py-0.2 rounded bg-pink-950/60 hover:bg-pink-900 text-pink-300 border border-pink-800/60 font-mono text-[11px]">#${tag}</span>`;
        });
    }

    function insertBoardTag(tagStr, targetId = 'boardTopicBody') {
      const el = document.getElementById(targetId);
      if (!el) return;
      const cur = el.value;
      const prefix = (cur && !cur.endsWith(' ')) ? ' ' : '';
      el.value = cur + prefix + tagStr + ' ';
      el.focus();
    }

    function insertBoardSelfTag(targetId = 'boardTopicBody') {
      const un = (localStorage.getItem('tincan_username') || '').trim().replace(/^@/, '');
      if (!un) {
        switchBoardTab('verify');
        requestAgentVerificationForm();
        return;
      }
      insertBoardTag('@' + un, targetId);
    }

    function quickSearchBoardEntity(entityToken) {
      switchBoardTab('discussions');
      const inp = document.getElementById('boardSearchInput');
      if (inp) {
        inp.value = entityToken;
        searchCyberspaceBoard();
      }
    }

    async function loadBoardDynamicRoster() {
      try {
        const res = await fetch('/api/board/roster');
        if (!res.ok) return;
        const data = await res.json();
        const userBox = document.getElementById('boardDynamicUserChips');
        if (userBox && Array.isArray(data.users)) {
          userBox.innerHTML = data.users.slice(0, 14).map(u => {
            const handle = (u.username || '').replace(/^@/, '');
            const verifiedIcon = u.verified ? '✅' : '👤';
            return `<button type="button" onclick="insertBoardTag('@${escapeHtml(handle)}', 'boardTopicBody')" title="${escapeHtml(u.full_name || handle)} (${escapeHtml(u.role || 'Peer')})" class="px-2 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-700">${verifiedIcon} @${escapeHtml(handle)}</button>`;
          }).join('');
        }
      } catch (e) {}
    }

    async function inspectCyberspaceUserProfile(usernameOrHandle) {
      const clean = (usernameOrHandle || '').replace(/^@/, '').trim();
      if (!clean) return;
      try {
        const res = await fetch(`/api/board/profile?user=${encodeURIComponent(clean)}`);
        if (!res.ok) return;
        const data = await res.json();
        const drawer = document.getElementById('boardProfileDrawer');
        const nameEl = document.getElementById('boardProfileName');
        const pillEl = document.getElementById('boardProfileVerifiedPill');
        const metaEl = document.getElementById('boardProfileMeta');
        const topicsEl = document.getElementById('boardProfileTopics');
        if (!drawer) return;
        drawer.classList.remove('hidden');

        const p = data.profile || {};
        if (nameEl) nameEl.innerText = `${p.full_name || clean} (@${clean})`;
        if (pillEl) {
          if (data.verified) {
            pillEl.innerText = '✅ Verified Cyberspace Citizen';
            pillEl.className = 'px-2 py-0.5 rounded-full bg-emerald-950 text-emerald-300 border border-emerald-600 text-[10px] font-bold';
          } else {
            pillEl.innerText = '⚠️ Unverified Peer';
            pillEl.className = 'px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-600 text-[10px] font-bold';
          }
        }
        if (metaEl) {
          metaEl.innerHTML = `
            <div class="p-2 bg-slate-900/90 rounded border border-slate-800">
              <div class="text-[9px] text-slate-500 uppercase">Role / Institution</div>
              <div class="text-emerald-300 font-bold truncate">${escapeHtml(p.role || 'Mesh Collaborator')}</div>
            </div>
            <div class="p-2 bg-slate-900/90 rounded border border-slate-800">
              <div class="text-[9px] text-slate-500 uppercase">SHA-256 Attestation</div>
              <div class="text-cyan-300 truncate">${escapeHtml(p.attestation_hash || 'pending-verification')}</div>
            </div>
            <div class="p-2 bg-slate-900/90 rounded border border-slate-800">
              <div class="text-[9px] text-slate-500 uppercase">Graph Contributions</div>
              <div class="text-indigo-300 font-bold">${data.authored_count || 0} topics · ${data.reply_count || 0} replies · ${data.mentioned_count || 0} mentions</div>
            </div>
          `;
        }
        if (topicsEl) {
          const bioLine = p.bio ? `<div class="text-slate-300 italic pb-1">"${escapeHtml(p.bio)}"</div>` : '';
          const authoredLinks = (data.authored_topics || []).slice(0, 4).map(t =>
            `<span onclick="quickSearchBoardEntity('${escapeHtml(t.title)}')" class="cursor-pointer px-1.5 py-0.5 rounded bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-800 inline-block mr-1 mb-1">📌 ${escapeHtml(t.title)}</span>`
          ).join('');
          topicsEl.innerHTML = `${bioLine}<div><span class="text-slate-500 mr-1">Filter Board:</span> <button type="button" onclick="quickSearchBoardEntity('@${escapeHtml(clean)}')" class="px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700">🔍 Show All Threads with @${escapeHtml(clean)}</button> ${authoredLinks}</div>`;
        }
      } catch (e) {}
    }

    async function refreshBoardVerificationBadge() {
      const badge = document.getElementById('boardVerifiedBadge');
      const attBadge = document.getElementById('boardAttestationBadge');
      const subtext = document.getElementById('boardVerifierSubtext');
      const pendingCountBadge = document.getElementById('boardPendingVerifyCount');
      if (!badge) return;
      try {
        const unParam = encodeURIComponent(localStorage.getItem('tincan_username') || '');
        const res = await fetch(`/api/verify/status?peer_id=${encodeURIComponent(myPeerId)}&username=${unParam}`);
        if (!res.ok) return;
        const data = await res.json();
        const un = (data.profile && data.profile.username) || localStorage.getItem('tincan_username') || myPeerId;
        const pendingArr = data.pending_requests || [];
        if (pendingCountBadge) {
          pendingCountBadge.innerText = String(pendingArr.length);
        }
        if (data.verified) {
          badge.innerText = `✅ Verified Citizen (@${String(un).replace(/^@/, '')})`;
          badge.className = 'px-2 py-0.5 rounded-full bg-emerald-900/90 text-emerald-300 border border-emerald-500 text-[10px] font-bold';
          if (attBadge && data.profile && data.profile.attestation_hash) {
            attBadge.innerText = `SHA256:${data.profile.attestation_hash.slice(0, 10)}`;
            attBadge.classList.remove('hidden');
          }
          if (subtext) {
            subtext.innerText = `Attested by @verifier-agent. You can tag yourself (@${String(un).replace(/^@/, '')}), tag peers, vote, and summon @ai-agents.`;
          }
        } else {
          badge.innerText = '⚠️ Unverified Peer — Fill Form';
          badge.className = 'px-2 py-0.5 rounded-full bg-amber-950 text-amber-300 border border-amber-600 text-[10px] font-bold';
        }
      } catch (e) {}
    }

    function prefillVerificationFormDefaults() {
      const fn = document.getElementById('verifyFormFullName');
      const un = document.getElementById('verifyFormUsername');
      const em = document.getElementById('verifyFormEmail');
      const ph = document.getElementById('verifyFormPhone');
      const rl = document.getElementById('verifyFormRole');
      if (fn && !fn.value && localStorage.getItem('tincan_fullname')) fn.value = localStorage.getItem('tincan_fullname');
      if (un && !un.value && localStorage.getItem('tincan_username')) un.value = localStorage.getItem('tincan_username');
      if (em && !em.value && localStorage.getItem('tincan_email')) em.value = localStorage.getItem('tincan_email');
      if (ph && !ph.value && localStorage.getItem('tincan_phone')) ph.value = localStorage.getItem('tincan_phone');
      if (rl && !rl.value && localStorage.getItem('tincan_role')) rl.value = localStorage.getItem('tincan_role');
    }

    function prefillVerificationFormFromSignal(payload) {
      prefillVerificationFormDefaults();
      const reqInp = document.getElementById('verifyFormRequestId');
      const reqBadge = document.getElementById('verifyFormRequestIdBadge');
      const codeInp = document.getElementById('verifyFormChallengeCode');
      const userInp = document.getElementById('verifyFormUsername');
      const fb = document.getElementById('verifyDispatchFeedback');
      const reqId = payload.request_id || (payload.form && payload.form.request_id) || '';
      const challenge = payload.challenge_code || (payload.form && payload.form.challenge_code) || '';
      if (reqInp && reqId) reqInp.value = reqId;
      if (reqBadge && reqId) reqBadge.innerText = `Form #${reqId}`;
      if (codeInp && challenge) codeInp.value = challenge;
      if (userInp && payload.target_username && !userInp.value) userInp.value = payload.target_username;
      if (fb) {
        fb.classList.remove('hidden');
        fb.innerHTML = `🛡️ <strong>@verifier-agent</strong> dispatched Verification Form <code>#${escapeHtml(reqId)}</code> with Challenge Code <code>${escapeHtml(challenge)}</code>. Complete &amp; submit the form below!`;
      }
      loadVerificationCenterData();
    }

    async function requestAgentVerificationForm() {
      const un = (localStorage.getItem('tincan_username') || '').trim();
      switchBoardTab('verify');
      try {
        const res = await fetch('/api/verify/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username: un,
            reason: 'Requested Cyberspace Identity Verification Form from Discussion Board'
          })
        });
        const data = await res.json();
        playXpChime();
        spawnPacketFlight('@verifier-agent', myPeerId, 'verification_form', '🛡️ Verify Form');
        prefillVerificationFormFromSignal(data);
      } catch (err) {
        prefillVerificationFormDefaults();
      }
    }

    async function dispatchVerifierAgentFormFromCenter() {
      const targetEl = document.getElementById('verifyDispatchTargetUser');
      const reasonEl = document.getElementById('verifyDispatchReason');
      const targetUser = (targetEl ? targetEl.value.trim() : '') || (localStorage.getItem('tincan_username') || '').trim();
      const reason = (reasonEl ? reasonEl.value.trim() : '') || 'Mandatory Cyberspace Identity Verification';
      try {
        const res = await fetch('/api/verify/send', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username: targetUser,
            reason
          })
        });
        const data = await res.json();
        playXpChime();
        spawnPacketFlight('@verifier-agent', targetUser || myPeerId, 'verification_form', '🛡️ Verify Form');
        prefillVerificationFormFromSignal(data);
      } catch (e) {}
    }

    async function submitCyberspaceVerificationForm() {
      const fullName = (document.getElementById('verifyFormFullName')?.value || '').trim();
      const username = (document.getElementById('verifyFormUsername')?.value || '').trim().replace(/^@/, '');
      const email = (document.getElementById('verifyFormEmail')?.value || '').trim();
      const phone = (document.getElementById('verifyFormPhone')?.value || '').trim();
      const role = (document.getElementById('verifyFormRole')?.value || 'Researcher / Student').trim();
      const bio = (document.getElementById('verifyFormBio')?.value || '').trim();
      const challengeCode = (document.getElementById('verifyFormChallengeCode')?.value || '').trim();
      const requestId = (document.getElementById('verifyFormRequestId')?.value || '').trim();
      const consent = Boolean(document.getElementById('verifyFormConsent')?.checked);
      const statusBox = document.getElementById('verifyFormStatusMsg');

      const showStatus = (msg, isErr = false) => {
        if (!statusBox) return;
        statusBox.classList.remove('hidden');
        statusBox.className = isErr
          ? 'p-2.5 rounded-lg text-xs bg-red-950/80 border border-red-600 text-red-200 font-mono'
          : 'p-2.5 rounded-lg text-xs bg-emerald-950/80 border border-emerald-500 text-emerald-200 font-mono';
        statusBox.innerHTML = msg;
      };

      try {
        const res = await fetch('/api/verify/submit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            full_name: fullName,
            username,
            email,
            phone_number: phone,
            role,
            bio,
            challenge_code: challengeCode || undefined,
            request_id: requestId || undefined,
            consent_pii: consent
          })
        });
        const data = await res.json();
        if (!res.ok) {
          showStatus(`⚠️ Verification Error: ${escapeHtml(data.error || 'Could not verify identity')}`, true);
          return;
        }
        localStorage.setItem('tincan_registration_epoch', REGISTRATION_EPOCH);
        localStorage.setItem('tincan_fullname', fullName);
        localStorage.setItem('tincan_username', username);
        localStorage.setItem('tincan_email', email);
        localStorage.setItem('tincan_phone', phone);
        localStorage.setItem('tincan_role', role);
        localStorage.setItem('tincan_consent_pii', 'true');
        const hudName = document.getElementById('hudAccountName');
        if (hudName) hudName.innerText = '@' + username;

        playXpChime();
        spawnPacketFlight(myPeerId, '@verifier-agent', 'verified', '✅ Attested');
        showStatus(`✅ <strong>Identity Verified &amp; Attested by @verifier-agent!</strong> Citizen Handle: <code>@${escapeHtml(username)}</code> · SHA-256 Attestation: <code>${escapeHtml(data.attestation_hash || '')}</code>`, false);
        await refreshBoardVerificationBadge();
        await loadBoardDynamicRoster();
        await loadVerificationCenterData();
        await loadCyberspaceBoard();
      } catch (err) {
        showStatus(`⚠️ Network error: ${escapeHtml(err.message)}`, true);
      }
    }

    async function loadVerificationCenterData() {
      try {
        const res = await fetch('/api/verify/list');
        if (!res.ok) return;
        const data = await res.json();
        const pendingEl = document.getElementById('verifyPendingList');
        const citizensEl = document.getElementById('verifyCitizensList');
        const countEl = document.getElementById('verifyCitizensCount');
        const badgeEl = document.getElementById('boardPendingVerifyCount');

        const reqs = (data.requests || []).filter(r => r.status === 'pending');
        if (badgeEl) badgeEl.innerText = String(reqs.length);

        if (pendingEl) {
          if (!reqs.length) {
            pendingEl.innerHTML = '<div class="text-slate-500 text-[11px] py-2">No pending verification forms. Click "Dispatch Form via @verifier-agent" above to generate a fresh challenge form.</div>';
          } else {
            pendingEl.innerHTML = reqs.map(r => `
              <div class="p-2 bg-slate-900 rounded border border-amber-800/60 flex items-center justify-between gap-2">
                <div>
                  <div class="text-amber-300 font-bold">#${escapeHtml(r.request_id)} · Challenge: <code>${escapeHtml(r.challenge_code || '')}</code></div>
                  <div class="text-[10px] text-slate-400">Target: ${escapeHtml(r.target_username || r.peer_id)} · ${escapeHtml(r.reason || '')}</div>
                </div>
                <button type="button" onclick='prefillVerificationFormFromSignal(${JSON.stringify({request_id: r.request_id, challenge_code: r.challenge_code, target_username: r.target_username})})' class="px-2 py-1 rounded bg-amber-500 text-slate-950 font-bold text-[10px] shrink-0">
                  ✍️ Load Form
                </button>
              </div>
            `).join('');
          }
        }

        const citizens = data.verified_citizens || [];
        if (countEl) countEl.innerText = `${citizens.length} verified`;
        if (citizensEl) {
          if (!citizens.length) {
            citizensEl.innerHTML = '<div class="text-slate-500 text-[11px] py-2">No verified citizens yet.</div>';
          } else {
            citizensEl.innerHTML = citizens.map(c => `
              <div onclick="inspectCyberspaceUserProfile('${escapeHtml(c.username)}')" class="cursor-pointer p-2 bg-slate-900 hover:bg-slate-800 rounded border border-emerald-900/60 flex items-center justify-between gap-2 transition">
                <div>
                  <div class="text-emerald-300 font-bold">✅ @${escapeHtml(c.username)} <span class="text-slate-400 font-normal">(${escapeHtml(c.full_name)})</span></div>
                  <div class="text-[10px] text-slate-400">${escapeHtml(c.role || 'Citizen')} · ${escapeHtml(c.bio || '')}</div>
                </div>
                <span class="px-1.5 py-0.5 rounded bg-slate-950 text-cyan-300 border border-slate-800 text-[9px]">SHA256:${escapeHtml((c.attestation_hash || '').slice(0, 10))}</span>
              </div>
            `).join('');
          }
        }
      } catch (e) {}
    }

    async function loadCyberspaceBoard() {
      refreshBoardVerificationBadge();
      loadBoardDynamicRoster();
      try {
        const sortBy = document.getElementById('boardSortSelect')?.value || 'hot';
        const verifiedOnly = document.getElementById('boardVerifiedOnlyToggle')?.checked ? '1' : '0';
        const catParam = activeBoardCategoryFilter ? `&category=${encodeURIComponent(activeBoardCategoryFilter)}` : '';
        const res = await fetch(`/api/board/topics?limit=40&sort_by=${encodeURIComponent(sortBy)}&verified_only=${verifiedOnly}${catParam}`);
        if (!res.ok) return;
        const data = await res.json();
        const gBadge = document.getElementById('boardGraphStatsBadge');
        if (gBadge && data.graph_stats) {
          gBadge.innerText = `Graph: ${data.graph_stats.total_nodes || 0} nodes · ${data.graph_stats.total_edges || 0} edges`;
        }
        renderCyberspaceTopics(data.topics || [], false);
      } catch (e) {}
    }

    async function searchCyberspaceBoard() {
      const inp = document.getElementById('boardSearchInput');
      const modeSel = document.getElementById('boardSearchMode');
      const q = inp ? inp.value.trim() : '';
      const mode = modeSel ? modeSel.value : 'hybrid';
      if (!q) {
        resetCyberspaceSearch();
        return;
      }
      try {
        const res = await fetch(`/api/board/search?q=${encodeURIComponent(q)}&mode=${encodeURIComponent(mode)}&top_k=15`);
        if (!res.ok) return;
        const data = await res.json();
        const synBox = document.getElementById('boardSynthesisBox');
        const synText = document.getElementById('boardSynthesisText');
        const subEntities = document.getElementById('boardSubgraphEntities');
        if (synBox && synText) {
          synBox.classList.remove('hidden');
          synText.innerHTML = `<strong>${escapeHtml(data.synthesis || '')}</strong>`;
          const nodes = (data.subgraph && data.subgraph.nodes) || [];
          if (subEntities) {
            subEntities.innerHTML = nodes.slice(0, 14).map(n => {
              const badgeTone = n.type === 'agent' ? 'bg-indigo-950 text-indigo-300 border-indigo-700' :
                                n.type === 'user' ? 'bg-cyan-950 text-cyan-300 border-cyan-700' :
                                n.type === 'tag' ? 'bg-pink-950/70 text-pink-300 border-pink-800' :
                                'bg-slate-800 text-slate-300 border-slate-700';
              return `<span onclick="quickSearchBoardEntity('${escapeHtml(n.label)}')" class="cursor-pointer px-1.5 py-0.5 rounded border text-[10px] ${badgeTone}">${escapeHtml(n.type)}: ${escapeHtml(n.label)} (PPR:${Number(n.ppr_score || 0).toFixed(3)})</span>`;
            }).join('');
          }
        }
        renderCyberspaceTopics(data.results || [], true);
        playXpChime();
      } catch (e) {}
    }

    function resetCyberspaceSearch() {
      const inp = document.getElementById('boardSearchInput');
      if (inp) inp.value = '';
      const synBox = document.getElementById('boardSynthesisBox');
      if (synBox) synBox.classList.add('hidden');
      loadCyberspaceBoard();
    }

    async function voteCyberspaceItem(targetType, targetId, direction) {
      try {
        const res = await fetch('/api/board/vote', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            target_type: targetType,
            target_id: targetId,
            peer_id: myPeerId,
            direction
          })
        });
        if (res.ok) {
          playXpChime();
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function markAcceptedSolution(topicId, postId) {
      try {
        const res = await fetch('/api/board/solution', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            post_id: postId,
            peer_id: myPeerId
          })
        });
        if (res.ok) {
          activeBoardTopicId = topicId;
          playXpChime();
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function togglePinTopic(topicId, currentPinned) {
      try {
        const res = await fetch('/api/board/topic/update', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            peer_id: myPeerId,
            pinned: !currentPinned
          })
        });
        if (res.ok) {
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function deleteCyberspaceTopic(topicId) {
      if (!window.confirm('Delete this topic from the Cyberspace Knowledge Base?')) return;
      try {
        const res = await fetch('/api/board/topic/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ topic_id: topicId, peer_id: myPeerId })
        });
        if (res.ok) {
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    async function deleteCyberspacePost(topicId, postId) {
      try {
        const res = await fetch('/api/board/post/delete', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ post_id: postId, peer_id: myPeerId })
        });
        if (res.ok) {
          activeBoardTopicId = topicId;
          await loadCyberspaceBoard();
        }
      } catch (e) {}
    }

    function setReplyToNestedPost(topicId, postId, authorHandle) {
      activeReplyParentPostByTopic[topicId] = postId;
      const indicator = document.getElementById(`replyParentBanner-${topicId}`);
      const inp = document.getElementById(`replyInput-${topicId}`);
      if (indicator) {
        indicator.classList.remove('hidden');
        indicator.innerHTML = `<span>↪ Replying to post <code>#${escapeHtml(postId)}</code> (@${escapeHtml(authorHandle)})</span> <button type="button" onclick="clearReplyToNestedPost('${topicId}')" class="text-red-300 hover:underline ml-2">✕ Cancel</button>`;
      }
      if (inp) {
        if (!inp.value.includes(`@${authorHandle}`)) {
          inp.value = `@${authorHandle} ` + inp.value;
        }
        inp.focus();
      }
    }

    function clearReplyToNestedPost(topicId) {
      delete activeReplyParentPostByTopic[topicId];
      const indicator = document.getElementById(`replyParentBanner-${topicId}`);
      if (indicator) indicator.classList.add('hidden');
    }

    function renderCyberspaceTopics(topics, isSearchResult = false) {
      const feed = document.getElementById('boardTopicsFeed');
      if (!feed) return;
      if (!topics.length) {
        feed.innerHTML = '<div class="p-4 bg-slate-900/60 rounded-xl border border-slate-800 text-center text-slate-400 font-mono">No matching Cyberspace topics found. Start a new topic above!</div>';
        return;
      }

      const myUn = (localStorage.getItem('tincan_username') || '').toLowerCase();

      feed.innerHTML = topics.map(t => {
        const author = (t.author_username || 'peer').replace(/^@/, '');
        const posts = t.posts || [];
        const isExpanded = activeBoardTopicId === t.topic_id || isSearchResult;
        const canModifyTopic = isAdmin || t.author_peer_id === myPeerId || (myUn && author.toLowerCase() === myUn);

        const scoreBadges = (t.bm25_score !== undefined || t.graphrag_score !== undefined) ? `
          <div class="flex flex-wrap items-center gap-1 font-mono text-[10px]">
            <span class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700">Hybrid: ${Number(t.score || 0).toFixed(3)}</span>
            <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">BM25: ${Number(t.bm25_score || 0).toFixed(3)}</span>
            <span class="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700">GraphRAG: ${Number(t.graphrag_score || 0).toFixed(3)}</span>
          </div>
        ` : '';

        const snippetHtml = t.highlighted_snippet ? `
          <div class="p-2 bg-emerald-950/30 border border-emerald-800/50 rounded text-[11px] text-slate-300 font-mono">
            <span class="text-emerald-300 font-bold">📚 BM25 Context Match:</span> ${t.highlighted_snippet}
          </div>
        ` : '';

        const graphPathsHtml = (t.graph_paths && t.graph_paths.length) ? `
          <div class="mt-1 p-2 bg-slate-950/90 rounded border border-indigo-900/60 font-mono text-[10px] text-indigo-300">
            <span class="font-bold text-cyan-300">🕸️ GraphRAG Traversal Paths:</span> ${t.graph_paths.map(p => escapeHtml(p)).join(' · ')}
          </div>
        ` : '';

        const tagsHtml = (t.tags || []).map(tag =>
          `<span onclick="quickSearchBoardEntity('#${escapeHtml(tag)}')" class="cursor-pointer px-1.5 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-pink-300 border border-slate-700 font-mono text-[10px]">#${escapeHtml(tag)}</span>`
        ).join('');

        // Organize posts with nested indentation for parent_post_id
        const postMap = {};
        posts.forEach(p => { postMap[p.post_id] = p; });

        const postsHtml = posts.map(p => {
          const pAuthor = (p.author_username || 'peer').replace(/^@/, '');
          const isAgent = Boolean(p.is_agent);
          const isAccepted = Boolean(p.is_accepted);
          const parentPost = p.parent_post_id ? postMap[p.parent_post_id] : null;
          const indentCls = p.parent_post_id ? 'ml-5 border-l-2 border-l-cyan-700/60' : '';
          const canDeletePost = isAdmin || p.author_peer_id === myPeerId || (myUn && pAuthor.toLowerCase() === myUn);

          return `
            <div class="p-2.5 rounded-lg border ${indentCls} ${isAccepted ? 'bg-emerald-950/40 border-emerald-500/70' : (isAgent ? 'bg-indigo-950/40 border-indigo-700/60' : 'bg-slate-950/80 border-slate-800')} space-y-1.5">
              <div class="flex flex-wrap items-center justify-between gap-1 font-mono text-[10px]">
                <div class="flex items-center gap-1.5 flex-wrap">
                  <span onclick="${isAgent ? `quickSearchBoardEntity('@${escapeHtml(pAuthor)}')` : `inspectCyberspaceUserProfile('${escapeHtml(pAuthor)}')`}" class="cursor-pointer font-bold ${isAgent ? 'text-indigo-300' : 'text-cyan-300'} hover:underline">
                    ${isAgent ? '🤖' : '✅'} @${escapeHtml(pAuthor)}
                  </span>
                  ${parentPost ? `<span class="text-slate-500">↪ in reply to @${escapeHtml((parentPost.author_username || 'peer').replace(/^@/, ''))}</span>` : ''}
                  ${isAccepted ? '<span class="px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/50 font-bold">✅ Accepted Solution</span>' : ''}
                </div>
                <div class="flex items-center gap-1.5">
                  <button type="button" onclick="voteCyberspaceItem('post', '${p.post_id}', 'up')" class="px-1.5 py-0.2 rounded bg-slate-900 hover:bg-slate-800 text-emerald-300 border border-slate-700">▲ ${Number(p.upvotes || 0)}</button>
                  <button type="button" onclick="setReplyToNestedPost('${t.topic_id}', '${p.post_id}', '${escapeHtml(pAuthor)}')" class="px-1.5 py-0.2 rounded bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-slate-700">↪ Reply</button>
                  ${!isAccepted ? `<button type="button" onclick="markAcceptedSolution('${t.topic_id}', '${p.post_id}')" class="px-1.5 py-0.2 rounded bg-slate-900 hover:bg-emerald-950 text-slate-400 hover:text-emerald-300 border border-slate-800" title="Mark as Accepted Solution">✓ Solution</button>` : ''}
                  ${canDeletePost ? `<button type="button" onclick="deleteCyberspacePost('${t.topic_id}', '${p.post_id}')" class="px-1 py-0.2 rounded text-red-400 hover:bg-red-950">🗑️</button>` : ''}
                  <span class="text-slate-500">${p.created_at ? new Date(p.created_at * 1000).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : ''}</span>
                </div>
              </div>
              <div class="text-slate-200 text-xs leading-relaxed">${formatBoardMentions(p.body)}</div>
            </div>
          `;
        }).join('');

        return `
          <div class="p-3.5 bg-slate-900/90 rounded-xl border ${t.pinned ? 'border-amber-500/50' : (t.resolved ? 'border-emerald-500/50' : 'border-slate-800')} hover:border-indigo-500/50 transition space-y-2.5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5">
              <div class="flex items-center gap-1.5 flex-wrap">
                ${t.pinned ? '<span class="px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono text-[10px] font-bold">📌 PINNED</span>' : ''}
                ${t.resolved ? '<span class="px-1.5 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 font-mono text-[10px] font-bold">✅ SOLVED</span>' : ''}
                <span onclick="setBoardCategoryFilter('${escapeHtml(t.category || 'cyberspace')}')" class="cursor-pointer px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800 font-mono text-[10px] uppercase font-bold">#${escapeHtml(t.category || 'cyberspace')}</span>
                <h4 onclick="toggleBoardTopicThread('${t.topic_id}')" class="cursor-pointer font-bold text-white text-sm hover:text-cyan-300 transition">${escapeHtml(t.title)}</h4>
              </div>
              <div class="flex items-center gap-1.5 font-mono text-[10px]">
                ${scoreBadges}
                <div class="flex items-center bg-slate-950 rounded-lg border border-slate-800 px-1.5 py-0.5 gap-1">
                  <button type="button" onclick="voteCyberspaceItem('topic', '${t.topic_id}', 'up')" class="text-emerald-400 hover:text-emerald-300 font-bold" title="Upvote Topic">▲</button>
                  <span class="text-white font-bold">${Number(t.upvotes || 0)}</span>
                  <button type="button" onclick="voteCyberspaceItem('topic', '${t.topic_id}', 'down')" class="text-slate-500 hover:text-rose-400" title="Downvote Topic">▼</button>
                </div>
              </div>
            </div>

            <div class="text-slate-200 text-xs leading-relaxed">${formatBoardMentions(t.body)}</div>

            ${snippetHtml}

            <div class="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-800/80">
              <div class="flex flex-wrap items-center gap-1.5">
                <span onclick="inspectCyberspaceUserProfile('${escapeHtml(author)}')" class="cursor-pointer font-mono text-[10px] ${t.author_verified ? 'text-emerald-400' : 'text-amber-300'} font-semibold hover:underline">
                  ${t.author_verified ? '✅' : '⚠️'} @${escapeHtml(author)}
                </span>
                <span class="text-slate-600">·</span>
                <span class="font-mono text-[10px] text-slate-400">👁️ ${Number(t.views || 1)} views</span>
                <span class="text-slate-600">·</span>
                ${tagsHtml}
              </div>
              <div class="flex items-center gap-1.5 font-mono text-[10px]">
                <button type="button" onclick="togglePinTopic('${t.topic_id}', ${Boolean(t.pinned)})" class="px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-amber-300 border border-slate-700" title="Pin/Unpin Topic">📌 ${t.pinned ? 'Unpin' : 'Pin'}</button>
                ${canModifyTopic ? `<button type="button" onclick="deleteCyberspaceTopic('${t.topic_id}')" class="px-2 py-0.5 rounded bg-red-950/60 hover:bg-red-900 text-red-300 border border-red-800/60" title="Delete Topic">🗑️</button>` : ''}
                <button type="button" onclick="toggleBoardTopicThread('${t.topic_id}')" class="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-cyan-300 font-bold border border-slate-700">
                  💬 ${posts.length} Repl${posts.length === 1 ? 'y' : 'ies'} / Thread
                </button>
              </div>
            </div>

            ${graphPathsHtml}

            <div id="boardThread-${t.topic_id}" class="${isExpanded ? '' : 'hidden'} pt-2 space-y-2 border-t border-slate-800">
              <div class="space-y-2">${postsHtml || '<div class="text-slate-500 font-mono text-[11px]">No replies yet. Tag an @username or @gemini-brain below!</div>'}</div>
              <div id="replyParentBanner-${t.topic_id}" class="hidden px-2.5 py-1 rounded bg-cyan-950/70 border border-cyan-700 text-cyan-200 font-mono text-[10px] flex items-center justify-between"></div>
              <div class="flex flex-wrap gap-1 pt-1 font-mono text-[10px]">
                <button type="button" onclick="insertBoardSelfTag('replyInput-${t.topic_id}')" class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">🙋 @Me</button>
                <button type="button" onclick="insertBoardTag('@gemini-brain', 'replyInput-${t.topic_id}')" class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">🤖 @gemini-brain</button>
                <button type="button" onclick="insertBoardTag('@claude-brain', 'replyInput-${t.topic_id}')" class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">🤖 @claude-brain</button>
                <button type="button" onclick="insertBoardTag('@openai-brain', 'replyInput-${t.topic_id}')" class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">🤖 @openai-brain</button>
                <button type="button" onclick="insertBoardTag('@verifier-agent', 'replyInput-${t.topic_id}')" class="px-1.5 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800">🛡️ @verifier-agent</button>
              </div>
              <div class="flex gap-2">
                <input id="replyInput-${t.topic_id}" type="text" placeholder="Reply with @username, @gemini-brain, @verifier-agent, or #tags..." onkeydown="if(event.key==='Enter') replyCyberspaceTopic('${t.topic_id}')" class="flex-1 px-3 py-1.5 rounded-lg bg-slate-950 border border-slate-700 text-white font-mono text-xs focus:border-cyan-400 focus:outline-none" />
                <button type="button" onclick="replyCyberspaceTopic('${t.topic_id}')" class="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs">
                  Reply
                </button>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    function toggleBoardTopicThread(topicId) {
      activeBoardTopicId = (activeBoardTopicId === topicId) ? null : topicId;
      const el = document.getElementById(`boardThread-${topicId}`);
      if (el) el.classList.toggle('hidden');
    }

    async function createCyberspaceTopic() {
      if (!requireVerifiedIdentity('create a topic on the Cyberspace Knowledge Board')) {
        requestAgentVerificationForm();
        return;
      }
      const titleEl = document.getElementById('boardTopicTitle');
      const catEl = document.getElementById('boardTopicCategory');
      const tagsEl = document.getElementById('boardTopicTags');
      const bodyEl = document.getElementById('boardTopicBody');
      const title = titleEl ? titleEl.value.trim() : '';
      const category = catEl ? catEl.value.trim() || 'cyberspace' : 'cyberspace';
      const tags = tagsEl ? tagsEl.value.trim() : '';
      const body = bodyEl ? bodyEl.value.trim() : '';
      if (!title || !body) {
        alert('Please enter both a Topic Title and Post Body.');
        return;
      }
      const username = (localStorage.getItem('tincan_username') || '').trim();
      try {
        const res = await fetch('/api/board/topics', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            peer_id: myPeerId,
            username,
            title,
            category,
            tags,
            body,
            auto_agent_reply: true
          })
        });
        const data = await res.json();
        if (res.status === 403 && data.require_verification) {
          requestAgentVerificationForm();
          return;
        }
        if (res.ok && data.topic) {
          if (titleEl) titleEl.value = '';
          if (tagsEl) tagsEl.value = '';
          if (bodyEl) bodyEl.value = '';
          activeBoardTopicId = data.topic.topic_id;
          playXpChime();
          spawnPacketFlight(myPeerId, 'relay', 'cyberspace_topic', `#${category}`);
          await loadCyberspaceBoard();
        } else {
          alert('Could not create topic: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Failed to post topic: ' + err.message);
      }
    }

    async function replyCyberspaceTopic(topicId) {
      if (!requireVerifiedIdentity('reply on the Cyberspace Knowledge Board')) {
        requestAgentVerificationForm();
        return;
      }
      const inp = document.getElementById(`replyInput-${topicId}`);
      const body = inp ? inp.value.trim() : '';
      if (!body) return;
      const username = (localStorage.getItem('tincan_username') || '').trim();
      const parentPostId = activeReplyParentPostByTopic[topicId] || '';
      try {
        const res = await fetch('/api/board/reply', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            topic_id: topicId,
            peer_id: myPeerId,
            username,
            body,
            parent_post_id: parentPostId,
            auto_agent_reply: true
          })
        });
        const data = await res.json();
        if (res.status === 403 && data.require_verification) {
          requestAgentVerificationForm();
          return;
        }
        if (res.ok) {
          if (inp) inp.value = '';
          clearReplyToNestedPost(topicId);
          activeBoardTopicId = topicId;
          playXpChime();
          spawnPacketFlight(myPeerId, 'relay', 'cyberspace_reply', '💬 Board Reply');
          await loadCyberspaceBoard();
        } else {
          alert('Reply error: ' + (data.error || 'Unknown error'));
        }
      } catch (err) {
        alert('Reply failed: ' + err.message);
      }
    }

    // =========================================================================
    // Tab 2: GraphRAG + Okapi BM25 IR Diagnostics Lab
    // =========================================================================
    async function runIrLabSearch() {
      const q = (document.getElementById('boardLabSearchInput')?.value || '').trim();
      const mode = document.getElementById('boardLabSearchMode')?.value || 'hybrid';
      if (!q) return;
      try {
        const res = await fetch(`/api/board/search?q=${encodeURIComponent(q)}&mode=${encodeURIComponent(mode)}&top_k=12`);
        if (!res.ok) return;
        const data = await res.json();
        const diag = data.bm25_diagnostics || {};
        const paramsEl = document.getElementById('bm25CorpusParams');
        const tbody = document.getElementById('bm25TermTableBody');
        const synEl = document.getElementById('irLabSynthesisBox');
        const seedsEl = document.getElementById('irLabSeedBadges');
        const subStatsEl = document.getElementById('graphragSubgraphStats');
        const listEl = document.getElementById('irLabResultsList');

        if (paramsEl) {
          paramsEl.innerText = `N=${diag.corpus_size || 0} docs · avgdl=${diag.avg_doc_length || 0} · k1=${diag.k1 || 1.5} · b=${diag.b || 0.75}`;
        }
        if (tbody) {
          const terms = diag.query_terms || [];
          if (!terms.length) {
            tbody.innerHTML = '<tr><td colspan="3" class="py-2 text-slate-500 text-center">No lexical tokens parsed.</td></tr>';
          } else {
            tbody.innerHTML = terms.map(t => `
              <tr>
                <td class="py-1 text-cyan-300 font-bold">${escapeHtml(t.term)}</td>
                <td class="py-1 text-slate-300">${Number(t.df || 0)} / ${Number(diag.corpus_size || 0)}</td>
                <td class="py-1 text-right text-emerald-400 font-bold">${Number(t.idf || 0).toFixed(4)}</td>
              </tr>
            `).join('');
          }
        }
        if (synEl) {
          synEl.innerHTML = escapeHtml(data.synthesis || '');
        }
        const sub = data.subgraph || {};
        if (subStatsEl) {
          subStatsEl.innerText = `PPR α=0.85 · ${(sub.nodes || []).length} active nodes · ${(sub.edges || []).length} edges`;
        }
        if (seedsEl) {
          seedsEl.innerHTML = (sub.seed_entities || []).map(s =>
            `<span class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 text-[10px]">Seed: ${escapeHtml(s)}</span>`
          ).join('');
        }
        if (listEl) {
          const results = data.results || [];
          listEl.innerHTML = results.map((r, idx) => `
            <div class="p-3 bg-slate-950/90 rounded-lg border border-slate-800 space-y-1.5">
              <div class="flex flex-wrap items-center justify-between gap-2">
                <span onclick="activeBoardTopicId='${r.topic_id}'; switchBoardTab('discussions');" class="cursor-pointer font-bold text-white hover:text-cyan-300 text-xs">#${idx + 1} · ${escapeHtml(r.title)} <span class="text-slate-400 font-normal">(@${escapeHtml((r.author_username || '').replace(/^@/, ''))})</span></span>
                <div class="flex items-center gap-1.5 text-[10px]">
                  <span class="px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700">Hybrid: ${Number(r.score || 0).toFixed(4)}</span>
                  <span class="px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-700">BM25: ${Number(r.bm25_score || 0).toFixed(4)} (raw ${Number(r.bm25_raw || 0).toFixed(2)})</span>
                  <span class="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700">GraphRAG PPR: ${Number(r.graphrag_score || 0).toFixed(4)}</span>
                </div>
              </div>
              <div class="text-[11px] text-slate-300">${r.highlighted_snippet || escapeHtml(r.body || '')}</div>
              ${(r.graph_paths && r.graph_paths.length) ? `<div class="text-[10px] text-cyan-300">🕸️ Paths: ${r.graph_paths.map(p => escapeHtml(p)).join(' · ')}</div>` : ''}
            </div>
          `).join('');
        }
      } catch (e) {}
    }

    // =========================================================================
    // Tab 3: Interactive HTML5 Canvas Knowledge Graph & Shortest-Path Finder
    // =========================================================================
    async function loadAndDrawBoardGraph() {
      try {
        const res = await fetch('/api/board/graph');
        if (!res.ok) return;
        boardGraphSnapshot = await res.json();
        layoutBoardGraphNodes();
        drawBoardGraphCanvas();
      } catch (e) {}
    }

    function layoutBoardGraphNodes() {
      const canvas = document.getElementById('boardGraphCanvas');
      const w = canvas ? canvas.width : 860;
      const h = canvas ? canvas.height : 380;
      const nodes = (boardGraphSnapshot.nodes || []).slice(0, 48);
      const edges = boardGraphSnapshot.edges || [];

      boardGraphLayoutNodes = nodes.map((n, i) => {
        const angle = (2 * Math.PI * i) / Math.max(1, nodes.length);
        const radius = n.type === 'topic' ? 85 : (n.type === 'agent' ? 135 : 155);
        return {
          ...n,
          x: w / 2 + Math.cos(angle) * radius * (1.2 + (i % 3) * 0.18),
          y: h / 2 + Math.sin(angle) * (radius * 0.82),
          vx: 0,
          vy: 0
        };
      });

      const idMap = {};
      boardGraphLayoutNodes.forEach(n => { idMap[n.id] = n; });

      // Run 45 iterations of force-directed relaxation
      for (let iter = 0; iter < 45; iter++) {
        for (let i = 0; i < boardGraphLayoutNodes.length; i++) {
          for (let j = i + 1; j < boardGraphLayoutNodes.length; j++) {
            const a = boardGraphLayoutNodes[i];
            const b = boardGraphLayoutNodes[j];
            let dx = b.x - a.x;
            let dy = b.y - a.y;
            let distSq = dx * dx + dy * dy + 1;
            let force = 1600 / distSq;
            let dist = Math.sqrt(distSq);
            a.vx -= (dx / dist) * force;
            a.vy -= (dy / dist) * force;
            b.vx += (dx / dist) * force;
            b.vy += (dy / dist) * force;
          }
        }
        edges.forEach(e => {
          const s = idMap[e.source];
          const t = idMap[e.target];
          if (!s || !t) return;
          const dx = t.x - s.x;
          const dy = t.y - s.y;
          const dist = Math.sqrt(dx * dx + dy * dy) || 1;
          const spring = (dist - 95) * 0.025;
          s.vx += (dx / dist) * spring;
          s.vy += (dy / dist) * spring;
          t.vx -= (dx / dist) * spring;
          t.vy -= (dy / dist) * spring;
        });
        boardGraphLayoutNodes.forEach(n => {
          n.vx += (w / 2 - n.x) * 0.015;
          n.vy += (h / 2 - n.y) * 0.015;
          n.x = Math.max(48, Math.min(w - 48, n.x + n.vx * 0.25));
          n.y = Math.max(28, Math.min(h - 38, n.y + n.vy * 0.25));
          n.vx *= 0.6;
          n.vy *= 0.6;
        });
      }
    }

    function drawBoardGraphCanvas() {
      const canvas = document.getElementById('boardGraphCanvas');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      const w = canvas.width;
      const h = canvas.height;
      ctx.clearRect(0, 0, w, h);

      const idMap = {};
      boardGraphLayoutNodes.forEach(n => { idMap[n.id] = n; });

      // Draw edges
      (boardGraphSnapshot.edges || []).forEach(e => {
        const s = idMap[e.source];
        const t = idMap[e.target];
        if (!s || !t) return;
        const isHighlighted = selectedGraphNodeId && (e.source === selectedGraphNodeId || e.target === selectedGraphNodeId);
        ctx.beginPath();
        ctx.moveTo(s.x, s.y);
        ctx.lineTo(t.x, t.y);
        ctx.strokeStyle = isHighlighted ? 'rgba(34, 211, 238, 0.85)' : 'rgba(100, 116, 139, 0.28)';
        ctx.lineWidth = isHighlighted ? 2.0 : 1.0;
        ctx.stroke();
      });

      // Draw nodes
      boardGraphLayoutNodes.forEach(n => {
        const color = n.type === 'topic' ? '#6366f1' :
                      n.type === 'user' ? '#10b981' :
                      n.type === 'agent' ? '#f59e0b' :
                      n.type === 'tag' ? '#ec4899' : '#38bdf8';
        const r = n.id === selectedGraphNodeId ? 10 : Math.min(9, 5 + Math.sqrt(n.degree || 1));
        ctx.beginPath();
        ctx.arc(n.x, n.y, r, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = n.id === selectedGraphNodeId ? 2.5 : 1.2;
        ctx.strokeStyle = n.id === selectedGraphNodeId ? '#ffffff' : '#0f172a';
        ctx.stroke();

        ctx.font = '10px ui-monospace, SFMono-Regular, Menlo, monospace';
        ctx.fillStyle = '#e2e8f0';
        const lbl = (n.label || n.id).slice(0, 22);
        ctx.fillText(lbl, n.x + r + 4, n.y + 3);
      });
    }

    (function initBoardGraphCanvasInteraction() {
      setTimeout(() => {
        const canvas = document.getElementById('boardGraphCanvas');
        if (!canvas) return;
        canvas.addEventListener('click', (ev) => {
          const rect = canvas.getBoundingClientRect();
          const scaleX = canvas.width / rect.width;
          const scaleY = canvas.height / rect.height;
          const mx = (ev.clientX - rect.left) * scaleX;
          const my = (ev.clientY - rect.top) * scaleY;
          let clicked = null;
          for (const n of boardGraphLayoutNodes) {
            const dx = mx - n.x;
            const dy = my - n.y;
            if (dx * dx + dy * dy <= 144) {
              clicked = n;
              break;
            }
          }
          if (clicked) {
            selectedGraphNodeId = clicked.id;
            drawBoardGraphCanvas();
            const insp = document.getElementById('boardGraphNodeInspector');
            if (insp) {
              const neighbors = (boardGraphSnapshot.edges || [])
                .filter(e => e.source === clicked.id || e.target === clicked.id)
                .map(e => `${e.relation} → ${e.source === clicked.id ? e.target : e.source}`);
              insp.innerHTML = `
                <div><strong class="text-cyan-300">${escapeHtml(clicked.type.toUpperCase())}: ${escapeHtml(clicked.label)}</strong> · Degree: ${clicked.degree || 0} · Connections: ${escapeHtml(neighbors.slice(0, 5).join(', '))}</div>
                <button type="button" onclick="quickSearchBoardEntity('${escapeHtml(clicked.label)}')" class="px-2 py-0.5 rounded bg-indigo-600 text-white font-bold text-[10px]">🔍 Search Node in Board</button>
              `;
            }
          }
        });
      }, 400);
    })();

    async function findCyberspaceEntityPath() {
      const src = (document.getElementById('graphPathSource')?.value || '').trim();
      const dst = (document.getElementById('graphPathTarget')?.value || '').trim();
      const out = document.getElementById('graphPathOutput');
      if (!src || !dst || !out) return;
      try {
        const res = await fetch(`/api/board/graph/path?from=${encodeURIComponent(src)}&to=${encodeURIComponent(dst)}`);
        const data = await res.json();
        out.classList.remove('hidden');
        if (data.found) {
          out.innerHTML = `✅ <strong>Shortest Path (${data.hops} hop${data.hops === 1 ? '' : 's'}):</strong> <code>${escapeHtml(data.formatted_path)}</code>`;
        } else {
          out.innerHTML = `⚠️ ${escapeHtml(data.message || 'No path found between those entities.')}`;
        }
      } catch (e) {}
    }

    // Init Playlist, Sponsors, Cyberspace Board & Analytics (Visibility-Aware Polling)
    loadPlaylist(false).then(() => renderAdminCrudTables());
    loadSponsorsData();
    loadCyberspaceBoard();
    loadAnalytics(true);
    if (isAdmin) {
      const bBtn = document.getElementById('billingAdminSponsorBtn');
      if (bBtn) bBtn.classList.remove('hidden');
    }
    setInterval(() => loadAnalytics(false), 15000);
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden) {
        pollMeshState(true);
        pollSignals(true);
        loadAnalytics(true);
        loadSponsorsData();
      }
    });
  </script>

  <!-- Modal: Admin Edit Video -->
  <div id="adminEditVideoModal" class="hidden fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-pink-700 rounded-xl max-w-md w-full p-4 space-y-3 font-mono text-xs shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-pink-300 text-sm flex items-center gap-1.5"><span>✏️</span> Edit Relay Video</span>
        <button onclick="closeEditVideoModal()" class="text-slate-400 hover:text-white text-base">✕</button>
      </div>
      <input type="hidden" id="editVideoId">
      <div class="space-y-2">
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Title</label>
          <input type="text" id="editVideoTitle" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Creator Handle</label>
          <input type="text" id="editVideoCreator" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Category</label>
            <select id="editVideoCategory" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
              <option value="spotlight">spotlight</option>
              <option value="instruction">instruction</option>
              <option value="ad">ad (sponsored)</option>
            </select>
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Duration (Seconds)</label>
            <input type="number" id="editVideoDuration" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Embed Stream URL</label>
          <input type="text" id="editVideoEmbedUrl" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
      </div>
      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick="closeEditVideoModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">Cancel</button>
        <button onclick="adminSubmitSaveVideoEdit()" class="px-4 py-1.5 bg-pink-600 hover:bg-pink-500 text-white font-bold rounded">Save Changes</button>
      </div>
    </div>
  </div>

  <!-- Modal: Admin Edit Sponsor -->
  <div id="adminEditSponsorModal" class="hidden fixed inset-0 z-[120] bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
    <div class="bg-slate-900 border border-amber-700 rounded-xl max-w-md w-full p-4 space-y-3 font-mono text-xs shadow-2xl">
      <div class="flex items-center justify-between border-b border-slate-800 pb-2">
        <span class="font-bold text-amber-300 text-sm flex items-center gap-1.5"><span>✏️</span> Edit Sponsor Creative</span>
        <button onclick="closeEditSponsorModal()" class="text-slate-400 hover:text-white text-base">✕</button>
      </div>
      <input type="hidden" id="editSponsorId">
      <div class="space-y-2">
        <div class="grid grid-cols-3 gap-2">
          <div class="col-span-2">
            <label class="text-[10px] text-slate-400 block mb-0.5">Sponsor Name</label>
            <input type="text" id="editSponsorName" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Icon Emoji</label>
            <input type="text" id="editSponsorIcon" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Tagline</label>
          <input type="text" id="editSponsorTagline" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">CTA Text</label>
            <input type="text" id="editSponsorCta" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Badge</label>
            <input type="text" id="editSponsorBadge" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
        <div>
          <label class="text-[10px] text-slate-400 block mb-0.5">Destination URL</label>
          <input type="text" id="editSponsorUrl" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
        </div>
        <div class="grid grid-cols-2 gap-2">
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Reward Tokens</label>
            <input type="number" id="editSponsorRewardTokens" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
          <div>
            <label class="text-[10px] text-slate-400 block mb-0.5">Reward USD</label>
            <input type="number" step="0.01" id="editSponsorRewardUsd" class="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-white">
          </div>
        </div>
      </div>
      <div class="flex justify-end gap-2 pt-2 border-t border-slate-800">
        <button onclick="closeEditSponsorModal()" class="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded">Cancel</button>
        <button onclick="adminSubmitSaveSponsorEdit()" class="px-4 py-1.5 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold rounded">Save Sponsor</button>
      </div>
    </div>
  </div>
  </script>
</body>
</html>
"""

"""TinCan MeshOS Gamification & Live Telemetry Engine.

Implements thread-safe real-time state tracking for peer XP, quest progression,
packet flight ring buffers, multi-cursor presence, watch party synchronization,
and dual-model AI arena voting across the TinCan mesh.
"""

from __future__ import annotations

import copy
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

QUEST_CATALOG: Dict[str, Dict[str, Any]] = {
    "workstation_handshake": {
        "title": "First Handshake",
        "badge": "🟢 Mesh Initiate",
        "xp": 50,
        "description": "Connect a workstation or WebRTC peer to the mesh",
    },
    "sealed_courier": {
        "title": "Sealed Courier",
        "badge": "🥫 Cipher Postmaster",
        "xp": 100,
        "description": "Send an Ed25519-signed ciphertext envelope",
    },
    "inbox_decryption": {
        "title": "Zero-Knowledge Reader",
        "badge": "🔐 Zero-Knowledge Reader",
        "xp": 75,
        "description": "Poll and verify a sealed TinCan mailbox",
    },
    "brain_arena_match": {
        "title": "Synapse Arbiter",
        "badge": "🧠 Synapse Arbiter",
        "xp": 150,
        "description": "Run a dual-model AI Arena match and vote on the winner",
    },
    "curator_drop": {
        "title": "Broadcast DJ",
        "badge": "📺 Broadcast DJ",
        "xp": 125,
        "description": "Ingest a video into the Relay Watch Party collection",
    },
    "coop_hitl_trigger": {
        "title": "HITL Commander",
        "badge": "⚡ HITL Commander",
        "xp": 200,
        "description": "Approve and trigger a cooperative peer action",
    },
    "watchparty_reaction": {
        "title": "Party Signal",
        "badge": "🔥 Vibe Synchronizer",
        "xp": 15,
        "description": "Emit a live watch-party reaction across the room",
    },
    "mentor_guidance": {
        "title": "Mentor Guidance",
        "badge": "🎓 Trusted Mentor",
        "xp": 250,
        "description": "Dispatch or complete an approval-gated Mentor-Mentee walkthrough step",
    },
    "mentee_hand_raise": {
        "title": "Apprentice Signal",
        "badge": "✋ Active Mentee",
        "xp": 150,
        "description": "Raise hand for a Mentor pair-programming or code-review session",
    },
    "cyberspace_post": {
        "title": "Cyberspace Architect",
        "badge": "🌐 Cyberspace Scribe",
        "xp": 120,
        "description": "Publish a topic or reply with @username or @agent tags on the Cyberspace Board",
    },
    "cyberspace_verified": {
        "title": "Verified Citizen",
        "badge": "✅ Verified Citizen",
        "xp": 200,
        "description": "Complete the @verifier-agent Identity Verification Form in Cyberspace",
    },
}


class TinCanMeshOSEngine:
    """Thread-safe gamification, telemetry, and live sync engine for TinCan MeshOS."""

    def __init__(self, seed: bool = True) -> None:
        self._lock = threading.RLock()
        self.total_xp: int = 0
        self.peers: Dict[str, Dict[str, Any]] = {}
        self.quests: Dict[str, Dict[str, Any]] = {}
        self.cursors: Dict[str, Dict[str, Any]] = {}
        self.flights: List[Dict[str, Any]] = []
        self.reactions: List[Dict[str, Any]] = []
        self.arena_votes: Dict[str, int] = {}
        self.watch_party: Dict[str, Any] = {
            "peer_id": "",
            "video_idx": 0,
            "is_playing": False,
            "current_time": 0.0,
            "updated_at": 0.0,
        }

        self._init_quests()

        if seed:
            self._seed_initial_state()

    def _init_quests(self) -> None:
        """Initialize quest tracking table from QUEST_CATALOG."""
        for key, info in QUEST_CATALOG.items():
            self.quests[key] = {
                "key": key,
                "title": info["title"],
                "badge": info["badge"],
                "xp": info["xp"],
                "description": info["description"],
                "completions": 0,
                "completed_by": [],
                "last_completed": 0.0,
            }

    def _seed_initial_state(self) -> None:
        """Seed rich L3 baseline state with 550 total XP across 2 peers and 2 initial flights."""
        now = time.time()
        self.total_xp = 550

        self.peers["peer-primary-mac"] = {
            "peer_id": "peer-primary-mac",
            "display_name": "Mac Studio (M1 Max)",
            "xp": 350,
            "actions_count": 4,
            "envelopes_sealed": 2,
            "tokens_routed": 1450,
            "votes_cast": 1,
            "reactions_sent": 2,
            "badges": ["🟢 Mesh Initiate", "🥫 Cipher Postmaster"],
            "last_active": now,
        }

        self.peers["peer-secondary-node"] = {
            "peer_id": "peer-secondary-node",
            "display_name": "Collaborator MacBook",
            "xp": 200,
            "actions_count": 2,
            "envelopes_sealed": 1,
            "tokens_routed": 600,
            "votes_cast": 0,
            "reactions_sent": 1,
            "badges": ["🟢 Mesh Initiate"],
            "last_active": now - 30.0,
        }

        # Seed quest completions
        if "workstation_handshake" in self.quests:
            self.quests["workstation_handshake"]["completions"] = 2
            self.quests["workstation_handshake"]["completed_by"] = [
                "peer-primary-mac",
                "peer-secondary-node",
            ]
            self.quests["workstation_handshake"]["last_completed"] = now - 120.0

        if "sealed_courier" in self.quests:
            self.quests["sealed_courier"]["completions"] = 1
            self.quests["sealed_courier"]["completed_by"] = ["peer-primary-mac"]
            self.quests["sealed_courier"]["last_completed"] = now - 60.0

        if "coop_hitl_trigger" in self.quests:
            self.quests["coop_hitl_trigger"]["completions"] = 1
            self.quests["coop_hitl_trigger"]["completed_by"] = ["peer-primary-mac"]
            self.quests["coop_hitl_trigger"]["last_completed"] = now - 45.0

        # Seed 2 initial packet flights
        self.flights = [
            {
                "id": "flight-seed-01",
                "from_node": "peer-primary-mac",
                "to_node": "peer-secondary-node",
                "kind": "envelope",
                "label": "X25519",
                "byte_size": 512,
                "timestamp": now - 50.0,
            },
            {
                "id": "flight-seed-02",
                "from_node": "peer-secondary-node",
                "to_node": "peer-primary-mac",
                "kind": "handshake",
                "label": "Ed25519",
                "byte_size": 256,
                "timestamp": now - 20.0,
            },
        ]

    def get_tier_info(self, xp: Optional[int] = None) -> Dict[str, Any]:
        """Compute readiness tier, unlocked themes, and progress percentage for given or total XP."""
        with self._lock:
            target_xp = self.total_xp if xp is None else int(xp)

        if target_xp >= 2000:
            tier_code = "L5"
            tier_name = "L5: Autonomous Cognitive Mesh"
            next_tier_xp = 2000
            unlocked_themes = [
                "slate",
                "amber-crt",
                "crypto-emerald",
                "webrtc-cyan",
                "messiah-gold",
            ]
            progress_pct = 100.0
        elif target_xp >= 1000:
            tier_code = "L4"
            tier_name = "L4: CRDT Gossip & Real-Time WebRTC Mesh"
            next_tier_xp = 2000
            unlocked_themes = [
                "slate",
                "amber-crt",
                "crypto-emerald",
                "webrtc-cyan",
            ]
            progress_pct = round(((target_xp - 1000) / 1000.0) * 100.0, 2)
        elif target_xp >= 500:
            tier_code = "L3"
            tier_name = "L3: Cryptographic Multi-Account Bridge"
            next_tier_xp = 1000
            unlocked_themes = ["slate", "amber-crt", "crypto-emerald"]
            progress_pct = round(((target_xp - 500) / 500.0) * 100.0, 2)
        elif target_xp >= 200:
            tier_code = "L2"
            tier_name = "L2: Local Shared Workspace"
            next_tier_xp = 500
            unlocked_themes = ["slate", "amber-crt"]
            progress_pct = round(((target_xp - 200) / 300.0) * 100.0, 2)
        else:
            tier_code = "L1"
            tier_name = "L1: Isolated Node"
            next_tier_xp = 200
            unlocked_themes = ["slate"]
            progress_pct = round((max(0, target_xp) / 200.0) * 100.0, 2)

        progress_pct = max(0.0, min(100.0, float(progress_pct)))

        return {
            "tier_code": tier_code,
            "tier_name": tier_name,
            "xp": target_xp,
            "next_tier_xp": next_tier_xp,
            "progress_pct": progress_pct,
            "unlocked_themes": list(unlocked_themes),
        }

    def award_xp(
        self,
        peer_id: str,
        action_key: str,
        custom_xp: Optional[int] = None,
        display_name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Award XP to a peer, update quest completion, badges, and stats."""
        meta = metadata or {}
        now = time.time()

        with self._lock:
            # Resolve awarded XP amount
            if custom_xp is not None:
                awarded = int(custom_xp)
            elif action_key in QUEST_CATALOG:
                awarded = int(QUEST_CATALOG[action_key]["xp"])
            else:
                awarded = 10

            # Ensure peer exists
            if peer_id not in self.peers:
                self.peers[peer_id] = {
                    "peer_id": peer_id,
                    "display_name": display_name or peer_id,
                    "xp": 0,
                    "actions_count": 0,
                    "envelopes_sealed": 0,
                    "tokens_routed": 0,
                    "votes_cast": 0,
                    "reactions_sent": 0,
                    "badges": [],
                    "last_active": now,
                }
            elif display_name:
                self.peers[peer_id]["display_name"] = display_name

            peer = self.peers[peer_id]
            peer["xp"] += awarded
            peer["actions_count"] += 1
            peer["last_active"] = now

            # Increment specific action telemetry counters
            if action_key == "sealed_courier" or meta.get("sealed"):
                peer["envelopes_sealed"] += int(meta.get("envelopes_count", 1))
            if action_key == "brain_arena_match" or meta.get("vote"):
                peer["votes_cast"] += int(meta.get("votes_count", 1))
            if action_key == "watchparty_reaction" or meta.get("reaction"):
                peer["reactions_sent"] += int(meta.get("reactions_count", 1))
            if "tokens_routed" in meta:
                peer["tokens_routed"] += int(meta["tokens_routed"])

            # Award badge if defined in catalog
            if action_key in QUEST_CATALOG:
                badge = QUEST_CATALOG[action_key]["badge"]
                if badge not in peer["badges"]:
                    peer["badges"].append(badge)

            # Update total XP
            self.total_xp += awarded

            # Update quest tracker
            if action_key in self.quests:
                q = self.quests[action_key]
                q["completions"] += 1
                if peer_id not in q["completed_by"]:
                    q["completed_by"].append(peer_id)
                q["last_completed"] = now

            return {
                "awarded_xp": awarded,
                "total_xp": self.total_xp,
                "tier": self.get_tier_info(),
                "peer": copy.deepcopy(peer),
            }

    def update_cursor(
        self,
        peer_id: str,
        x: float,
        y: float,
        window_id: str = "desktop",
        display_name: Optional[str] = None,
        room: str = "main",
    ) -> Dict[str, Any]:
        """Update live spatial cursor presence for a peer in a room."""
        now = time.time()
        with self._lock:
            name = (
                display_name
                or (self.peers[peer_id]["display_name"] if peer_id in self.peers else peer_id)
            )
            cursor_info = {
                "peer_id": peer_id,
                "display_name": name,
                "x": float(x),
                "y": float(y),
                "window_id": window_id,
                "room": room,
                "updated_at": now,
            }
            self.cursors[peer_id] = cursor_info

            if peer_id in self.peers:
                self.peers[peer_id]["last_active"] = now

            return copy.deepcopy(cursor_info)

    def record_flight(
        self,
        from_node: str,
        to_node: str,
        kind: str = "envelope",
        label: str = "X25519",
        byte_size: int = 256,
    ) -> Dict[str, Any]:
        """Record packet flight telemetry, maintaining a ring buffer capped at 30 flights."""
        flight = {
            "id": f"fl-{uuid.uuid4().hex[:8]}",
            "from_node": from_node,
            "to_node": to_node,
            "kind": kind,
            "label": label,
            "byte_size": int(byte_size),
            "timestamp": time.time(),
        }
        with self._lock:
            self.flights.append(flight)
            if len(self.flights) > 30:
                self.flights = self.flights[-30:]
            return copy.deepcopy(flight)

    def sync_watch_party(
        self,
        peer_id: str,
        video_idx: int = 0,
        is_playing: bool = True,
        current_time: float = 0.0,
    ) -> Dict[str, Any]:
        """Synchronize video player playback state across mesh participants."""
        now = time.time()
        with self._lock:
            self.watch_party = {
                "peer_id": peer_id,
                "video_idx": int(video_idx),
                "is_playing": bool(is_playing),
                "current_time": float(current_time),
                "updated_at": now,
            }
            if peer_id in self.peers:
                self.peers[peer_id]["last_active"] = now
            return copy.deepcopy(self.watch_party)

    def add_reaction(
        self,
        peer_id: str,
        emoji: str,
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Emit a watch-party reaction, award watchparty_reaction XP, and cap buffer at 25."""
        with self._lock:
            award_res = self.award_xp(
                peer_id=peer_id,
                action_key="watchparty_reaction",
                display_name=display_name,
            )
            name = display_name or award_res["peer"]["display_name"]
            reaction = {
                "id": f"rx-{uuid.uuid4().hex[:8]}",
                "peer_id": peer_id,
                "display_name": name,
                "emoji": emoji,
                "timestamp": time.time(),
            }
            self.reactions.append(reaction)
            if len(self.reactions) > 25:
                self.reactions = self.reactions[-25:]
            return copy.deepcopy(reaction)

    def vote_arena(
        self,
        peer_id: str,
        winner_alias: str,
        prompt_preview: str = "",
        display_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Increment votes for winner, award brain_arena_match XP, and record flight."""
        with self._lock:
            self.arena_votes[winner_alias] = self.arena_votes.get(winner_alias, 0) + 1
            award_res = self.award_xp(
                peer_id=peer_id,
                action_key="brain_arena_match",
                display_name=display_name,
                metadata={"winner_alias": winner_alias, "prompt_preview": prompt_preview},
            )
            flight = self.record_flight(
                from_node=peer_id,
                to_node=winner_alias,
                kind="arena_vote",
                label=f"Vote: {winner_alias}",
                byte_size=128,
            )
            return {
                "winner_alias": winner_alias,
                "votes": self.arena_votes[winner_alias],
                "prompt_preview": prompt_preview,
                "flight": flight,
                "xp_awarded": award_res["awarded_xp"],
                "total_xp": self.total_xp,
            }

    def get_leaderboard(self) -> List[Dict[str, Any]]:
        """Return list of peers sorted descending by XP."""
        with self._lock:
            board = [copy.deepcopy(peer) for peer in self.peers.values()]
            board.sort(key=lambda p: (p["xp"], p.get("last_active", 0.0)), reverse=True)
            return board

    def get_state(self, room: str = "main") -> Dict[str, Any]:
        """Aggregate snapshot of MeshOS gamification and live interaction state."""
        with self._lock:
            now = time.time()
            recent_cursors = [
                copy.deepcopy(c)
                for c in self.cursors.values()
                if c.get("room") == room and (now - c.get("updated_at", 0.0) <= 300.0)
            ]
            return {
                "xp": self.total_xp,
                "tier": self.get_tier_info(),
                "quests": [copy.deepcopy(q) for q in self.quests.values()],
                "leaderboard": self.get_leaderboard(),
                "cursors": recent_cursors,
                "watch_party": copy.deepcopy(self.watch_party),
                "flights": [copy.deepcopy(f) for f in self.flights],
                "arena_votes": copy.deepcopy(self.arena_votes),
                "room": room,
                "timestamp": now,
            }


__all__ = [
    "QUEST_CATALOG",
    "TinCanMeshOSEngine",
]

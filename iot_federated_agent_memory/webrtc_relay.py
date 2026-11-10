"""WebRTC UDP Peer Video, Voice & Screensharing Signaling Relay Service."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class PeerSession:
    peer_id: str
    display_name: str
    udp_address: str = "redacted"
    udp_port: int = 50000
    connected_at: float = 0.0
    active_stream: bool = True
    room: str = "main"
    has_video: bool = False
    has_audio: bool = False
    has_screen: bool = False


class WebRTCSignalingRelay:
    """Manages WebRTC SDP offers/answers, ICE candidates, rooms, and low-latency UDP streams."""

    def __init__(self):
        self._lock = threading.Lock()
        self.peers: Dict[str, PeerSession] = {}
        self.signaling_messages: List[Dict[str, Any]] = []
        self._next_seq: int = 1

    def register_peer(
        self,
        peer_id: str,
        display_name: str,
        udp_address: str = "redacted",
        udp_port: int = 50000,
        room: str = "main",
        has_video: bool = False,
        has_audio: bool = False,
        has_screen: bool = False,
    ) -> PeerSession:
        with self._lock:
            # Privacy Guard: Never store or expose raw client IP addresses in PeerSession
            session = PeerSession(
                peer_id=peer_id,
                display_name=display_name,
                udp_address="redacted",
                udp_port=int(udp_port),
                connected_at=time.time(),
                active_stream=True,
                room=room or "main",
                has_video=bool(has_video),
                has_audio=bool(has_audio),
                has_screen=bool(has_screen),
            )
            self.peers[peer_id] = session
            return session

    def leave_peer(self, peer_id: str) -> bool:
        with self._lock:
            if peer_id in self.peers:
                self.peers[peer_id].active_stream = False
                return True
            return False

    def exchange_signal(
        self,
        sender_id: str,
        receiver_id: str,
        signal_type: str,
        sdp_or_candidate: Dict[str, Any],
        room: str = "main",
    ) -> Dict[str, Any]:
        with self._lock:
            seq = self._next_seq
            self._next_seq += 1
            msg = {
                "seq": seq,
                "from": sender_id,
                "to": receiver_id,
                "room": room or "main",
                "type": signal_type,  # "offer", "answer", "candidate", "hangup"
                "payload": sdp_or_candidate,
                "timestamp": time.time(),
            }
            self.signaling_messages.append(msg)
            # Keep bounded buffer of recent 1000 signaling messages
            if len(self.signaling_messages) > 1000:
                self.signaling_messages = self.signaling_messages[-1000:]
            return msg

    def poll_signals(
        self,
        receiver_id: str,
        room: str = "main",
        since_seq: int = 0,
    ) -> Dict[str, Any]:
        """Return queued SDP offers/answers and ICE candidates for receiver_id or broadcast in room."""
        with self._lock:
            matched = [
                m
                for m in self.signaling_messages
                if m["seq"] > since_seq
                and m.get("from") != receiver_id
                and m.get("room", "main") == (room or "main")
                and (m.get("to") in (receiver_id, "*", "room", None, ""))
            ]
            latest_seq = self._next_seq - 1
            room_peers = [
                asdict(p)
                for p in self.peers.values()
                if p.active_stream and p.room == (room or "main")
            ]
            return {
                "room": room or "main",
                "receiver_id": receiver_id,
                "latest_seq": latest_seq,
                "signals": matched,
                "peers": room_peers,
            }

    def get_room_peers(self, room: str = "main") -> List[Dict[str, Any]]:
        with self._lock:
            return [
                asdict(p)
                for p in self.peers.values()
                if p.active_stream and p.room == (room or "main")
            ]

    def get_active_streams(self) -> List[Dict[str, Any]]:
        with self._lock:
            return [asdict(p) for p in self.peers.values() if p.active_stream]

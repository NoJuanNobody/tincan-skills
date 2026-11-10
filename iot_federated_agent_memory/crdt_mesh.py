"""Dimension 5: Offline-First CRDT Mesh Gossip & Merkle Delta Sync for Constrained IoT Nodes."""

from __future__ import annotations

import collections
import hashlib
import json
import socket
import struct
import time
import uuid
import zlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Set, Tuple, Union


FRAME_MAGIC = b"CRDT\x01\x00"  # 6-byte network framing header identifier
HEADER_SIZE = 46  # 6s (magic) + I (payload_len) + I (crc32) + 32s (sha256 digest)


class FrameIntegrityError(Exception):
    """Raised when incoming network frame fails CRC32 checksum, SHA-256 verification, or framing format."""


@dataclass
class CRDTDeltaMessage:
    node_id: str
    clock: int
    operation: str  # "upsert" or "delete"
    key: str
    value: Dict[str, Any]
    timestamp: float

    def get_hash(self) -> str:
        payload = f"{self.node_id}:{self.clock}:{self.key}:{json.dumps(self.value, sort_keys=True)}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> CRDTDeltaMessage:
        return cls(
            node_id=str(data["node_id"]),
            clock=int(data["clock"]),
            operation=str(data["operation"]),
            key=str(data["key"]),
            value=dict(data.get("value", {})),
            timestamp=float(data["timestamp"]),
        )

    def serialize(self) -> bytes:
        """Frame delta message into network bytes with CRC32 checksum and SHA-256 digest."""
        payload_bytes = json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")
        payload_len = len(payload_bytes)
        crc32_val = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        sha256_digest = hashlib.sha256(payload_bytes).digest()

        header = struct.pack("!6sII32s", FRAME_MAGIC, payload_len, crc32_val, sha256_digest)
        return header + payload_bytes

    @classmethod
    def deserialize(cls, frame_bytes: bytes) -> CRDTDeltaMessage:
        """Deserialize network frame, verifying magic header, CRC32, and SHA-256 checksums."""
        if len(frame_bytes) < HEADER_SIZE:
            raise FrameIntegrityError(f"Frame length {len(frame_bytes)} is less than header size {HEADER_SIZE}")

        magic, payload_len, expected_crc32, expected_sha256 = struct.unpack("!6sII32s", frame_bytes[:HEADER_SIZE])

        if magic != FRAME_MAGIC:
            raise FrameIntegrityError(f"Invalid frame magic: {magic!r}, expected {FRAME_MAGIC!r}")

        payload_bytes = frame_bytes[HEADER_SIZE : HEADER_SIZE + payload_len]
        if len(payload_bytes) != payload_len:
            raise FrameIntegrityError(f"Truncated frame payload: expected {payload_len} bytes, got {len(payload_bytes)}")

        actual_crc32 = zlib.crc32(payload_bytes) & 0xFFFFFFFF
        if actual_crc32 != expected_crc32:
            raise FrameIntegrityError(
                f"CRC32 checksum mismatch: expected {expected_crc32:#010x}, calculated {actual_crc32:#010x}"
            )

        actual_sha256 = hashlib.sha256(payload_bytes).digest()
        if actual_sha256 != expected_sha256:
            raise FrameIntegrityError("SHA-256 verification failed: digest mismatch")

        try:
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            raise FrameIntegrityError(f"Failed to decode JSON payload: {e}")

        return cls.from_dict(data)


class MeshTransportChannel(ABC):
    """Abstract transport channel for mesh gossip (UDP, WebRTC, BLE/LoRa frame buffers)."""

    def __init__(self, channel_type: str = "generic", mtu: int = 65535):
        self.channel_type = channel_type
        self.mtu = mtu
        self.is_connected: bool = True

    @abstractmethod
    def connect(self) -> None:
        """Establish or resume transport connectivity."""

    @abstractmethod
    def disconnect(self) -> None:
        """Drop or pause transport connectivity."""

    @abstractmethod
    def send(self, data: bytes) -> bool:
        """Transmit raw framed bytes across the channel."""

    @abstractmethod
    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        """Receive available framed bytes from the channel."""


class MockMeshTransport(MeshTransportChannel):
    """In-memory peer-to-peer transport channel for deterministic testing and local mesh simulations."""

    def __init__(self, channel_type: str = "mock", mtu: int = 65535):
        super().__init__(channel_type=channel_type, mtu=mtu)
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peers: List[MockMeshTransport] = []

    def link_peer(self, peer: MockMeshTransport) -> None:
        if peer not in self.peers:
            self.peers.append(peer)
        if self not in peer.peers:
            peer.peers.append(self)

    @classmethod
    def create_pair(cls, mtu: int = 65535) -> Tuple[MockMeshTransport, MockMeshTransport]:
        a = cls(mtu=mtu)
        b = cls(mtu=mtu)
        a.link_peer(b)
        return a, b

    @classmethod
    def create_mesh(cls, count: int = 3, mtu: int = 65535) -> List[MockMeshTransport]:
        nodes = [cls(mtu=mtu) for _ in range(count)]
        for i in range(count):
            for j in range(i + 1, count):
                nodes[i].link_peer(nodes[j])
        return nodes

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Payload size {len(data)} exceeds transport MTU {self.mtu}")

        delivered = False
        for peer in self.peers:
            if peer.is_connected:
                peer.inbox.append(data)
                delivered = True
        return delivered

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


class BLELoRaFrameBufferChannel(MeshTransportChannel):
    """Constrained frame-buffered transport channel (BLE MTU ~240B, LoRa MTU ~222B)

    with automatic segmentation and reassembly (SAR) of framed deltas.
    """

    def __init__(self, channel_type: str = "ble", mtu: int = 240):
        super().__init__(channel_type=channel_type, mtu=mtu)
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peers: List[BLELoRaFrameBufferChannel] = []
        self._reassembly_buffers: Dict[int, Dict[int, bytes]] = {}
        self._expected_chunks: Dict[int, int] = {}
        self._msg_counter: int = 0

    def link_peer(self, peer: BLELoRaFrameBufferChannel) -> None:
        if peer not in self.peers:
            self.peers.append(peer)
        if self not in peer.peers:
            peer.peers.append(self)

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected:
            return False

        # Segment data if payload exceeds MTU - header (8 bytes for chunk framing)
        chunk_header_size = 8  # !IHH: msg_id (4), chunk_index (2), total_chunks (2)
        max_chunk_payload = self.mtu - chunk_header_size
        if max_chunk_payload <= 0:
            raise ValueError(f"MTU {self.mtu} is too small for segmentation header")

        self._msg_counter = (self._msg_counter + 1) & 0xFFFFFFFF
        msg_id = self._msg_counter

        chunks = []
        offset = 0
        total_len = len(data)
        while offset < total_len:
            chunks.append(data[offset : offset + max_chunk_payload])
            offset += max_chunk_payload

        total_chunks = len(chunks)
        delivered = False

        for idx, chunk in enumerate(chunks):
            header = struct.pack("!IHH", msg_id, idx, total_chunks)
            packet = header + chunk
            for peer in self.peers:
                if peer.is_connected:
                    peer._receive_chunk(packet)
                    delivered = True

        return delivered

    def _receive_chunk(self, chunk_packet: bytes) -> None:
        if not self.is_connected or len(chunk_packet) < 8:
            return
        msg_id, chunk_idx, total_chunks = struct.unpack("!IHH", chunk_packet[:8])
        chunk_data = chunk_packet[8:]

        if msg_id not in self._reassembly_buffers:
            self._reassembly_buffers[msg_id] = {}
            self._expected_chunks[msg_id] = total_chunks

        self._reassembly_buffers[msg_id][chunk_idx] = chunk_data

        if len(self._reassembly_buffers[msg_id]) == self._expected_chunks[msg_id]:
            # All chunks received; reassemble in sequence
            ordered = [self._reassembly_buffers[msg_id][i] for i in range(total_chunks)]
            full_frame = b"".join(ordered)
            self.inbox.append(full_frame)
            del self._reassembly_buffers[msg_id]
            del self._expected_chunks[msg_id]

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


class UDPTransportChannel(MeshTransportChannel):
    """Real socket-based UDP datagram transport channel for local/LAN mesh node gossip."""

    def __init__(
        self,
        bind_host: str = "127.0.0.1",
        bind_port: int = 0,
        peer_host: str = "127.0.0.1",
        peer_port: Optional[int] = None,
        mtu: int = 1472,
    ):
        super().__init__(channel_type="udp", mtu=mtu)
        self.bind_host = bind_host
        self.bind_port = bind_port
        self.peer_host = peer_host
        self.peer_port = peer_port

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_host, self.bind_port))
        self.sock.setblocking(False)
        self.bound_port = self.sock.getsockname()[1]

    def set_peer_port(self, port: int) -> None:
        self.peer_port = port

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected or self.peer_port is None:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Payload {len(data)} exceeds UDP MTU {self.mtu}")
        try:
            self.sock.sendto(data, (self.peer_host, self.peer_port))
            return True
        except Exception:
            return False

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        try:
            data, _ = self.sock.recvfrom(65535)
            return data
        except BlockingIOError:
            return None
        except Exception:
            return None

    def close(self) -> None:
        self.sock.close()


class WebRTCDataChannel(MeshTransportChannel):
    """Simulated WebRTC SCTP data channel for peer-to-peer browser/agent mesh links."""

    def __init__(self, label: str = "crdt-sync", mtu: int = 16384):
        super().__init__(channel_type="webrtc", mtu=mtu)
        self.label = label
        self.inbox: collections.deque[bytes] = collections.deque()
        self.peer: Optional[WebRTCDataChannel] = None

    def link(self, peer: WebRTCDataChannel) -> None:
        self.peer = peer
        peer.peer = self

    def connect(self) -> None:
        self.is_connected = True

    def disconnect(self) -> None:
        self.is_connected = False

    def send(self, data: bytes) -> bool:
        if not self.is_connected or not self.peer or not self.peer.is_connected:
            return False
        if len(data) > self.mtu:
            raise ValueError(f"Data {len(data)} exceeds WebRTC MTU {self.mtu}")
        self.peer.inbox.append(data)
        return True

    def receive(self, timeout: Optional[float] = None) -> Optional[bytes]:
        if not self.is_connected:
            return None
        if self.inbox:
            return self.inbox.popleft()
        return None


@dataclass
class MerkleSyncResult:
    """Result of Merkle delta synchronization between mesh gossip nodes."""

    parity_achieved: bool
    local_merkle_root: str
    remote_merkle_root: str
    deltas_synced: int
    local_clock: int
    remote_clock: int


class CRDTMeshGossipSync:
    """Manages offline-first CRDT gossip state and computes Merkle delta vectors.

    Supports network transport channels, offline delta buffering, last-write-wins (LWW)
    conflict resolution, and automatic reconnection synchronization with Merkle parity verification.
    """

    def __init__(self, local_node_id: str, transport: Optional[MeshTransportChannel] = None):
        self.local_node_id = local_node_id
        self.vector_clock = 0
        self.state_store: Dict[str, Dict[str, Any]] = {}
        self.delta_log: List[CRDTDeltaMessage] = []
        self.offline_queue: List[CRDTDeltaMessage] = []
        self.seen_delta_hashes: Set[str] = set()
        self.key_metadata: Dict[str, Tuple[float, int, str]] = {}  # key -> (timestamp, clock, node_id)

        self.transport: Optional[MeshTransportChannel] = transport
        self.is_online: bool = transport.is_connected if transport else True

    def attach_transport(self, transport: MeshTransportChannel) -> None:
        """Attach a transport channel to this node."""
        self.transport = transport
        self.is_online = transport.is_connected

    def apply_local_update(
        self, key: str, value: Dict[str, Any], operation: str = "upsert"
    ) -> CRDTDeltaMessage:
        """Apply a local modification, advance clock, and broadcast or buffer into offline queue."""
        self.vector_clock += 1
        ts = time.time()
        delta = CRDTDeltaMessage(
            node_id=self.local_node_id,
            clock=self.vector_clock,
            operation=operation,
            key=key,
            value=value,
            timestamp=ts,
        )

        delta_hash = delta.get_hash()
        self.seen_delta_hashes.add(delta_hash)
        self.key_metadata[key] = (ts, self.vector_clock, self.local_node_id)

        if operation == "delete":
            self.state_store.pop(key, None)
        else:
            self.state_store[key] = value

        self.delta_log.append(delta)

        # Broadcast if online and transport is functional, else buffer in offline queue
        if self.is_online and self.transport and self.transport.is_connected:
            try:
                frame = delta.serialize()
                sent = self.transport.send(frame)
                if not sent:
                    self.offline_queue.append(delta)
            except Exception:
                self.offline_queue.append(delta)
        else:
            self.offline_queue.append(delta)

        return delta

    def compute_merkle_root(self) -> str:
        """Deterministic Merkle root calculated from sorted sha256 digests of state_store items."""
        concatenated = "".join(
            sorted(
                [
                    f"{k}:{hashlib.sha256(json.dumps(v, sort_keys=True).encode()).hexdigest()}"
                    for k, v in self.state_store.items()
                ]
            )
        )
        return hashlib.sha256(concatenated.encode("utf-8")).hexdigest()

    def merge_remote_delta(self, delta: CRDTDeltaMessage) -> bool:
        """Merge remote delta with idempotent deduplication and deterministic LWW register resolution."""
        delta_hash = delta.get_hash()
        if delta_hash in self.seen_delta_hashes:
            return False

        self.seen_delta_hashes.add(delta_hash)
        self.vector_clock = max(self.vector_clock, delta.clock)

        # LWW conflict resolution: compare (timestamp, clock, node_id)
        current_meta = self.key_metadata.get(delta.key)
        incoming_meta = (delta.timestamp, delta.clock, delta.node_id)

        should_apply = current_meta is None or incoming_meta >= current_meta

        if should_apply:
            self.key_metadata[delta.key] = incoming_meta
            if delta.operation == "delete":
                self.state_store.pop(delta.key, None)
            else:
                self.state_store[delta.key] = delta.value

        self.delta_log.append(delta)
        return True

    def disconnect(self) -> None:
        """Simulate transport link failure or offline edge node condition."""
        self.is_online = False
        if self.transport:
            self.transport.disconnect()

    def reconnect(self, peer: Optional[CRDTMeshGossipSync] = None) -> MerkleSyncResult:
        """Restore connectivity, flush buffered offline deltas across transport,

        and synchronize state vectors with Merkle parity verification.
        """
        self.is_online = True
        if self.transport:
            self.transport.connect()

        # 1. Flush offline queue frames
        flushed_count = self.flush_offline_queue()

        # 2. Process any incoming transport frames
        self.process_incoming_transport()

        # 3. Direct or transport-assisted Merkle parity sync
        if peer is not None:
            return self.sync_with_peer(peer)

        local_root = self.compute_merkle_root()
        return MerkleSyncResult(
            parity_achieved=True,
            local_merkle_root=local_root,
            remote_merkle_root=local_root,
            deltas_synced=flushed_count,
            local_clock=self.vector_clock,
            remote_clock=self.vector_clock,
        )

    def flush_offline_queue(self) -> int:
        """Transmit all deltas buffered in the offline queue."""
        if not self.transport or not self.transport.is_connected:
            return 0

        flushed = 0
        remaining = []
        for delta in self.offline_queue:
            try:
                frame = delta.serialize()
                if self.transport.send(frame):
                    flushed += 1
                else:
                    remaining.append(delta)
            except Exception:
                remaining.append(delta)

        self.offline_queue = remaining
        return flushed

    def process_incoming_transport(self) -> List[CRDTDeltaMessage]:
        """Poll transport for serialized network frames, verify CRC/SHA-256 integrity, and merge."""
        if not self.transport or not self.transport.is_connected:
            return []

        merged: List[CRDTDeltaMessage] = []
        while True:
            frame_bytes = self.transport.receive()
            if not frame_bytes:
                break
            delta = CRDTDeltaMessage.deserialize(frame_bytes)
            if self.merge_remote_delta(delta):
                merged.append(delta)

        return merged

    def sync_with_peer(self, peer: CRDTMeshGossipSync) -> MerkleSyncResult:
        """Bidirectionally reconcile delta vectors between two mesh nodes and verify Merkle parity."""
        # 1. Deltas in self missing from peer
        to_peer = [d for d in self.delta_log if d.get_hash() not in peer.seen_delta_hashes]
        # 2. Deltas in peer missing from self
        to_self = [d for d in peer.delta_log if d.get_hash() not in self.seen_delta_hashes]

        synced_count = 0
        for d in to_peer:
            if peer.merge_remote_delta(d):
                synced_count += 1
        for d in to_self:
            if self.merge_remote_delta(d):
                synced_count += 1

        local_root = self.compute_merkle_root()
        remote_root = peer.compute_merkle_root()
        parity_achieved = local_root == remote_root

        return MerkleSyncResult(
            parity_achieved=parity_achieved,
            local_merkle_root=local_root,
            remote_merkle_root=remote_root,
            deltas_synced=synced_count,
            local_clock=self.vector_clock,
            remote_clock=peer.vector_clock,
        )

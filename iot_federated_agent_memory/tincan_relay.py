"""
TinCan Blind Relay Backend.

Implements store-and-forward ciphertext mailboxes per recipient address.
Invariants:
- The relay NEVER reads plaintext or decrypts. It stores sealed ciphertexts only.
- Outer envelopes are signed by senders; relay verifies outer Ed25519 signature to prevent spoofing.
- Assigns monotonic sequence numbers (seq) per recipient for ordering and gap/replay detection.
- Supports instant and long-polling inbox retrieval.
"""

from __future__ import annotations

import base64
import json
import logging
import sqlite3
import threading
import time
import uuid
from typing import Any, Dict, List, Optional

from .tincan_core import (
    validate_address,
    decode_address,
    address_to_verify_key,
    verify_envelope as core_verify_envelope,
)

logger = logging.getLogger("tincan.relay")


class TinCanBlindRelay:
    """Threadsafe SQLite store-and-forward blind relay for TinCan ciphertext envelopes."""

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self._lock = threading.RLock()
        self._cond = threading.Condition(self._lock)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.presence: Dict[str, Dict[str, Any]] = {}
        self._init_db()

    def touch_presence(
        self,
        address: str,
        event: str = "poll",
        read_seq: Optional[int] = None,
    ) -> None:
        if not address:
            return
        addr_clean = address.split("@")[0].strip()
        now = time.time()
        with self._lock:
            entry = self.presence.setdefault(
                addr_clean,
                {
                    "address": addr_clean,
                    "first_seen_at": now,
                    "last_seen_at": now,
                    "last_event": event,
                    "last_read_seq": 0,
                    "poll_count": 0,
                },
            )
            entry["last_seen_at"] = now
            entry["last_event"] = event
            if event == "inbox_poll":
                entry["poll_count"] = int(entry.get("poll_count", 0)) + 1
            if read_seq is not None and int(read_seq) > int(entry.get("last_read_seq", 0)):
                entry["last_read_seq"] = int(read_seq)

    def _init_db(self) -> None:
        with self._lock:
            cur = self.conn.cursor()
            if self.db_path != ":memory:":
                cur.execute("PRAGMA journal_mode=WAL;")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS envelopes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipient TEXT NOT NULL,
                    seq INTEGER NOT NULL,
                    envelope_id TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    ciphertext TEXT NOT NULL,
                    nonce TEXT NOT NULL,
                    sig TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    created_at REAL NOT NULL,
                    raw_envelope TEXT,
                    UNIQUE(recipient, seq)
                );
                """
            )
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_envelopes_recipient_seq ON envelopes(recipient, seq);"
            )
            self.conn.commit()

    def _verify_envelope(self, payload: Dict[str, Any]) -> bool:
        """Verify outer signature of incoming envelope (supports JSON dict and pipe formats)."""
        # 1. Try core JSON envelope format directly
        if "signature" in payload:
            try:
                if core_verify_envelope(payload):
                    return True
            except Exception:
                pass

            # Try stripping alias keys if they were added after signing
            try:
                clean = {
                    k: v for k, v in payload.items()
                    if k not in ("to", "from", "box", "ciphertext", "sig", "ts", "delivered_at", "created_at")
                }
                if core_verify_envelope(clean):
                    return True
            except Exception:
                pass

        # Also support when sig is passed in 'sig' or 'signature'
        sig = payload.get("sig") or payload.get("signature")
        if not sig:
            return False

        sender = payload.get("from") or payload.get("sender")
        recipient = payload.get("to") or payload.get("recipient")
        ciphertext = payload.get("box") or payload.get("ciphertext") or payload.get("payload")
        nonce = payload.get("nonce", "")
        ts = payload.get("ts") if payload.get("ts") is not None else payload.get("timestamp", 0)

        # 2. Try minimal canonical dict format
        try:
            cand = {
                "sender": sender,
                "recipient": recipient,
                "timestamp": ts,
                "seq": payload.get("seq", 0),
                "payload": ciphertext,
                "signature": sig,
            }
            if core_verify_envelope(cand):
                return True
        except Exception:
            pass

        # 3. Try pipe format: 1|to|from|ts|nonce|box
        try:
            to_norm = recipient.split("@")[0].strip()
            from_norm = sender.split("@")[0].strip()
            vk = address_to_verify_key(from_norm)
            sig_bytes = base64.b64decode(sig)

            variations = [
                f"1|{to_norm}|{from_norm}|{ts}|{nonce}|{ciphertext}",
                f"1|{to_norm}|{from_norm}|{int(float(ts))}|{nonce}|{ciphertext}",
                f"1|{to_norm}|{from_norm}|{float(ts)}|{nonce}|{ciphertext}",
            ]
            for can in variations:
                try:
                    vk.verify(can.encode("utf-8"), sig_bytes)
                    return True
                except Exception:
                    continue
        except Exception:
            pass

        return False

    def send(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a sealed ciphertext envelope for a recipient.
        Verifies sender signature, assigns per-recipient monotonic seq, and stores ciphertext.
        The relay never holds private keys and cannot decrypt.
        """
        recipient = payload.get("to") or payload.get("recipient")
        sender = payload.get("from") or payload.get("sender")
        ciphertext = payload.get("box") or payload.get("ciphertext") or payload.get("payload")
        nonce = payload.get("nonce", "")
        sig = payload.get("sig") or payload.get("signature", "")
        ts = payload.get("ts") if payload.get("ts") is not None else payload.get("timestamp", time.time())
        envelope_id = payload.get("envelope_id") or payload.get("id") or str(uuid.uuid4())

        if not recipient or not sender or not ciphertext or not sig:
            raise ValueError("Envelope missing required fields: 'to'/'recipient', 'from'/'sender', 'box'/'ciphertext', 'sig'/'signature'")

        recipient_clean = recipient.split("@")[0].strip()
        sender_clean = sender.split("@")[0].strip()

        if not validate_address(recipient_clean):
            raise ValueError(f"Invalid recipient TinCan address: {recipient}")
        if not validate_address(sender_clean):
            raise ValueError(f"Invalid sender TinCan address: {sender}")

        # Verify envelope outer signature
        if not self._verify_envelope(payload):
            raise ValueError(f"Invalid envelope signature from sender {sender}")

        now = time.time()
        with self._cond:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT COALESCE(MAX(seq), 0) + 1 FROM envelopes WHERE recipient = ?",
                (recipient_clean,),
            )
            seq = int(cur.fetchone()[0])

            cur.execute(
                """
                INSERT INTO envelopes (recipient, seq, envelope_id, sender, ciphertext, nonce, sig, timestamp, created_at, raw_envelope)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (recipient_clean, seq, envelope_id, sender_clean, ciphertext, nonce, sig, float(ts), now, json.dumps(payload)),
            )
            self.conn.commit()
            self._cond.notify_all()

        self.touch_presence(sender_clean, event="send")

        return {
            "status": "ok",
            "seq": seq,
            "envelope_id": envelope_id,
            "recipient": recipient_clean,
            "delivered_at": now,
        }

    def inbox(
        self,
        recipient: str,
        since_seq: int = 0,
        timeout: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Fetch sealed envelopes for recipient since given sequence number.
        Supports instant return (timeout=0) or long-polling (timeout > 0).
        """
        if not recipient:
            raise ValueError("Recipient address is required")

        recipient_clean = recipient.split("@")[0].strip()
        since_seq = int(since_seq)
        timeout = float(timeout)

        with self._cond:
            cur = self.conn.cursor()
            cur.execute(
                "SELECT 1 FROM envelopes WHERE recipient = ? AND seq > ? LIMIT 1",
                (recipient_clean, since_seq),
            )
            has_messages = cur.fetchone() is not None

            if not has_messages and timeout > 0:
                start = time.time()
                while True:
                    remaining = timeout - (time.time() - start)
                    if remaining <= 0:
                        break
                    self._cond.wait(timeout=remaining)
                    cur.execute(
                        "SELECT 1 FROM envelopes WHERE recipient = ? AND seq > ? LIMIT 1",
                        (recipient_clean, since_seq),
                    )
                    if cur.fetchone() is not None:
                        break

            cur.execute(
                """
                SELECT seq, envelope_id, sender, recipient, ciphertext, nonce, sig, timestamp, created_at, raw_envelope
                FROM envelopes
                WHERE recipient = ? AND seq > ?
                ORDER BY seq ASC
                """,
                (recipient_clean, since_seq),
            )
            rows = cur.fetchall()

            messages: List[Dict[str, Any]] = []
            for row in rows:
                messages.append({
                    "seq": row[0],
                    "envelope_id": row[1],
                    "from": row[2],
                    "sender": row[2],
                    "to": row[3],
                    "recipient": row[3],
                    "box": row[4],
                    "ciphertext": row[4],
                    "payload": row[4],
                    "nonce": row[5],
                    "sig": row[6],
                    "signature": row[6],
                    "ts": row[7],
                    "timestamp": row[7],
                    "created_at": row[8],
                    "delivered_at": row[8],
                    "raw_envelope": row[9],
                })

            latest_seq = max([m["seq"] for m in messages], default=since_seq)
            self.touch_presence(recipient_clean, event="inbox_poll", read_seq=latest_seq)

            return {
                "status": "ok",
                "address": recipient_clean,
                "messages": messages,
                "latest_seq": latest_seq,
                "count": len(messages),
            }

    def whoami(self, address: Optional[str] = None) -> Dict[str, Any]:
        """Return relay status, crypto info, and optional recipient mailbox + presence metrics."""
        address_clean = address.split("@")[0].strip() if address else None

        with self._lock:
            cur = self.conn.cursor()
            cur.execute("SELECT COUNT(DISTINCT recipient), COUNT(*) FROM envelopes")
            total_recipients, total_envelopes = cur.fetchone()

            mailbox_stats = None
            peer_presence = None
            if address_clean:
                cur.execute(
                    "SELECT COUNT(*), COALESCE(MAX(seq), 0) FROM envelopes WHERE recipient = ?",
                    (address_clean,),
                )
                m_count, m_seq = cur.fetchone()
                p_info = self.presence.get(address_clean)
                now = time.time()
                if p_info:
                    age = max(0.0, now - float(p_info["last_seen_at"]))
                    state = "online" if age <= 120 else ("idle" if age <= 900 else "offline")
                    last_read = int(p_info.get("last_read_seq", 0))
                    peer_presence = {
                        "state": state,
                        "is_on_computer": state in ("online", "idle"),
                        "seconds_since_active": round(age, 1),
                        "last_seen_at": p_info["last_seen_at"],
                        "last_event": p_info["last_event"],
                        "last_read_seq": last_read,
                        "unread_count": max(0, int(m_seq) - last_read),
                        "poll_count": p_info.get("poll_count", 0),
                    }
                else:
                    peer_presence = {
                        "state": "offline",
                        "is_on_computer": False,
                        "seconds_since_active": None,
                        "last_seen_at": None,
                        "last_event": "never_seen",
                        "last_read_seq": 0,
                        "unread_count": int(m_seq),
                        "poll_count": 0,
                    }
                mailbox_stats = {
                    "address": address_clean,
                    "count": int(m_count),
                    "latest_seq": int(m_seq),
                    "presence": peer_presence,
                }

            return {
                "service": "tincan-blind-relay",
                "status": "online",
                "mode": "blind-store-and-forward",
                "cipher": "X25519-XSalsa20-Poly1305",
                "address": address_clean,
                "total_mailboxes": int(total_recipients or 0),
                "total_envelopes": int(total_envelopes or 0),
                "mailbox_stats": mailbox_stats,
                "presence": peer_presence,
            }

    def get_stats(self) -> Dict[str, Any]:
        """Concise status dictionary for server health / status dashboard."""
        info = self.whoami()
        return {
            "status": "online",
            "mode": "blind-store-and-forward",
            "total_envelopes": info["total_envelopes"],
            "total_mailboxes": info["total_mailboxes"],
        }

    def clear(self) -> None:
        """Clear all stored envelopes (used primarily in test suites)."""
        with self._cond:
            cur = self.conn.cursor()
            cur.execute("DELETE FROM envelopes;")
            self.conn.commit()
            self._cond.notify_all()

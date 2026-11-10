"""
TinCan MCP Protocol Server & Client Tools.

Exposes MCP tools for agent-to-agent encrypted communication over the TinCan Blind Relay:
- tincan_whoami(): returns current local address, alias, and public key.
- tincan_send(recipient_address, message, speak=False): encrypts, signs, and posts ciphertext to relay.
- tincan_read(since_seq=0): fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages.
- tincan_list_contacts(): lists trusted aliases and addresses.
- tincan_add_contact(alias, address): pins contact key.

Can be used programmatically in Python, as an MCP stdio server for Claude Code/IDE harnesses,
or via CLI.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import sys
import time
import urllib.parse
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

import nacl.signing

from .tincan_core import (
    ContactBook,
    DecryptionError,
    InvalidAddressError,
    KeyConflictError,
    TinCanIdentity,
    address_to_verify_key,
    decode_address,
    encode_address,
    open_payload,
    seal_payload,
    sign_envelope as core_sign_envelope,
    validate_address,
    verify_envelope as core_verify_envelope,
)
from .tincan_relay import TinCanBlindRelay

logger = logging.getLogger("tincan.mcp")

MCP_TOOLS_DEFINITIONS = [
    {
        "name": "tincan_whoami",
        "description": "Returns current local TinCan identity, address (tc:...), alias, and public key.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "tincan_send",
        "description": "Encrypts, signs, and posts sealed ciphertext to relay for a recipient address or contact alias.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipient_address": {
                    "type": "string",
                    "description": "Recipient TinCan address (tc:...) or trusted alias from contacts.",
                },
                "message": {
                    "type": "string",
                    "description": "Plaintext message content to seal and send.",
                },
                "speak": {
                    "type": "boolean",
                    "description": "Request recipient to vocalize message via TTS (kokoro-say).",
                    "default": False,
                },
            },
            "required": ["recipient_address", "message"],
        },
    },
    {
        "name": "tincan_read",
        "description": "Fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "since_seq": {
                    "type": "integer",
                    "description": "Sequence number offset (only return messages after since_seq).",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
    {
        "name": "tincan_list_contacts",
        "description": "Lists trusted contacts, pinned public keys, and aliases.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "tincan_add_contact",
        "description": "Pins a contact's public key and associates it with an alias (TOFU).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "alias": {
                    "type": "string",
                    "description": "Human-readable name or alias for the contact.",
                },
                "address": {
                    "type": "string",
                    "description": "TinCan address (tc:<52 base32 chars>).",
                },
            },
            "required": ["alias", "address"],
        },
    },
]


class TinCanMCPClient:
    """Client implementing the TinCan identity, encryption, contact pinning, and relay interface."""

    def __init__(
        self,
        relay_url: Optional[str] = None,
        config_dir: Optional[str] = None,
        alias: str = "default",
        relay: Optional[TinCanBlindRelay] = None,
    ):
        self.relay_url = (relay_url or os.environ.get("TINCAN_RELAY_URL", "http://localhost:8080")).rstrip("/")
        self.config_dir = config_dir or os.environ.get("TINCAN_DIR", os.path.expanduser("~/.tin-can"))
        self.alias = alias
        self.relay = relay

        self.identities_dir = os.path.join(self.config_dir, "identities")
        self.contacts_file = os.path.join(self.config_dir, "contacts.json")

        os.makedirs(self.identities_dir, exist_ok=True)
        self.identity = self._load_or_create_identity()
        self.address = self.identity.address
        self.public_key_hex = bytes(self.identity.verify_key).hex()

        self.contact_book = ContactBook(raise_on_conflict=True)
        self.role_file = os.path.join(self.config_dir, "role.json")
        self._load_contacts()

    def get_my_role(self) -> str:
        """Returns the current operator's role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        env_role = os.environ.get("TINCAN_ROLE", "").strip().lower()
        if env_role in ("admin", "moderator", "mentor", "mentee", "peer"):
            return env_role
        if os.path.exists(self.role_file):
            try:
                with open(self.role_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                r = data.get(self.alias) or data.get("default") or data.get("role")
                if r and str(r).lower() in ("admin", "moderator", "mentor", "mentee", "peer"):
                    return str(r).lower()
            except Exception:
                pass
        return "peer"

    def set_my_role(self, role: str) -> str:
        """Sets and persists the operator's role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        norm = role.strip().lower()
        if norm not in ("admin", "moderator", "mentor", "mentee", "peer"):
            raise ValueError(f"Invalid role '{role}'. Choose from: admin, moderator, mentor, mentee, peer")
        data = {}
        if os.path.exists(self.role_file):
            try:
                with open(self.role_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
        data[self.alias] = norm
        with open(self.role_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return norm

    def _load_or_create_identity(self) -> TinCanIdentity:
        key_path = os.path.join(self.identities_dir, f"{self.alias}.key")
        if os.path.exists(key_path):
            with open(key_path, "rb") as f:
                seed = f.read()
            if len(seed) >= 32:
                return TinCanIdentity.from_private_bytes(seed[:32])

        # Generate new key and save with 0600 mode
        identity = TinCanIdentity.generate()
        fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with open(fd, "wb") as f:
            f.write(identity.signing_key.encode())
        return identity

    def _load_contacts(self) -> None:
        if os.path.exists(self.contacts_file):
            try:
                with open(self.contacts_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for alias, info in data.items():
                    addr = info.get("address") if isinstance(info, dict) else info
                    meta = info.get("metadata", {}) if isinstance(info, dict) else {}
                    if addr and validate_address(addr):
                        self.contact_book.pin(alias, addr, metadata=meta, raise_on_conflict=False)
            except Exception as exc:
                logger.warning("Could not load contacts from %s: %s", self.contacts_file, exc)

    def _save_contacts(self) -> None:
        try:
            contacts_dict = self.contact_book.list_contacts()
            with open(self.contacts_file, "w", encoding="utf-8") as f:
                json.dump(contacts_dict, f, indent=2)
        except Exception as exc:
            logger.warning("Could not persist contacts to %s: %s", self.contacts_file, exc)

    def find_alias(self, address: str) -> Optional[str]:
        aliases = self.contact_book.get_aliases_for_address(address)
        return aliases[0] if aliases else None

    def _http_post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.relay_url}{path}"
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json", "User-Agent": "TinCanMCP/1.0"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _http_get(self, path: str) -> Dict[str, Any]:
        url = f"{self.relay_url}{path}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "TinCanMCP/1.0"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # -------------------------------------------------------------------------
    # Core MCP Tools
    # -------------------------------------------------------------------------

    def tincan_whoami(self, **kwargs) -> Dict[str, Any]:
        """Returns current local address, alias, role, and public key."""
        my_role = self.get_my_role()
        return {
            "alias": self.alias,
            "address": self.address,
            "role": my_role,
            "is_admin": my_role in ("admin", "moderator"),
            "public_key": self.public_key_hex,
            "public_key_b32": self.address[3:].split("@")[0],
            "relay_url": self.relay_url,
            "contacts_count": len(self.contact_book),
        }

    def tincan_send(
        self,
        recipient_address: str,
        message: str,
        speak: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Encrypts, signs, and posts ciphertext to relay."""
        if not recipient_address:
            raise ValueError("recipient_address is required")
        if not message:
            raise ValueError("message content is required")

        # Check if recipient_address is a known alias
        resolved_address = recipient_address
        resolved_alias = None
        if self.contact_book.has_alias(recipient_address):
            resolved_alias = recipient_address
            resolved_address = self.contact_book.get_address(recipient_address)
        else:
            resolved_alias = self.find_alias(recipient_address)

        clean_recipient = resolved_address.split("@")[0].strip()
        if not validate_address(clean_recipient):
            raise ValueError(f"Invalid recipient TinCan address: {resolved_address}")

        # Assemble inner plaintext message
        envelope_id = kwargs.get("id") or str(uuid.uuid4())
        inner_msg = {
            "id": envelope_id,
            "kind": kwargs.get("kind", "chat"),
            "text": str(message),
            "speak": bool(speak),
            "sender_role": kwargs.get("sender_role") or self.get_my_role(),
            "expects_reply": kwargs.get("expects_reply", False),
            "reply_to": kwargs.get("reply_to"),
            "hop": int(kwargs.get("hop", 0)),
            "as": self.alias,
            "created_at": time.time(),
        }

        # Encrypt inner message into SealedBox (X25519)
        ciphertext_b64 = self.identity.seal_for(clean_recipient, json.dumps(inner_msg))

        # Sign envelope using TinCanIdentity (Ed25519)
        nonce = base64.b64encode(os.urandom(16)).decode("ascii")
        timestamp = float(kwargs.get("timestamp", time.time()))
        seq = int(kwargs.get("seq", self.identity.next_seq()))

        envelope = self.identity.create_envelope(
            recipient=clean_recipient,
            payload=ciphertext_b64,
            seq=seq,
            timestamp=timestamp,
            envelope_id=envelope_id,
            speak=bool(speak),
            nonce=nonce,
        )

        if self.relay is not None:
            relay_resp = self.relay.send(envelope)
        else:
            relay_resp = self._http_post("/api/tincan/send", envelope)

        return {
            "status": "sent",
            "seq": relay_resp.get("seq"),
            "envelope_id": envelope_id,
            "recipient": clean_recipient,
            "alias": resolved_alias,
            "speak": bool(speak),
            "delivered_at": relay_resp.get("delivered_at"),
        }

    def tincan_read(self, since_seq: int = 0, **kwargs) -> List[Dict[str, Any]]:
        """
        Fetches inbox ciphertext from relay, decrypts using local private key,
        verifies sender signature, returns decrypted messages.
        """
        since_seq = int(since_seq)
        timeout = float(kwargs.get("timeout", 0.0))

        if self.relay is not None:
            raw_inbox = self.relay.inbox(self.address, since_seq=since_seq, timeout=timeout)
        else:
            raw_inbox = self._http_get(
                f"/api/tincan/inbox?address={urllib.parse.quote(self.address)}&since_seq={since_seq}&timeout={timeout}"
            )

        decrypted_messages: List[Dict[str, Any]] = []
        for msg in raw_inbox.get("messages", []):
            sender = msg.get("from") or msg.get("sender")
            box = msg.get("box") or msg.get("ciphertext") or msg.get("payload")
            sig = msg.get("signature") or msg.get("sig")
            nonce = msg.get("nonce", "")
            ts = msg.get("timestamp") if msg.get("timestamp") is not None else msg.get("ts", 0)
            seq = msg.get("seq")
            envelope_id = msg.get("envelope_id")

            # Verify sender signature
            verified = False
            raw_env_str = msg.get("raw_envelope")
            if raw_env_str:
                try:
                    raw_dict = json.loads(raw_env_str)
                    if "signature" in raw_dict and core_verify_envelope(raw_dict):
                        verified = True
                except Exception:
                    pass

            if not verified:
                try:
                    # 1. Try dict format stripping extraneous helper keys
                    clean = {
                        k: v for k, v in msg.items()
                        if k not in ("to", "from", "box", "ciphertext", "sig", "ts", "delivered_at", "created_at", "raw_envelope")
                    }
                    if "signature" in clean and core_verify_envelope(clean):
                        verified = True
                except Exception:
                    verified = False

            if not verified:
                # 2. Try pipe format fallback
                try:
                    to_norm = self.address.split("@")[0].strip()
                    from_norm = sender.split("@")[0].strip()
                    vk = address_to_verify_key(from_norm)
                    sig_bytes = base64.b64decode(sig)
                    for can in [
                        f"1|{to_norm}|{from_norm}|{ts}|{nonce}|{box}",
                        f"1|{to_norm}|{from_norm}|{int(float(ts))}|{nonce}|{box}",
                    ]:
                        try:
                            vk.verify(can.encode("utf-8"), sig_bytes)
                            verified = True
                            break
                        except Exception:
                            continue
                except Exception:
                    verified = False

            # Decrypt SealedBox
            try:
                plain_str = self.identity.open_sealed(box)
                try:
                    inner = json.loads(plain_str)
                    if not isinstance(inner, dict):
                        inner = {"text": str(inner), "speak": msg.get("speak", False)}
                except (json.JSONDecodeError, ValueError):
                    inner = {"text": plain_str, "speak": msg.get("speak", False)}
            except Exception as exc:
                inner = {"error": f"Failed to decrypt: {exc}", "text": None}

            sender_alias = self.find_alias(sender)
            sender_meta: Dict[str, Any] = {}
            if sender_alias:
                c_info = self.contact_book.get_contact(sender_alias)
                if c_info:
                    sender_meta = c_info.get("metadata", {})

            decrypted_messages.append({
                "seq": seq,
                "envelope_id": envelope_id or inner.get("id"),
                "sender": sender,
                "sender_alias": sender_alias,
                "sender_role": sender_meta.get("role", "peer"),
                "sender_trust_mentor_tts": bool(sender_meta.get("trust_mentor_tts", False)),
                "recipient": self.address,
                "timestamp": ts,
                "verified": verified,
                "message": inner.get("text"),
                "speak": inner.get("speak", False),
                "inner": inner,
            })

        return decrypted_messages

    def tincan_list_contacts(self, **kwargs) -> List[Dict[str, Any]]:
        """Lists trusted aliases, addresses, and mentorship roles."""
        result = []
        for alias, info in sorted(self.contact_book.list_contacts().items()):
            addr = info.get("address", "")
            meta = info.get("metadata") or {}
            pub_hex = None
            if validate_address(addr):
                try:
                    pub_hex = decode_address(addr).hex()
                except Exception:
                    pass
            result.append({
                "alias": alias,
                "address": addr,
                "public_key": pub_hex,
                "pinned_at": info.get("pinned_at"),
                "role": meta.get("role", "peer"),
                "trust_mentor_tts": bool(meta.get("trust_mentor_tts", False)),
            })
        return result

    def tincan_add_contact(
        self,
        alias: str,
        address: str,
        role: str = "peer",
        trust_mentor_tts: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """Pins contact key with optional role ('admin', 'moderator', 'mentor', 'mentee', 'peer')."""
        if not alias:
            raise ValueError("alias is required")
        if not address:
            raise ValueError("address is required")

        clean_addr = address.split("@")[0].strip()
        pub_bytes = decode_address(clean_addr)
        pk_hex = pub_bytes.hex()
        norm_role = role if role in ("admin", "moderator", "mentor", "mentee", "peer") else "peer"
        meta = {"role": norm_role, "trust_mentor_tts": bool(trust_mentor_tts)}

        self.contact_book.pin(alias, clean_addr, metadata=meta)
        self._save_contacts()

        contact_info = self.contact_book.get_contact(alias)
        pinned_at = contact_info["pinned_at"] if contact_info else time.time()

        return {
            "status": "pinned",
            "alias": alias,
            "address": clean_addr,
            "public_key": pk_hex,
            "pinned_at": pinned_at,
            "role": norm_role,
            "trust_mentor_tts": bool(trust_mentor_tts),
        }

    def set_contact_role(
        self,
        alias: str,
        role: Optional[str] = None,
        trust_mentor_tts: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update role ('admin', 'moderator', 'mentor', 'mentee', 'peer') and voice-gate policy for a pinned contact."""
        if not self.contact_book.has_alias(alias):
            raise ValueError(f"Unknown contact alias '{alias}'. Pin them first with 'tincan add-contact {alias} <tc:address>'.")
        c_info = self.contact_book.get_contact(alias) or {}
        addr = c_info["address"]
        meta = dict(c_info.get("metadata") or {})
        if role is not None:
            norm_r = str(role).strip().lower()
            if norm_r not in ("admin", "moderator", "mentor", "mentee", "peer"):
                raise ValueError(f"Invalid role '{role}'. Choose from: admin, moderator, mentor, mentee, peer")
            meta["role"] = norm_r
        if trust_mentor_tts is not None:
            meta["trust_mentor_tts"] = bool(trust_mentor_tts)
        self.contact_book.pin(alias, addr, metadata=meta)
        self._save_contacts()
        return {
            "status": "updated",
            "alias": alias,
            "address": addr,
            "role": meta.get("role", "peer"),
            "trust_mentor_tts": bool(meta.get("trust_mentor_tts", False)),
        }


# -----------------------------------------------------------------------------
# Module-level tool exports & Singleton Management
# -----------------------------------------------------------------------------

_default_client: Optional[TinCanMCPClient] = None


def get_default_client() -> TinCanMCPClient:
    global _default_client
    if _default_client is None:
        _default_client = TinCanMCPClient()
    return _default_client


def set_default_client(client: TinCanMCPClient) -> None:
    global _default_client
    _default_client = client


def tincan_whoami(**kwargs) -> Dict[str, Any]:
    """Returns current local address, alias, and public key."""
    return get_default_client().tincan_whoami(**kwargs)


def tincan_send(
    recipient_address: str,
    message: str,
    speak: bool = False,
    **kwargs,
) -> Dict[str, Any]:
    """Encrypts, signs, and posts ciphertext to relay."""
    return get_default_client().tincan_send(
        recipient_address=recipient_address,
        message=message,
        speak=speak,
        **kwargs,
    )


def tincan_read(since_seq: int = 0, **kwargs) -> List[Dict[str, Any]]:
    """Fetches inbox ciphertext from relay, decrypts using local private key, verifies sender signature, returns decrypted messages."""
    return get_default_client().tincan_read(since_seq=since_seq, **kwargs)


def tincan_list_contacts(**kwargs) -> List[Dict[str, Any]]:
    """Lists trusted aliases and addresses."""
    return get_default_client().tincan_list_contacts(**kwargs)


def tincan_add_contact(alias: str, address: str, **kwargs) -> Dict[str, Any]:
    """Pins contact key."""
    return get_default_client().tincan_add_contact(alias=alias, address=address, **kwargs)


# -----------------------------------------------------------------------------
# MCP JSON-RPC 2.0 Protocol Handler
# -----------------------------------------------------------------------------

def handle_mcp_request(
    request: Dict[str, Any],
    client: Optional[TinCanMCPClient] = None,
) -> Optional[Dict[str, Any]]:
    """Handle standard Model Context Protocol (MCP) JSON-RPC requests."""
    cl = client or get_default_client()
    req_id = request.get("id")
    method = request.get("method", "")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                },
                "serverInfo": {
                    "name": "tincan-mcp",
                    "version": "1.0.0",
                },
            },
        }

    if method == "notifications/initialized" or method == "initialized":
        return None

    if method == "ping":
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": MCP_TOOLS_DEFINITIONS,
            },
        }

    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        try:
            if tool_name == "tincan_whoami":
                result = cl.tincan_whoami(**arguments)
            elif tool_name == "tincan_send":
                result = cl.tincan_send(**arguments)
            elif tool_name == "tincan_read":
                result = cl.tincan_read(**arguments)
            elif tool_name == "tincan_list_contacts":
                result = cl.tincan_list_contacts(**arguments)
            elif tool_name == "tincan_add_contact":
                result = cl.tincan_add_contact(**arguments)
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {tool_name}",
                    },
                }

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result, indent=2),
                        }
                    ],
                },
            }
        except Exception as exc:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "isError": True,
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error executing {tool_name}: {exc}",
                        }
                    ],
                },
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Unknown MCP method: {method}",
        },
    }


def run_stdio_server(client: Optional[TinCanMCPClient] = None) -> None:
    """Run interactive MCP JSON-RPC server over stdio."""
    cl = client or get_default_client()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_mcp_request(req, client=cl)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()

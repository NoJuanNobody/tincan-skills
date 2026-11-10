"""TinCan 2 Cryptographic Core & Addressing Library.

Provides end-to-end cryptographic identity, addressing, sealed delivery,
message signing/verification, and TOFU (Trust On First Use) key pinning
for federated IoT agents using PyNaCl.
"""

from __future__ import annotations

import base64
import binascii
import json
import logging
import time
from typing import Any, Dict, List, Optional, Set, Union

import nacl.exceptions
import nacl.public
import nacl.signing

logger = logging.getLogger("tincan.core")

ADDRESS_PREFIX = "tc:"
PUBKEY_LEN_BYTES = 32
B32_PUBKEY_LEN = 52  # 32 bytes * 8 / 5 = 51.2 -> 52 base32 characters without padding


class TinCanCryptoError(Exception):
    """Base exception for TinCan cryptographic errors."""
    pass


class KeyConflictError(TinCanCryptoError, ValueError):
    """Raised when an address mismatch is detected for an alias in TOFU key pinning."""
    pass


class DecryptionError(TinCanCryptoError):
    """Raised when sealed payload decryption fails."""
    pass


class InvalidAddressError(TinCanCryptoError, ValueError):
    """Raised when an address cannot be validated or decoded."""
    pass


# ============================================================================
# Addressing: tc:<base32-encoded-pubkey>
# ============================================================================

def encode_address(pubkey_bytes: bytes) -> str:
    """Encode 32-byte Ed25519 public key bytes into canonical TinCan address: tc:<base32>.
    
    The base32 string is lowercase and padding '=' characters are stripped.
    """
    if not isinstance(pubkey_bytes, (bytes, bytearray)):
        raise TypeError(f"pubkey_bytes must be bytes, got {type(pubkey_bytes).__name__}")
    if len(pubkey_bytes) != PUBKEY_LEN_BYTES:
        raise ValueError(f"pubkey_bytes must be exactly {PUBKEY_LEN_BYTES} bytes, got {len(pubkey_bytes)}")
    
    b32 = base64.b32encode(pubkey_bytes).decode("ascii").lower().rstrip("=")
    return f"{ADDRESS_PREFIX}{b32}"


def decode_address(address: str) -> bytes:
    """Decode a TinCan address 'tc:<base32>' into raw 32-byte public key bytes.
    
    Validates prefix, length, base32 alphabet, and decoded byte length.
    Raises InvalidAddressError on invalid address format.
    """
    if not isinstance(address, str):
        raise InvalidAddressError(f"Address must be a string, got {type(address).__name__}")
    
    if not address.startswith(ADDRESS_PREFIX):
        raise InvalidAddressError(f"Address must start with '{ADDRESS_PREFIX}' prefix: {address!r}")
    
    body = address[len(ADDRESS_PREFIX):].strip().lower().rstrip("=")
    if len(body) != B32_PUBKEY_LEN:
        raise InvalidAddressError(
            f"Invalid address body length: expected {B32_PUBKEY_LEN} base32 chars, got {len(body)}"
        )
    
    # Restore base32 padding to multiple of 8
    pad_len = (8 - len(body) % 8) % 8
    padded_b32 = (body + "=" * pad_len).upper()
    
    try:
        raw_bytes = base64.b32decode(padded_b32)
    except (binascii.Error, ValueError) as err:
        raise InvalidAddressError(f"Invalid base32 encoding in address: {err}") from err
    
    if len(raw_bytes) != PUBKEY_LEN_BYTES:
        raise InvalidAddressError(
            f"Decoded address must yield {PUBKEY_LEN_BYTES} bytes, got {len(raw_bytes)}"
        )
    
    return raw_bytes


def validate_address(address: Any) -> bool:
    """Return True if the given string is a valid TinCan address, False otherwise."""
    try:
        decode_address(address)
        return True
    except (InvalidAddressError, TypeError, ValueError):
        return False


def pubkey_to_address(pubkey: Union[nacl.signing.VerifyKey, nacl.public.PublicKey, bytes, str, Any]) -> str:
    """Convert a VerifyKey, PublicKey, 32-byte pubkey, or TinCanIdentity to a canonical address."""
    if isinstance(pubkey, str):
        if validate_address(pubkey):
            return pubkey
        raise InvalidAddressError(f"Invalid address string: {pubkey}")
    if isinstance(pubkey, (nacl.signing.VerifyKey, nacl.public.PublicKey)):
        return encode_address(bytes(pubkey))
    if isinstance(pubkey, (bytes, bytearray)):
        return encode_address(bytes(pubkey))
    if hasattr(pubkey, "address") and isinstance(pubkey.address, str):
        return pubkey.address
    raise TypeError(f"Cannot convert {type(pubkey).__name__} to TinCan address")


def address_to_verify_key(address: str) -> nacl.signing.VerifyKey:
    """Decode a TinCan address and return an Ed25519 VerifyKey."""
    pub_bytes = decode_address(address)
    return nacl.signing.VerifyKey(pub_bytes)


def address_to_curve25519_pubkey(address: str) -> nacl.public.PublicKey:
    """Decode a TinCan address (Ed25519 pubkey) and convert it to an X25519 encryption PublicKey."""
    vk = address_to_verify_key(address)
    return vk.to_curve25519_public_key()


# ============================================================================
# Identity & Keypair Management
# ============================================================================

class TinCanIdentity:
    """Cryptographic identity for a TinCan 2 agent.
    
    Combines an Ed25519 signing keypair for non-repudiable envelope signatures
    with a converted X25519 encryption keypair for SealedBox message privacy.
    Identified canonically by its 'tc:<base32>' address.
    """

    def __init__(self, signing_key: nacl.signing.SigningKey):
        if not isinstance(signing_key, nacl.signing.SigningKey):
            raise TypeError(f"Expected nacl.signing.SigningKey, got {type(signing_key).__name__}")
        self.signing_key: nacl.signing.SigningKey = signing_key
        self.verify_key: nacl.signing.VerifyKey = signing_key.verify_key
        self.encryption_private_key: nacl.public.PrivateKey = signing_key.to_curve25519_private_key()
        self.encryption_public_key: nacl.public.PublicKey = self.verify_key.to_curve25519_public_key()
        self.address: str = encode_address(bytes(self.verify_key))
        self._seq: int = 0

    @classmethod
    def generate(cls) -> TinCanIdentity:
        """Generate a fresh random Ed25519 identity."""
        sk = nacl.signing.SigningKey.generate()
        return cls(sk)

    @classmethod
    def from_seed(cls, seed: bytes) -> TinCanIdentity:
        """Generate a deterministic identity from a 32-byte seed."""
        sk = nacl.signing.SigningKey(seed)
        return cls(sk)

    @classmethod
    def from_private_bytes(cls, priv_bytes: bytes) -> TinCanIdentity:
        """Instantiate identity from 32-byte private signing key bytes."""
        sk = nacl.signing.SigningKey(priv_bytes)
        return cls(sk)

    def next_seq(self) -> int:
        """Monotonically increment and return the next sequence number."""
        self._seq += 1
        return self._seq

    @property
    def current_seq(self) -> int:
        return self._seq

    def create_envelope(
        self,
        recipient: str,
        payload: Any,
        seq: Optional[int] = None,
        timestamp: Optional[float] = None,
        **extra_fields: Any,
    ) -> Dict[str, Any]:
        """Create and sign an envelope addressed to recipient."""
        if seq is None:
            seq = self.next_seq()
        if timestamp is None:
            timestamp = time.time()
        
        envelope = {
            "sender": self.address,
            "recipient": recipient,
            "timestamp": timestamp,
            "seq": seq,
            "payload": payload,
            **extra_fields,
        }
        return sign_envelope(self.signing_key, envelope)

    def seal_for(
        self,
        recipient: Union[str, nacl.public.PublicKey, nacl.signing.VerifyKey, TinCanIdentity],
        plaintext: Union[str, bytes],
    ) -> str:
        """Encrypt and seal a plaintext payload for the given recipient."""
        return seal_payload(recipient, plaintext)

    def open_sealed(self, ciphertext_b64: str) -> str:
        """Decrypt and open a sealed payload addressed to this identity."""
        return open_payload(self.encryption_private_key, ciphertext_b64)

    def open_sealed_bytes(self, ciphertext_b64: str) -> bytes:
        """Decrypt and open a sealed payload returning raw decrypted bytes."""
        return open_payload_bytes(self.encryption_private_key, ciphertext_b64)

    def __repr__(self) -> str:
        return f"<TinCanIdentity address={self.address[:16]}... seq={self._seq}>"


def generate_identity() -> TinCanIdentity:
    """Convenience helper to generate a fresh TinCanIdentity."""
    return TinCanIdentity.generate()


# ============================================================================
# Sealed Delivery (X25519 SealedBox)
# ============================================================================

def _resolve_encryption_pubkey(
    recipient: Union[str, nacl.public.PublicKey, nacl.signing.VerifyKey, TinCanIdentity, bytes]
) -> nacl.public.PublicKey:
    """Resolve various recipient representations into a nacl.public.PublicKey."""
    if isinstance(recipient, TinCanIdentity):
        return recipient.encryption_public_key
    if isinstance(recipient, nacl.public.PublicKey):
        return recipient
    if isinstance(recipient, nacl.signing.VerifyKey):
        return recipient.to_curve25519_public_key()
    if isinstance(recipient, str):
        if recipient.startswith(ADDRESS_PREFIX):
            return address_to_curve25519_pubkey(recipient)
        # Try raw base64 or hex 32-byte key
        try:
            raw = base64.b64decode(recipient)
            if len(raw) == PUBKEY_LEN_BYTES:
                return nacl.public.PublicKey(raw)
        except Exception:
            pass
        raise ValueError(f"Unrecognized recipient public key string format: {recipient}")
    if isinstance(recipient, (bytes, bytearray)):
        if len(recipient) == PUBKEY_LEN_BYTES:
            return nacl.public.PublicKey(bytes(recipient))
        raise ValueError(f"Recipient public key bytes must be 32 bytes, got {len(recipient)}")
    raise TypeError(f"Cannot resolve recipient public key from {type(recipient).__name__}")


def _resolve_encryption_privkey(
    recipient_privkey: Union[nacl.public.PrivateKey, nacl.signing.SigningKey, TinCanIdentity, bytes]
) -> nacl.public.PrivateKey:
    """Resolve various recipient private key representations into a nacl.public.PrivateKey."""
    if isinstance(recipient_privkey, TinCanIdentity):
        return recipient_privkey.encryption_private_key
    if isinstance(recipient_privkey, nacl.public.PrivateKey):
        return recipient_privkey
    if isinstance(recipient_privkey, nacl.signing.SigningKey):
        return recipient_privkey.to_curve25519_private_key()
    if isinstance(recipient_privkey, (bytes, bytearray)):
        if len(recipient_privkey) == PUBKEY_LEN_BYTES:
            return nacl.public.PrivateKey(bytes(recipient_privkey))
        raise ValueError(f"Private key bytes must be 32 bytes, got {len(recipient_privkey)}")
    raise TypeError(f"Cannot resolve private key from {type(recipient_privkey).__name__}")


def seal_payload(
    recipient_pubkey: Union[str, nacl.public.PublicKey, nacl.signing.VerifyKey, TinCanIdentity, bytes],
    plaintext_bytes_or_str: Union[str, bytes, bytearray, Any],
) -> str:
    """Seal a payload for recipient using X25519 SealedBox encryption.
    
    Args:
        recipient_pubkey: Recipient's TinCan address ('tc:...'), PublicKey, VerifyKey,
            TinCanIdentity, or 32-byte key.
        plaintext_bytes_or_str: Content to encrypt (str, bytes, or json-serializable obj).

    Returns:
        Base64-encoded ciphertext string.
    """
    pubkey = _resolve_encryption_pubkey(recipient_pubkey)

    if isinstance(plaintext_bytes_or_str, str):
        plaintext_bytes = plaintext_bytes_or_str.encode("utf-8")
    elif isinstance(plaintext_bytes_or_str, (bytes, bytearray)):
        plaintext_bytes = bytes(plaintext_bytes_or_str)
    else:
        plaintext_bytes = json.dumps(plaintext_bytes_or_str, sort_keys=True).encode("utf-8")

    box = nacl.public.SealedBox(pubkey)
    ciphertext = box.encrypt(plaintext_bytes)
    return base64.b64encode(ciphertext).decode("ascii")


def open_payload_bytes(
    recipient_privkey: Union[nacl.public.PrivateKey, nacl.signing.SigningKey, TinCanIdentity, bytes],
    ciphertext_b64: Union[str, bytes],
) -> bytes:
    """Open and decrypt a sealed payload returning raw decrypted bytes.
    
    Args:
        recipient_privkey: Recipient's X25519 PrivateKey, Ed25519 SigningKey,
            TinCanIdentity, or 32-byte private key.
        ciphertext_b64: Base64-encoded ciphertext string.

    Returns:
        Decrypted plaintext as raw bytes.

    Raises:
        DecryptionError: If decryption fails (e.g., wrong key or corrupted ciphertext).
    """
    privkey = _resolve_encryption_privkey(recipient_privkey)

    try:
        if isinstance(ciphertext_b64, str):
            raw_ciphertext = base64.b64decode(ciphertext_b64.encode("ascii"))
        else:
            raw_ciphertext = base64.b64decode(ciphertext_b64)
    except Exception as err:
        raise DecryptionError(f"Failed to decode base64 ciphertext: {err}") from err

    try:
        box = nacl.public.SealedBox(privkey)
        return box.decrypt(raw_ciphertext)
    except nacl.exceptions.CryptoError as err:
        raise DecryptionError(f"SealedBox decryption failed: {err}") from err


def open_payload(
    recipient_privkey: Union[nacl.public.PrivateKey, nacl.signing.SigningKey, TinCanIdentity, bytes],
    ciphertext_b64: Union[str, bytes],
) -> str:
    """Open and decrypt a sealed payload using the recipient's private key.
    
    Args:
        recipient_privkey: Recipient's X25519 PrivateKey, Ed25519 SigningKey,
            TinCanIdentity, or 32-byte private key.
        ciphertext_b64: Base64-encoded ciphertext string.

    Returns:
        Decrypted plaintext as a string (utf-8 decoded with latin-1 fallback for binary).

    Raises:
        DecryptionError: If decryption fails (e.g., wrong key or corrupted ciphertext).
    """
    decrypted_bytes = open_payload_bytes(recipient_privkey, ciphertext_b64)
    try:
        return decrypted_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return decrypted_bytes.decode("latin-1")


# ============================================================================
# Envelope Signing & Verification
# ============================================================================

REQUIRED_ENVELOPE_FIELDS = ("sender", "recipient", "timestamp", "seq", "payload")


def canonical_envelope_bytes(envelope_dict: Dict[str, Any]) -> bytes:
    """Compute the deterministic canonical JSON representation of envelope contents to sign.
    
    Strips the 'signature' field if present and sorts all keys.
    """
    clean_dict = {k: v for k, v in envelope_dict.items() if k != "signature"}
    for field in REQUIRED_ENVELOPE_FIELDS:
        if field not in clean_dict:
            raise ValueError(f"Missing required envelope field: {field}")
    return json.dumps(clean_dict, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_envelope(
    signing_key: Union[nacl.signing.SigningKey, TinCanIdentity],
    envelope_dict: Dict[str, Any],
) -> Dict[str, Any]:
    """Sign an envelope dictionary with an Ed25519 signing key.
    
    Args:
        signing_key: nacl.signing.SigningKey or TinCanIdentity.
        envelope_dict: Envelope containing sender, recipient, timestamp, seq, payload.

    Returns:
        A new envelope dictionary containing all original fields plus 'signature' (base64 string).
    """
    if isinstance(signing_key, TinCanIdentity):
        sk = signing_key.signing_key
    elif isinstance(signing_key, nacl.signing.SigningKey):
        sk = signing_key
    else:
        raise TypeError(f"Expected SigningKey or TinCanIdentity, got {type(signing_key).__name__}")

    canonical_bytes = canonical_envelope_bytes(envelope_dict)
    signed_obj = sk.sign(canonical_bytes)
    sig_b64 = base64.b64encode(signed_obj.signature).decode("ascii")

    signed_envelope = dict(envelope_dict)
    signed_envelope["signature"] = sig_b64
    return signed_envelope


def verify_envelope(
    signed_dict: Dict[str, Any],
    verify_key: Optional[Union[nacl.signing.VerifyKey, TinCanIdentity, str, bytes]] = None,
) -> bool:
    """Verify an envelope dictionary's Ed25519 signature.
    
    If verify_key is omitted, extracts the sender's public key from signed_dict['sender'].
    
    Returns:
        True if the signature is authentic and envelope intact; False on any tamper or error.
    """
    if not isinstance(signed_dict, dict):
        return False

    if "signature" not in signed_dict:
        return False

    sig_raw = signed_dict["signature"]
    if not isinstance(sig_raw, str):
        return False

    try:
        sig_bytes = base64.b64decode(sig_raw.encode("ascii"))
    except Exception:
        return False

    if len(sig_bytes) != 64:
        return False

    # Resolve verify key
    vk: Optional[nacl.signing.VerifyKey] = None
    try:
        if verify_key is not None:
            if isinstance(verify_key, nacl.signing.VerifyKey):
                vk = verify_key
            elif isinstance(verify_key, TinCanIdentity):
                vk = verify_key.verify_key
            elif isinstance(verify_key, str):
                vk = address_to_verify_key(verify_key)
            elif isinstance(verify_key, (bytes, bytearray)):
                vk = nacl.signing.VerifyKey(bytes(verify_key))
            else:
                return False
        else:
            sender = signed_dict.get("sender")
            if not isinstance(sender, str) or not validate_address(sender):
                return False
            vk = address_to_verify_key(sender)
    except Exception:
        return False

    if vk is None:
        return False

    # Compute canonical bytes
    try:
        canonical_bytes = canonical_envelope_bytes(signed_dict)
    except Exception:
        return False

    # Verify signature
    try:
        vk.verify(canonical_bytes, sig_bytes)
        return True
    except nacl.exceptions.BadSignatureError:
        return False
    except Exception:
        return False


# ============================================================================
# In-Memory Contact Book with TOFU Key Pinning
# ============================================================================

class ContactBook:
    """In-memory contact book with Trust-On-First-Use (TOFU) key pinning.
    
    Maps human-readable aliases to canonical TinCan addresses ('tc:<base32>').
    Once an alias is pinned to an address on first use, any subsequent attempt
    to re-pin or contact that alias with a differing address triggers a warning
    and raises KeyConflictError (or returns False if raise_on_conflict is False).
    """

    def __init__(self, raise_on_conflict: bool = True):
        self.raise_on_conflict: bool = raise_on_conflict
        # alias -> {"address": str, "pinned_at": float, "metadata": dict}
        self._contacts: Dict[str, Dict[str, Any]] = {}
        # reverse mapping: address -> Set[alias]
        self._address_to_aliases: Dict[str, Set[str]] = {}

    def pin(
        self,
        alias: str,
        address: str,
        metadata: Optional[Dict[str, Any]] = None,
        raise_on_conflict: Optional[bool] = None,
    ) -> bool:
        """Pin an alias to a TinCan address on first use.
        
        Args:
            alias: Human-readable identifier for the peer/agent.
            address: Canonical TinCan address ('tc:...').
            metadata: Optional dictionary of attributes.
            raise_on_conflict: Override instance-level raise_on_conflict.

        Returns:
            True if pinned or matches existing pin; False if conflict and not raising.

        Raises:
            InvalidAddressError: If the address format is invalid.
            KeyConflictError: If the alias is already pinned to a different address.
        """
        if not isinstance(alias, str) or not alias.strip():
            raise ValueError(f"Alias must be a non-empty string, got {alias!r}")

        if not validate_address(address):
            raise InvalidAddressError(f"Cannot pin invalid TinCan address: {address}")

        should_raise = self.raise_on_conflict if raise_on_conflict is None else raise_on_conflict

        if alias in self._contacts:
            pinned_address = self._contacts[alias]["address"]
            if pinned_address != address:
                logger.warning(
                    "TOFU KEY CONFLICT: Alias '%s' is already pinned to %s, rejected new address %s",
                    alias, pinned_address, address,
                )
                if should_raise:
                    raise KeyConflictError(
                        f"TOFU conflict for alias '{alias}': already pinned to {pinned_address}, got {address}"
                    )
                return False
            # Matching address: optionally update metadata
            if metadata:
                self._contacts[alias].setdefault("metadata", {}).update(metadata)
            return True

        # First use: pin the address
        self._contacts[alias] = {
            "address": address,
            "pinned_at": time.time(),
            "metadata": dict(metadata or {}),
        }
        self._address_to_aliases.setdefault(address, set()).add(alias)
        logger.info("TOFU PINNED: Alias '%s' -> %s", alias, address)
        return True

    def add_contact(
        self,
        alias: str,
        address: str,
        metadata: Optional[Dict[str, Any]] = None,
        raise_on_conflict: Optional[bool] = None,
    ) -> bool:
        """Alias for pin()."""
        return self.pin(alias, address, metadata=metadata, raise_on_conflict=raise_on_conflict)

    def verify_or_pin(
        self,
        alias: str,
        address: str,
        metadata: Optional[Dict[str, Any]] = None,
        raise_on_conflict: Optional[bool] = None,
    ) -> bool:
        """Verify address matches pinned alias, or pin it on first use."""
        return self.pin(alias, address, metadata=metadata, raise_on_conflict=raise_on_conflict)

    def verify(
        self,
        alias: str,
        address: str,
        raise_on_conflict: Optional[bool] = None,
    ) -> bool:
        """Check if an address matches a previously pinned alias.
        
        Returns False if alias has never been pinned.
        Raises KeyConflictError if alias is pinned to a different address and should_raise is True.
        """
        if alias not in self._contacts:
            return False
        
        pinned_address = self._contacts[alias]["address"]
        if pinned_address != address:
            should_raise = self.raise_on_conflict if raise_on_conflict is None else raise_on_conflict
            logger.warning(
                "TOFU KEY MISMATCH: Alias '%s' pinned to %s, received %s",
                alias, pinned_address, address,
            )
            if should_raise:
                raise KeyConflictError(
                    f"TOFU key mismatch for '{alias}': pinned={pinned_address}, got={address}"
                )
            return False
        return True

    def get_address(self, alias: str) -> Optional[str]:
        """Get the pinned address for an alias, or None if unknown."""
        contact = self._contacts.get(alias)
        return contact["address"] if contact else None

    def get_contact(self, alias: str) -> Optional[Dict[str, Any]]:
        """Get copy of full contact record for an alias."""
        contact = self._contacts.get(alias)
        if not contact:
            return None
        return {
            "address": contact["address"],
            "pinned_at": contact["pinned_at"],
            "metadata": dict(contact.get("metadata", {})),
        }

    def get_aliases_for_address(self, address: str) -> List[str]:
        """Get all aliases pinned to a specific address."""
        return sorted(list(self._address_to_aliases.get(address, set())))

    def has_alias(self, alias: str) -> bool:
        """Check whether an alias is currently pinned."""
        return alias in self._contacts

    def remove(self, alias: str) -> bool:
        """Unpin a contact alias."""
        if alias in self._contacts:
            addr = self._contacts[alias]["address"]
            del self._contacts[alias]
            if addr in self._address_to_aliases:
                self._address_to_aliases[addr].discard(alias)
                if not self._address_to_aliases[addr]:
                    del self._address_to_aliases[addr]
            return True
        return False

    def list_contacts(self) -> Dict[str, Dict[str, Any]]:
        """Return a copy of all pinned contacts."""
        return {
            alias: {
                "address": info["address"],
                "pinned_at": info["pinned_at"],
                "metadata": dict(info.get("metadata", {})),
            }
            for alias, info in self._contacts.items()
        }

    def clear(self) -> None:
        """Clear all pinned contacts."""
        self._contacts.clear()
        self._address_to_aliases.clear()

    def __len__(self) -> int:
        return len(self._contacts)

    def __contains__(self, alias: str) -> bool:
        return alias in self._contacts

    def __getitem__(self, alias: str) -> str:
        addr = self.get_address(alias)
        if addr is None:
            raise KeyError(f"Unknown contact alias: {alias!r}")
        return addr

    def __setitem__(self, alias: str, address: str) -> None:
        self.pin(alias, address)

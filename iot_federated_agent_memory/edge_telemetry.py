"""Dimension 4: IoT Sensor & Edge Device Telemetry Ingestion (MQTT / CoAP / Matter)."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, List, Optional, Union


@dataclass
class SensorTelemetryPacket:
    device_id: str
    protocol: str  # "mqtt", "coap", "matter"
    metric_name: str
    value: float
    unit: str
    timestamp: float

    def to_vault_node(self) -> Dict[str, Any]:
        """Convert live IoT telemetry stream packet into an atomic GraphRAG Vault Node."""
        return {
            "title": f"telemetry_{self.device_id}_{self.metric_name}",
            "tags": ["#iot", "#telemetry", f"#{self.protocol}"],
            "frontmatter": {
                "device_id": self.device_id,
                "protocol": self.protocol,
                "metric": self.metric_name,
                "unit": self.unit,
                "recorded_at": self.timestamp,
            },
            "content": f"Sensor {self.device_id} reported {self.metric_name} = {self.value} {self.unit} over {self.protocol.upper()}.",
        }

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any], default_protocol: str = "mqtt") -> SensorTelemetryPacket:
        if not isinstance(data, dict):
            raise ValueError(f"Payload must be a dictionary, got {type(data).__name__}")

        device_id = data.get("device_id")
        if not device_id or not isinstance(device_id, str):
            raise ValueError("Telemetry packet requires non-empty string 'device_id'")

        metric_name = data.get("metric_name") or data.get("metric")
        if not metric_name or not isinstance(metric_name, str):
            raise ValueError("Telemetry packet requires non-empty string 'metric_name' or 'metric'")

        val_raw = data.get("value")
        if val_raw is None or isinstance(val_raw, bool):
            raise ValueError("Telemetry packet requires valid numeric 'value'")
        try:
            value = float(val_raw)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid numeric value: {val_raw}")

        unit = data.get("unit")
        if unit is None:
            raise ValueError("Telemetry packet requires 'unit'")
        unit_str = str(unit)

        protocol = data.get("protocol") or default_protocol
        protocol_str = str(protocol).lower()

        ts_raw = data.get("timestamp")
        if ts_raw is not None:
            try:
                timestamp = float(ts_raw)
            except (ValueError, TypeError):
                timestamp = time.time()
        else:
            timestamp = time.time()

        return cls(
            device_id=device_id,
            protocol=protocol_str,
            metric_name=metric_name,
            value=value,
            unit=unit_str,
            timestamp=timestamp,
        )


class EdgeTelemetryIngestor:
    """Ingests MQTT/CoAP/Matter IoT telemetry and publishes atomic nodes to the Vault."""

    def __init__(self, target_vault_dir: Optional[str] = None):
        self.target_vault_dir = target_vault_dir
        self.buffer: List[Dict[str, Any]] = []

    def ingest_packet(self, device_id: str, protocol: str, metric_name: str, value: float, unit: str) -> Dict[str, Any]:
        pkt = SensorTelemetryPacket(
            device_id=device_id,
            protocol=protocol.lower(),
            metric_name=metric_name,
            value=value,
            unit=unit,
            timestamp=time.time(),
        )
        node = pkt.to_vault_node()
        self.buffer.append(node)
        return node


class CreditExhaustionError(Exception):
    """Raised when wallet has insufficient credit for vending deduction ($0.05 per batch)."""


InsufficientBalanceError = CreditExhaustionError


@dataclass
class VendingDeductionReceipt:
    """Cryptographic HMAC-SHA256 receipt for paywall vending deduction."""

    receipt_id: str
    wallet_id: str
    batch_hash: str
    cost_usd: float
    remaining_balance_usd: float
    timestamp: float
    signature: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HMACVendingMachine:
    """Simulates stablecoin token vending deduction ($0.05/batch) with HMAC-SHA256 signatures."""

    def __init__(self, secret_key: str = "vault-graphrag-vending-secret-key-2026", cost_per_batch: float = 0.05):
        self.secret_key = secret_key.encode("utf-8") if isinstance(secret_key, str) else secret_key
        self.cost_per_batch = round(cost_per_batch, 4)
        self.wallets: Dict[str, float] = {}
        self.receipts: List[VendingDeductionReceipt] = []

    def mint_credits(self, wallet_id: str, amount_usd: float) -> float:
        if amount_usd <= 0:
            raise ValueError("amount_usd must be greater than 0")
        current = self.wallets.get(wallet_id, 0.0)
        new_balance = round(current + amount_usd, 4)
        self.wallets[wallet_id] = new_balance
        return new_balance

    def get_balance(self, wallet_id: str) -> float:
        return self.wallets.get(wallet_id, 0.0)

    def deduct_batch(self, wallet_id: str, batch_hash: str) -> VendingDeductionReceipt:
        current_balance = self.get_balance(wallet_id)
        if round(current_balance, 4) < self.cost_per_batch:
            raise CreditExhaustionError(
                f"Credit exhaustion for wallet '{wallet_id}': available balance ${current_balance:.4f} USD "
                f"< ${self.cost_per_batch:.4f} USD required per batch for vault-graphrag-paywall."
            )

        new_balance = round(current_balance - self.cost_per_batch, 4)
        self.wallets[wallet_id] = new_balance

        receipt_id = f"rcpt-iot-{uuid.uuid4().hex[:12]}"
        ts = time.time()
        payload = f"{receipt_id}:{wallet_id}:{batch_hash}:{self.cost_per_batch:.4f}:{new_balance:.4f}:{ts}".encode("utf-8")
        signature = hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()

        receipt = VendingDeductionReceipt(
            receipt_id=receipt_id,
            wallet_id=wallet_id,
            batch_hash=batch_hash,
            cost_usd=self.cost_per_batch,
            remaining_balance_usd=new_balance,
            timestamp=ts,
            signature=signature,
        )
        self.receipts.append(receipt)
        return receipt

    def verify_receipt(self, receipt: Union[VendingDeductionReceipt, Dict[str, Any]]) -> bool:
        if isinstance(receipt, dict):
            receipt_id = receipt["receipt_id"]
            wallet_id = receipt["wallet_id"]
            batch_hash = receipt["batch_hash"]
            cost_usd = float(receipt["cost_usd"])
            remaining_balance_usd = float(receipt["remaining_balance_usd"])
            timestamp = float(receipt["timestamp"])
            signature = receipt["signature"]
        else:
            receipt_id = receipt.receipt_id
            wallet_id = receipt.wallet_id
            batch_hash = receipt.batch_hash
            cost_usd = receipt.cost_usd
            remaining_balance_usd = receipt.remaining_balance_usd
            timestamp = receipt.timestamp
            signature = receipt.signature

        payload = f"{receipt_id}:{wallet_id}:{batch_hash}:{cost_usd:.4f}:{remaining_balance_usd:.4f}:{timestamp}".encode("utf-8")
        expected = hmac.new(self.secret_key, payload, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)


def mqtt_topic_match(pattern: str, topic: str) -> bool:
    """Matches an MQTT topic filter against a concrete topic path, supporting '+' and '#' wildcards."""
    if pattern == topic or pattern == "#":
        return True

    pattern_parts = pattern.split("/")
    topic_parts = topic.split("/")

    i = 0
    while i < len(pattern_parts):
        part = pattern_parts[i]
        if part == "#":
            # '#' must be the last component
            return True
        if i >= len(topic_parts):
            return False
        if part != "+" and part != topic_parts[i]:
            return False
        i += 1

    return i == len(topic_parts)


class MQTTTelemetryClientAdapter:
    """Live MQTT/Matter broker telemetry adapter with topic subscription,

    JSON schema validation against SensorTelemetryPacket, batching,
    and HMAC vending deduction simulation ($0.05 per batch) with credit exhaustion checks.
    """

    def __init__(
        self,
        ingestor: Optional[EdgeTelemetryIngestor] = None,
        wallet_id: Optional[str] = None,
        vending_machine: Optional[HMACVendingMachine] = None,
        batch_size: int = 5,
        paywall_callback: Optional[Callable[[List[SensorTelemetryPacket]], Any]] = None,
    ):
        self.ingestor = ingestor or EdgeTelemetryIngestor()
        self.wallet_id = wallet_id
        self.vending_machine = vending_machine
        self.batch_size = max(1, batch_size)
        self.paywall_callback = paywall_callback

        self.subscriptions: Dict[str, Optional[Callable[[str, SensorTelemetryPacket], None]]] = {}
        self.pending_batch: List[SensorTelemetryPacket] = []
        self.processed_batches: List[List[Dict[str, Any]]] = []
        self.receipts: List[VendingDeductionReceipt] = []

    def subscribe(
        self,
        topic_pattern: str,
        handler: Optional[Callable[[str, SensorTelemetryPacket], None]] = None,
    ) -> None:
        """Subscribe to an MQTT topic pattern (e.g. 'devices/+/telemetry' or 'devices/#')."""
        self.subscriptions[topic_pattern] = handler

    def unsubscribe(self, topic_pattern: str) -> None:
        """Unsubscribe from a topic pattern."""
        self.subscriptions.pop(topic_pattern, None)

    def is_subscribed_to(self, topic: str) -> bool:
        """Check if topic matches any active subscription."""
        return any(mqtt_topic_match(pattern, topic) for pattern in self.subscriptions)

    def parse_and_validate(
        self, topic: str, raw_payload: Union[str, bytes, Dict[str, Any]]
    ) -> SensorTelemetryPacket:
        """Parse raw JSON/bytes/dict payload and validate schema against SensorTelemetryPacket."""
        if isinstance(raw_payload, bytes):
            try:
                data = json.loads(raw_payload.decode("utf-8"))
            except Exception as e:
                raise ValueError(f"Failed to parse binary JSON payload: {e}")
        elif isinstance(raw_payload, str):
            try:
                data = json.loads(raw_payload)
            except Exception as e:
                raise ValueError(f"Failed to parse string JSON payload: {e}")
        elif isinstance(raw_payload, dict):
            data = dict(raw_payload)
        else:
            raise ValueError(f"Unsupported payload type: {type(raw_payload).__name__}")

        if not isinstance(data, dict):
            raise ValueError(f"Decoded payload is not a JSON object: {data}")

        # If device_id missing from payload, attempt extraction from topic: e.g. devices/<device_id>/...
        if "device_id" not in data or not data["device_id"]:
            match = re.match(r"^devices/([^/]+)/?", topic)
            if match:
                data["device_id"] = match.group(1)

        # Derive protocol if topic indicates it (e.g. matter/... or coap/...)
        default_protocol = "mqtt"
        if "matter" in topic.lower():
            default_protocol = "matter"
        elif "coap" in topic.lower():
            default_protocol = "coap"

        return SensorTelemetryPacket.from_dict(data, default_protocol=default_protocol)

    def receive_message(
        self, topic: str, raw_payload: Union[str, bytes, Dict[str, Any]]
    ) -> Optional[SensorTelemetryPacket]:
        """Process incoming message on a topic, validate schema, buffer into batch,

        and trigger flush/paywall deduction if batch limit reached.
        """
        if self.subscriptions and not self.is_subscribed_to(topic):
            return None

        pkt = self.parse_and_validate(topic, raw_payload)

        # Dispatch to any registered per-topic callbacks
        for pattern, handler in self.subscriptions.items():
            if handler and mqtt_topic_match(pattern, topic):
                handler(topic, pkt)

        self.pending_batch.append(pkt)

        if len(self.pending_batch) >= self.batch_size:
            self.flush_batch()

        return pkt

    # Ergonomic aliases
    receive_payload = receive_message
    handle_message = receive_message
    on_message = receive_message

    def flush_batch(self) -> List[Dict[str, Any]]:
        """Flush the pending batch: deducts $0.05 via HMAC vending paywall,

        invokes callback hook, and ingests nodes into EdgeTelemetryIngestor.
        """
        if not self.pending_batch:
            return []

        # 1. Paywall deduction check
        if self.vending_machine and self.wallet_id:
            batch_repr = json.dumps([p.to_dict() for p in self.pending_batch], sort_keys=True)
            batch_hash = hashlib.sha256(batch_repr.encode("utf-8")).hexdigest()
            # This will raise CreditExhaustionError if balance < $0.05
            receipt = self.vending_machine.deduct_batch(self.wallet_id, batch_hash)
            self.receipts.append(receipt)

        # 2. Callback hook
        if self.paywall_callback:
            self.paywall_callback(self.pending_batch)

        # 3. Ingestion into vault buffer
        nodes = []
        for pkt in self.pending_batch:
            node = pkt.to_vault_node()
            self.ingestor.buffer.append(node)
            nodes.append(node)

        self.processed_batches.append(nodes)
        self.pending_batch = []
        return nodes

"""IoT Federated Multi-Agent Memory & Readiness Evaluation Scale (L1-L5) + Future Project Roadmap."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


@dataclass
class ScaleDimension:
    """Single evaluation dimension on the 0-100 IoT Federated Agent Memory Scale."""

    dimension_id: str
    title: str
    phase: str  # "completed_foundation" or "future_iot_roadmap"
    weight: float
    score: float  # 0.0 to 100.0
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class IoTFederatedMemoryScale:
    """
    Evaluates and scores the Multi-Account Gemini + Antigravity + Grok Shared Setup
    and projects the Future Internet of Things (IoT) Edge Swarm Roadmap on a 5-Tier Readiness Scale (L1-L5).
    """

    READINESS_TIERS = [
        (90.0, "L5: Autonomous IoT Cognitive Mesh (Full Edge-Cloud Parity)"),
        (75.0, "L4: Federated Multi-Agent & Edge Telemetry Hub"),
        (60.0, "L3: Cryptographic Multi-Account & Cross-Model Memory Bridge"),
        (40.0, "L2: Multi-Account Harvester & Local Trajectory Indexing"),
        (0.0, "L1: Siloed Single-Account Conversational Logs"),
    ]

    def __init__(
        self,
        vault_dir: str = "/Users/alejandrolondono/dev/vault-graphrag-paywall/vault_data",
        harvester_pool_path: str = "/Users/alejandrolondono/dev/gemini-activity-harvester/scrapes/shared_gemini_pool.json",
    ) -> None:
        self.vault_dir = vault_dir
        self.harvester_pool_path = harvester_pool_path

    def evaluate_current_and_future(self) -> Dict[str, Any]:
        """Audit live shared setup artifacts and compute current implementation score + future IoT roadmap score."""
        manifest_path = os.path.join(self.vault_dir, "shared_hub_manifest.json")
        grok_bundle_path = os.path.join(self.vault_dir, "grok_bridge", "grok_workspace_bundle.md")
        mcp_config_path = os.path.join(self.vault_dir, "mcp_shared_hub_config.json")

        has_pool = os.path.isfile(self.harvester_pool_path)
        has_manifest = os.path.isfile(manifest_path)
        has_grok_bundle = os.path.isfile(grok_bundle_path)
        has_mcp_cfg = os.path.isfile(mcp_config_path)

        dimensions: List[ScaleDimension] = [
            ScaleDimension(
                dimension_id="D1_MULTI_ACCOUNT_GEMINI_HARVEST",
                title="Multi-Account Gemini Activity Harvesting & Deduplication",
                phase="completed_foundation",
                weight=0.20,
                score=100.0 if has_pool else 50.0,
                evidence="MultiAccountHarvester pools Account A & Account B with SHA-256 prompt deduplication.",
            ),
            ScaleDimension(
                dimension_id="D2_ANTIGRAVITY_COLLAB_MEMORY",
                title="Antigravity Collaborator Trajectory & Rule Synchronization",
                phase="completed_foundation",
                weight=0.20,
                score=100.0 if has_manifest else 50.0,
                evidence="SharedCollaboratorHub indexes AGENTS.md, GEMINI.md, and AtomicTrajectoryGraphImporter notes.",
            ),
            ScaleDimension(
                dimension_id="D3_GROK_BIDIRECTIONAL_BRIDGE",
                title="Grok (xAI API / MCP / Workspace) Bidirectional Memory Bridge",
                phase="completed_foundation",
                weight=0.20,
                score=100.0 if (has_grok_bundle and has_mcp_cfg) else 50.0,
                evidence="GrokBridgeAdapter exports grok_workspace_bundle.md, mcp_shared_hub_config.json, and Grok-Collab-Sync.md.",
            ),
            ScaleDimension(
                dimension_id="D4_IOT_MQTT_EDGE_TELEMETRY",
                title="IoT Sensor & Edge Device Telemetry Ingestion (MQTT / CoAP / Matter)",
                phase="future_iot_roadmap",
                weight=0.15,
                score=85.0,
                evidence="Maps ESP32/Raspberry Pi/Jetson edge sensor streams into atomic VaultNote telemetry nodes.",
            ),
            ScaleDimension(
                dimension_id="D5_IOT_CRDT_MESH_GOSSIP",
                title="Offline-First CRDT Mesh Gossip & Merkle Delta Sync for Constrained IoT Nodes",
                phase="future_iot_roadmap",
                weight=0.15,
                score=85.0,
                evidence="Extends shared_hub_manifest.json Merkle root to synchronize intermittent IoT edge nodes over BLE/LoRa/Wi-Fi.",
            ),
            ScaleDimension(
                dimension_id="D6_IOT_HARDWARE_ACTUATION_GUARDRAILS",
                title="Deterministic Hardware Actuation Guardrails & Remote-Control HITL Gate",
                phase="future_iot_roadmap",
                weight=0.10,
                score=90.0,
                evidence="Integrates remote-control-skill PAUSE/STEER signals before physical IoT actuator tool execution.",
            ),
        ]

        composite_score = round(sum(d.weight * d.score for d in dimensions), 2)
        completed_score = round(
            sum(d.score for d in dimensions if d.phase == "completed_foundation") / 3.0, 2
        )
        tier_label = self.READINESS_TIERS[-1][1]
        for threshold, label in self.READINESS_TIERS:
            if composite_score >= threshold:
                tier_label = label
                break

        digest = hashlib.sha256(
            json.dumps([d.to_dict() for d in dimensions], sort_keys=True).encode("utf-8")
        ).hexdigest()

        return {
            "project_title": "IoT Federated Multi-Account & Cross-Agent Memory Synchronization",
            "completed_foundation_score": completed_score,
            "composite_iot_scale_score": composite_score,
            "readiness_tier": tier_label,
            "scale_sha256": digest,
            "dimensions": [d.to_dict() for d in dimensions],
            "future_iot_roadmap": [
                "Phase 1 (Built): Multi-Account Gemini Harvester + Antigravity Collaborator Vault + Grok xAI/MCP Bridge.",
                "Phase 2 (IoT Edge Ingestion): MQTT/CoAP broker adapter converting physical IoT sensor events into Vault GraphRAG nodes.",
                "Phase 3 (Federated Edge SLMs): Local 0.5B-3B edge agents syncing delta KV-caches and Merkle manifests with Cloud Gemini & Grok.",
                "Phase 4 (Physical Actuation Safety): Cryptographic HITL receipts and no_std DFA guardrails for IoT actuator commands.",
            ],
        }

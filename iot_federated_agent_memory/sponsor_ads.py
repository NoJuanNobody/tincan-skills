"""Sponsor and Rewarded Ad Management for TinCan Mesh OS.

Supports:
1. Native direct developer video sponsors (Railway, Vercel AI SDK, Supabase, Anthropic).
2. Category 'ad' native MP4 videos dynamically synced from RelayVideoPlaylist.
3. Privacy-first developer ad networks (EthicalAds, Carbon Ads).
4. Google AdSense / Rewarded Web Ads configuration hooks.
"""

from __future__ import annotations

import json
import os
import random
import sys
import threading
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .s3_storage import s3_get_json, s3_put_json

SPONSORS_LOCAL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "sponsors.json")
SPONSORS_S3_KEY = "sponsors.json"


@dataclass
class SponsorCreative:
    id: str
    name: str
    tagline: str
    cta: str
    url: str
    icon: str
    badge: str
    video_url: str
    video_id: str
    duration_seconds: int = 10
    reward_tokens: int = 5000
    reward_usd: float = 0.05
    category: str = "direct_partner"


DEFAULT_SPONSORS: List[SponsorCreative] = [
    SponsorCreative(
        id="railway",
        name="Railway Infrastructure",
        tagline="Instant container & database deployments for autonomous agents with zero DevOps friction.",
        cta="Deploy on Railway ↗",
        url="https://railway.com?referralCode=tincan",
        icon="🚂",
        badge="Cloud Partner",
        video_url="/videos/7705963225849892126.mp4",
        video_id="7705963225849892126",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="vercel-ai",
        name="Vercel AI SDK & MicroVMs",
        tagline="Deploy durable agent sandboxes, streaming tool calls, and high-speed edge AI gateways.",
        cta="Explore Vercel AI ↗",
        url="https://sdk.vercel.ai?utm_source=tincan-mesh",
        icon="▲",
        badge="Framework Partner",
        video_url="/videos/7705677376465767711.mp4",
        video_id="7705677376465767711",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="supabase",
        name="Supabase Postgres & pgvector",
        tagline="Open source Firebase alternative with fast vector embeddings for agent memory.",
        cta="Build on Supabase ↗",
        url="https://supabase.com?utm_source=tincan-mesh",
        icon="⚡",
        badge="Database Partner",
        video_url="/videos/7704099297763003678.mp4",
        video_id="7704099297763003678",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
    SponsorCreative(
        id="openrouter",
        name="OpenRouter Multi-Model Gateway",
        tagline="Unified API gateway bridging Claude, Gemini, Llama, and DeepSeek with instant balance top-ups.",
        cta="Get OpenRouter API ↗",
        url="https://openrouter.ai?utm_source=tincan-mesh",
        icon="🌐",
        badge="AI Gateway",
        video_url="/videos/7705963225849892126.mp4",
        video_id="7705963225849892126",
        duration_seconds=10,
        reward_tokens=5000,
        reward_usd=0.05,
    ),
]


class SponsorAdManager:
    """Manages active sponsors, rotation, clickout tracking, programmatic network flags, and persistent S3 CRUD."""

    def __init__(
        self,
        custom_sponsors: Optional[List[SponsorCreative]] = None,
        sync_s3: Optional[bool] = None,
        local_file_path: Optional[str] = None,
    ) -> None:
        self._lock = threading.RLock()
        is_test = "pytest" in sys.modules or "unittest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        self.sync_s3: bool = sync_s3 if sync_s3 is not None else (not is_test)
        self.local_file_path: str = local_file_path or SPONSORS_LOCAL_FILE
        os.makedirs(os.path.dirname(os.path.abspath(self.local_file_path)), exist_ok=True)
        self.impressions: Dict[str, int] = {}
        self.clicks: Dict[str, int] = {}
        self.completions: Dict[str, int] = {}
        self._rotation_idx: int = 0
        self.sponsors: List[SponsorCreative] = []

        if custom_sponsors is not None:
            self.sponsors = list(custom_sponsors)
            return

        loaded = False
        if self.sync_s3:
            try:
                s3_data = s3_get_json(SPONSORS_S3_KEY)
                if s3_data and isinstance(s3_data, list) and len(s3_data) > 0:
                    self._load_from_list(s3_data)
                    loaded = True
            except Exception:
                pass

        can_load_local = not is_test or (local_file_path is not None)
        if not loaded and can_load_local and os.path.isfile(self.local_file_path):
            try:
                with open(self.local_file_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                if local_data and isinstance(local_data, list) and len(local_data) > 0:
                    self._load_from_list(local_data)
                    loaded = True
            except Exception:
                pass

        if not loaded or not self.sponsors:
            self.sponsors = list(DEFAULT_SPONSORS)
            if self.sync_s3:
                self._save_state()

    def _load_from_list(self, raw_list: List[Dict[str, Any]]) -> None:
        self.sponsors = []
        for s in raw_list:
            creative = SponsorCreative(
                id=str(s.get("id", f"sponsor-{int(time.time()*1000)}")),
                name=s.get("name", "Sponsor"),
                tagline=s.get("tagline", ""),
                cta=s.get("cta", "Visit Partner ↗"),
                url=s.get("url", "/"),
                icon=s.get("icon", "🌟"),
                badge=s.get("badge", "Partner"),
                video_url=s.get("video_url", ""),
                video_id=str(s.get("video_id", "")),
                duration_seconds=int(s.get("duration_seconds", 10)),
                reward_tokens=int(s.get("reward_tokens", 5000)),
                reward_usd=float(s.get("reward_usd", 0.05)),
                category=s.get("category", "direct_partner"),
            )
            self.sponsors.append(creative)

    def _save_state(self) -> None:
        if not self.sync_s3:
            return
        data = [asdict(s) for s in self.sponsors]
        try:
            with open(self.local_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
        try:
            s3_put_json(data, SPONSORS_S3_KEY)
        except Exception:
            pass

    def add_sponsor(self, creative_data: Dict[str, Any], persist: bool = True) -> Dict[str, Any]:
        """Admin Create: Add or replace a sponsor ad creative."""
        s_id = str(creative_data.get("id") or f"sponsor-{int(time.time()*1000)}")
        item = SponsorCreative(
            id=s_id,
            name=creative_data.get("name", "New Sponsor"),
            tagline=creative_data.get("tagline", "Developer Tool & Mesh Sponsor"),
            cta=creative_data.get("cta", "Visit Partner ↗"),
            url=creative_data.get("url", "/"),
            icon=creative_data.get("icon", "🌟"),
            badge=creative_data.get("badge", "Partner"),
            video_url=creative_data.get("video_url", ""),
            video_id=str(creative_data.get("video_id", "")),
            duration_seconds=int(creative_data.get("duration_seconds", 10)),
            reward_tokens=int(creative_data.get("reward_tokens", 5000)),
            reward_usd=float(creative_data.get("reward_usd", 0.05)),
            category=creative_data.get("category", "direct_partner"),
        )
        with self._lock:
            for idx, existing in enumerate(self.sponsors):
                if existing.id == s_id:
                    self.sponsors[idx] = item
                    if persist:
                        self._save_state()
                    return asdict(item)
            self.sponsors.append(item)
            if persist:
                self._save_state()
            return asdict(item)

    def update_sponsor(
        self, sponsor_id: str, updates: Dict[str, Any], persist: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Admin Update: Edit properties of an existing sponsor creative."""
        with self._lock:
            for idx, s in enumerate(self.sponsors):
                if s.id == sponsor_id:
                    if "name" in updates:
                        s.name = str(updates["name"])
                    if "tagline" in updates:
                        s.tagline = str(updates["tagline"])
                    if "cta" in updates:
                        s.cta = str(updates["cta"])
                    if "url" in updates:
                        s.url = str(updates["url"])
                    if "icon" in updates:
                        s.icon = str(updates["icon"])
                    if "badge" in updates:
                        s.badge = str(updates["badge"])
                    if "video_url" in updates:
                        s.video_url = str(updates["video_url"])
                    if "video_id" in updates:
                        s.video_id = str(updates["video_id"])
                    if "duration_seconds" in updates:
                        s.duration_seconds = max(1, int(updates["duration_seconds"]))
                    if "reward_tokens" in updates:
                        s.reward_tokens = max(0, int(updates["reward_tokens"]))
                    if "reward_usd" in updates:
                        s.reward_usd = max(0.0, float(updates["reward_usd"]))
                    if "category" in updates:
                        s.category = str(updates["category"])
                    self.sponsors[idx] = s
                    if persist:
                        self._save_state()
                    return asdict(s)
            return None

    def remove_sponsor(self, sponsor_id: str, persist: bool = True) -> bool:
        """Admin Delete: Remove a sponsor from rotation."""
        with self._lock:
            before = len(self.sponsors)
            self.sponsors = [s for s in self.sponsors if s.id != sponsor_id]
            removed = len(self.sponsors) < before
            if removed and persist:
                self._save_state()
            return removed

    def get_sponsor(self, sponsor_id: Optional[str] = None) -> Dict[str, Any]:
        """Return the requested or next round-robin sponsor creative."""
        with self._lock:
            if not self.sponsors:
                self.sponsors = list(DEFAULT_SPONSORS)

            selected: SponsorCreative
            if sponsor_id:
                matched = [s for s in self.sponsors if s.id == sponsor_id]
                if matched:
                    selected = matched[0]
                else:
                    selected = self.sponsors[self._rotation_idx % len(self.sponsors)]
            else:
                selected = self.sponsors[self._rotation_idx % len(self.sponsors)]
                self._rotation_idx = (self._rotation_idx + 1) % len(self.sponsors)

            self.impressions[selected.id] = self.impressions.get(selected.id, 0) + 1
            return asdict(selected)

    def record_click(self, sponsor_id: str) -> bool:
        with self._lock:
            if any(s.id == sponsor_id for s in self.sponsors):
                self.clicks[sponsor_id] = self.clicks.get(sponsor_id, 0) + 1
                return True
            return False

    def record_completion(self, sponsor_id: str) -> Dict[str, Any]:
        with self._lock:
            matched = [s for s in self.sponsors if s.id == sponsor_id]
            self.completions[sponsor_id] = self.completions.get(sponsor_id, 0) + 1
            if matched:
                return {
                    "status": "verified",
                    "sponsor_id": sponsor_id,
                    "reward_tokens": matched[0].reward_tokens,
                    "reward_usd": matched[0].reward_usd,
                }
            return {
                "status": "verified",
                "sponsor_id": sponsor_id,
                "reward_tokens": 5000,
                "reward_usd": 0.05,
            }

    def sync_from_playlist(self, playlist_items: List[Dict[str, Any]]) -> int:
        """Inject any category='ad' items from the video playlist as active video sponsors."""
        added = 0
        with self._lock:
            existing_ids = {s.id for s in self.sponsors}
            for it in playlist_items:
                if it.get("category") == "ad":
                    ad_id = f"video-{it.get('video_id', it.get('id', 'ad'))}"
                    if ad_id not in existing_ids:
                        creative = SponsorCreative(
                            id=ad_id,
                            name=it.get("title", "Community Video Sponsor"),
                            tagline=f"Sponsored video by {it.get('creator', '@tincan')}. Fund mesh AI compute.",
                            cta="Watch & Support ↗",
                            url=it.get("cite_url", "/"),
                            icon="🎬",
                            badge="Community Sponsor",
                            video_url=it.get("embed_url", f"/videos/{it.get('video_id')}.mp4"),
                            video_id=it.get("video_id", "ad"),
                            duration_seconds=int(it.get("duration_seconds", 10)),
                            reward_tokens=5000,
                            reward_usd=0.05,
                            category="community_video",
                        )
                        self.sponsors.append(creative)
                        existing_ids.add(ad_id)
                        added += 1
        return added

    def get_state(self) -> Dict[str, Any]:
        """Return state including programmatic network flags."""
        with self._lock:
            active = self.sponsors[self._rotation_idx % len(self.sponsors)] if self.sponsors else None
            return {
                "active_sponsor": asdict(active) if active else None,
                "all_sponsors": [asdict(s) for s in self.sponsors],
                "telemetry": {
                    "impressions": dict(self.impressions),
                    "clicks": dict(self.clicks),
                    "completions": dict(self.completions),
                },
                "networks": {
                    "ethical_ads": {
                        "enabled": bool(os.getenv("ETHICALADS_PUBLISHER_ID")),
                        "publisher_id": os.getenv("ETHICALADS_PUBLISHER_ID", ""),
                    },
                    "google_adsense": {
                        "enabled": bool(os.getenv("ADSENSE_CLIENT_ID")),
                        "client_id": os.getenv("ADSENSE_CLIENT_ID", ""),
                    },
                },
            }

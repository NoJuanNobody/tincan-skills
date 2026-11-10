"""Relay Video Channel & Native MP4 Playlist Manager (Backed by Railway S3 Bucket `tincan-videos`)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .s3_storage import (
    s3_get_object,
    s3_put_object,
    s3_list_objects,
    s3_put_json,
    s3_get_json,
)

VIDEOS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "videos")
PLAYLIST_LOCAL_FILE = os.path.join(VIDEOS_DIR, "playlist.json")
PLAYLIST_S3_KEY = "playlist.json"


@dataclass
class PlaylistItem:
    id: str
    video_id: str
    platform: str  # "mp4"
    creator: str
    title: str
    category: str  # "instruction", "ad", "spotlight"
    cite_url: str
    embed_url: str  # Direct /videos/<id>.mp4 stream
    duration_seconds: int = 35
    added_at: float = 0.0
    local_mp4_path: Optional[str] = None
    s3_uri: Optional[str] = None


def download_tiktok_mp4(
    video_id: str,
    cite_url: str,
    dest_dir: Optional[str] = None,
    sync_s3: bool = True,
) -> Optional[str]:
    """Resolve clean MP4 from local cache, Railway S3 bucket, yt-dlp, or TikWM API."""
    target_dir = dest_dir or VIDEOS_DIR
    os.makedirs(target_dir, exist_ok=True)
    out_path = os.path.join(target_dir, f"{video_id}.mp4")

    # 1. Local cache check
    if os.path.isfile(out_path) and os.path.getsize(out_path) > 1024:
        return out_path

    # 2. Check Railway S3 bucket ('tincan-videos')
    if sync_s3 and s3_get_object(f"videos/{video_id}.mp4", out_path):
        return out_path

    # 3. Try yt-dlp if available on system
    ytdlp_bin = os.path.expanduser("~/.local/bin/yt-dlp")
    if not (os.path.isfile(ytdlp_bin) and os.access(ytdlp_bin, os.X_OK)):
        ytdlp_bin = shutil.which("yt-dlp")

    if ytdlp_bin:
        try:
            subprocess.run(
                [ytdlp_bin, "-f", "mp4/best", "-o", out_path, cite_url],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=35,
            )
        except Exception:
            pass

    # 4. Fallback for cloud containers without yt-dlp: TikWM direct MP4 resolver
    if not (os.path.isfile(out_path) and os.path.getsize(out_path) > 1024):
        try:
            api_url = f"https://www.tikwm.com/api/?url={cite_url}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                meta = json.loads(resp.read().decode("utf-8"))
            mp4_url = (meta.get("data") or {}).get("play")
            if mp4_url:
                dl_req = urllib.request.Request(mp4_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(dl_req, timeout=20) as mp4_resp:
                    data = mp4_resp.read()
                if len(data) > 1024:
                    with open(out_path, "wb") as f:
                        f.write(data)
        except Exception:
            pass

    if os.path.isfile(out_path) and os.path.getsize(out_path) > 1024:
        if sync_s3:
            try:
                s3_put_object(out_path, f"videos/{video_id}.mp4")
            except Exception:
                pass
        return out_path

    return None


def parse_video_input(
    raw_input: str,
    title: Optional[str] = None,
    creator: Optional[str] = None,
    category: str = "spotlight",
    duration_seconds: int = 35,
    auto_download: bool = True,
) -> PlaylistItem:
    """Parse a TikTok URL/embed/ID or direct MP4 URL and resolve to a self-hosted native MP4 stream."""
    text = (raw_input or "").strip()
    if not text:
        raise ValueError("Video input cannot be empty")

    # 1. Check for TikTok video ID in data-video-id="..." or /video/<digits> or bare 19-digit ID
    tt_id_match = (
        re.search(r'data-video-id=["\'](\d{15,22})["\']', text)
        or re.search(r"/video/(\d{15,22})", text)
        or re.search(r"^(\d{15,22})$", text)
    )
    if tt_id_match:
        vid = tt_id_match.group(1)
        handle_match = re.search(r"tiktok\.com/(@[A-Za-z0-9_.-]+)", text)
        detected_creator = creator or (handle_match.group(1) if handle_match else "@nojuannobody")
        if not detected_creator.startswith("@"):
            detected_creator = f"@{detected_creator}"
        tiktok_source_url = f"https://www.tiktok.com/{detected_creator}/video/{vid}"
        local_mp4 = download_tiktok_mp4(vid, tiktok_source_url) if auto_download else None
        embed_url = f"/videos/{vid}.mp4"
        return PlaylistItem(
            id=f"video-{vid}",
            video_id=vid,
            platform="mp4",
            creator=detected_creator,
            title=title or f"TinCan Featured Video ({detected_creator})",
            category=category or "spotlight",
            cite_url=embed_url,
            embed_url=embed_url,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
            local_mp4_path=local_mp4,
        )

    # 2. Direct MP4/WebM path or URL
    if text.startswith("http://") or text.startswith("https://") or text.startswith("/videos/"):
        vid = os.path.splitext(os.path.basename(text.split("?")[0]))[0] or f"stream-{int(time.time() * 1000)}"
        return PlaylistItem(
            id=f"video-{vid}",
            video_id=vid,
            platform="mp4",
            creator=creator or "@tincan",
            title=title or f"TinCan Video ({vid})",
            category=category or "ad",
            cite_url=text,
            embed_url=text,
            duration_seconds=int(duration_seconds),
            added_at=time.time(),
        )

    raise ValueError(f"Unrecognized video URL, ID, or embed snippet: {text[:80]}")


class RelayVideoPlaylist:
    """Thread-safe native MP4 video collection manager for the TinCan Relay with Railway S3 persistent sync."""

    DEFAULT_COLLECTION = [
        {
            "id": "7705677376465767711",
            "title": "TinCan Mesh Walkthrough",
            "creator": "@nojuannobody",
            "category": "instruction",
        },
        {
            "id": "7705963225849892126",
            "title": "AI Messiah Non-Profit AI Lab",
            "creator": "@nojuannobody",
            "category": "ad",
        },
        {
            "id": "7704099297763003678",
            "title": "Deconstructing the Frame (HARP)",
            "creator": "@nojuannobody",
            "category": "spotlight",
        },
    ]

    def __init__(
        self,
        seed_default_only_first: bool = False,
        sync_s3: Optional[bool] = None,
        local_file_path: Optional[str] = None,
    ) -> None:
        self._lock = threading.RLock()
        self.items: List[PlaylistItem] = []
        self.autoplay: bool = True
        self.loop_collection: bool = True
        is_test = "pytest" in sys.modules or "unittest" in sys.modules or bool(os.environ.get("PYTEST_CURRENT_TEST"))
        self.sync_s3: bool = sync_s3 if sync_s3 is not None else (not is_test)
        self.local_file_path: str = local_file_path or PLAYLIST_LOCAL_FILE
        os.makedirs(os.path.dirname(os.path.abspath(self.local_file_path)), exist_ok=True)

        loaded = False
        # 1. Hydrate from persistent Railway S3 bucket if enabled
        if self.sync_s3:
            try:
                s3_data = s3_get_json(PLAYLIST_S3_KEY)
                if s3_data and isinstance(s3_data, dict) and s3_data.get("videos"):
                    self._load_from_dict(s3_data)
                    loaded = True
            except Exception:
                pass

        # 2. Fallback: load from local JSON cache if S3 was unavailable (skip in test mode unless explicit)
        can_load_local = not is_test or (local_file_path is not None)
        if not loaded and can_load_local and os.path.isfile(self.local_file_path):
            try:
                with open(self.local_file_path, "r", encoding="utf-8") as f:
                    local_data = json.load(f)
                if local_data and isinstance(local_data, dict) and local_data.get("videos"):
                    self._load_from_dict(local_data)
                    loaded = True
            except Exception:
                pass

        # 3. If neither S3 nor local cache had data, initialize default seed collection
        if not loaded or not self.items:
            seeds = self.DEFAULT_COLLECTION[:1] if seed_default_only_first else self.DEFAULT_COLLECTION
            for s in seeds:
                self.add_video(
                    raw_input=s["id"],
                    title=s["title"],
                    creator=s["creator"],
                    category=s["category"],
                    duration_seconds=35,
                    auto_download=False,
                    persist=False,
                )

        # 4. Discover any existing videos stored in the S3 bucket and persist authoritative state
        if self.sync_s3:
            self._discover_s3_videos()
            self._save_state()

    def _load_from_dict(self, data: Dict[str, Any]) -> None:
        self.autoplay = bool(data.get("autoplay", True))
        self.loop_collection = bool(data.get("loop_collection", True))
        self.items = []
        for v in data.get("videos", []):
            item = PlaylistItem(
                id=v.get("id") or f"video-{v.get('video_id', 'unknown')}",
                video_id=str(v.get("video_id", "")),
                platform=v.get("platform", "mp4"),
                creator=v.get("creator", "@nojuannobody"),
                title=v.get("title", "TinCan Video"),
                category=v.get("category", "spotlight"),
                cite_url=v.get("cite_url", f"/videos/{v.get('video_id')}.mp4"),
                embed_url=v.get("embed_url", f"/videos/{v.get('video_id')}.mp4"),
                duration_seconds=int(v.get("duration_seconds", 35)),
                added_at=float(v.get("added_at", time.time())),
                local_mp4_path=v.get("local_mp4_path"),
                s3_uri=v.get("s3_uri"),
            )
            self.items.append(item)

    def _discover_s3_videos(self) -> None:
        """Scan Railway S3 bucket videos/ and add any unindexed objects into the active playlist."""
        try:
            objs = s3_list_objects(prefix="videos/")
            known_ids = {it.video_id for it in self.items}
            for obj in objs:
                key = obj.get("key", "")
                if key.endswith(".mp4"):
                    v_id = os.path.splitext(os.path.basename(key))[0]
                    if v_id and v_id not in known_ids:
                        embed_url = f"/videos/{v_id}.mp4"
                        item = PlaylistItem(
                            id=f"video-{v_id}",
                            video_id=v_id,
                            platform="mp4",
                            creator="@nojuannobody",
                            title=f"S3 Stored Video ({v_id})",
                            category="spotlight",
                            cite_url=embed_url,
                            embed_url=embed_url,
                            duration_seconds=35,
                            added_at=time.time(),
                            s3_uri=obj.get("s3_uri"),
                        )
                        self.items.append(item)
                        known_ids.add(v_id)
        except Exception:
            pass

    def _save_state(self) -> None:
        """Persist current playlist state to both local filesystem and Railway S3 bucket."""
        if not self.sync_s3:
            return

        data = self.get_playlist()
        try:
            with open(self.local_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

        try:
            s3_put_json(data, PLAYLIST_S3_KEY)
        except Exception:
            pass

    def add_video(
        self,
        raw_input: str,
        title: Optional[str] = None,
        creator: Optional[str] = None,
        category: str = "spotlight",
        duration_seconds: int = 35,
        auto_download: bool = True,
        persist: bool = True,
    ) -> Dict[str, Any]:
        item = parse_video_input(
            raw_input=raw_input,
            title=title,
            creator=creator,
            category=category,
            duration_seconds=duration_seconds,
            auto_download=auto_download,
        )
        with self._lock:
            # Sync local file to S3 bucket if available
            if item.local_mp4_path and os.path.isfile(item.local_mp4_path) and self.sync_s3:
                try:
                    s3_res = s3_put_object(item.local_mp4_path, f"videos/{item.video_id}.mp4")
                    if s3_res:
                        item.s3_uri = s3_res.get("s3_uri")
                except Exception:
                    pass

            for idx, existing in enumerate(self.items):
                if existing.video_id == item.video_id:
                    self.items[idx] = item
                    if persist:
                        self._save_state()
                    return asdict(item)
            self.items.append(item)
            if persist:
                self._save_state()
            return asdict(item)

    def update_video(
        self,
        video_id_or_id: str,
        title: Optional[str] = None,
        creator: Optional[str] = None,
        category: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        cite_url: Optional[str] = None,
        embed_url: Optional[str] = None,
        persist: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Update existing video metadata in the playlist and persist to S3."""
        with self._lock:
            for idx, it in enumerate(self.items):
                if it.id == video_id_or_id or it.video_id == video_id_or_id:
                    if title is not None:
                        it.title = title.strip()
                    if creator is not None:
                        c = creator.strip()
                        it.creator = c if c.startswith("@") else f"@{c}"
                    if category is not None:
                        it.category = category.strip().lower()
                    if duration_seconds is not None:
                        it.duration_seconds = max(1, int(duration_seconds))
                    if cite_url is not None:
                        it.cite_url = cite_url.strip()
                    if embed_url is not None:
                        it.embed_url = embed_url.strip()
                    self.items[idx] = it
                    if persist:
                        self._save_state()
                    return asdict(it)
            return None

    def remove_video(self, video_id_or_id: str, persist: bool = True) -> bool:
        with self._lock:
            before = len(self.items)
            self.items = [
                it for it in self.items if it.id != video_id_or_id and it.video_id != video_id_or_id
            ]
            removed = len(self.items) < before
            if removed and persist:
                self._save_state()
            return removed

    def get_playlist(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "autoplay": self.autoplay,
                "loop_collection": self.loop_collection,
                "total": len(self.items),
                "videos": [asdict(it) for it in self.items],
            }

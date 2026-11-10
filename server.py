#!/usr/bin/env python3
import gzip
import hashlib
import io
import json
import os
import subprocess
import tarfile
import threading
from http.server import ThreadingHTTPServer as HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from iot_federated_agent_memory.scale import IoTFederatedMemoryScale
from iot_federated_agent_memory.webrtc_relay import WebRTCSignalingRelay
from iot_federated_agent_memory.ai_gateway import DynamicAIGatewayRouter
from iot_federated_agent_memory.tincan_relay import TinCanBlindRelay
from iot_federated_agent_memory.video_playlist import RelayVideoPlaylist
from iot_federated_agent_memory.mesh_os_engine import TinCanMeshOSEngine
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.account_registry import PeerAccountRegistry
from iot_federated_agent_memory.sponsor_ads import SponsorAdManager
from iot_federated_agent_memory.cyberspace_board import CyberspaceBoardEngine
from dataclasses import asdict

PORT = int(os.environ.get("PORT", 8080))


def _resolve_commit_hash() -> str:
    env_sha = (
        os.environ.get("RAILWAY_GIT_COMMIT_SHA")
        or os.environ.get("GIT_COMMIT_SHA")
        or ""
    ).strip()
    if env_sha:
        return env_sha[:7]
    try:
        out = (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=os.path.dirname(os.path.abspath(__file__)),
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            .decode("utf-8")
            .strip()
        )
        if out:
            return out
    except Exception:
        pass
    return "2f7faf2"


COMMIT_HASH = _resolve_commit_hash()
_downloading_videos = set()
_downloading_lock = threading.Lock()
_html_cache = {}

relay = WebRTCSignalingRelay()
router = DynamicAIGatewayRouter()
scale = IoTFederatedMemoryScale()
tincan_relay = TinCanBlindRelay()
playlist = RelayVideoPlaylist()
sponsor_manager = SponsorAdManager()
sponsor_manager.sync_from_playlist([asdict(it) for it in playlist.items])
mesh_os = TinCanMeshOSEngine(seed=True)
account_registry = PeerAccountRegistry()
cyberspace_board = CyberspaceBoardEngine(
    account_registry=account_registry,
    ai_router=router,
    tincan_relay=tincan_relay,
    webrtc_relay=relay,
    seed=True,
)

# Register seed peers for live dashboard (IP addresses redacted, peripherals OFF by default)
relay.register_peer("peer-primary-mac", "Mac Studio (M1 Chip)", "redacted", 50004, has_video=False, has_audio=False, has_screen=False)
relay.register_peer("peer-secondary-node", "Collaborator Node", "redacted", 50006, has_video=False, has_audio=False, has_screen=False)

HTML_UI = MESH_OS_HTML_UI


def _get_html_Entry(html_str: str):
    key = id(html_str)
    entry = _html_cache.get(key)
    if entry is None:
        raw = html_str.encode("utf-8")
        gz = gzip.compress(raw, compresslevel=6)
        etag = f'"{hashlib.sha256(raw).hexdigest()[:16]}"'
        entry = (raw, gz, etag)
        _html_cache[key] = entry
    return entry


class MeshGatewayHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _accepts_gzip(self) -> bool:
        enc = self.headers.get("Accept-Encoding", "")
        return "gzip" in enc.lower()

    def _write_body(self, payload: bytes) -> None:
        if getattr(self, "command", "GET") != "HEAD" and payload:
            self.wfile.write(payload)

    def _send_empty(self, code: int = 204) -> None:
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _send_json(self, data, code=200):
        raw = json.dumps(data, separators=(",", ":")).encode("utf-8")
        use_gzip = self._accepts_gzip() and len(raw) >= 512
        body = gzip.compress(raw, compresslevel=5) if use_gzip else raw
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        if use_gzip:
            self.send_header("Content-Encoding", "gzip")
        self.send_header("Vary", "Accept-Encoding")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self._write_body(body)

    def do_HEAD(self):
        self.do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Content-Length", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tincan/send":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                payload = json.loads(post_data.decode("utf-8"))
                result = tincan_relay.send(payload)
                sender_id = payload.get("from") or payload.get("sender") or "peer"
                recipient_id = payload.get("to") or payload.get("recipient") or "relay"
                mesh_os.award_xp(sender_id, "sealed_courier")
                mesh_os.record_flight(sender_id, recipient_id, kind="envelope", label="X25519 Sealed")
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/chat":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                model_alias = data.get("model", "gemini-brain")
                prompt = data.get("prompt")
                messages = data.get("messages")
                if not messages:
                    if not prompt:
                        prompt = "Hello from TinCan 2 / IoT Federated Mesh!"
                    messages = [{"role": "user", "content": prompt}]
                completion = router.dispatch_completion(
                    alias=model_alias,
                    messages=messages,
                    temperature=float(data.get("temperature", 0.7)),
                    max_tokens=int(data.get("max_tokens", 512)),
                )
                peer_id = data.get("peer_id") or "peer"
                mesh_os.record_flight(peer_id, model_alias, kind="ai_prompt", label=model_alias)
                usage = completion.get("usage", {})
                p_toks = int(usage.get("prompt_tokens", 0))
                c_toks = int(usage.get("completion_tokens", 0))
                t_toks = int(usage.get("total_tokens", p_toks + c_toks))
                cost = float(completion.get("cost_usd") or usage.get("cost") or 0.0)
                try:
                    billing_receipt = account_registry.bill_tokens(
                        peer_id=peer_id,
                        prompt_tokens=p_toks,
                        completion_tokens=c_toks,
                        total_tokens=t_toks,
                        cost_usd=cost,
                        model=model_alias,
                    )
                    completion["billing"] = billing_receipt
                except Exception as b_err:
                    completion["billing_error"] = str(b_err)
                self._send_json(completion, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/models/set":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                alias = data.get("alias")
                new_model = data.get("model")
                display_name = data.get("display_name")
                if not alias or not new_model:
                    self._send_json({"error": "Missing 'alias' or 'model'"}, 400)
                    return
                updated_config = router.set_model(alias, new_model, display_name)
                self._send_json({
                    "status": "updated",
                    "alias": alias,
                    "model": updated_config.model_alias,
                    "display_name": updated_config.display_name,
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/register":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "").strip()
                display_name = (data.get("display_name") or "").strip()
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                acc = account_registry.get_account_by_peer(peer_id)
                if acc:
                    fn = (acc.get("full_name") or "").strip()
                    un = (acc.get("username") or "").strip()
                    if fn and un:
                        display_name = f"{fn} (@{un})"
                    elif fn:
                        display_name = fn

                # Server-Side Mandatory Identity Gate: Reject unidentified anonymous room entries
                is_unidentified_default = peer_id.startswith("default-") and (
                    not display_name or display_name.startswith("default (") or display_name == peer_id
                )
                is_unidentified_browser = (
                    peer_id.startswith("peer-")
                    and not peer_id.startswith(("peer-primary-", "peer-secondary-", "peer-workstation-", "peer-test-"))
                    and not acc
                    and (not display_name or display_name == peer_id or display_name.startswith("peer-"))
                )
                if is_unidentified_default or is_unidentified_browser:
                    self._send_json(
                        {
                            "error": "Mandatory Identity Gate: You must identify yourself (Full Name, Username, Email & Phone) before entering the room.",
                            "require_identity": True,
                        },
                        403,
                    )
                    return

                if not display_name:
                    display_name = peer_id
                session = relay.register_peer(
                    peer_id=peer_id,
                    display_name=display_name,
                    udp_address="redacted",
                    udp_port=int(data.get("udp_port", 50000)),
                    room=data.get("room", "main"),
                    has_video=bool(data.get("has_video", False)),
                    has_audio=bool(data.get("has_audio", False)),
                    has_screen=bool(data.get("has_screen", False)),
                )
                mesh_os.award_xp(peer_id, "workstation_handshake", display_name=display_name)
                mesh_os.record_flight(peer_id, "relay", kind="webrtc", label="UDP Handshake")
                self._send_json({
                    "status": "registered",
                    "peer_id": session.peer_id,
                    "display_name": session.display_name,
                    "room": session.room,
                    "peers": relay.get_room_peers(session.room),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/webrtc/signal":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sender_id = data.get("from") or data.get("sender_id")
                receiver_id = data.get("to") or data.get("receiver_id") or "*"
                signal_type = data.get("type") or data.get("signal_type")
                payload = data.get("payload") or {}
                room = data.get("room", "main")
                if not sender_id or not signal_type:
                    self._send_json({"error": "Missing 'from' or 'type'"}, 400)
                    return
                msg = relay.exchange_signal(
                    sender_id=sender_id,
                    receiver_id=receiver_id,
                    signal_type=signal_type,
                    sdp_or_candidate=payload,
                    room=room,
                )
                self._send_json({"status": "signaled", "signal": msg}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path in ("/api/webrtc/leave", "/api/mesh/kick"):
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                room = data.get("room", "main")
                if not peer_id:
                    self._send_json({"error": "Missing 'peer_id'"}, 400)
                    return
                left = relay.leave_peer(peer_id)
                relay.exchange_signal(peer_id, "*", "hangup", {"peer_id": peer_id}, room=room)
                with mesh_os._lock:
                    if peer_id in mesh_os.cursors:
                        del mesh_os.cursors[peer_id]
                self._send_json({"status": "left", "peer_id": peer_id, "removed": left}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/add":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                raw_input = data.get("url") or data.get("input") or data.get("video_id") or data.get("embed")
                if not raw_input:
                    self._send_json({"error": "Missing 'url', 'input', or 'video_id'"}, 400)
                    return
                added = playlist.add_video(
                    raw_input=raw_input,
                    title=data.get("title"),
                    creator=data.get("creator"),
                    category=data.get("category", "spotlight"),
                    duration_seconds=int(data.get("duration_seconds", 35)),
                )
                peer_id = data.get("peer_id") or "curator-peer"
                mesh_os.award_xp(peer_id, "curator_drop")
                self._send_json({
                    "status": "added",
                    "item": added,
                    "playlist": playlist.get_playlist(),
                }, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/remove":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                vid = data.get("id") or data.get("video_id")
                if not vid:
                    self._send_json({"error": "Missing 'id' or 'video_id'"}, 400)
                    return
                removed = playlist.remove_video(vid)
                self._send_json({
                    "status": "removed" if removed else "not_found",
                    "playlist": playlist.get_playlist(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/playlist/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                vid = data.get("id") or data.get("video_id")
                if not vid:
                    self._send_json({"error": "Missing 'id' or 'video_id'"}, 400)
                    return
                updated = playlist.update_video(
                    video_id_or_id=vid,
                    title=data.get("title"),
                    creator=data.get("creator"),
                    category=data.get("category"),
                    duration_seconds=data.get("duration_seconds"),
                    cite_url=data.get("cite_url"),
                    embed_url=data.get("embed_url"),
                )
                if updated:
                    sponsor_manager.sync_from_playlist([asdict(it) for it in playlist.items])
                    self._send_json({
                        "status": "updated",
                        "item": updated,
                        "playlist": playlist.get_playlist(),
                    }, 200)
                else:
                    self._send_json({"error": "Video not found", "video_id": vid}, 404)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/add":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                if not data.get("name"):
                    self._send_json({"error": "Missing sponsor 'name'"}, 400)
                    return
                added = sponsor_manager.add_sponsor(data)
                self._send_json({
                    "status": "added",
                    "sponsor": added,
                    "state": sponsor_manager.get_state(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                s_id = data.get("id")
                if not s_id:
                    self._send_json({"error": "Missing sponsor 'id'"}, 400)
                    return
                updated = sponsor_manager.update_sponsor(s_id, data)
                if updated:
                    self._send_json({
                        "status": "updated",
                        "sponsor": updated,
                        "state": sponsor_manager.get_state(),
                    }, 200)
                else:
                    self._send_json({"error": "Sponsor not found", "id": s_id}, 404)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/sponsors/remove":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                s_id = data.get("id")
                if not s_id:
                    self._send_json({"error": "Missing sponsor 'id'"}, 400)
                    return
                removed = sponsor_manager.remove_sponsor(s_id)
                self._send_json({
                    "status": "removed" if removed else "not_found",
                    "id": s_id,
                    "state": sponsor_manager.get_state(),
                }, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/cursor":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = (data.get("peer_id") or "peer").strip()
                display_name = (data.get("display_name") or "").strip()
                acc = account_registry.get_account_by_peer(peer_id)
                if acc:
                    fn = (acc.get("full_name") or "").strip()
                    un = (acc.get("username") or "").strip()
                    if fn and un:
                        display_name = f"{fn} (@{un})"
                    elif fn:
                        display_name = fn

                # Server-Side Mandatory Identity Gate: Reject unidentified browser cursors
                is_unidentified_cursor = (
                    peer_id.startswith("peer-")
                    and not peer_id.startswith(("peer-primary-", "peer-secondary-", "peer-workstation-", "peer-test-"))
                    and not acc
                    and (not display_name or display_name == peer_id or display_name.startswith("peer-"))
                )
                if is_unidentified_cursor:
                    with mesh_os._lock:
                        mesh_os.cursors.pop(peer_id, None)
                    self._send_json(
                        {
                            "error": "Mandatory Identity Gate: Please complete identity registration before entering the room.",
                            "require_identity": True,
                        },
                        403,
                    )
                    return

                cursor = mesh_os.update_cursor(
                    peer_id=peer_id,
                    x=float(data.get("x", 0.0)),
                    y=float(data.get("y", 0.0)),
                    window_id=data.get("window_id", "desktop"),
                    display_name=display_name or peer_id,
                    room=data.get("room", "main"),
                )
                self._send_json({"status": "ok", "cursor": cursor}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/watchparty":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                wp = mesh_os.sync_watch_party(
                    peer_id=data.get("peer_id") or "peer",
                    video_idx=int(data.get("video_idx", 0)),
                    is_playing=bool(data.get("is_playing", True)),
                    current_time=float(data.get("current_time", 0.0)),
                )
                self._send_json({"status": "synced", "watch_party": wp}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/react":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                emoji = data.get("emoji") or "🔥"
                rx = mesh_os.add_reaction(peer_id=peer_id, emoji=emoji, display_name=data.get("display_name"))
                self._send_json({"status": "reacted", "reaction": rx, "total_xp": mesh_os.total_xp}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/quest":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                action_key = data.get("action_key") or "sealed_courier"
                award = mesh_os.award_xp(
                    peer_id=peer_id,
                    action_key=action_key,
                    display_name=data.get("display_name"),
                )
                flight = mesh_os.record_flight(
                    from_node=data.get("from_node") or peer_id,
                    to_node=data.get("to_node") or "relay",
                    kind=action_key,
                    label=action_key,
                )
                self._send_json({"status": "awarded", "award": award, "flight": flight}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/mesh/arena/vote":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "peer"
                winner_alias = data.get("winner_alias") or "gemini-brain"
                res = mesh_os.vote_arena(
                    peer_id=peer_id,
                    winner_alias=winner_alias,
                    prompt_preview=data.get("prompt_preview", ""),
                    display_name=data.get("display_name"),
                )
                self._send_json({"status": "voted", **res}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/account/register":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                name = data.get("name") or data.get("full_name")
                phone = data.get("phone") or data.get("phone_number")
                email = data.get("email")
                username = data.get("username") or name
                role = data.get("role", "Researcher / Student")
                consent_pii = bool(data.get("consent_pii", True))
                account = account_registry.register_account(
                    peer_id=peer_id,
                    full_name=name,
                    phone_number=phone,
                    email=email,
                    username=username,
                    role=role,
                    consent_pii=consent_pii,
                )
                try:
                    mesh_os.award_xp(peer_id, "account_created")
                except Exception:
                    pass
                self._send_json({"status": "success", "account": account}, 201)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/ads/click":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                sponsor_id = data.get("sponsor_id", "")
                success = sponsor_manager.record_click(sponsor_id)
                self._send_json({"status": "ok", "recorded": success, "sponsor_id": sponsor_id}, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/account/billing/topup":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id")
                tokens = int(data.get("tokens", 0))
                amount_usd = float(data.get("amount_usd", 0.0))
                sponsor_id = data.get("sponsor_id")
                if sponsor_id:
                    sponsor_manager.record_completion(sponsor_id)
                account = account_registry.top_up_credits(peer_id, amount_usd=amount_usd, tokens=tokens)
                self._send_json({"status": "topup_success", "account": account}, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topics":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "anonymous-peer"
                title = data.get("title") or ""
                body = data.get("body") or ""
                category = data.get("category") or "cyberspace"
                tags = data.get("tags") or []
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                author_username = data.get("username") or data.get("author_username")
                require_verification = bool(data.get("require_verification", False))
                auto_agent_reply = bool(data.get("auto_agent_reply", True))

                result = cyberspace_board.create_topic(
                    peer_id=peer_id,
                    title=title,
                    body=body,
                    category=category,
                    tags=tags,
                    author_username=author_username,
                    require_verification=require_verification,
                    auto_agent_reply=auto_agent_reply,
                )
                if result.get("require_verification"):
                    self._send_json(result, 403)
                    return

                mesh_os.award_xp(peer_id, "cyberspace_post", display_name=result.get("author_username"))
                mesh_os.record_flight(peer_id, "relay", kind="cyberspace_topic", label=f"#{category}")
                self._send_json({"status": "created", "topic": result}, 201)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topic/update":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                tags = data.get("tags")
                if isinstance(tags, str):
                    tags = [t.strip() for t in tags.split(",") if t.strip()]
                result = cyberspace_board.update_topic(
                    topic_id=topic_id,
                    peer_id=peer_id,
                    title=data.get("title"),
                    body=data.get("body"),
                    category=data.get("category"),
                    tags=tags,
                    pinned=data.get("pinned"),
                    locked=data.get("locked"),
                    resolved=data.get("resolved"),
                )
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/topic/delete":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.delete_topic(topic_id=topic_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/reply":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                body = data.get("body") or ""
                author_username = data.get("username") or data.get("author_username")
                parent_post_id = data.get("parent_post_id") or ""
                require_verification = bool(data.get("require_verification", False))
                auto_agent_reply = bool(data.get("auto_agent_reply", True))

                result = cyberspace_board.create_post(
                    topic_id=topic_id,
                    peer_id=peer_id,
                    body=body,
                    author_username=author_username,
                    parent_post_id=parent_post_id,
                    require_verification=require_verification,
                    auto_agent_reply=auto_agent_reply,
                )
                if result.get("require_verification"):
                    self._send_json(result, 403)
                    return

                mesh_os.award_xp(peer_id, "cyberspace_post", display_name=result.get("author_username"))
                mesh_os.record_flight(peer_id, "relay", kind="cyberspace_reply", label="Board Reply")
                self._send_json(result, 201)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/post/delete":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                post_id = data.get("post_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.delete_post(post_id=post_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/vote":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                target_type = data.get("target_type") or "topic"
                target_id = data.get("target_id") or data.get("id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                direction = data.get("direction") or "up"
                result = cyberspace_board.vote_item(
                    target_type=target_type,
                    target_id=target_id,
                    peer_id=peer_id,
                    direction=direction,
                )
                mesh_os.award_xp(peer_id, "cyberspace_vote")
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/solution":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                topic_id = data.get("topic_id") or ""
                post_id = data.get("post_id") or ""
                peer_id = data.get("peer_id") or "anonymous-peer"
                result = cyberspace_board.accept_solution(topic_id=topic_id, post_id=post_id, peer_id=peer_id)
                self._send_json(result, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/board/search":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                query_str = data.get("query") or data.get("q") or ""
                mode = data.get("mode") or "hybrid"
                top_k = int(data.get("top_k", 10))
                max_hops = int(data.get("max_hops", 2))
                res = cyberspace_board.search(query=query_str, mode=mode, top_k=top_k, max_hops=max_hops)
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/verify/send":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or "anonymous-peer"
                username = data.get("username") or data.get("target_username") or ""
                reason = data.get("reason") or "Mandatory Cyberspace Identity Verification"
                res = cyberspace_board.dispatch_verification_form(
                    peer_id=peer_id,
                    target_username=username,
                    reason=reason,
                )
                mesh_os.record_flight("@verifier-agent", peer_id, kind="verification_form", label="🛡️ Verify Form")
                self._send_json(res, 200)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        elif parsed.path == "/api/verify/submit":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8")) if post_data else {}
                peer_id = data.get("peer_id") or ""
                full_name = data.get("full_name") or data.get("name") or ""
                username = data.get("username") or ""
                email = data.get("email") or ""
                phone_number = data.get("phone_number") or data.get("phone") or ""
                role = data.get("role") or "Researcher / Student"
                bio = data.get("bio") or ""
                consent_pii = bool(data.get("consent_pii", True))
                request_id = data.get("request_id")
                challenge_code = data.get("challenge_code")

                res = cyberspace_board.submit_verification_form(
                    peer_id=peer_id,
                    full_name=full_name,
                    username=username,
                    email=email,
                    phone_number=phone_number,
                    role=role,
                    bio=bio,
                    consent_pii=consent_pii,
                    request_id=request_id,
                    challenge_code=challenge_code,
                )
                try:
                    mesh_os.award_xp(peer_id, "cyberspace_verified", display_name=f"{full_name} (@{username.lstrip('@')})")
                    mesh_os.record_flight(peer_id, "@verifier-agent", kind="verified", label="✅ Attested")
                except Exception:
                    pass
                self._send_json(res, 200)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as e:
                self._send_json({"error": str(e)}, 500)
        else:
            self._send_empty(404)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/health", "/call", "/tv", "/os", "/mesh", "/board", "/cyberspace"):
            raw, gz, etag = _get_html_Entry(HTML_UI)
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            use_gzip = self._accepts_gzip()
            body = gz if use_gzip else raw
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Vary", "Accept-Encoding")
            if use_gzip:
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self._write_body(body)
        elif parsed.path == "/api/mesh/state":
            query = parse_qs(parsed.query)
            room = query.get("room", ["main"])[0]
            state = mesh_os.get_state(room=room)
            state["active_webrtc_streams"] = relay.get_active_streams()
            self._send_json(state, 200)
        elif parsed.path == "/api/mesh/sync":
            query = parse_qs(parsed.query)
            room = query.get("room", ["main"])[0]
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            since_str = query.get("since_seq", query.get("since", ["0"]))[0]
            inc_analytics = query.get("include_analytics", ["0"])[0] in ("1", "true", "yes")
            try:
                since_seq = int(since_str)
            except ValueError:
                since_seq = 0
            state = mesh_os.get_state(room=room)
            state["active_webrtc_streams"] = relay.get_active_streams()
            signals_payload = (
                relay.poll_signals(receiver_id=peer_id, room=room, since_seq=since_seq)
                if peer_id
                else {"signals": [], "latest_seq": since_seq, "peers": []}
            )
            payload = {
                "state": state,
                "signals": signals_payload,
            }
            if inc_analytics:
                payload["analytics"] = router.get_analytics()
            self._send_json(payload, 200)
        elif parsed.path == "/api/mesh/leaderboard":
            self._send_json({
                "leaderboard": mesh_os.get_leaderboard(),
                "tier": mesh_os.get_tier_info(),
            }, 200)
        elif parsed.path == "/api/playlist":
            self._send_json(playlist.get_playlist(), 200)
        elif parsed.path == "/api/ads/sponsor":
            query = parse_qs(parsed.query)
            sponsor_id = query.get("id", [None])[0]
            sponsor = sponsor_manager.get_sponsor(sponsor_id)
            state = sponsor_manager.get_state()
            self._send_json({
                "sponsor": sponsor,
                "networks": state["networks"],
                "total_sponsors": len(state["all_sponsors"]),
            }, 200)
        elif parsed.path in ("/api/ads/state", "/api/sponsors", "/api/sponsor/list"):
            self._send_json(sponsor_manager.get_state(), 200)
        elif parsed.path.startswith("/videos/") and parsed.path.endswith(".mp4"):
            from iot_federated_agent_memory.video_playlist import VIDEOS_DIR, download_tiktok_mp4
            from iot_federated_agent_memory.s3_storage import s3_get_object
            import re

            fname = os.path.basename(parsed.path)
            vid = os.path.splitext(fname)[0]
            file_path = os.path.join(VIDEOS_DIR, f"{vid}.mp4")
            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                # 1. Attempt immediate synchronous pull from persistent Railway S3 bucket
                try:
                    s3_get_object(f"videos/{vid}.mp4", file_path)
                except Exception:
                    pass

            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                with _downloading_lock:
                    already_downloading = vid in _downloading_videos
                    if not already_downloading:
                        _downloading_videos.add(vid)

                if not already_downloading:
                    def _bg_download(v_id: str, dest_dir: str):
                        try:
                            download_tiktok_mp4(v_id, f"https://www.tiktok.com/@nojuannobody/video/{v_id}", dest_dir)
                        finally:
                            with _downloading_lock:
                                _downloading_videos.discard(v_id)

                    threading.Thread(target=_bg_download, args=(vid, VIDEOS_DIR), daemon=True).start()

            if not os.path.isfile(file_path) or os.path.getsize(file_path) < 1024:
                self._send_empty(404)
                return

            stat = os.stat(file_path)
            file_size = stat.st_size
            etag = f'"{file_size}-{int(stat.st_mtime)}"'
            if self.headers.get("If-None-Match") == etag:
                self.send_response(304)
                self.send_header("ETag", etag)
                self.send_header("Cache-Control", "public, max-age=86400, immutable")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            range_header = self.headers.get("Range")
            chunk_size = 65536
            if range_header:
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    length = max(0, end - start + 1)
                    self.send_response(206)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Accept-Ranges", "bytes")
                    self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                    self.send_header("Content-Length", str(length))
                    self.send_header("ETag", etag)
                    self.send_header("Cache-Control", "public, max-age=86400, immutable")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    if getattr(self, "command", "GET") != "HEAD" and length > 0:
                        with open(file_path, "rb") as f:
                            f.seek(start)
                            remaining = length
                            while remaining > 0:
                                buf = f.read(min(chunk_size, remaining))
                                if not buf:
                                    break
                                self.wfile.write(buf)
                                remaining -= len(buf)
                    return

            self.send_response(200)
            self.send_header("Content-Type", "video/mp4")
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Content-Length", str(file_size))
            self.send_header("ETag", etag)
            self.send_header("Cache-Control", "public, max-age=86400, immutable")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            if getattr(self, "command", "GET") != "HEAD" and file_size > 0:
                with open(file_path, "rb") as f:
                    while True:
                        buf = f.read(chunk_size)
                        if not buf:
                            break
                        self.wfile.write(buf)
        elif parsed.path == "/api/webrtc/signals":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            room = query.get("room", ["main"])[0]
            since_str = query.get("since_seq", query.get("since", ["0"]))[0]
            try:
                since_seq = int(since_str)
            except ValueError:
                since_seq = 0
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            self._send_json(relay.poll_signals(receiver_id=peer_id, room=room, since_seq=since_seq), 200)
        elif parsed.path == "/api/account/get":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", [None])[0]
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            acc = account_registry.get_account_by_peer(peer_id)
            if acc:
                self._send_json({"status": "found", "account": acc}, 200)
            else:
                self._send_json({"error": "Account not found", "peer_id": peer_id}, 404)
        elif parsed.path == "/api/account/list":
            accounts = account_registry.list_accounts()
            self._send_json({"count": len(accounts), "accounts": accounts}, 200)
        elif parsed.path == "/api/account/billing":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", [None])[0]
            if not peer_id:
                self._send_json({"error": "Missing 'peer_id' query parameter"}, 400)
                return
            summary = account_registry.get_billing_summary(peer_id)
            status_code = 200 if "error" not in summary else 404
            self._send_json(summary, status_code)
        elif parsed.path == "/api/board/topics":
            query = parse_qs(parsed.query)
            category = query.get("category", [None])[0]
            tag = query.get("tag", [None])[0]
            user = query.get("user", query.get("username", [None]))[0]
            agent = query.get("agent", [None])[0]
            sort_by = query.get("sort_by", query.get("sort", ["hot"]))[0]
            verified_only = query.get("verified_only", ["0"])[0] in ("1", "true", "yes")
            limit = int(query.get("limit", ["50"])[0])
            res = cyberspace_board.list_topics(
                category=category,
                tag=tag,
                mentioned_user=user,
                mentioned_agent=agent,
                sort_by=sort_by,
                verified_only=verified_only,
                limit=limit,
            )
            self._send_json(res, 200)
        elif parsed.path == "/api/board/topic":
            query = parse_qs(parsed.query)
            topic_id = query.get("id", query.get("topic_id", [None]))[0]
            if not topic_id:
                self._send_json({"error": "Missing 'id' or 'topic_id' query parameter"}, 400)
                return
            inc_views = query.get("increment_views", ["1"])[0] not in ("0", "false", "no")
            topic = cyberspace_board.get_topic(topic_id, increment_views=inc_views)
            if not topic:
                self._send_json({"error": f"Topic '{topic_id}' not found"}, 404)
                return
            self._send_json({"status": "ok", "topic": topic}, 200)
        elif parsed.path == "/api/board/search":
            query = parse_qs(parsed.query)
            q_str = query.get("q", query.get("query", [""]))[0]
            mode = query.get("mode", ["hybrid"])[0]
            top_k = int(query.get("top_k", ["10"])[0])
            max_hops = int(query.get("max_hops", ["2"])[0])
            res = cyberspace_board.search(query=q_str, mode=mode, top_k=top_k, max_hops=max_hops)
            self._send_json(res, 200)
        elif parsed.path == "/api/board/graph":
            self._send_json(cyberspace_board.graphrag.get_full_graph_snapshot(), 200)
        elif parsed.path == "/api/board/graph/path":
            query = parse_qs(parsed.query)
            src = query.get("from", query.get("source", [""]))[0]
            dst = query.get("to", query.get("target", [""]))[0]
            max_hops = int(query.get("max_hops", ["5"])[0])
            self._send_json(cyberspace_board.graphrag.find_entity_path(src, dst, max_hops=max_hops), 200)
        elif parsed.path == "/api/board/roster":
            self._send_json(cyberspace_board.get_roster_and_profiles(), 200)
        elif parsed.path == "/api/board/profile":
            query = parse_qs(parsed.query)
            user_or_peer = query.get("user", query.get("username", query.get("peer_id", [""])))[0]
            if not user_or_peer:
                self._send_json({"error": "Missing 'user' or 'peer_id' query parameter"}, 400)
                return
            self._send_json(cyberspace_board.get_user_profile(user_or_peer), 200)
        elif parsed.path == "/api/verify/status":
            query = parse_qs(parsed.query)
            peer_id = query.get("peer_id", query.get("peer", [None]))[0]
            username = query.get("username", query.get("user", [None]))[0]
            if not peer_id and not username:
                self._send_json({"error": "Missing 'peer_id' or 'username' query parameter"}, 400)
                return
            self._send_json(cyberspace_board.get_verification_status(peer_id=peer_id or "", username=username), 200)
        elif parsed.path == "/api/verify/list":
            self._send_json(cyberspace_board.list_verifications(), 200)
        elif parsed.path == "/api/status":
            audit = scale.evaluate_current_and_future()
            self._send_json({
                "status": "online",
                "service": "iot-federated-agent-memory",
                "readiness_tier": audit["readiness_tier"],
                "composite_score": audit["composite_iot_scale_score"],
                "active_webrtc_streams": relay.get_active_streams(),
                "ai_providers": {k: v.available_credits for k, v in router.providers.items()},
                "tincan_relay": tincan_relay.get_stats(),
                "mesh_os": {
                    "xp": mesh_os.total_xp,
                    "tier": mesh_os.get_tier_info(),
                },
            })
        elif parsed.path == "/api/streams":
            self._send_json(relay.get_active_streams())
        elif parsed.path == "/api/providers":
            self._send_json(router.get_analytics()["providers"])
        elif parsed.path == "/api/models/analytics":
            self._send_json(router.get_analytics())
        elif parsed.path == "/api/tincan/inbox":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            since_seq_str = query.get("since_seq", query.get("since", ["0"]))[0]
            timeout_str = query.get("timeout", ["0.0"])[0]
            try:
                since_seq = int(since_seq_str)
            except ValueError:
                since_seq = 0
            try:
                timeout = float(timeout_str)
            except ValueError:
                timeout = 0.0

            if not address:
                self._send_json({"error": "Missing 'address' or 'addr' query parameter"}, 400)
                return
            try:
                res = tincan_relay.inbox(address, since_seq=since_seq, timeout=timeout)
                mesh_os.award_xp(address.split("@")[0], "inbox_decryption")
                self._send_json(res)
            except ValueError as ve:
                self._send_json({"error": str(ve)}, 400)
            except Exception as exc:
                self._send_json({"error": str(exc)}, 500)
        elif parsed.path == "/api/tincan/whoami":
            query = parse_qs(parsed.query)
            address = query.get("address", query.get("addr", [None]))[0]
            res = tincan_relay.whoami(address)
            self._send_json(res)
        elif parsed.path == "/api/version":
            self._send_json({
                "service": "tincan",
                "commit": COMMIT_HASH,
                "version": "2.2.0",
                "relay_url": "https://iot-federated-agent-memory-production.up.railway.app",
            })
        elif parsed.path in ("/install.sh", "/install_peer.sh"):
            install_script_path = os.path.join(os.path.dirname(__file__), "install_peer.sh")
            if os.path.exists(install_script_path):
                with open(install_script_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/x-shellscript; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self._write_body(content)
            else:
                self._send_empty(404)
        elif parsed.path == "/download/bundle.tar.gz":
            # Privacy Guard: Workspace tarball download is disabled to prevent leaking local files or PII.
            self._send_json({"error": "Bundle download disabled for privacy and security protection."}, 403)
        else:
            self._send_empty(404)


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), MeshGatewayHandler)
    print(f"[*] IoT Federated Agent Mesh listening on port {PORT}")
    server.serve_forever()

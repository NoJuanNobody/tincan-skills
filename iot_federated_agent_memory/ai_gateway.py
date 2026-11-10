"""Dynamic Multi-Lab AI Gateway Router and Live OpenRouter Cost & Credit Dashboard."""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
import urllib.request
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional


def _resolve_openrouter_key_fallback() -> Optional[str]:
    """Resolve OPENROUTER_API_KEY strictly from environment (CLI subprocess scraping disabled)."""
    return os.environ.get("OPENROUTER_API_KEY")


@dataclass
class LabProviderConfig:
    lab_id: str
    display_name: str
    model_alias: str
    endpoint: str
    api_key_env: str
    available_credits: float
    is_active: bool
    input_cost_per_1m: float = 1.0
    output_cost_per_1m: float = 3.0
    total_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0


class DynamicAIGatewayRouter:
    """Manages hot-swappable AI provider models, live OpenRouter billing/credits, and per-call cost tracking."""

    OPENROUTER_ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
    OPENROUTER_CREDITS_URL = "https://openrouter.ai/api/v1/credits"
    OPENROUTER_KEY_URL = "https://openrouter.ai/api/v1/auth/key"

    DEFAULT_LABS = {
        "claude-brain": LabProviderConfig(
            lab_id="anthropic",
            display_name="Anthropic Claude Sonnet",
            model_alias="anthropic/claude-sonnet-5.5",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=100.0,
            is_active=True,
            input_cost_per_1m=3.00,
            output_cost_per_1m=15.00,
        ),
        "grok-brain": LabProviderConfig(
            lab_id="xai",
            display_name="xAI Grok",
            model_alias="x-ai/grok-4.7",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=50.0,
            is_active=True,
            input_cost_per_1m=2.00,
            output_cost_per_1m=10.00,
        ),
        "gemini-brain": LabProviderConfig(
            lab_id="google",
            display_name="Google Gemini Flash",
            model_alias="google/gemini-2.5-flash",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=80.0,
            is_active=True,
            input_cost_per_1m=0.15,
            output_cost_per_1m=0.60,
        ),
        "openai-brain": LabProviderConfig(
            lab_id="openai",
            display_name="OpenAI GPT-4o",
            model_alias="openai/gpt-4o",
            endpoint=OPENROUTER_ENDPOINT,
            api_key_env="OPENROUTER_API_KEY",
            available_credits=60.0,
            is_active=True,
            input_cost_per_1m=2.50,
            output_cost_per_1m=10.00,
        ),
    }

    def __init__(self, openrouter_key: Optional[str] = None):
        self.openrouter_key = openrouter_key if openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")
        self.providers: Dict[str, LabProviderConfig] = {
            k: LabProviderConfig(**asdict(v)) for k, v in self.DEFAULT_LABS.items()
        }
        self.routing_log: List[Dict[str, Any]] = []
        self._billing_cache: Optional[Dict[str, Any]] = None
        self._billing_cached_at: float = 0.0
        self._billing_refreshing: bool = False
        self._billing_lock = threading.Lock()
        self.BILLING_CACHE_TTL: float = 60.0

    def route_request(self, requested_alias: str, estimated_cost: float = 0.02) -> LabProviderConfig:
        """Route request to the target lab, or fallback if credit pool is exhausted."""
        primary = self.providers.get(requested_alias)
        if primary and primary.is_active and primary.available_credits >= estimated_cost:
            primary.available_credits -= estimated_cost
            self.routing_log.append({
                "timestamp": time.time(),
                "alias": requested_alias,
                "lab": primary.lab_id,
                "model": primary.model_alias,
                "cost": estimated_cost,
                "status": "routed",
            })
            return primary

        # Fallback to any active provider with available credit balance
        for alias, config in self.providers.items():
            if config.is_active and config.available_credits >= estimated_cost:
                config.available_credits -= estimated_cost
                self.routing_log.append({
                    "timestamp": time.time(),
                    "alias": requested_alias,
                    "fallback_to": alias,
                    "lab": config.lab_id,
                    "model": config.model_alias,
                    "status": "fallback",
                })
                return config

        raise RuntimeError("All AI lab subscription credit pools are exhausted.")

    def swap_lab_endpoint(self, alias: str, new_model: str, new_endpoint: Optional[str] = None) -> None:
        if alias in self.providers:
            self.providers[alias].model_alias = new_model
            if new_endpoint:
                self.providers[alias].endpoint = new_endpoint

    def set_model(self, alias: str, new_model: str, display_name: Optional[str] = None) -> LabProviderConfig:
        """Set or update model name for a provider alias."""
        if alias not in self.providers:
            self.providers[alias] = LabProviderConfig(
                lab_id="custom",
                display_name=display_name or alias,
                model_alias=new_model,
                endpoint=self.OPENROUTER_ENDPOINT,
                api_key_env="OPENROUTER_API_KEY",
                available_credits=50.0,
                is_active=True,
            )
        else:
            self.providers[alias].model_alias = new_model
            if display_name:
                self.providers[alias].display_name = display_name
        return self.providers[alias]

    def record_usage(
        self,
        alias: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        cost: float = 0.0,
    ) -> None:
        if alias in self.providers:
            provider = self.providers[alias]
            provider.total_calls += 1
            provider.total_prompt_tokens += prompt_tokens
            provider.total_completion_tokens += completion_tokens
            provider.total_tokens += total_tokens
            if cost <= 0.0 and (prompt_tokens > 0 or completion_tokens > 0):
                cost = (
                    (prompt_tokens / 1_000_000.0) * provider.input_cost_per_1m
                    + (completion_tokens / 1_000_000.0) * provider.output_cost_per_1m
                )
            provider.total_cost += cost

    def _fetch_openrouter_billing_sync(self, api_key: str) -> Dict[str, Any]:
        """Perform the synchronous OpenRouter billing HTTP requests and update cache."""
        now = time.time()
        headers = {"Authorization": f"Bearer {api_key}", "Accept": "application/json"}
        credits_data: Dict[str, Any] = {}
        key_data: Dict[str, Any] = {}

        try:
            req_c = urllib.request.Request(self.OPENROUTER_CREDITS_URL, headers=headers, method="GET")
            with urllib.request.urlopen(req_c, timeout=5.0) as resp_c:
                credits_data = (json.loads(resp_c.read().decode("utf-8")) or {}).get("data") or {}
        except Exception:
            pass

        try:
            req_k = urllib.request.Request(self.OPENROUTER_KEY_URL, headers=headers, method="GET")
            with urllib.request.urlopen(req_k, timeout=5.0) as resp_k:
                key_data = (json.loads(resp_k.read().decode("utf-8")) or {}).get("data") or {}
        except Exception:
            pass

        total_credits = float(credits_data.get("total_credits") or 0.0)
        total_usage = float(credits_data.get("total_usage") or 0.0)
        remaining_balance = max(0.0, total_credits - total_usage)

        billing = {
            "connected": bool(credits_data or key_data),
            "account_total_credits_usd": round(total_credits, 4),
            "account_total_usage_usd": round(total_usage, 6),
            "account_remaining_balance_usd": round(remaining_balance, 4),
            "key_label": "pooled-mesh-key [redacted]",
            "key_limit_usd": key_data.get("limit"),
            "key_remaining_usd": round(float(key_data["limit_remaining"]), 6) if key_data.get("limit_remaining") is not None else None,
            "key_usage_total_usd": round(float(key_data.get("usage") or 0.0), 6),
            "key_usage_daily_usd": round(float(key_data.get("usage_daily") or 0.0), 6),
            "key_usage_weekly_usd": round(float(key_data.get("usage_weekly") or 0.0), 6),
            "key_usage_monthly_usd": round(float(key_data.get("usage_monthly") or 0.0), 6),
            "fetched_at": now,
        }
        with self._billing_lock:
            self._billing_cache = billing
            self._billing_cached_at = now
            self._billing_refreshing = False
        return billing

    def get_openrouter_billing(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Fetch real-time OpenRouter account credits with stale-while-revalidate background refresh."""
        now = time.time()
        if not force_refresh and self._billing_cached_at and (now - self._billing_cached_at) < self.BILLING_CACHE_TTL and self._billing_cache:
            return self._billing_cache

        api_key = self.openrouter_key or _resolve_openrouter_key_fallback()
        if not api_key:
            return {
                "connected": False,
                "account_total_credits_usd": 0.0,
                "account_total_usage_usd": 0.0,
                "account_remaining_balance_usd": 0.0,
                "key_label": "not_configured",
                "key_limit_usd": None,
                "key_remaining_usd": None,
                "key_usage_total_usd": 0.0,
                "key_usage_daily_usd": 0.0,
                "key_usage_weekly_usd": 0.0,
                "key_usage_monthly_usd": 0.0,
            }

        # Stale-while-revalidate: if we already have cached billing data and force_refresh is False,
        # refresh asynchronously in a background thread so HTTP polling never blocks p99 latency.
        if not force_refresh and self._billing_cache is not None:
            with self._billing_lock:
                should_spawn = not self._billing_refreshing
                if should_spawn:
                    self._billing_refreshing = True
            if should_spawn:
                threading.Thread(
                    target=self._fetch_openrouter_billing_sync,
                    args=(api_key,),
                    daemon=True,
                ).start()
            return self._billing_cache

        return self._fetch_openrouter_billing_sync(api_key)

    def get_analytics(self, include_live_billing: bool = True) -> Dict[str, Any]:
        """Aggregate usage analytics, per-model token rates, and live OpenRouter account spend."""
        session_calls = sum(p.total_calls for p in self.providers.values())
        session_tokens = sum(p.total_tokens for p in self.providers.values())
        session_spend = sum(p.total_cost for p in self.providers.values())
        billing = self.get_openrouter_billing() if include_live_billing else {}

        return {
            "total_calls": session_calls,
            "total_tokens": session_tokens,
            "total_spend_usd": round(session_spend, 6),
            "openrouter": billing,
            "providers": {
                k: {
                    "display_name": p.display_name,
                    "model": p.model_alias,
                    "input_cost_per_1m_usd": p.input_cost_per_1m,
                    "output_cost_per_1m_usd": p.output_cost_per_1m,
                    "est_cost_per_1k_prompt_usd": round((p.input_cost_per_1m * 0.5 + p.output_cost_per_1m * 0.5) / 1000.0, 6),
                    "total_calls": p.total_calls,
                    "prompt_tokens": p.total_prompt_tokens,
                    "completion_tokens": p.total_completion_tokens,
                    "total_tokens": p.total_tokens,
                    "cost_usd": round(p.total_cost, 6),
                    "remaining_credits": round(
                        billing.get("account_remaining_balance_usd", p.available_credits)
                        if billing.get("connected")
                        else p.available_credits,
                        4,
                    ),
                    "is_active": p.is_active,
                }
                for k, p in self.providers.items()
            },
            "recent_routing_log": self.routing_log[-20:],
        }

    def dispatch_completion(
        self,
        alias: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """Dispatch real chat completion to OpenRouter using single OPENROUTER_API_KEY."""
        config = self.route_request(alias)
        api_key = self.openrouter_key if self.openrouter_key is not None else os.environ.get("OPENROUTER_API_KEY")

        if not api_key:
            # Simulated offline response if no API key is injected
            self.record_usage(alias, 10, 32, 42, 0.0)
            return {
                "id": f"sim-{alias}",
                "model": config.model_alias,
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": f"[Simulated {config.display_name} via OpenRouter router: key pending]",
                    }
                }],
                "usage": {"total_tokens": 42},
            }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/NoJuanNobody/tin-can",
            "X-Title": "TinCan 2 / IoT Federated Agent Memory",
        }
        payload = {
            "model": config.model_alias,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(
            config.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as http_err:
            # If a configured model alias is unavailable on OpenRouter (400/404), retry with google/gemini-2.5-flash
            if http_err.code in (400, 404) and payload.get("model") != "google/gemini-2.5-flash":
                fallback_payload = dict(payload, model="google/gemini-2.5-flash")
                req_fb = urllib.request.Request(
                    config.endpoint,
                    data=json.dumps(fallback_payload).encode("utf-8"),
                    headers=headers,
                    method="POST",
                )
                with urllib.request.urlopen(req_fb, timeout=30) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
            else:
                raise
        usage = data.get("usage", {})
        prompt_toks = int(usage.get("prompt_tokens", 0))
        comp_toks = int(usage.get("completion_tokens", 0))
        total_toks = int(usage.get("total_tokens", prompt_toks + comp_toks))
        cost = float(usage.get("cost") or 0.0)
        self.record_usage(alias, prompt_toks, comp_toks, total_toks, cost)
        return data

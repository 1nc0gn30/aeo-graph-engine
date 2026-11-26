"""
Sovereign Multi-Provider AI Gateway for AEO Graph Engine (v2.1.0).

Supports 15+ genuine providers across:
  - Offline deterministic heuristic engine (zero egress, zero key)
  - Local Sovereign Agents & Daemons (zero API key):
      agy_bridge (:18000), ollama_local / ollama (:11434), azoth_local (:8136),
      agy_cli, hermes_cli, grok_cli, codex_cli (loop-guarded), claude_code (harness-guarded),
      lm_studio (:1234), vllm (:8000)
  - Cloud & Custom APIs (server-side proxied, 0600 storage in ~/.config/aeo-graph-engine/):
      openai, anthropic, gemini_api, openrouter, xai_grok, perplexity, groq,
      deepseek, ollama_cloud, custom_openai

Security invariants:
  - Never saves keys into CWD (defaults to ~/.config/aeo-graph-engine/secrets.json, chmod 0600)
  - Never invokes shell=True; validates model names via SAFE_MODEL_RE
  - Redacts all API keys in public status & export helpers
Zero external runtime dependencies (Python standard library only).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .ai_config import synthesize_config_from_prompt
from .compat import atomic_write_text

SAFE_MODEL_RE = re.compile(r"^[A-Za-z0-9._:/@-]{1,120}$")

SECRET_KEY_FIELDS = (
    "openai",
    "anthropic",
    "gemini_api",
    "openrouter",
    "xai_grok",
    "perplexity",
    "groq",
    "deepseek",
    "ollama_cloud",
    "custom_openai",
)

DEFAULT_CONFIG_PATH = Path.home() / ".config" / "aeo-graph-engine" / "secrets.json"

DEFAULT_AI_GATEWAY_CONFIG: Dict[str, Any] = {
    "active_provider": "heuristic",
    "active_model": "default",
    "temperature": 0.3,
    "max_tokens": 1500,
    "endpoints": {
        "agy_bridge": "http://127.0.0.1:18000/v1",
        "ollama": "http://127.0.0.1:11434",
        "ollama_local": "http://127.0.0.1:11434",
        "azoth_local": "http://127.0.0.1:8136",
        "lm_studio": "http://127.0.0.1:1234/v1",
        "vllm": "http://127.0.0.1:8000/v1",
        "openai": "https://api.openai.com/v1",
        "anthropic": "https://api.anthropic.com/v1",
        "gemini_api": "https://generativelanguage.googleapis.com/v1beta",
        "openrouter": "https://openrouter.ai/api/v1",
        "xai_grok": "https://api.x.ai/v1",
        "perplexity": "https://api.perplexity.ai",
        "groq": "https://api.groq.com/openai/v1",
        "deepseek": "https://api.deepseek.com/v1",
        "ollama_cloud": "https://ollama.com/api",
        "custom_openai": "http://127.0.0.1:18000/v1",
    },
    "mcp_gateway_port": 8091,
    "keys": {k: "" for k in SECRET_KEY_FIELDS},
}

PROVIDER_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "heuristic",
        "name": "Built-in Rule Heuristic Engine",
        "type": "offline",
        "group": "offline",
        "description": "100% Offline, Deterministic, Zero API Keys Needed",
        "default_port": None,
        "default_model": "deterministic-rule-synthesizer-v2",
    },
    {
        "id": "agy_bridge",
        "name": "AGY Bridge (Local Proxy :18000)",
        "type": "local",
        "group": "local_daemon",
        "description": "OpenAI-compatible Antigravity local model bridge (zero API key)",
        "default_port": 18000,
        "default_url": "http://127.0.0.1:18000/v1",
        "default_model": "gemini-3.8-flash-high",
    },
    {
        "id": "ollama_local",
        "name": "Ollama (Local LLM :11434)",
        "type": "local",
        "group": "local_daemon",
        "description": "Private local Ollama inference on GPU/CPU",
        "default_port": 11434,
        "default_url": "http://127.0.0.1:11434",
        "default_model": "hermes3-64k:latest",
    },
    {
        "id": "azoth_local",
        "name": "AZOTH Local Archon (:8136)",
        "type": "local",
        "group": "local_daemon",
        "description": "ZothOS sovereign Archon local agent daemon",
        "default_port": 8136,
        "default_url": "http://127.0.0.1:8136",
        "default_model": "azoth-archon",
    },
    {
        "id": "agy_cli",
        "name": "AGY CLI (Antigravity Local)",
        "type": "local",
        "group": "local_cli",
        "description": "Direct non-interactive agy CLI execution",
        "default_model": "gemini-3.8-flash-high",
    },
    {
        "id": "hermes_cli",
        "name": "Hermes Agent CLI",
        "type": "local",
        "group": "local_cli",
        "description": "Direct non-interactive hermes chat --oneshot execution",
        "default_model": "hermes-default",
    },
    {
        "id": "grok_cli",
        "name": "Grok CLI (Local Binary)",
        "type": "local",
        "group": "local_cli",
        "description": "Direct non-interactive grok -p CLI execution",
        "default_model": "grok-default",
    },
    {
        "id": "codex_cli",
        "name": "Codex CLI (Loop-Guarded)",
        "type": "local",
        "group": "local_cli",
        "description": "OpenAI Codex CLI (detects recursive wrapper loops safely)",
        "default_model": "codex-default",
    },
    {
        "id": "claude_code",
        "name": "Claude Code CLI (Harness-Guarded)",
        "type": "local",
        "group": "local_cli",
        "description": "Anthropic Claude Code CLI (detects installer stub safely)",
        "default_model": "claude-code",
    },
    {
        "id": "lm_studio",
        "name": "LM Studio (Local :1234)",
        "type": "local",
        "group": "local_daemon",
        "description": "OpenAI-compatible local server on LM Studio",
        "default_port": 1234,
        "default_url": "http://127.0.0.1:1234/v1",
        "default_model": "default",
    },
    {
        "id": "vllm",
        "name": "vLLM / llama.cpp (Local :8000)",
        "type": "local",
        "group": "local_daemon",
        "description": "High-throughput OpenAI-compatible local server",
        "default_port": 8000,
        "default_url": "http://127.0.0.1:8000/v1",
        "default_model": "default",
    },
    {
        "id": "openai",
        "name": "OpenAI (GPT-4o / o3-mini)",
        "type": "cloud",
        "group": "cloud",
        "description": "OpenAI chat completions API",
        "env_var": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    {
        "id": "anthropic",
        "name": "Anthropic Claude (Server-Proxied)",
        "type": "cloud",
        "group": "cloud",
        "description": "Anthropic Messages API via local server proxy",
        "env_var": "ANTHROPIC_API_KEY",
        "default_model": "claude-3-5-haiku-20241022",
    },
    {
        "id": "gemini_api",
        "name": "Google Gemini API",
        "type": "cloud",
        "group": "cloud",
        "description": "Google Generative Language API",
        "env_var": "GEMINI_API_KEY",
        "default_model": "gemini-2.5-flash",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter (Unified Multi-Model)",
        "type": "cloud",
        "group": "cloud",
        "description": "Unified OpenAI-compatible router for 200+ models",
        "env_var": "OPENROUTER_API_KEY",
        "default_model": "meta-llama/llama-3.3-70b-instruct",
    },
    {
        "id": "xai_grok",
        "name": "xAI Grok API",
        "type": "cloud",
        "group": "cloud",
        "description": "xAI OpenAI-compatible completions API",
        "env_var": "XAI_API_KEY",
        "default_model": "grok-3-mini",
    },
    {
        "id": "perplexity",
        "name": "Perplexity AI (Sonar)",
        "type": "cloud",
        "group": "cloud",
        "description": "Web-grounded answer engine API",
        "env_var": "PERPLEXITY_API_KEY",
        "default_model": "sonar",
    },
    {
        "id": "groq",
        "name": "Groq (Llama-3.3 70B)",
        "type": "cloud",
        "group": "cloud",
        "description": "Low-latency OpenAI-compatible inference",
        "env_var": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    {
        "id": "deepseek",
        "name": "DeepSeek API",
        "type": "cloud",
        "group": "cloud",
        "description": "DeepSeek OpenAI-compatible API",
        "env_var": "DEEPSEEK_API_KEY",
        "default_model": "deepseek-chat",
    },
    {
        "id": "ollama_cloud",
        "name": "Ollama Cloud",
        "type": "cloud",
        "group": "cloud",
        "description": "Hosted Ollama API endpoint",
        "env_var": "OLLAMA_API_KEY",
        "default_model": "llama3.3",
    },
    {
        "id": "custom_openai",
        "name": "Custom OpenAI-Compatible",
        "type": "cloud",
        "group": "cloud",
        "description": "Any OpenAI-compatible base URL & optional Bearer key",
        "env_var": "CUSTOM_OPENAI_API_KEY",
        "default_model": "default",
    },
]

_CLI_CANDIDATES: Dict[str, List[str]] = {
    "agy_cli": [
        str(Path.home() / ".gemini" / "antigravity-cli" / "bin" / "agy"),
        "agy",
    ],
    "hermes_cli": [
        str(Path.home() / ".local" / "bin" / "hermes"),
        "hermes",
    ],
    "grok_cli": [
        str(Path.home() / ".grok" / "bin" / "grok"),
        "grok",
    ],
    "codex_cli": [
        str(Path.home() / ".local" / "bin" / "codex"),
        "/usr/local/bin/codex",
        "codex",
    ],
    "claude_code": [
        str(Path.home() / ".local" / "bin" / "claude"),
        "/usr/local/bin/claude",
        "claude",
    ],
}


def validate_model_name(model: Optional[str]) -> str:
    """Validates model names against strict safe character allowlist (blocks CLI flag injection)."""
    if not model:
        return "default"
    cleaned = str(model).strip()
    if cleaned.startswith("-") or not SAFE_MODEL_RE.fullmatch(cleaned):
        raise ValueError(f"Invalid model identifier '{cleaned}'.")
    return cleaned


def redact_secrets(payload: Any) -> Any:
    """Recursively redacts any secret / API key fields from dicts/lists before export."""
    if isinstance(payload, dict):
        out: Dict[str, Any] = {}
        for k, v in payload.items():
            kl = str(k).lower()
            if (
                kl in SECRET_KEY_FIELDS
                or kl in ("api_key", "apikey", "secret", "token", "authorization", "x-api-key")
                or kl.endswith("_key")
                or kl.endswith("_token")
                or kl.endswith("_secret")
            ):
                if isinstance(v, dict):
                    out[k] = {subk: "[REDACTED]" if subv else "" for subk, subv in v.items()}
                else:
                    out[k] = "[REDACTED]" if v else ""
            elif kl == "keys" and isinstance(v, dict):
                out[k] = {subk: "[REDACTED]" if subv else "" for subk, subv in v.items()}
            else:
                out[k] = redact_secrets(v)
        return out
    if isinstance(payload, list):
        return [redact_secrets(item) for item in payload]
    return payload


def _resolve_cli_binary(provider_id: str) -> Optional[str]:
    for cand in _CLI_CANDIDATES.get(provider_id, []):
        if os.path.isabs(cand):
            if os.path.isfile(cand) and os.access(cand, os.X_OK):
                return cand
        else:
            found = shutil.which(cand)
            if found:
                return found
    return None


def _is_harness_or_loop_wrapper(binary_path: str, provider_id: str) -> Optional[str]:
    """Detects known installer stubs (claude) or recursive wrapper loops (codex) in 0ms."""
    try:
        raw = Path(binary_path).read_bytes()[:4096]
    except Exception:
        return None
    if raw.startswith(b"\x7fELF"):
        return None  # Real compiled binary
    text = raw.decode("utf-8", errors="ignore")
    if provider_id == "codex_cli" and (
        "sovereign-agent-bridge" in text or "/usr/local/bin/codex" in text or "gatekeep" in text
    ):
        return "Codex wrapper delegates recursively through sovereign-agent-bridge; install real codex CLI to enable."
    if provider_id == "claude_code" and (
        "npm install -g @anthropic-ai/claude-code" in text
        or "ZothOS" in text
        or "not installed" in text.lower()
        or "installer" in text.lower()
    ):
        return "Claude Code installer stub detected (CLI not installed yet)."
    return None


def _normalize_provider(provider: str) -> str:
    p = (provider or "heuristic").strip().lower()
    if p == "ollama":
        return "ollama_local"
    return p


class AIGateway:
    """
    Manages AI provider keys (0600 outside repo), local server ports,
    live discovery/health checks, and real LLM completion + AEO citation analysis.
    """

    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        if config_path:
            self.config_path = Path(config_path).resolve()
        else:
            self.config_path = DEFAULT_CONFIG_PATH
        self.config = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """Loads configuration merging defaults, 0600 secrets file, and env vars."""
        cfg = json.loads(json.dumps(DEFAULT_AI_GATEWAY_CONFIG))

        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    disk_cfg = json.load(f)
                if isinstance(disk_cfg, dict):
                    if "active_provider" in disk_cfg:
                        cfg["active_provider"] = str(disk_cfg["active_provider"])
                    if "active_model" in disk_cfg:
                        cfg["active_model"] = str(disk_cfg["active_model"])
                    if "temperature" in disk_cfg:
                        cfg["temperature"] = float(disk_cfg["temperature"])
                    if "endpoints" in disk_cfg and isinstance(disk_cfg["endpoints"], dict):
                        cfg["endpoints"].update(disk_cfg["endpoints"])
                    if "keys" in disk_cfg and isinstance(disk_cfg["keys"], dict):
                        cfg["keys"].update(disk_cfg["keys"])
                    if "mcp_gateway_port" in disk_cfg:
                        cfg["mcp_gateway_port"] = int(disk_cfg["mcp_gateway_port"])
            except Exception:
                pass

        # Environment variable overrides
        env_map = {
            "OPENAI_API_KEY": ("keys", "openai"),
            "ANTHROPIC_API_KEY": ("keys", "anthropic"),
            "GEMINI_API_KEY": ("keys", "gemini_api"),
            "GOOGLE_API_KEY": ("keys", "gemini_api"),
            "OPENROUTER_API_KEY": ("keys", "openrouter"),
            "XAI_API_KEY": ("keys", "xai_grok"),
            "PERPLEXITY_API_KEY": ("keys", "perplexity"),
            "GROQ_API_KEY": ("keys", "groq"),
            "DEEPSEEK_API_KEY": ("keys", "deepseek"),
            "OLLAMA_API_KEY": ("keys", "ollama_cloud"),
            "CUSTOM_OPENAI_API_KEY": ("keys", "custom_openai"),
            "AGY_BRIDGE_URL": ("endpoints", "agy_bridge"),
            "OLLAMA_HOST": ("endpoints", "ollama"),
            "LM_STUDIO_URL": ("endpoints", "lm_studio"),
            "VLLM_URL": ("endpoints", "vllm"),
            "AZOTH_URL": ("endpoints", "azoth_local"),
        }
        for env_var, (section, key) in env_map.items():
            val = os.environ.get(env_var)
            if val:
                if section == "endpoints":
                    if not val.startswith(("http://", "https://")):
                        val = f"http://{val}"
                    # Normalize 0.0.0.0 host bindings to loopback 127.0.0.1 for client calls
                    val = val.replace("://0.0.0.0", "://127.0.0.1")
                cfg[section][key] = val
                if key == "ollama":
                    cfg["endpoints"]["ollama_local"] = val

        return cfg

    def save_config(self, new_config: Dict[str, Any]) -> bool:
        """Saves configuration atomically with strict 0600 file permissions."""
        try:
            if "active_provider" in new_config:
                self.config["active_provider"] = str(new_config["active_provider"])
            if "active_model" in new_config:
                self.config["active_model"] = validate_model_name(str(new_config["active_model"]))
            if "temperature" in new_config:
                self.config["temperature"] = max(0.0, min(2.0, float(new_config["temperature"])))
            if "endpoints" in new_config and isinstance(new_config["endpoints"], dict):
                self.config["endpoints"].update(new_config["endpoints"])
                if "ollama_local" in new_config["endpoints"]:
                    self.config["endpoints"]["ollama"] = new_config["endpoints"]["ollama_local"]
                elif "ollama" in new_config["endpoints"]:
                    self.config["endpoints"]["ollama_local"] = new_config["endpoints"]["ollama"]
            if "keys" in new_config and isinstance(new_config["keys"], dict):
                for k, v in new_config["keys"].items():
                    if v == "":
                        self.config["keys"][k] = ""
                    elif isinstance(v, str) and not v.startswith("●●●") and v != "[REDACTED]":
                        self.config["keys"][k] = v.strip()
            if "mcp_gateway_port" in new_config:
                self.config["mcp_gateway_port"] = int(new_config["mcp_gateway_port"])

            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(self.config_path.parent, 0o700)
            except OSError:
                pass
            atomic_write_text(self.config_path, json.dumps(self.config, indent=2))
            try:
                os.chmod(self.config_path, 0o600)
            except OSError:
                pass
            return True
        except Exception:
            return False

    def clear_keys(self) -> bool:
        """Clears all stored cloud API keys from memory and 0600 secrets file."""
        for k in SECRET_KEY_FIELDS:
            self.config["keys"][k] = ""
        return self.save_config({})

    def get_public_status(self) -> Dict[str, Any]:
        """Returns safe status report with masked API keys (zero plaintext secrets)."""
        masked_keys: Dict[str, str] = {}
        for provider, key in self.config.get("keys", {}).items():
            if key and len(key) > 8:
                masked_keys[provider] = f"{key[:4]}...{key[-4:]}"
            elif key:
                masked_keys[provider] = "●●●●●●"
            else:
                masked_keys[provider] = ""

        return {
            "active_provider": self.config.get("active_provider", "heuristic"),
            "active_model": self.config.get("active_model", "default"),
            "temperature": self.config.get("temperature", 0.3),
            "endpoints": self.config.get("endpoints", {}),
            "mcp_gateway_port": self.config.get("mcp_gateway_port", 8091),
            "keys_status": {p: bool(k) for p, k in self.config.get("keys", {}).items()},
            "masked_keys": masked_keys,
            "storage_mode": "server_0600_secrets",
            "supported_providers": PROVIDER_CATALOG,
        }

    def discover_providers(self) -> Dict[str, Any]:
        """Live-probes local bridges/daemons/CLIs and reports configured cloud providers."""
        discovered: List[Dict[str, Any]] = []
        recommended: Optional[str] = None

        for meta in PROVIDER_CATALOG:
            pid = meta["id"]
            entry = dict(meta)
            if pid == "heuristic":
                entry.update({"available": True, "status": "online", "latency_ms": 0.1, "models": [meta["default_model"]]})
            elif meta["group"] == "local_daemon":
                res = self.test_connection(pid)
                entry.update({
                    "available": bool(res.get("success")),
                    "status": "online" if res.get("success") else "offline",
                    "latency_ms": res.get("latency_ms"),
                    "models": res.get("models", []),
                    "detail": res.get("message", ""),
                })
                if res.get("success") and recommended is None and pid in ("agy_bridge", "ollama_local", "azoth_local"):
                    recommended = pid
            elif meta["group"] == "local_cli":
                bin_path = _resolve_cli_binary(pid)
                if not bin_path:
                    entry.update({"available": False, "status": "not_installed", "detail": "Binary not found on PATH"})
                else:
                    guard_msg = _is_harness_or_loop_wrapper(bin_path, pid)
                    if guard_msg:
                        entry.update({"available": False, "status": "guarded", "binary": bin_path, "detail": guard_msg})
                    else:
                        entry.update({"available": True, "status": "ready", "binary": bin_path, "detail": f"CLI ready at {bin_path}"})
                        if recommended is None:
                            recommended = pid
            else:
                has_key = bool(self.config.get("keys", {}).get(pid))
                entry.update({
                    "available": has_key,
                    "status": "configured" if has_key else "needs_key",
                    "detail": "API key loaded in server 0600 store" if has_key else f"Provide {meta.get('env_var', 'API key')} to enable",
                })
            discovered.append(entry)

        return {
            "active_provider": self.config.get("active_provider", "heuristic"),
            "active_model": self.config.get("active_model", "default"),
            "recommended_provider": recommended or "heuristic",
            "providers": discovered,
            "local_online_count": sum(1 for d in discovered if d.get("type") == "local" and d.get("available")),
            "cloud_configured_count": sum(1 for d in discovered if d.get("type") == "cloud" and d.get("available")),
        }

    def test_connection(
        self,
        provider: str,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Tests connectivity to any local daemon, local CLI, or cloud API provider."""
        raw_provider = (provider or "heuristic").strip().lower()
        norm_provider = _normalize_provider(raw_provider)

        if model:
            try:
                validate_model_name(model)
            except ValueError as exc:
                return {"success": False, "provider": raw_provider, "message": str(exc)}

        target_endpoint = (
            endpoint
            or self.config.get("endpoints", {}).get(raw_provider)
            or self.config.get("endpoints", {}).get(norm_provider, "")
        )
        if target_endpoint:
            target_endpoint = target_endpoint.replace("://0.0.0.0", "://127.0.0.1")
        target_key = api_key or self.config.get("keys", {}).get(norm_provider, "")

        if norm_provider == "heuristic":
            return {
                "success": True,
                "provider": "heuristic",
                "latency_ms": 0.1,
                "message": "Built-in Heuristic Engine is active and ready (100% offline).",
                "models": ["deterministic-rule-synthesizer-v2"],
            }

        start_time = time.time()

        try:
            # 1. Local Ollama (:11434)
            if norm_provider == "ollama_local":
                url = f"{target_endpoint.rstrip('/')}/api/tags"
                req = urllib.request.Request(url, headers={"User-Agent": "AEO-Graph-Engine/2.1"})
                with urllib.request.urlopen(req, timeout=3) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                        return {
                            "success": True,
                            "provider": raw_provider,
                            "endpoint": target_endpoint,
                            "latency_ms": latency,
                            "models": models[:16],
                            "message": f"Connected to Ollama in {latency}ms ({len(models)} models: {', '.join(models[:3]) or 'none'})",
                        }

            # 2. Local OpenAI-compatible daemons (AGY Bridge :18000, LM Studio :1234, vLLM :8000)
            if norm_provider in ("agy_bridge", "lm_studio", "vllm"):
                base = target_endpoint.rstrip("/")
                url = f"{base}/models" if base.endswith("/v1") else f"{base}/v1/models"
                headers = {"User-Agent": "AEO-Graph-Engine/2.1"}
                if target_key:
                    headers["Authorization"] = f"Bearer {target_key}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                        return {
                            "success": True,
                            "provider": norm_provider,
                            "endpoint": target_endpoint,
                            "latency_ms": latency,
                            "models": models[:16],
                            "message": f"Connected to {norm_provider.upper()} at {target_endpoint} in {latency}ms ({len(models)} model(s)).",
                        }

            # 3. AZOTH Local Archon (:8136)
            if norm_provider == "azoth_local":
                url = f"{target_endpoint.rstrip('/')}/health"
                req = urllib.request.Request(url, headers={"User-Agent": "AEO-Graph-Engine/2.1"})
                with urllib.request.urlopen(req, timeout=3) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        return {
                            "success": True,
                            "provider": "azoth_local",
                            "endpoint": target_endpoint,
                            "latency_ms": latency,
                            "models": ["azoth-archon"],
                            "message": f"Connected to AZOTH Archon at {target_endpoint} in {latency}ms.",
                        }

            # 4. Local Sovereign CLI agents (zero shell=True, loop/harness guarded)
            if norm_provider in _CLI_CANDIDATES:
                bin_path = _resolve_cli_binary(norm_provider)
                if not bin_path:
                    return {
                        "success": False,
                        "provider": norm_provider,
                        "latency_ms": round((time.time() - start_time) * 1000, 1),
                        "message": f"CLI binary for '{norm_provider}' not found on PATH.",
                    }
                guard_msg = _is_harness_or_loop_wrapper(bin_path, norm_provider)
                if guard_msg:
                    return {
                        "success": False,
                        "provider": norm_provider,
                        "latency_ms": round((time.time() - start_time) * 1000, 1),
                        "message": guard_msg,
                    }
                proc = subprocess.run(
                    [bin_path, "--version"],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=4,
                    shell=False,
                )
                latency = round((time.time() - start_time) * 1000, 1)
                ver_line = ((proc.stdout or proc.stderr or "").strip().splitlines() or ["ready"])[0][:80]
                return {
                    "success": proc.returncode == 0,
                    "provider": norm_provider,
                    "binary": bin_path,
                    "latency_ms": latency,
                    "models": [ver_line],
                    "message": f"CLI {norm_provider} ready ({ver_line}) in {latency}ms." if proc.returncode == 0 else f"CLI exited {proc.returncode}: {ver_line}",
                }

            # 5. Cloud OpenAI-compatible providers
            if norm_provider in ("openai", "groq", "openrouter", "perplexity", "xai_grok", "deepseek", "custom_openai"):
                if not target_key and norm_provider != "custom_openai":
                    return {
                        "success": False,
                        "provider": norm_provider,
                        "message": f"API Key not provided for {norm_provider.upper()}.",
                    }
                base_url = target_endpoint or DEFAULT_AI_GATEWAY_CONFIG["endpoints"].get(norm_provider, "https://api.openai.com/v1")
                url = f"{base_url.rstrip('/')}/models"
                headers = {"User-Agent": "AEO-Graph-Engine/2.1"}
                if target_key:
                    headers["Authorization"] = f"Bearer {target_key}"
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=6) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        models = [m.get("id") for m in data.get("data", []) if m.get("id")]
                        return {
                            "success": True,
                            "provider": norm_provider,
                            "latency_ms": latency,
                            "models": models[:10],
                            "message": f"{norm_provider.upper()} API Key verified in {latency}ms.",
                        }

            # 6. Google Gemini API
            if norm_provider == "gemini_api":
                if not target_key:
                    return {"success": False, "provider": "gemini_api", "message": "Gemini API Key not provided."}
                base_url = (target_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
                url = f"{base_url}/models?key={urllib.parse.quote(target_key)}"
                req = urllib.request.Request(url, headers={"User-Agent": "AEO-Graph-Engine/2.1"})
                with urllib.request.urlopen(req, timeout=6) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        data = json.loads(response.read().decode("utf-8"))
                        models = [m.get("name", "").split("/")[-1] for m in data.get("models", []) if m.get("name")]
                        return {
                            "success": True,
                            "provider": "gemini_api",
                            "latency_ms": latency,
                            "models": models[:10],
                            "message": f"Google Gemini API connected in {latency}ms ({len(models)} models).",
                        }

            # 7. Ollama Cloud
            if norm_provider == "ollama_cloud":
                if not target_key:
                    return {"success": False, "provider": "ollama_cloud", "message": "Ollama Cloud API Key not provided."}
                base_url = (target_endpoint or "https://ollama.com/api").rstrip("/")
                req = urllib.request.Request(
                    f"{base_url}/tags",
                    headers={"Authorization": f"Bearer {target_key}", "User-Agent": "AEO-Graph-Engine/2.1"},
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    data = json.loads(response.read().decode("utf-8"))
                    models = [m.get("name") for m in data.get("models", []) if m.get("name")]
                    return {
                        "success": True,
                        "provider": "ollama_cloud",
                        "latency_ms": latency,
                        "models": models[:10],
                        "message": f"Ollama Cloud connected in {latency}ms.",
                    }

            # 8. Anthropic Claude
            if norm_provider == "anthropic":
                if not target_key:
                    return {"success": False, "provider": "anthropic", "message": "Anthropic API Key not provided."}
                url = "https://api.anthropic.com/v1/messages"
                test_payload = {
                    "model": validate_model_name(model or "claude-3-5-haiku-20241022"),
                    "max_tokens": 1,
                    "messages": [{"role": "user", "content": "ping"}],
                }
                req = urllib.request.Request(
                    url,
                    data=json.dumps(test_payload).encode("utf-8"),
                    headers={
                        "x-api-key": target_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                        "User-Agent": "AEO-Graph-Engine/2.1",
                    },
                )
                with urllib.request.urlopen(req, timeout=6) as response:
                    latency = round((time.time() - start_time) * 1000, 1)
                    if response.status == 200:
                        return {
                            "success": True,
                            "provider": "anthropic",
                            "latency_ms": latency,
                            "message": f"Anthropic Claude API connected in {latency}ms.",
                        }

        except urllib.error.HTTPError as e:
            latency = round((time.time() - start_time) * 1000, 1)
            err_body = ""
            try:
                err_body = e.read().decode("utf-8", errors="ignore")
            except Exception:
                pass
            return {
                "success": False,
                "provider": raw_provider,
                "latency_ms": latency,
                "http_status": e.code,
                "message": f"HTTP {e.code} from {raw_provider}: {e.reason} ({err_body[:120]})",
            }
        except Exception as e:
            latency = round((time.time() - start_time) * 1000, 1)
            return {
                "success": False,
                "provider": raw_provider,
                "latency_ms": latency,
                "message": f"Connection failed to {target_endpoint or raw_provider}: {str(e)}",
            }

        return {
            "success": False,
            "provider": raw_provider,
            "message": f"Unknown provider or unsupported test protocol for '{raw_provider}'.",
        }

    def complete_prompt(
        self,
        prompt: str,
        *,
        system_prompt: str = "You are an Answer Engine Optimization (AEO) and Schema.org technical analyst. Be concise, concrete, and accurate.",
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Executes a real completion call against the requested or active provider."""
        norm_provider = _normalize_provider(provider or self.config.get("active_provider", "heuristic"))
        chosen_model = validate_model_name(model or self.config.get("active_model") or "default")
        target_endpoint = (
            endpoint or self.config.get("endpoints", {}).get(norm_provider, "")
        ).replace("://0.0.0.0", "://127.0.0.1")
        target_key = api_key or self.config.get("keys", {}).get(norm_provider, "")
        temp = float(self.config.get("temperature", 0.3))

        if norm_provider == "heuristic":
            return {"success": False, "provider": "heuristic", "error": "Heuristic mode does not invoke an LLM."}

        t0 = time.time()
        try:
            # 1. OpenAI-compatible HTTP endpoints (AGY Bridge, LM Studio, vLLM, OpenAI, OpenRouter, Groq, xAI, Perplexity, DeepSeek, Custom)
            if norm_provider in (
                "agy_bridge", "lm_studio", "vllm", "openai", "openrouter",
                "xai_grok", "perplexity", "groq", "deepseek", "custom_openai"
            ):
                if chosen_model == "default":
                    meta = next((m for m in PROVIDER_CATALOG if m["id"] == norm_provider), {})
                    chosen_model = meta.get("default_model", "gemini-3.8-flash-high")
                base = (target_endpoint or DEFAULT_AI_GATEWAY_CONFIG["endpoints"].get(norm_provider, "")).rstrip("/")
                url = f"{base}/chat/completions" if base.endswith("/v1") or norm_provider == "perplexity" else f"{base}/v1/chat/completions"
                headers = {"Content-Type": "application/json", "User-Agent": "AEO-Graph-Engine/2.1"}
                if target_key:
                    headers["Authorization"] = f"Bearer {target_key}"
                body = {
                    "model": chosen_model,
                    "temperature": temp,
                    "max_tokens": int(self.config.get("max_tokens", 1200)),
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                }
                req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["choices"][0]["message"]["content"]
                    return {
                        "success": True,
                        "provider": norm_provider,
                        "model": data.get("model", chosen_model),
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "content": text,
                    }

            # 2. Ollama Local / Ollama Cloud
            if norm_provider in ("ollama_local", "ollama_cloud"):
                if chosen_model == "default":
                    probe = self.test_connection(norm_provider, endpoint=target_endpoint, api_key=target_key)
                    models = probe.get("models") or []
                    chosen_model = models[0] if models else "hermes3:8b"
                base = target_endpoint.rstrip("/")
                url = f"{base}/chat" if base.endswith("/api") else f"{base}/api/chat"
                headers = {"Content-Type": "application/json", "User-Agent": "AEO-Graph-Engine/2.1"}
                if target_key:
                    headers["Authorization"] = f"Bearer {target_key}"
                body = {
                    "model": chosen_model,
                    "stream": False,
                    "options": {"temperature": temp},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                }
                req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("message", {}).get("content", "")
                    return {
                        "success": True,
                        "provider": norm_provider,
                        "model": chosen_model,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "content": text,
                    }

            # 3. AZOTH Local (:8136)
            if norm_provider == "azoth_local":
                url = f"{target_endpoint.rstrip('/')}/api/chat"
                body = {"message": f"{system_prompt}\n\n{prompt}"}
                req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "AEO-Graph-Engine/2.1"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data.get("response") or data.get("reply") or data.get("message") or json.dumps(data)
                    return {
                        "success": True,
                        "provider": "azoth_local",
                        "model": "azoth-archon",
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "content": str(text),
                    }

            # 4. Anthropic Claude
            if norm_provider == "anthropic":
                if not target_key:
                    return {"success": False, "provider": "anthropic", "error": "Anthropic API key required."}
                if chosen_model == "default":
                    chosen_model = "claude-3-5-haiku-20241022"
                body = {
                    "model": chosen_model,
                    "max_tokens": int(self.config.get("max_tokens", 1200)),
                    "system": system_prompt,
                    "messages": [{"role": "user", "content": prompt}],
                }
                req = urllib.request.Request(
                    "https://api.anthropic.com/v1/messages",
                    data=json.dumps(body).encode("utf-8"),
                    headers={
                        "x-api-key": target_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = "".join(c.get("text", "") for c in data.get("content", []) if isinstance(c, dict))
                    return {
                        "success": True,
                        "provider": "anthropic",
                        "model": chosen_model,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "content": text,
                    }

            # 5. Google Gemini API
            if norm_provider == "gemini_api":
                if not target_key:
                    return {"success": False, "provider": "gemini_api", "error": "Gemini API key required."}
                if chosen_model == "default":
                    chosen_model = "gemini-2.5-flash"
                base = (target_endpoint or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
                url = f"{base}/models/{urllib.parse.quote(chosen_model)}:generateContent?key={urllib.parse.quote(target_key)}"
                body = {"contents": [{"parts": [{"text": f"{system_prompt}\n\n{prompt}"}]}]}
                req = urllib.request.Request(
                    url,
                    data=json.dumps(body).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
                    text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
                    return {
                        "success": True,
                        "provider": "gemini_api",
                        "model": chosen_model,
                        "latency_ms": round((time.time() - t0) * 1000, 1),
                        "content": text,
                    }

            # 6. Local Sovereign CLIs (shell=False, loop/harness guarded)
            if norm_provider in _CLI_CANDIDATES:
                bin_path = _resolve_cli_binary(norm_provider)
                if not bin_path:
                    return {"success": False, "provider": norm_provider, "error": f"{norm_provider} not installed."}
                guard_msg = _is_harness_or_loop_wrapper(bin_path, norm_provider)
                if guard_msg:
                    return {"success": False, "provider": norm_provider, "error": guard_msg}

                full_prompt = f"{system_prompt}\n\n{prompt}"
                if norm_provider == "agy_cli":
                    cli_model = chosen_model if chosen_model != "default" else "gemini-3.8-flash-high"
                    cmd = [bin_path, "--model", cli_model, "-p", full_prompt, "--output-format", "text"]
                elif norm_provider == "hermes_cli":
                    cmd = [bin_path, "chat", "-q", full_prompt, "--oneshot", "-Q"]
                elif norm_provider == "grok_cli":
                    cmd = [bin_path, "-p", full_prompt, "--output-format", "plain"]
                else:
                    return {"success": False, "provider": norm_provider, "error": f"Non-interactive execution unavailable for {norm_provider}."}

                proc = subprocess.run(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    shell=False,
                )
                if proc.returncode != 0:
                    return {
                        "success": False,
                        "provider": norm_provider,
                        "error": (proc.stderr or proc.stdout or f"Exit {proc.returncode}").strip()[:240],
                    }
                return {
                    "success": True,
                    "provider": norm_provider,
                    "model": chosen_model,
                    "latency_ms": round((time.time() - t0) * 1000, 1),
                    "content": proc.stdout.strip(),
                }

        except Exception as exc:
            return {
                "success": False,
                "provider": norm_provider,
                "latency_ms": round((time.time() - t0) * 1000, 1),
                "error": str(exc),
            }

        return {"success": False, "provider": norm_provider, "error": f"Unsupported provider '{norm_provider}'."}

    def simulate_answer_engine_perception(
        self,
        brand_name: str,
        domain: str,
        query: Optional[str] = None,
        *,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Evaluates how an Answer Engine (Perplexity, ChatGPT Search, Claude) perceives
        the target entity. Invokes the configured/requested live AI provider when active,
        or returns an honest, clearly-labeled deterministic offline heuristic evaluation
        (never returning hardcoded '98.5%' scores on empty/invalid domains).
        """
        clean_brand = (brand_name or "").strip() or "Unnamed Entity"
        clean_domain = (domain or "").strip().replace("https://", "").replace("http://", "").rstrip("/")
        sim_query = query or f"What is {clean_brand} ({clean_domain}) and what makes it notable?"

        chosen_provider = _normalize_provider(provider or self.config.get("active_provider", "heuristic"))

        # Try genuine live LLM invocation when a non-heuristic provider is active or specified
        if chosen_provider != "heuristic":
            schema_excerpt = json.dumps(schema, indent=2)[:1800] if isinstance(schema, dict) else "No Schema.org JSON-LD provided."
            llm_prompt = (
                f"Evaluate how an AI Answer Engine (Perplexity, ChatGPT Search, Claude) would ground and cite this brand.\n"
                f"Brand: {clean_brand}\nDomain: {clean_domain}\nQuery: {sim_query}\n"
                f"Description: {description or '(not provided)'}\n"
                f"Schema.org JSON-LD:\n{schema_excerpt}\n\n"
                f"Respond with a concise 4-bullet technical grounding audit: (1) Entity clarity, "
                f"(2) Citation readiness estimate (0-100% with reason), (3) Missing structured-data signals, "
                f"(4) Sample 2-sentence answer synthesis."
            )
            llm_res = self.complete_prompt(
                llm_prompt,
                provider=chosen_provider,
                model=model,
                api_key=api_key,
                endpoint=endpoint,
                timeout=35,
            )
            if llm_res.get("success") and llm_res.get("content"):
                return {
                    "mode": "live_llm",
                    "provider": llm_res["provider"],
                    "model": llm_res["model"],
                    "latency_ms": llm_res["latency_ms"],
                    "brand_name": clean_brand,
                    "domain": clean_domain,
                    "query": sim_query,
                    "simulated_answer": llm_res["content"],
                    "simulated_engine": f"{llm_res['provider']} ({llm_res['model']})",
                    "citation_confidence": "live-evaluated",
                    "top_sources_cited": [
                        f"https://{clean_domain}/llms.txt",
                        f"https://{clean_domain}/#schema-graph",
                        f"https://{clean_domain}/ai.txt",
                    ] if clean_domain else [],
                }
            fallback_note = f"Live provider '{chosen_provider}' unavailable ({llm_res.get('error', 'unreachable')}); fell back to deterministic offline heuristic."
        else:
            fallback_note = "Executed in deterministic offline heuristic mode (select a live local or cloud provider for LLM synthesis)."

        # Honest deterministic offline heuristic (scores vary genuinely with input quality)
        score = 0
        signals: List[str] = []
        gaps: List[str] = []

        if clean_brand and clean_brand != "Unnamed Entity":
            score += 15
            signals.append(f"Brand entity label provided ({clean_brand})")
        else:
            gaps.append("Missing canonical brand/entity name")

        valid_tld = bool(re.fullmatch(r"[A-Za-z0-9.-]+\.[A-Za-z]{2,12}", clean_domain)) and not clean_domain.endswith((".invalid", ".local", ".test", ".localhost"))
        if valid_tld:
            score += 20
            signals.append(f"Syntactically valid public domain ({clean_domain})")
        else:
            gaps.append(f"Domain '{clean_domain or '(empty)'}' is non-routable or invalid for public AI indexing")

        if description and len(description.strip()) >= 40:
            score += 20
            signals.append("Substantive entity description provided (>=40 chars)")
        else:
            gaps.append("No detailed entity description supplied for answer-lead grounding")

        graph_nodes = schema.get("@graph", []) if isinstance(schema, dict) else []
        if isinstance(graph_nodes, list) and graph_nodes:
            score += 25
            types_present = {
                t for n in graph_nodes if isinstance(n, dict)
                for t in ([n.get("@type")] if isinstance(n.get("@type"), str) else (n.get("@type") or []))
            }
            signals.append(f"Linked JSON-LD @graph supplied ({len(graph_nodes)} nodes: {', '.join(sorted(types_present))})")
            if "FAQPage" in types_present:
                score += 20
                signals.append("FAQPage Q&A schema present for direct citation")
            else:
                gaps.append("FAQPage node missing from @graph")
        else:
            gaps.append("No Schema.org JSON-LD @graph payload supplied to verify entity linking")

        confidence_pct = f"{score}.0%"
        answer_lines = [
            f"### Offline Heuristic Evaluation — {clean_brand} ({clean_domain or 'no-domain'})",
            f"**Note:** {fallback_note}",
            f"**Estimated Readiness Score:** {confidence_pct} (based solely on supplied local inputs — no live web crawl or LLM call performed).",
            "",
            "**Observed Signals:**",
            *([f"- {s}" for s in signals] or ["- None"]),
            "",
            "**Gaps Limiting AI Citations:**",
            *([f"- {g}" for g in gaps] or ["- None detected in local payload"]),
        ]

        return {
            "mode": "offline_heuristic",
            "provider": "heuristic",
            "model": "deterministic-rule-synthesizer-v2",
            "brand_name": clean_brand,
            "domain": clean_domain,
            "query": sim_query,
            "simulated_answer": "\n".join(answer_lines),
            "simulated_engine": "Offline Deterministic Heuristic (No LLM Invoked)",
            "citation_confidence": confidence_pct,
            "heuristic_score": score,
            "notice": fallback_note,
            "top_sources_cited": [
                f"https://{clean_domain}/llms.txt",
                f"https://{clean_domain}/#schema-graph",
                f"https://{clean_domain}/ai.txt",
            ] if clean_domain else [],
        }

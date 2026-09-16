"""
AI Bot Inspector & WAF Probe Specialist for AEO Graph Engine.

Probes live URLs using authentic User-Agent signatures of 10 major AI Search Bots
and LLM crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended,
Applebot-Extended, Meta-ExternalAgent, Bytespider, Diffbot, Cohere-training-data-crawler).

Detects Web Application Firewall (WAF) challenges (Cloudflare Turnstile/CAPTCHA/Challenge,
AWS WAF, DataDome, PerimeterX/HUMAN, Akamai, Imperva), HTTP status codes (200, 403, 429, 503),
latency metrics, server infrastructure, and X-Robots-Tag restrictions (noai, noimageai, noindex).

Zero external runtime dependencies (Python standard library only).
"""

import concurrent.futures
import http.client
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple, Union


# ---------------------------------------------------------------------------
# Registry of 10 Major AI Search Bots and Crawlers
# ---------------------------------------------------------------------------

AI_BOT_REGISTRY: Dict[str, Dict[str, Any]] = {
    "gptbot": {
        "id": "gptbot",
        "name": "GPTBot",
        "operator": "OpenAI",
        "purpose": "AI Model Training & Web Ingestion",
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.2; +https://openai.com/gptbot)",
        "doc_url": "https://platform.openai.com/docs/gptbot",
    },
    "oai-searchbot": {
        "id": "oai-searchbot",
        "name": "OAI-SearchBot",
        "operator": "OpenAI Search",
        "purpose": "Search Engine Indexing & Real-Time AI Search",
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)",
        "doc_url": "https://platform.openai.com/docs/searchbot",
    },
    "claudebot": {
        "id": "claudebot",
        "name": "ClaudeBot",
        "operator": "Anthropic",
        "purpose": "Claude AI Training & Knowledge Ingestion",
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ClaudeBot/1.0; +claudebot@anthropic.com)",
        "doc_url": "https://darkvisitors.com/agents/claudebot",
    },
    "perplexitybot": {
        "id": "perplexitybot",
        "name": "PerplexityBot",
        "operator": "Perplexity AI",
        "purpose": "Conversational Search Engine Indexing",
        "user_agent": "Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot)",
        "doc_url": "https://docs.perplexity.ai/docs/perplexitybot",
    },
    "google-extended": {
        "id": "google-extended",
        "name": "Google-Extended",
        "operator": "Google (Gemini / Vertex)",
        "purpose": "Gemini & Vertex AI Training Data Collection",
        "user_agent": "Mozilla/5.0 (compatible; Google-Extended/1.0; +https://developers.google.com/search/docs/crawling-indexing/google-extended)",
        "doc_url": "https://developers.google.com/search/docs/crawling-indexing/google-extended",
    },
    "applebot-extended": {
        "id": "applebot-extended",
        "name": "Applebot-Extended",
        "operator": "Apple (Apple Intelligence)",
        "purpose": "Apple Intelligence & Siri Foundation Models",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15 (Applebot/0.1; +http://www.apple.com/go/applebot)",
        "doc_url": "https://support.apple.com/en-us/119829",
    },
    "meta-externalagent": {
        "id": "meta-externalagent",
        "name": "Meta-ExternalAgent",
        "operator": "Meta (Meta AI / LLaMA)",
        "purpose": "Meta AI Assistant & LLaMA Foundation Training",
        "user_agent": "Mozilla/5.0 (compatible; Meta-ExternalAgent/1.1; +https://developers.facebook.com/docs/sharing/bot)",
        "doc_url": "https://developers.facebook.com/docs/sharing/bot",
    },
    "bytespider": {
        "id": "bytespider",
        "name": "Bytespider",
        "operator": "ByteDance (TikTok AI)",
        "purpose": "TikTok / Doubao AI Search & Model Training",
        "user_agent": "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)",
        "doc_url": "https://darkvisitors.com/agents/bytespider",
    },
    "diffbot": {
        "id": "diffbot",
        "name": "Diffbot",
        "operator": "Diffbot (Knowledge Graph)",
        "purpose": "Knowledge Graph Extraction & Web Structuring",
        "user_agent": "Mozilla/5.0 (compatible; Diffbot/0.1; +http://www.diffbot.com/robot/)",
        "doc_url": "https://docs.diffbot.com/docs/knowledge-graph-crawling",
    },
    "cohere-training-data-crawler": {
        "id": "cohere-training-data-crawler",
        "name": "Cohere-training-data-crawler",
        "operator": "Cohere",
        "purpose": "Command R+ & Enterprise LLM Pre-training",
        "user_agent": "Mozilla/5.0 (compatible; Cohere-training-data-crawler/1.0; +https://cohere.com/crawler)",
        "doc_url": "https://docs.cohere.com",
    },
}

# Bot Aliases for flexible, case-insensitive lookups
BOT_ALIASES: Dict[str, str] = {
    "gptbot": "gptbot",
    "gpt-bot": "gptbot",
    "gpt_bot": "gptbot",
    "openai": "gptbot",
    "oai-searchbot": "oai-searchbot",
    "oaisearchbot": "oai-searchbot",
    "oai_searchbot": "oai-searchbot",
    "openai-search": "oai-searchbot",
    "searchbot": "oai-searchbot",
    "claudebot": "claudebot",
    "claude-bot": "claudebot",
    "claude_bot": "claudebot",
    "claude": "claudebot",
    "anthropic": "claudebot",
    "perplexitybot": "perplexitybot",
    "perplexity-bot": "perplexitybot",
    "perplexity_bot": "perplexitybot",
    "perplexity": "perplexitybot",
    "google-extended": "google-extended",
    "google_extended": "google-extended",
    "googleextended": "google-extended",
    "google-gemini": "google-extended",
    "gemini": "google-extended",
    "applebot-extended": "applebot-extended",
    "applebot_extended": "applebot-extended",
    "applebotextended": "applebot-extended",
    "apple-intelligence": "applebot-extended",
    "applebot": "applebot-extended",
    "meta-externalagent": "meta-externalagent",
    "meta_externalagent": "meta-externalagent",
    "metaexternalagent": "meta-externalagent",
    "meta-agent": "meta-externalagent",
    "meta": "meta-externalagent",
    "llama": "meta-externalagent",
    "bytespider": "bytespider",
    "byte-spider": "bytespider",
    "bytedance": "bytespider",
    "tiktok": "bytespider",
    "diffbot": "diffbot",
    "diff-bot": "diffbot",
    "cohere-training-data-crawler": "cohere-training-data-crawler",
    "cohere_training_data_crawler": "cohere-training-data-crawler",
    "cohere-crawler": "cohere-training-data-crawler",
    "cohere": "cohere-training-data-crawler",
}


def normalize_bot_id(bot_id: str) -> str:
    """Normalizes any bot ID string to its canonical registry ID."""
    clean = bot_id.strip().lower().replace("_", "-")
    return BOT_ALIASES.get(clean, clean)


def get_bot_registry() -> Dict[str, Dict[str, Any]]:
    """Returns the full dictionary of supported AI bots."""
    return AI_BOT_REGISTRY


def get_bot_info(bot_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves metadata and User-Agent for a given bot ID or alias."""
    norm_id = normalize_bot_id(bot_id)
    return AI_BOT_REGISTRY.get(norm_id)


def list_supported_bots() -> List[Dict[str, Any]]:
    """Returns a list of all supported bots with full metadata."""
    return list(AI_BOT_REGISTRY.values())


# ---------------------------------------------------------------------------
# X-Robots-Tag Header Parsing
# ---------------------------------------------------------------------------

AI_RESTRICTION_KEYWORDS = {
    "noai",
    "noimageai",
    "no-ai",
    "no-image-ai",
    "none",
    "noindex",
}


def parse_x_robots_tag(headers: Dict[str, str]) -> Tuple[Optional[str], List[str], List[str]]:
    """
    Parses X-Robots-Tag header values and identifies AI-specific restriction directives.
    
    Returns:
        (raw_header_value, parsed_directives, ai_restrictions)
    """
    raw_tag: Optional[str] = None
    for k, v in headers.items():
        if k.lower() == "x-robots-tag":
            raw_tag = v
            break

    if not raw_tag:
        return None, [], []

    # Split directives by comma
    raw_directives = [d.strip() for d in raw_tag.split(",") if d.strip()]
    directives: List[str] = []
    ai_restrictions: List[str] = []

    for d in raw_directives:
        directives.append(d)
        d_lower = d.lower()
        if d_lower in AI_RESTRICTION_KEYWORDS:
            ai_restrictions.append(d)
        elif any(kw in d_lower for kw in ("noai", "noimageai", "no-ai")):
            ai_restrictions.append(d)

    return raw_tag, directives, ai_restrictions


# ---------------------------------------------------------------------------
# Heuristic WAF & Bot Protection Detection
# ---------------------------------------------------------------------------

def detect_waf_signatures(
    headers: Dict[str, str],
    body: str,
    status_code: int
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Inspects response headers, body content, and status code to detect
    Web Application Firewall (WAF) challenges, CAPTCHAs, and bot blocks.
    
    Returns:
        (waf_detected: bool, waf_vendor: Optional[str], evidence: List[str])
    """
    evidence: List[str] = []
    vendor: Optional[str] = None
    waf_detected = False

    # Normalize headers for case-insensitive lookup
    h_lower = {k.lower(): str(v) for k, v in headers.items()}
    server = h_lower.get("server", "").lower()
    body_lower = body.lower()

    # 1. Cloudflare Detection
    cf_ray = h_lower.get("cf-ray")
    cf_mitigated = h_lower.get("cf-mitigated", "").lower()
    cf_chl_bypass = h_lower.get("cf-chl-bypass")

    if "cloudflare" in server or cf_ray or cf_mitigated:
        is_cf_block = False
        if "challenge" in cf_mitigated:
            evidence.append("Cloudflare header 'cf-mitigated: challenge' detected")
            is_cf_block = True

        if "cf-browser-verification" in body_lower:
            evidence.append("Cloudflare Browser Verification challenge in HTML body")
            is_cf_block = True
        elif "challenge-platform" in body_lower or "cf-challenge" in body_lower:
            evidence.append("Cloudflare Challenge Platform JavaScript in HTML body")
            is_cf_block = True
        elif "attention required! | cloudflare" in body_lower:
            evidence.append("Cloudflare Access Denied / Attention Required page")
            is_cf_block = True
        elif "just a moment..." in body_lower and ("turnstile" in body_lower or "cloudflare" in body_lower):
            evidence.append("Cloudflare Turnstile waiting/challenge interstitial")
            is_cf_block = True
        elif "checking your browser before accessing" in body_lower:
            evidence.append("Cloudflare Under Attack mode challenge page")
            is_cf_block = True
        elif status_code in (403, 503) and ("cloudflare" in server or cf_ray):
            evidence.append(f"Cloudflare Edge returned HTTP {status_code} block")
            is_cf_block = True

        if is_cf_block:
            vendor = "Cloudflare"
            waf_detected = True
        elif "cloudflare" in server:
            # Edge is Cloudflare but not actively blocking this request
            pass

    # 2. AWS WAF Detection
    if not waf_detected:
        aws_action = h_lower.get("x-amzn-waf-action")
        aws_err = h_lower.get("x-amzn-errortype", "").lower()
        if aws_action:
            evidence.append(f"AWS WAF action header: {aws_action}")
            vendor = "AWS WAF"
            waf_detected = True
        elif "waf" in aws_err:
            evidence.append(f"AWS WAF error header: {aws_err}")
            vendor = "AWS WAF"
            waf_detected = True
        elif "awswaf" in body_lower or "aws waf" in body_lower or "waf.amazonaws.com" in body_lower:
            if status_code in (403, 405) or "token-action" in body_lower:
                evidence.append("AWS WAF challenge/block signatures found in body")
                vendor = "AWS WAF"
                waf_detected = True

    # 3. DataDome Detection
    if not waf_detected:
        if "x-datadome" in h_lower or "datadome" in server or "datadome=" in h_lower.get("set-cookie", ""):
            evidence.append("DataDome anti-bot headers/cookies detected")
            vendor = "DataDome"
            waf_detected = True
        elif "datadome.js" in body_lower or "captcha-delivery.com" in body_lower or "datadome captcha" in body_lower:
            evidence.append("DataDome JavaScript CAPTCHA challenge in body")
            vendor = "DataDome"
            waf_detected = True

    # 4. PerimeterX / HUMAN Security
    if not waf_detected:
        if any(k.startswith("x-px-") for k in h_lower) or "perimeterx" in server:
            evidence.append("PerimeterX / HUMAN Security headers detected")
            vendor = "PerimeterX (HUMAN)"
            waf_detected = True
        elif "client.perimeterx.net" in body_lower or "_pxappid" in body_lower or "perimeterx" in body_lower:
            if status_code in (403, 429) or "automation tools" in body_lower:
                evidence.append("PerimeterX sensor challenge found in body")
                vendor = "PerimeterX (HUMAN)"
                waf_detected = True

    # 5. Akamai Bot Manager
    if not waf_detected:
        if "akamai-bot-risk" in h_lower or "akamai-grn" in h_lower or "akamaighost" in server:
            if status_code in (403, 503) or "reference #" in body_lower:
                evidence.append("Akamai Bot Manager edge block detected")
                vendor = "Akamai"
                waf_detected = True

    # 6. Imperva / Incapsula
    if not waf_detected:
        if "x-iinfo" in h_lower or "incapsula" in h_lower.get("x-cdn", "").lower() or "incap_ses" in h_lower.get("set-cookie", ""):
            if status_code in (403, 503) or "incapsula incident id" in body_lower:
                evidence.append("Imperva Incapsula blocking signature detected")
                vendor = "Imperva Incapsula"
                waf_detected = True

    # 7. Vercel Security Checkpoint
    if not waf_detected:
        if "vercel security checkpoint" in body_lower or "deployment protection" in body_lower:
            if status_code in (401, 403):
                evidence.append("Vercel Security Checkpoint / Protection active")
                vendor = "Vercel Security"
                waf_detected = True

    # Generic WAF heuristic for 403 with generic CAPTCHA
    if not waf_detected and status_code in (401, 403):
        if "captcha" in body_lower or "robot" in body_lower or "security check" in body_lower:
            evidence.append(f"HTTP {status_code} with automated challenge/CAPTCHA page")
            vendor = "Generic WAF / Security Shield"
            waf_detected = True

    return waf_detected, vendor, evidence


# ---------------------------------------------------------------------------
# Recommendations Engine
# ---------------------------------------------------------------------------

def generate_bot_recommendations(summary: Dict[str, Any]) -> List[str]:
    """Generates actionable AEO and WAF remediation advice based on probe results."""
    recs: List[str] = []
    waf_detected = summary.get("waf_detected", False)
    waf_vendor = summary.get("waf_vendor")
    blocked_count = summary.get("blocked_count", 0)
    warning_count = summary.get("warning_count", 0)
    allowed_count = summary.get("allowed_count", 0)
    total_bots = summary.get("total_bots", 10)
    bot_results: Dict[str, Dict[str, Any]] = summary.get("bot_results", {})

    blocked_bots = [
        res["name"] for res in bot_results.values()
        if res.get("status_category") == "blocked"
    ]
    warn_bots = [
        res["name"] for res in bot_results.values()
        if res.get("status_category") == "warning"
    ]
    ai_restricted_bots = [
        res["name"] for res in bot_results.values()
        if res.get("ai_restrictions")
    ]

    # Cloudflare recommendations
    if waf_detected and waf_vendor == "Cloudflare":
        if blocked_count > 0:
            recs.append(
                f"Cloudflare WAF is actively blocking AI bots ({', '.join(blocked_bots)}). "
                "Navigate to Cloudflare Dashboard -> Security -> WAF -> AI Scrapers and Crawlers, "
                "and set action to 'Allow' or 'Bypass' for verified AI Search Bots (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot)."
            )
        else:
            recs.append(
                "Cloudflare edge detected. Ensure 'Block AI Scrapers' managed rule remains disabled "
                "so future Answer Engine updates can index new schema markup and llms.txt."
            )

    # AWS WAF recommendations
    elif waf_detected and waf_vendor == "AWS WAF":
        recs.append(
            f"AWS WAF rule match detected. Whitelist AI Crawler User-Agents ({', '.join(blocked_bots or ['AI Bots'])}) "
            "or IP ranges in your AWS WAF WebACL rules to prevent search ranking penalties."
        )

    # DataDome / PerimeterX recommendations
    elif waf_detected and ("DataDome" in str(waf_vendor) or "PerimeterX" in str(waf_vendor)):
        recs.append(
            f"{waf_vendor} anti-bot protection is intercepting requests. Add crawler exceptions "
            "for verified AI Answer Engines to allow citation generation in Perplexity and ChatGPT."
        )

    # Generic Blocked Bots
    elif blocked_count > 0:
        recs.append(
            f"{blocked_count} AI bots ({', '.join(blocked_bots)}) were blocked with HTTP 401/403. "
            "Check server configuration (.htaccess, nginx.conf, Caddyfile) or edge CDN rules blocking AI User-Agents."
        )

    # X-Robots-Tag Restrictions
    if ai_restricted_bots:
        recs.append(
            f"X-Robots-Tag headers contain AI restriction directives (noai/noindex) impacting {', '.join(ai_restricted_bots)}. "
            "Remove 'noai' or 'noimageai' from HTTP response headers if you want full presence in AI search overviews."
        )

    # Rate Limiting (429) Warnings
    if warning_count > 0:
        recs.append(
            f"Rate limiting or warning responses observed for {', '.join(warn_bots)}. "
            "Review edge rate limiting thresholds to prevent false-positive throttling of multi-page AI search indexing."
        )

    # All Clear
    if allowed_count == total_bots and not waf_detected and not ai_restricted_bots:
        recs.append(
            "All 10 major AI Search Bots successfully connected without WAF interference or header restrictions. "
            "Ensure robots.txt and llms.txt are fully populated to maximize AEO citation visibility."
        )

    return recs


# ---------------------------------------------------------------------------
# BotInspector Class
# ---------------------------------------------------------------------------

class BotInspector:
    """
    AI Search Bot Inspector & Web Application Firewall Probe Engine.
    
    Probes live targets using real AI User-Agent strings, analyzes HTTP headers,
    measures latency, detects WAF barriers, and evaluates X-Robots-Tag policies.
    """

    def __init__(
        self,
        default_timeout: float = 5.0,
        custom_user_agents: Optional[Dict[str, str]] = None,
        max_workers: int = 5,
    ):
        self.default_timeout = default_timeout
        self.max_workers = max_workers
        self.registry = dict(AI_BOT_REGISTRY)

        # Allow overriding/extending bot User-Agents
        if custom_user_agents:
            for bot_id, ua in custom_user_agents.items():
                norm_id = normalize_bot_id(bot_id)
                if norm_id in self.registry:
                    self.registry[norm_id] = dict(self.registry[norm_id])
                    self.registry[norm_id]["user_agent"] = ua

    def _normalize_url(self, url: str) -> str:
        """Ensures URL has a proper scheme and format."""
        clean_url = url.strip()
        if not clean_url.startswith("http://") and not clean_url.startswith("https://"):
            clean_url = "https://" + clean_url
        return clean_url

    def inspect_bot(
        self,
        url: str,
        bot_id: str,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Probes a single URL with a specific AI Bot User-Agent.
        
        Args:
            url: Target URL to probe.
            bot_id: Identifier or alias for the bot (e.g. 'gptbot', 'ClaudeBot', 'perplexity').
            timeout: Optional custom timeout in seconds (defaults to self.default_timeout).
            
        Returns:
            Dict containing detailed probe metrics, status codes, headers, and WAF diagnostics.
        """
        target_url = self._normalize_url(url)
        norm_id = normalize_bot_id(bot_id)
        bot_meta = self.registry.get(norm_id)

        if not bot_meta:
            supported = ", ".join(self.registry.keys())
            raise ValueError(f"Unknown bot_id '{bot_id}'. Supported bots: {supported}")

        user_agent = bot_meta["user_agent"]
        effective_timeout = timeout if timeout is not None else self.default_timeout

        req = urllib.request.Request(
            target_url,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "identity",
                "Connection": "close",
            },
        )

        # Create permissive SSL context for scanning
        ssl_ctx = ssl.create_default_context()

        status_code = 0
        latency_ms = 0.0
        resp_headers: Dict[str, str] = {}
        body_text = ""
        error_msg: Optional[str] = None

        start_time = time.perf_counter()

        try:
            with urllib.request.urlopen(req, timeout=effective_timeout, context=ssl_ctx) as response:
                latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
                status_code = getattr(response, "status", getattr(response, "code", 200))
                resp_headers = {k.lower(): str(v) for k, v in response.headers.items()}
                # Read up to 64KB for WAF & header analysis
                raw_body = response.read(65536)
                body_text = raw_body.decode("utf-8", errors="ignore")

        except urllib.error.HTTPError as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            status_code = e.code
            resp_headers = {k.lower(): str(v) for k, v in e.headers.items()} if e.headers else {}
            try:
                raw_body = e.read(65536)
                body_text = raw_body.decode("utf-8", errors="ignore")
            except Exception:
                body_text = ""

        except urllib.error.URLError as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            status_code = 0
            reason = str(e.reason)
            if "timed out" in reason.lower():
                error_msg = f"Connection timed out after {effective_timeout}s"
            else:
                error_msg = f"Network connection error: {reason}"

        except (TimeoutError, http.client.RemoteDisconnected) as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            status_code = 0
            error_msg = f"Connection timed out or remote disconnected: {str(e)}"

        except Exception as e:
            latency_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            status_code = 0
            error_msg = f"Probe error: {str(e)}"

        # Analyze Server and Content-Type
        server_header = resp_headers.get("server", "")
        content_type_header = resp_headers.get("content-type", "")

        # Parse X-Robots-Tag
        raw_x_robots, directives, ai_restrictions = parse_x_robots_tag(resp_headers)

        # Detect WAF Signatures
        waf_detected, waf_vendor, waf_evidence = detect_waf_signatures(
            headers=resp_headers,
            body=body_text,
            status_code=status_code
        )

        # Determine access status category
        allowed = False
        status_category = "error"

        if status_code == 0:
            allowed = False
            status_category = "error"
        elif 200 <= status_code < 300:
            if waf_detected and waf_evidence:
                # Intercepted by WAF challenge despite 200 code
                allowed = False
                status_category = "blocked"
            elif ai_restrictions or "noindex" in directives:
                allowed = True
                status_category = "warning"
            else:
                allowed = True
                status_category = "allowed"
        elif status_code in (401, 403):
            allowed = False
            status_category = "blocked"
        elif status_code == 429:
            allowed = False
            status_category = "warning"
        elif 300 <= status_code < 400:
            allowed = True
            status_category = "warning"
        elif status_code in (503, 520, 521, 522, 523, 524) and waf_detected:
            allowed = False
            status_category = "blocked"
        elif status_code >= 500:
            allowed = False
            status_category = "error"
        else:
            allowed = False
            status_category = "warning"

        return {
            "bot_id": norm_id,
            "name": bot_meta["name"],
            "operator": bot_meta["operator"],
            "purpose": bot_meta["purpose"],
            "user_agent": user_agent,
            "url": target_url,
            "status_code": status_code,
            "latency_ms": latency_ms,
            "allowed": allowed,
            "status_category": status_category,
            "server": server_header,
            "content_type": content_type_header,
            "x_robots_tag": raw_x_robots,
            "x_robots_directives": directives,
            "ai_restrictions": ai_restrictions,
            "waf_detected": waf_detected,
            "waf_vendor": waf_vendor,
            "waf_evidence": waf_evidence,
            "headers": resp_headers,
            "error": error_msg,
        }

    def inspect_all_bots(
        self,
        url: str,
        timeout: Optional[float] = None,
        parallel: bool = True
    ) -> Dict[str, Any]:
        """
        Probes the target URL against all 10 major AI bots and returns a structured summary.
        
        Args:
            url: Target URL to inspect.
            timeout: Optional per-request timeout in seconds.
            parallel: Whether to execute probes concurrently (default True).
            
        Returns:
            Structured dictionary with summary counts, WAF detection, per-bot results, and recommendations.
        """
        target_url = self._normalize_url(url)
        bot_ids = list(self.registry.keys())
        bot_results: Dict[str, Dict[str, Any]] = {}

        if parallel and self.max_workers > 1:
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(bot_ids), self.max_workers)) as executor:
                future_to_bot = {
                    executor.submit(self.inspect_bot, target_url, bid, timeout): bid
                    for bid in bot_ids
                }
                for future in concurrent.futures.as_completed(future_to_bot):
                    bid = future_to_bot[future]
                    try:
                        res = future.result()
                        bot_results[bid] = res
                    except Exception as exc:
                        meta = self.registry.get(bid, {})
                        bot_results[bid] = {
                            "bot_id": bid,
                            "name": meta.get("name", bid),
                            "operator": meta.get("operator", "Unknown"),
                            "purpose": meta.get("purpose", ""),
                            "user_agent": meta.get("user_agent", ""),
                            "url": target_url,
                            "status_code": 0,
                            "latency_ms": 0.0,
                            "allowed": False,
                            "status_category": "error",
                            "server": "",
                            "content_type": "",
                            "x_robots_tag": None,
                            "x_robots_directives": [],
                            "ai_restrictions": [],
                            "waf_detected": False,
                            "waf_vendor": None,
                            "waf_evidence": [],
                            "headers": {},
                            "error": str(exc),
                        }
        else:
            for bid in bot_ids:
                try:
                    bot_results[bid] = self.inspect_bot(target_url, bid, timeout)
                except Exception as exc:
                    meta = self.registry.get(bid, {})
                    bot_results[bid] = {
                        "bot_id": bid,
                        "name": meta.get("name", bid),
                        "operator": meta.get("operator", "Unknown"),
                        "purpose": meta.get("purpose", ""),
                        "user_agent": meta.get("user_agent", ""),
                        "url": target_url,
                        "status_code": 0,
                        "latency_ms": 0.0,
                        "allowed": False,
                        "status_category": "error",
                        "server": "",
                        "content_type": "",
                        "x_robots_tag": None,
                        "x_robots_directives": [],
                        "ai_restrictions": [],
                        "waf_detected": False,
                        "waf_vendor": None,
                        "waf_evidence": [],
                        "headers": {},
                        "error": str(exc),
                    }

        # Calculate summary metrics
        total_bots = len(bot_results)
        allowed_count = sum(1 for r in bot_results.values() if r.get("status_category") == "allowed")
        blocked_count = sum(1 for r in bot_results.values() if r.get("status_category") == "blocked")
        warning_count = sum(1 for r in bot_results.values() if r.get("status_category") == "warning")
        error_count = sum(1 for r in bot_results.values() if r.get("status_category") == "error")

        waf_detected = any(r.get("waf_detected", False) for r in bot_results.values())
        waf_vendor = next((r["waf_vendor"] for r in bot_results.values() if r.get("waf_vendor")), None)

        summary_payload = {
            "target_url": target_url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "total_bots": total_bots,
            "allowed_count": allowed_count,
            "blocked_count": blocked_count,
            "warning_count": warning_count,
            "error_count": error_count,
            "waf_detected": waf_detected,
            "waf_vendor": waf_vendor,
            "bot_results": bot_results,
        }

        # Generate recommendations
        recommendations = generate_bot_recommendations(summary_payload)
        summary_payload["recommendations"] = recommendations

        return summary_payload

    def generate_markdown_report(self, summary: Dict[str, Any]) -> str:
        """Formats the inspection summary into a clean, human-readable Markdown report."""
        lines = [
            f"# AI Search Bot & WAF Inspection Report",
            f"**Target URL:** `{summary.get('target_url')}`",
            f"**Timestamp:** `{summary.get('timestamp')}`",
            "",
            "## Summary",
            f"- **Total Bots Tested:** {summary.get('total_bots', 0)}",
            f"- **Allowed:** {summary.get('allowed_count', 0)} / {summary.get('total_bots', 0)}",
            f"- **Blocked:** {summary.get('blocked_count', 0)}",
            f"- **Warnings:** {summary.get('warning_count', 0)}",
            f"- **Errors:** {summary.get('error_count', 0)}",
            f"- **WAF Detected:** {'Yes (' + str(summary.get('waf_vendor')) + ')' if summary.get('waf_detected') else 'No WAF Challenge Detected'}",
            "",
            "## Probe Results by Bot",
            "| Bot | Operator | Status | Latency | Category | WAF Detected |",
            "|---|---|---|---|---|---|",
        ]

        for bot_id, r in summary.get("bot_results", {}).items():
            st = r.get("status_code", 0)
            st_display = str(st) if st > 0 else "ERR"
            lat = f"{r.get('latency_ms', 0):.1f}ms"
            cat = r.get("status_category", "unknown").upper()
            waf = "YES (" + str(r.get("waf_vendor")) + ")" if r.get("waf_detected") else "No"
            lines.append(f"| **{r.get('name', bot_id)}** | {r.get('operator')} | `{st_display}` | {lat} | `{cat}` | {waf} |")

        recs = summary.get("recommendations", [])
        if recs:
            lines.extend(["", "## Actionable Recommendations"])
            for rec in recs:
                lines.append(f"- {rec}")

        return "\n".join(lines)

"""
Unit tests for AI Bot Inspector & WAF Probe Specialist.
Tests registry definitions, mocked HTTP probing, WAF heuristic detection,
X-Robots-Tag analysis, and summary generation.
"""

import io
import json
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from aeo_graph_engine.bot_inspector import (
    AI_BOT_REGISTRY,
    BotInspector,
    detect_waf_signatures,
    generate_bot_recommendations,
    get_bot_info,
    get_bot_registry,
    list_supported_bots,
    normalize_bot_id,
    parse_x_robots_tag,
)


class TestBotRegistry:
    """Tests registry of 10 major AI bots and alias resolution."""

    def test_registry_contains_10_major_bots(self):
        bots = get_bot_registry()
        assert len(bots) == 10
        expected_keys = {
            "gptbot",
            "oai-searchbot",
            "claudebot",
            "perplexitybot",
            "google-extended",
            "applebot-extended",
            "meta-externalagent",
            "bytespider",
            "diffbot",
            "cohere-training-data-crawler",
        }
        assert set(bots.keys()) == expected_keys

    def test_bot_operators_and_user_agents(self):
        gpt = get_bot_info("gptbot")
        assert gpt is not None
        assert gpt["name"] == "GPTBot"
        assert gpt["operator"] == "OpenAI"
        assert "GPTBot" in gpt["user_agent"]

        claude = get_bot_info("claudebot")
        assert claude is not None
        assert claude["name"] == "ClaudeBot"
        assert claude["operator"] == "Anthropic"
        assert "ClaudeBot" in claude["user_agent"]

        oai_search = get_bot_info("oai-searchbot")
        assert oai_search is not None
        assert "OAI-SearchBot" in oai_search["user_agent"]
        assert oai_search["operator"] == "OpenAI Search"

        perplexity = get_bot_info("perplexitybot")
        assert perplexity is not None
        assert "PerplexityBot" in perplexity["user_agent"]

        google = get_bot_info("google-extended")
        assert google is not None
        assert "Google-Extended" in google["user_agent"]
        assert "Google" in google["operator"]

        apple = get_bot_info("applebot-extended")
        assert apple is not None
        assert "Applebot" in apple["user_agent"]
        assert "Apple" in apple["operator"]

        meta = get_bot_info("meta-externalagent")
        assert meta is not None
        assert "Meta-ExternalAgent" in meta["user_agent"]

        bytespider = get_bot_info("bytespider")
        assert bytespider is not None
        assert "Bytespider" in bytespider["user_agent"]
        assert "ByteDance" in bytespider["operator"]

        diffbot = get_bot_info("diffbot")
        assert diffbot is not None
        assert "Diffbot" in diffbot["user_agent"]

        cohere = get_bot_info("cohere-training-data-crawler")
        assert cohere is not None
        assert "Cohere" in cohere["user_agent"]

    def test_bot_aliases_and_normalization(self):
        assert normalize_bot_id("GPTBot") == "gptbot"
        assert normalize_bot_id("gpt_bot") == "gptbot"
        assert normalize_bot_id("Claude") == "claudebot"
        assert normalize_bot_id("perplexity") == "perplexitybot"
        assert normalize_bot_id("google_extended") == "google-extended"
        assert normalize_bot_id("meta_externalagent") == "meta-externalagent"
        assert normalize_bot_id("tiktok") == "bytespider"
        assert normalize_bot_id("cohere") == "cohere-training-data-crawler"

    def test_list_supported_bots(self):
        bot_list = list_supported_bots()
        assert len(bot_list) == 10
        assert all("user_agent" in b and "name" in b for b in bot_list)


class TestXRobotsTagParsing:
    """Tests X-Robots-Tag header parsing and AI restriction detection."""

    def test_no_x_robots_tag(self):
        raw, directives, ai_restr = parse_x_robots_tag({"Content-Type": "text/html"})
        assert raw is None
        assert directives == []
        assert ai_restr == []

    def test_standard_robots_tag(self):
        headers = {"x-robots-tag": "noindex, nofollow"}
        raw, directives, ai_restr = parse_x_robots_tag(headers)
        assert raw == "noindex, nofollow"
        assert "noindex" in directives
        assert "nofollow" in directives
        assert "noindex" in ai_restr

    def test_ai_specific_restrictions(self):
        headers = {"X-Robots-Tag": "noai, noimageai"}
        raw, directives, ai_restr = parse_x_robots_tag(headers)
        assert raw == "noai, noimageai"
        assert "noai" in directives
        assert "noimageai" in directives
        assert "noai" in ai_restr
        assert "noimageai" in ai_restr


class TestWAFDetectionSignatures:
    """Tests WAF heuristic detection across various vendors."""

    def test_cloudflare_challenge_detection(self):
        headers = {"server": "cloudflare", "cf-ray": "8c3129849281-IAD"}
        body = "<html><head><title>Just a moment...</title></head><body><div id='cf-browser-verification'></div></body></html>"
        detected, vendor, evidence = detect_waf_signatures(headers, body, 403)
        assert detected is True
        assert vendor == "Cloudflare"
        assert any("browser verification" in e.lower() or "cloudflare" in e.lower() for e in evidence)

    def test_cloudflare_turnstile_challenge(self):
        headers = {"server": "cloudflare"}
        body = "<html><body>Just a moment... <script src='https://challenges.cloudflare.com/turnstile/v0/api.js'></script></body></html>"
        detected, vendor, evidence = detect_waf_signatures(headers, body, 200)
        assert detected is True
        assert vendor == "Cloudflare"

    def test_aws_waf_detection(self):
        headers = {"x-amzn-waf-action": "BLOCK", "x-amzn-errortype": "WafForbiddenException"}
        body = "403 Forbidden"
        detected, vendor, evidence = detect_waf_signatures(headers, body, 403)
        assert detected is True
        assert vendor == "AWS WAF"

    def test_datadome_detection(self):
        headers = {"x-datadome": "protected", "server": "datadome"}
        body = "<html><script src='https://geo.captcha-delivery.com/captcha/captcha.js'></script></html>"
        detected, vendor, evidence = detect_waf_signatures(headers, body, 403)
        assert detected is True
        assert vendor == "DataDome"

    def test_perimeterx_detection(self):
        headers = {"x-px-block": "1"}
        body = "Access to this page has been denied because we believe you are using automation tools."
        detected, vendor, evidence = detect_waf_signatures(headers, body, 403)
        assert detected is True
        assert vendor == "PerimeterX (HUMAN)"

    def test_clean_site_no_waf(self):
        headers = {"server": "nginx/1.24.0", "content-type": "text/html; charset=utf-8"}
        body = "<html><head><title>My Clean Site</title></head><body>Welcome!</body></html>"
        detected, vendor, evidence = detect_waf_signatures(headers, body, 200)
        assert detected is False
        assert vendor is None
        assert evidence == []


class TestBotInspectorProbe:
    """Tests BotInspector single-bot probing with mocked HTTP calls."""

    @patch("urllib.request.urlopen")
    def test_inspect_bot_allowed_200(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {
            "Server": "nginx/1.22.0",
            "Content-Type": "text/html; charset=utf-8",
        }
        mock_response.read.return_value = b"<html><head><title>Test Page</title></head><body>Welcome GPTBot</body></html>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        inspector = BotInspector()
        result = inspector.inspect_bot("https://example.com", "gptbot")

        assert result["bot_id"] == "gptbot"
        assert result["name"] == "GPTBot"
        assert result["status_code"] == 200
        assert result["allowed"] is True
        assert result["status_category"] == "allowed"
        assert result["waf_detected"] is False
        assert result["server"] == "nginx/1.22.0"
        assert result["error"] is None

        # Verify User-Agent sent in request
        args, kwargs = mock_urlopen.call_args
        req = args[0]
        assert "GPTBot" in req.get_header("User-agent")

    @patch("urllib.request.urlopen")
    def test_inspect_bot_blocked_cloudflare_403(self, mock_urlopen):
        http_error = urllib.error.HTTPError(
            url="https://example.com",
            code=403,
            msg="Forbidden",
            hdrs={"server": "cloudflare", "cf-ray": "8882937402-EWR"},
            fp=io.BytesIO(b"<html><head><title>Attention Required! | Cloudflare</title></head><body>cf-browser-verification</body></html>"),
        )
        mock_urlopen.side_effect = http_error

        inspector = BotInspector()
        result = inspector.inspect_bot("https://example.com", "claudebot")

        assert result["bot_id"] == "claudebot"
        assert result["status_code"] == 403
        assert result["allowed"] is False
        assert result["status_category"] == "blocked"
        assert result["waf_detected"] is True
        assert result["waf_vendor"] == "Cloudflare"

    @patch("urllib.request.urlopen")
    def test_inspect_bot_x_robots_tag_warning(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {
            "Server": "Caddy",
            "Content-Type": "text/html",
            "X-Robots-Tag": "noai, noimageai",
        }
        mock_response.read.return_value = b"<html><body>AEO site with header block</body></html>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        inspector = BotInspector()
        result = inspector.inspect_bot("https://example.com", "perplexitybot")

        assert result["status_code"] == 200
        assert result["allowed"] is True
        assert result["status_category"] == "warning"
        assert "noai" in result["ai_restrictions"]
        assert "noimageai" in result["ai_restrictions"]

    @patch("urllib.request.urlopen")
    def test_inspect_bot_connection_timeout(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("timed out")

        inspector = BotInspector(default_timeout=2.0)
        result = inspector.inspect_bot("https://timeout-site.test", "meta-externalagent")

        assert result["status_code"] == 0
        assert result["allowed"] is False
        assert result["status_category"] == "error"
        assert "timed out" in str(result["error"]).lower()

    def test_inspect_bot_unknown_id_raises_value_error(self):
        inspector = BotInspector()
        with pytest.raises(ValueError, match="Unknown bot_id 'nonexistent-crawler'"):
            inspector.inspect_bot("https://example.com", "nonexistent-crawler")


class TestBotInspectorAllBots:
    """Tests inspect_all_bots aggregate scoring and recommendations."""

    @patch("urllib.request.urlopen")
    def test_inspect_all_bots_clean_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.headers = {"Server": "Apache/2.4", "Content-Type": "text/html"}
        mock_response.read.return_value = b"<html><body>Welcome AI bots!</body></html>"
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = None
        mock_urlopen.return_value = mock_response

        inspector = BotInspector(max_workers=2)
        summary = inspector.inspect_all_bots("example.com", parallel=False)

        assert summary["target_url"] == "https://example.com"
        assert summary["total_bots"] == 10
        assert summary["allowed_count"] == 10
        assert summary["blocked_count"] == 0
        assert summary["warning_count"] == 0
        assert summary["error_count"] == 0
        assert summary["waf_detected"] is False
        assert len(summary["bot_results"]) == 10
        assert any("All 10 major AI Search Bots" in r for r in summary["recommendations"])

    @patch("urllib.request.urlopen")
    def test_inspect_all_bots_with_cloudflare_blocks(self, mock_urlopen):
        def side_effect_fn(req, *args, **kwargs):
            ua = req.get_header("User-agent", "")
            if "GPTBot" in ua or "ClaudeBot" in ua:
                return urllib.error.HTTPError(
                    url=req.full_url,
                    code=403,
                    msg="Forbidden",
                    hdrs={"server": "cloudflare", "cf-ray": "cf-12345"},
                    fp=io.BytesIO(b"<html><body>Attention Required! | Cloudflare</body></html>"),
                )
            # Other bots allowed
            resp = MagicMock()
            resp.status = 200
            resp.headers = {"server": "cloudflare"}
            resp.read.return_value = b"<html><body>Allowed</body></html>"
            resp.__enter__.return_value = resp
            resp.__exit__.return_value = None
            return resp

        mock_urlopen.side_effect = side_effect_fn

        inspector = BotInspector()
        summary = inspector.inspect_all_bots("https://cf-protected.com", parallel=False)

        assert summary["total_bots"] == 10
        assert summary["blocked_count"] == 2
        assert summary["allowed_count"] == 8
        assert summary["waf_detected"] is True
        assert summary["waf_vendor"] == "Cloudflare"

        # Check recommendations mention Cloudflare dashboard steps
        recs = summary["recommendations"]
        assert any("Cloudflare WAF is actively blocking" in r for r in recs)

    def test_generate_markdown_report(self):
        summary_mock = {
            "target_url": "https://example.com",
            "timestamp": "2026-09-16T21:00:00Z",
            "total_bots": 2,
            "allowed_count": 2,
            "blocked_count": 0,
            "warning_count": 0,
            "error_count": 0,
            "waf_detected": False,
            "waf_vendor": None,
            "bot_results": {
                "gptbot": {
                    "name": "GPTBot",
                    "operator": "OpenAI",
                    "status_code": 200,
                    "latency_ms": 45.2,
                    "status_category": "allowed",
                    "waf_detected": False,
                },
                "claudebot": {
                    "name": "ClaudeBot",
                    "operator": "Anthropic",
                    "status_code": 200,
                    "latency_ms": 50.1,
                    "status_category": "allowed",
                    "waf_detected": False,
                },
            },
            "recommendations": ["All 10 major AI Search Bots successfully connected."],
        }
        inspector = BotInspector()
        md = inspector.generate_markdown_report(summary_mock)
        assert "# AI Search Bot & WAF Inspection Report" in md
        assert "GPTBot" in md
        assert "ClaudeBot" in md
        assert "200" in md

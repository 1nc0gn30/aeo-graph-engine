"""
Security & REST Contract Regression Suite for AEO Graph Engine (v2.1.0).
Locks in SSRF guards, strict loopback CORS + OPTIONS 204, traversal equivalence,
array @type JSON-LD validation, strict POST /api/validate 400 errors,
POST /api/export-zip, 0-entity score 0.0, multi-provider AI discovery,
secret redaction, and zero NullAI default domain leakage.
"""

from __future__ import annotations

import http.client
import io
import json
import threading
import zipfile
from pathlib import Path

import pytest

from aeo_graph_engine.ai_gateway import AIGateway, redact_secrets, validate_model_name
from aeo_graph_engine.core import generate_schema_graph
from aeo_graph_engine.knowledge_graph import analyze_knowledge_graph
from aeo_graph_engine.net_guard import SSRFBlockedError, validate_public_url
from aeo_graph_engine.ui_server import start_ui_server, validate_loopback_origin
from aeo_graph_engine.validator import AEODiagnosticReport, validate_schema_jsonld_dict


@pytest.fixture
def live_server(monkeypatch):
    monkeypatch.delenv("AEO_ALLOW_PRIVATE_URLS", raising=False)
    server = start_ui_server(host="127.0.0.1", port=0)
    host, port = server.server_address
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        yield host, port
    finally:
        server.shutdown()
        server.server_close()


def _http_req(host: str, port: int, method: str, path: str, body: bytes | None = None, headers: dict | None = None):
    conn = http.client.HTTPConnection(host, port, timeout=5)
    try:
        conn.request(method, path, body=body, headers=headers or {})
        resp = conn.getresponse()
        raw = resp.read()
        return resp.status, dict(resp.getheaders()), raw
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# 1. SSRF Protection Tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("bad_url", [
    "http://127.0.0.1:8127/health",
    "http://localhost:3000/",
    "http://[::1]:8127/",
    "http://169.254.169.254/latest/meta-data/",
    "http://10.0.0.1/admin",
    "http://192.168.1.1/",
    "http://172.16.0.1/",
    "file:///etc/passwd",
    "ftp://example.com/file",
    "javascript:alert(1)",
    "http://user:pass@example.com/",
    "http://metadata.google.internal/computeMetadata/v1/",
])
def test_net_guard_blocks_ssrf_targets(bad_url, monkeypatch):
    monkeypatch.delenv("AEO_ALLOW_PRIVATE_URLS", raising=False)
    with pytest.raises(SSRFBlockedError):
        validate_public_url(bad_url)


def test_api_scan_blocks_ssrf_with_403(live_server):
    host, port = live_server
    for target in (
        f"http://127.0.0.1:{port}/health",
        "http://169.254.169.254/latest/meta-data/",
        "file:///etc/passwd",
        "http://10.0.0.1/",
    ):
        status, _, raw = _http_req(
            host,
            port,
            "POST",
            "/api/scan",
            body=json.dumps({"url": target, "max_pages": 1}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        assert status == 403, f"Expected 403 for {target}, got {status}: {raw}"
        data = json.loads(raw.decode("utf-8"))
        assert data.get("blocked") is True


# ---------------------------------------------------------------------------
# 2. Strict Loopback CORS & OPTIONS 204
# ---------------------------------------------------------------------------

def test_cors_origin_validator_rejects_spoofed_origins():
    assert validate_loopback_origin("http://127.0.0.1:3000") == (True, "http://127.0.0.1:3000")
    assert validate_loopback_origin("http://localhost:8127") == (True, "http://localhost:8127")
    assert validate_loopback_origin(None) == (True, None)
    assert validate_loopback_origin("https://evil.example.com")[0] is False
    assert validate_loopback_origin("http://127.0.0.1:8127.evil.com")[0] is False
    assert validate_loopback_origin("http://localhost.evil.com")[0] is False
    assert validate_loopback_origin("javascript://127.0.0.1")[0] is False


def test_http_cors_and_options_204(live_server):
    host, port = live_server

    # Valid loopback OPTIONS -> 204 No Content with echoed Origin
    st, hdrs, _ = _http_req(host, port, "OPTIONS", "/api/generate", headers={"Origin": "http://127.0.0.1:3000"})
    assert st == 204
    assert hdrs.get("Access-Control-Allow-Origin") == "http://127.0.0.1:3000"
    assert hdrs.get("Vary") == "Origin"

    # Evil origin OPTIONS -> 403
    st_evil, hdrs_evil, _ = _http_req(host, port, "OPTIONS", "/api/generate", headers={"Origin": "https://evil.example.com"})
    assert st_evil == 403
    assert "Access-Control-Allow-Origin" not in hdrs_evil

    # Spoofed loopback-prefix origin GET /health -> 403
    st_spoof, hdrs_spoof, _ = _http_req(host, port, "GET", "/health", headers={"Origin": "http://127.0.0.1:8127.evil.com"})
    assert st_spoof == 403
    assert "Access-Control-Allow-Origin" not in hdrs_spoof


# ---------------------------------------------------------------------------
# 3. Path Traversal Containment (Zero Existence Oracle)
# ---------------------------------------------------------------------------

def test_path_traversal_zero_oracle(live_server):
    host, port = live_server
    st1, _, raw1 = _http_req(host, port, "GET", "/../../../../../etc/passwd")
    st2, _, raw2 = _http_req(host, port, "GET", "/../../../../../etc/nonexistent_xyz")
    st3, _, raw3 = _http_req(host, port, "GET", "/%2e%2e/%2e%2e/%2e%2e/etc/passwd")
    assert st1 == st2 == st3 == 404
    assert raw1 == raw2 == raw3


# ---------------------------------------------------------------------------
# 4. Validator Array @type & Strict POST /api/validate 400
# ---------------------------------------------------------------------------

def test_validator_handles_array_type_without_crash():
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": ["Organization", "Corporation"], "@id": "https://acme.dev/#org", "name": "Acme"},
            {"@type": ["WebSite"], "@id": "https://acme.dev/#site", "name": "Acme Web"},
            {"@type": ["SoftwareApplication", "WebApplication"], "@id": "https://acme.dev/#app", "name": "Acme App"},
            {"@type": "FAQPage", "@id": "https://acme.dev/#faq", "name": "FAQ"},
        ],
    }
    report = AEODiagnosticReport("array-type-test")
    validate_schema_jsonld_dict(payload, report)
    assert report.errors == []
    assert report.score == 100.0


def test_api_validate_rejects_malformed_and_missing(live_server):
    host, port = live_server

    # Malformed JSON body
    st, _, _ = _http_req(host, port, "POST", "/api/validate", body=b"{not valid json", headers={"Content-Type": "application/json"})
    assert st == 400

    # Empty object body
    st2, _, _ = _http_req(host, port, "POST", "/api/validate", body=b"{}", headers={"Content-Type": "application/json"})
    assert st2 == 400

    # Invalid jsonld string
    st3, _, _ = _http_req(
        host,
        port,
        "POST",
        "/api/validate",
        body=json.dumps({"jsonld": "{broken"}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert st3 == 400

    # Valid jsonld string succeeds
    valid_ld = json.dumps({"@context": "https://schema.org", "@graph": [{"@type": "Organization", "@id": "https://x.dev/#o", "name": "X"}]})
    st4, _, raw4 = _http_req(
        host,
        port,
        "POST",
        "/api/validate",
        body=json.dumps({"jsonld": valid_ld}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert st4 == 200
    assert json.loads(raw4.decode("utf-8"))["artifacts_detected"]["schema_jsonld"] is True


# ---------------------------------------------------------------------------
# 5. POST /api/export-zip, Custom Domain Non-Leak & 0-Entity KG Score
# ---------------------------------------------------------------------------

def test_post_export_zip_and_no_secret_leak(live_server):
    host, port = live_server
    payload = {
        "site_name": "VectorForge",
        "domain": "vectorforge.dev",
        "niche": "developer_tools",
        "api_key": "sk-secret-must-never-export",
    }
    st, hdrs, raw = _http_req(
        host,
        port,
        "POST",
        "/api/export-zip",
        body=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    assert st == 200
    assert hdrs.get("Content-Type") == "application/zip"
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        names = set(zf.namelist())
        assert {"schema-graph.json", "llms.txt", "llms-full.txt", "ai.txt", "robots.txt"}.issubset(names)
        schema_txt = zf.read("schema-graph.json").decode("utf-8")
        assert "sk-secret-must-never-export" not in schema_txt
        assert "vectorforge.dev" in schema_txt
        assert "aeo.nullai.tech" not in schema_txt
        assert "NullAI" not in schema_txt


def test_custom_domain_never_leaks_nullai_defaults():
    graph = generate_schema_graph({"site_name": "AuditCorp", "domain": "auditcorp.example"}, niche="developer_tools")
    dumped = json.dumps(graph)
    assert "auditcorp.example" in dumped
    assert "NullAI" not in dumped
    assert "aeo.nullai.tech" not in dumped


def test_knowledge_graph_zero_entities_scores_zero():
    report = analyze_knowledge_graph("<div></div>")
    assert report.entities_count == 0
    assert report.entity_coverage_score == 0.0


# ---------------------------------------------------------------------------
# 6. Multi-Provider AI Discovery, Secret Redaction & Honest Heuristic
# ---------------------------------------------------------------------------

def test_providers_endpoint_and_secret_redaction(live_server, tmp_path):
    host, port = live_server
    st, _, raw = _http_req(host, port, "GET", "/api/providers")
    assert st == 200
    data = json.loads(raw.decode("utf-8"))
    ids = {p["id"] for p in data["providers"]}
    assert {"heuristic", "agy_bridge", "ollama_local", "azoth_local", "agy_cli", "hermes_cli", "grok_cli", "codex_cli", "claude_code", "openai", "anthropic", "gemini_api", "openrouter", "xai_grok", "custom_openai"}.issubset(ids)

    # Secret redaction helper
    redacted = redact_secrets({"keys": {"openai": "sk-1234567890", "gemini_api": "AIzaSyTest"}, "name": "ok"})
    assert redacted["keys"]["openai"] == "[REDACTED]"
    assert redacted["keys"]["gemini_api"] == "[REDACTED]"
    assert redacted["name"] == "ok"

    # Model injection blocked
    with pytest.raises(ValueError):
        validate_model_name("gemini; rm -rf /")
    with pytest.raises(ValueError):
        validate_model_name("--evil-flag")

    # Offline heuristic does NOT return canned 98.5% for bogus domain
    gw = AIGateway(tmp_path / "secrets.json")
    sim = gw.simulate_answer_engine_perception("FakeEmpty", "nonexistent.invalid", provider="heuristic")
    assert sim["mode"] == "offline_heuristic"
    assert sim["citation_confidence"] != "98.5%"
    assert sim["heuristic_score"] < 50

"""
Hardened Loopback Web UI & REST API Server for AEO Graph Engine (v2.1.0).

Security & Contract Guarantees:
  - Strict loopback-only CORS via urllib.parse + .port + netloc regex (zero wildcard '*')
  - OPTIONS returns 204 No Content for valid loopback origins and 403 for non-loopback origins
  - Path.is_relative_to() static file containment with zero path-existence oracle
  - SSRFBlockedError mapped cleanly to HTTP 403 across all scanning/crawling endpoints
  - Strict HTTP 400 on malformed JSON or missing/empty POST /api/validate payloads
  - Supports BOTH GET and POST /api/export-zip with zero secret leakage
  - Real computed validation score on POST /api/generate (zero hardcoded 100.0)
  - Multi-provider AI discovery (GET /api/providers), testing, simulation, and offline HTML scan
Zero external runtime dependencies (Python standard library only).
"""

from __future__ import annotations

import io
import json
import mimetypes
import re
import urllib.parse
import zipfile
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from . import __version__
from .ai_config import get_agent_json_schema, synthesize_config_from_prompt
from .ai_gateway import AIGateway, redact_secrets
from .benchmark import compare_sites
from .bot_inspector import BotInspector
from .claim_evidence_matrix import analyze_claim_evidence_matrix
from .core import (
    generate_ai_txt,
    generate_llms_full_txt,
    generate_llms_txt,
    generate_robots_txt,
    generate_schema_graph,
    resolve_config,
)
from .discovery import discover_project_metadata
from .extractor import extract_metadata_from_html
from .framework_exporter import AEORemediationGenerator, FrameworkExporter
from .injector import inject_jsonld_into_html
from .knowledge_graph import analyze_knowledge_graph
from .mcp_server import (
    crawl_sitemap_batch,
    generate_mcp_client_config,
    simulate_ai_citations,
    visualize_schema_graph,
)
from .net_guard import SSRFBlockedError
from .reporter import generate_markdown_report, generate_standalone_html_report
from .scanner import LiveAEOScanner
from .validator import AEODiagnosticReport, validate_schema_jsonld_dict

_LOOPBACK_NETLOC_RE = re.compile(r"^(?:127\.0\.0\.1|localhost)(?::\d{1,5})?$")
_MAX_BODY_BYTES = 5 * 1024 * 1024  # 5 MiB request body cap

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AEO Studio — Answer Engine &amp; Schema Knowledge Graph Workbench</title>
</head>
<body style="font-family:system-ui,sans-serif;background:#08080B;color:#EDEFF2;padding:2rem;">
  <h1>AEO Graph Engine &amp; Studio</h1>
  <p>Public UI bundle not found on disk. REST API is active on <code>/health</code> and <code>/api/*</code>.</p>
</body>
</html>
"""


def validate_loopback_origin(origin: Optional[str]) -> Tuple[bool, Optional[str]]:
    """
    Validates an HTTP Origin header.
    Returns (allowed, cors_origin_to_echo):
      - Missing Origin (same-origin / curl / CLI): (True, None)
      - Valid http(s)://(127.0.0.1|localhost)(:port)?: (True, origin)
      - Any external or spoofed origin (e.g. http://127.0.0.1:8127.evil.com): (False, None)
    """
    if not origin:
        return True, None
    try:
        parsed = urllib.parse.urlparse(origin)
        if parsed.scheme not in ("http", "https"):
            return False, None
        if parsed.path not in ("", "/") or parsed.params or parsed.query or parsed.fragment:
            return False, None
        # Force port parsing so malformed ports like '8127.evil.com' raise ValueError
        port = parsed.port
        if port is not None and not (1 <= port <= 65535):
            return False, None
        if parsed.hostname not in ("127.0.0.1", "localhost"):
            return False, None
        if not _LOOPBACK_NETLOC_RE.fullmatch(parsed.netloc):
            return False, None
        return True, f"{parsed.scheme}://{parsed.netloc}"
    except ValueError:
        return False, None


def _public_roots() -> list[Path]:
    return [
        Path(__file__).resolve().parent.parent.parent / "public",
        Path(__file__).resolve().parent / "public",
        Path.cwd() / "public",
    ]


def _build_export_zip_bytes(cfg_input: Dict[str, Any], niche: str = "developer_tools") -> bytes:
    safe_cfg = redact_secrets(cfg_input or {})
    # Never allow key fields to leak into bundle config
    for drop_key in ("keys", "api_key", "apiKey"):
        safe_cfg.pop(drop_key, None)

    cfg = resolve_config(safe_cfg, niche=niche)
    schema = generate_schema_graph(cfg, niche=niche)
    llms_txt = generate_llms_txt(cfg, niche=niche)
    llms_full = generate_llms_full_txt(cfg, niche=niche)
    ai_txt = generate_ai_txt(cfg, niche=niche)
    robots_txt = generate_robots_txt(cfg, niche=niche)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("schema-graph.json", json.dumps(schema, indent=2, ensure_ascii=False))
        zf.writestr("llms.txt", llms_txt)
        zf.writestr("llms-full.txt", llms_full)
        zf.writestr("ai.txt", ai_txt)
        zf.writestr("robots.txt", robots_txt)
    return zip_buffer.getvalue()


class AEOStudioHTTPHandler(BaseHTTPRequestHandler):
    """Hardened HTTP handler serving AEO Studio UI and REST endpoints."""

    def log_message(self, format, *args):
        pass

    def _check_origin(self) -> Tuple[bool, Optional[str]]:
        origin = self.headers.get("Origin")
        allowed, echo = validate_loopback_origin(origin)
        if not allowed:
            self._send_json(
                {"error": "Cross-origin requests are restricted to loopback origins (127.0.0.1 / localhost)."},
                status=403,
                cors_origin=None,
            )
            return False, None
        return True, echo

    def _send_security_headers(self, cors_origin: Optional[str] = None) -> None:
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "frame-ancestors 'self' http://127.0.0.1:3000 http://localhost:3000 http://127.0.0.1:8127 http://localhost:8127",
        )
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Vary", "Origin")
        if cors_origin:
            self.send_header("Access-Control-Allow-Origin", cors_origin)
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, data: Any, status: int = 200, cors_origin: Optional[str] = None) -> None:
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers(cors_origin)
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html_text: str, status: int = 200, cors_origin: Optional[str] = None) -> None:
        body = html_text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_security_headers(cors_origin)
        self.end_headers()
        self.wfile.write(body)

    def _send_not_found(self, cors_origin: Optional[str] = None) -> None:
        """Uniform 404 response (prevents any path-existence oracle)."""
        self._send_json({"error": "Not found"}, status=404, cors_origin=cors_origin)

    def _read_json_body(self, cors_origin: Optional[str]) -> Tuple[Optional[Dict[str, Any]], bool]:
        """Reads and parses JSON body. Returns (payload, ok)."""
        raw_len = self.headers.get("Content-Length", "0")
        try:
            content_length = int(raw_len)
        except ValueError:
            self._send_json({"error": "Invalid Content-Length header."}, status=400, cors_origin=cors_origin)
            return None, False

        if content_length < 0 or content_length > _MAX_BODY_BYTES:
            self._send_json({"error": "Request body exceeds maximum allowed size."}, status=413, cors_origin=cors_origin)
            return None, False

        if content_length == 0:
            return {}, True

        body = self.rfile.read(content_length)
        try:
            parsed = json.loads(body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            self._send_json({"error": f"Malformed JSON body: {exc}"}, status=400, cors_origin=cors_origin)
            return None, False

        if not isinstance(parsed, dict):
            self._send_json({"error": "JSON request body must be an object."}, status=400, cors_origin=cors_origin)
            return None, False

        return parsed, True

    def do_OPTIONS(self):
        ok, cors_origin = self._check_origin()
        if not ok:
            return
        self.send_response(204)
        self._send_security_headers(cors_origin)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_HEAD(self):
        ok, cors_origin = self._check_origin()
        if not ok:
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self._send_security_headers(cors_origin)
        self.end_headers()

    def do_GET(self):
        ok, cors_origin = self._check_origin()
        if not ok:
            return

        parsed = urllib.parse.urlparse(self.path)
        raw_path = parsed.path

        # Reject any raw traversal tokens early with uniform 404 (zero existence oracle)
        unquoted_path = urllib.parse.unquote(raw_path)
        if ".." in unquoted_path.split("/") or "\x00" in unquoted_path or "\\" in unquoted_path:
            return self._send_not_found(cors_origin)

        path = raw_path

        if path in ("/", "/index.html", "/ui", "/ui/"):
            for root in _public_roots():
                candidate = root / "index.html"
                if candidate.is_file():
                    try:
                        return self._send_html(candidate.read_text(encoding="utf-8"), cors_origin=cors_origin)
                    except Exception:
                        pass
            return self._send_html(_FALLBACK_HTML, cors_origin=cors_origin)

        if path in ("/health", "/api/health", "/api/status"):
            return self._send_json(
                {"status": "healthy", "engine": "aeo-graph-engine", "version": __version__},
                cors_origin=cors_origin,
            )

        if path == "/api/schema":
            return self._send_json(get_agent_json_schema(), cors_origin=cors_origin)

        if path == "/api/mcp/config":
            query = urllib.parse.parse_qs(parsed.query)
            client = query.get("client", ["claude_desktop"])[0]
            return self._send_json(generate_mcp_client_config(client), cors_origin=cors_origin)

        if path == "/api/discover":
            return self._send_json(discover_project_metadata("."), cors_origin=cors_origin)

        if path == "/api/providers":
            gateway = AIGateway()
            return self._send_json(gateway.discover_providers(), cors_origin=cors_origin)

        if path == "/api/export-zip":
            query = urllib.parse.parse_qs(parsed.query)
            niche = query.get("niche", ["developer_tools"])[0]
            site_name = query.get("site_name", ["AEO Graph Engine"])[0]
            domain = query.get("domain", [None])[0]
            cfg_in: Dict[str, Any] = {"site_name": site_name}
            if domain:
                cfg_in["domain"] = domain
            zip_bytes = _build_export_zip_bytes(cfg_in, niche=niche)
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="aeo-bundle.zip"')
            self.send_header("Content-Length", str(len(zip_bytes)))
            self._send_security_headers(cors_origin)
            self.end_headers()
            self.wfile.write(zip_bytes)
            return

        if path == "/api/ai/settings":
            gateway = AIGateway()
            return self._send_json(gateway.get_public_status(), cors_origin=cors_origin)

        if path == "/api/simulate-citation":
            query_params = urllib.parse.parse_qs(parsed.query)
            target = (
                query_params.get("url", [""])[0]
                or query_params.get("target", [""])[0]
                or query_params.get("content", [""])[0]
            )
            q_str = query_params.get("query", [None])[0]
            brand = query_params.get("brand_name", [None])[0]
            dom = query_params.get("domain", [None])[0]
            try:
                res = simulate_ai_citations(target, query=q_str, brand_name=brand, domain=dom)
                return self._send_json(res, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/visualize-schema":
            query_params = urllib.parse.parse_qs(parsed.query)
            fmt = query_params.get("format", ["mermaid"])[0]
            res = visualize_schema_graph(schema_input=None, format=fmt)
            return self._send_json(res, cors_origin=cors_origin)

        if path == "/api/crawl-sitemap":
            query_params = urllib.parse.parse_qs(parsed.query)
            target = (
                query_params.get("url", [""])[0]
                or query_params.get("sitemap_url", [""])[0]
                or query_params.get("domain", [""])[0]
            )
            max_pages = int(query_params.get("max_pages", [10])[0])
            if not target:
                return self._send_json({"error": "Missing 'url' or 'sitemap_url' parameter"}, status=400, cors_origin=cors_origin)
            try:
                res = crawl_sitemap_batch(target, max_pages=max_pages)
                return self._send_json(res, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/claims/demo":
            demo_text = (
                "AEO Graph Engine delivers automated Schema.org linked data graphs with zero external dependencies. "
                "The engine structures SearchGPT and Perplexity citation anchors with RFC-conforming JSON-LD output. "
                "Operators can configure crawler directives across 10 AI bot user agents locally."
            )
            matrix = analyze_claim_evidence_matrix(
                demo_text, base_url="https://aeo.nullai.tech", title="AEO Graph Engine Architecture"
            )
            return self._send_json(matrix.to_dict(), cors_origin=cors_origin)

        # Static file serving with strict Path.is_relative_to containment
        rel_path = unquoted_path.lstrip("/")
        if rel_path:
            for root in _public_roots():
                if not root.exists():
                    continue
                resolved_root = root.resolve()
                try:
                    static_file = (resolved_root / rel_path).resolve()
                except Exception:
                    return self._send_not_found(cors_origin)
                if static_file.is_relative_to(resolved_root) and static_file.is_file():
                    mime_type, _ = mimetypes.guess_type(str(static_file))
                    mime_type = mime_type or "application/octet-stream"
                    try:
                        data = static_file.read_bytes()
                        self.send_response(200)
                        self.send_header("Content-Type", mime_type)
                        self.send_header("Content-Length", str(len(data)))
                        self._send_security_headers(cors_origin)
                        self.end_headers()
                        self.wfile.write(data)
                        return
                    except Exception:
                        break

        return self._send_not_found(cors_origin)

    def do_POST(self):
        ok, cors_origin = self._check_origin()
        if not ok:
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        payload, body_ok = self._read_json_body(cors_origin)
        if not body_ok or payload is None:
            return

        if path == "/api/ai/settings":
            gateway = AIGateway()
            if payload.get("clear_keys"):
                saved = gateway.clear_keys()
            else:
                saved = gateway.save_config(payload)
            return self._send_json({"success": saved, "status": gateway.get_public_status()}, cors_origin=cors_origin)

        if path == "/api/ai/test":
            gateway = AIGateway()
            provider = payload.get("provider", "heuristic")
            endpoint = payload.get("endpoint")
            api_key = payload.get("api_key")
            model = payload.get("model")
            res = gateway.test_connection(provider, endpoint=endpoint, api_key=api_key, model=model)
            return self._send_json(res, cors_origin=cors_origin)

        if path == "/api/ai/simulate":
            gateway = AIGateway()
            brand_name = payload.get("brand_name", "")
            domain = payload.get("domain", "")
            query = payload.get("query")
            provider = payload.get("provider")
            model = payload.get("model")
            schema = payload.get("schema")
            description = payload.get("description")
            api_key = payload.get("api_key")
            endpoint = payload.get("endpoint")
            res = gateway.simulate_answer_engine_perception(
                brand_name,
                domain,
                query=query,
                provider=provider,
                model=model,
                schema=schema,
                description=description,
                api_key=api_key,
                endpoint=endpoint,
            )
            return self._send_json(res, cors_origin=cors_origin)

        if path == "/api/export-zip":
            niche = payload.get("niche", "developer_tools")
            cfg_in = payload.get("config") if isinstance(payload.get("config"), dict) else payload
            zip_bytes = _build_export_zip_bytes(cfg_in, niche=niche)
            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", 'attachment; filename="aeo-bundle.zip"')
            self.send_header("Content-Length", str(len(zip_bytes)))
            self._send_security_headers(cors_origin)
            self.end_headers()
            self.wfile.write(zip_bytes)
            return

        if path == "/api/export-framework":
            fw_name = payload.get("framework", "nextjs_app")
            niche = payload.get("niche", "developer_tools")
            cfg = resolve_config(payload.get("config", {}), niche=niche)
            exporter = FrameworkExporter(cfg)
            bundle = exporter.export(fw_name)
            return self._send_json({"framework": fw_name, "files": bundle}, cors_origin=cors_origin)

        if path == "/api/remediate":
            target_url = str(payload.get("url", "")).strip()
            target_fw = payload.get("framework", "nextjs_app")
            audit_data = payload.get("audit_data")
            if not audit_data and target_url:
                try:
                    scanner = LiveAEOScanner(target_url, max_pages=3)
                    audit_data = scanner.compute_audit_scores()
                except SSRFBlockedError as exc:
                    return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)
            remediator = AEORemediationGenerator(audit_data or {}, target_framework=target_fw)
            return self._send_json(remediator.generate_remediations(), cors_origin=cors_origin)

        if path == "/api/scan":
            target_url = str(payload.get("url", "")).strip()
            max_pages = max(1, min(20, int(payload.get("max_pages", 5))))
            if not target_url:
                return self._send_json({"error": "Missing 'url' parameter"}, status=400, cors_origin=cors_origin)
            try:
                scanner = LiveAEOScanner(target_url, max_pages=max_pages)
                results = scanner.compute_audit_scores()
                return self._send_json(results, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/scan-html":
            raw_html = str(payload.get("html", "")).strip()
            page_url = str(payload.get("url", "https://example.com/")).strip()
            if not raw_html:
                return self._send_json({"error": "Missing 'html' parameter for offline HTML audit."}, status=400, cors_origin=cors_origin)
            meta = extract_metadata_from_html(raw_html)
            schemas = meta.get("existing_jsonld", [])
            report = AEODiagnosticReport(page_url)
            if schemas:
                for sch in schemas:
                    if isinstance(sch, dict):
                        validate_schema_jsonld_dict(sch, report)
            else:
                report.add_error("No <script type='application/ld+json'> Schema.org block found in HTML", 35.0)
            if not meta.get("description"):
                report.add_warn("Missing <meta name='description'> tag", 10.0)
            if not meta.get("canonical_url"):
                report.add_warn("Missing <link rel='canonical'> tag", 10.0)
            if not meta.get("headings"):
                report.add_warn("No semantic heading elements (H1-H6) detected", 10.0)
            plain_words = len(re.sub(r"<[^>]+>", " ", raw_html).split())
            return self._send_json(
                {
                    "mode": "offline_html_audit",
                    "url": page_url,
                    "overall_aeo_score": round(report.score, 1),
                    "status": report.to_dict()["status"],
                    "title": meta.get("site_name") or meta.get("tagline") or "(No title)",
                    "description": meta.get("description") or "",
                    "canonical_url": meta.get("canonical_url") or "",
                    "headings": meta.get("headings", [])[:12],
                    "word_count": plain_words,
                    "schema_count": len(schemas),
                    "schemas": schemas,
                    "diagnostics": report.to_dict(),
                },
                cors_origin=cors_origin,
            )

        if path == "/api/agent/synthesize":
            prompt = str(payload.get("prompt", "")).strip()
            base_niche = payload.get("niche")
            if not prompt:
                return self._send_json({"error": "Missing 'prompt' parameter"}, status=400, cors_origin=cors_origin)
            cfg = synthesize_config_from_prompt(prompt, base_niche=base_niche)
            cfg["synthesis_mode"] = "offline_heuristic"
            use_llm = bool(payload.get("use_llm"))
            if use_llm:
                gateway = AIGateway()
                provider = payload.get("provider") or gateway.config.get("active_provider", "heuristic")
                if provider and provider != "heuristic":
                    llm_prompt = (
                        "Return ONLY valid JSON (no markdown fences) with keys: site_name, domain, tagline, description, niche "
                        f"for this product description: {prompt}"
                    )
                    res = gateway.complete_prompt(llm_prompt, provider=provider, model=payload.get("model"), timeout=25)
                    if res.get("success") and res.get("content"):
                        raw = res["content"].strip()
                        match = re.search(r"\{.*\}", raw, re.DOTALL)
                        if match:
                            try:
                                parsed_llm = json.loads(match.group(0))
                                for k in ("site_name", "domain", "tagline", "description", "niche"):
                                    if isinstance(parsed_llm.get(k), str) and parsed_llm[k].strip():
                                        cfg[k] = parsed_llm[k].strip()
                                cfg["synthesis_mode"] = f"live_llm:{res['provider']}"
                            except Exception:
                                pass
            return self._send_json(cfg, cors_origin=cors_origin)

        if path == "/api/generate":
            niche = payload.get("niche", "developer_tools")
            cfg = resolve_config(payload, niche=niche)
            schema = generate_schema_graph(cfg, niche=niche)
            llms = generate_llms_txt(cfg, niche=niche)
            llms_full = generate_llms_full_txt(cfg, niche=niche)
            ai = generate_ai_txt(cfg, niche=niche)
            robots = generate_robots_txt(cfg, niche=niche)

            val_report = AEODiagnosticReport(cfg.get("base_url", "generated"))
            validate_schema_jsonld_dict(schema, val_report)
            if not str(cfg.get("site_name", "")).strip():
                val_report.add_error("Site name is empty", 15.0)
            if not str(cfg.get("description", "")).strip():
                val_report.add_warn("Description is empty", 10.0)

            return self._send_json(
                {
                    "schema": schema,
                    "llms_txt": llms,
                    "llms_full_txt": llms_full,
                    "ai_txt": ai,
                    "robots_txt": robots,
                    "score": round(val_report.score, 1),
                    "validation": val_report.to_dict(),
                },
                cors_origin=cors_origin,
            )

        if path == "/api/inject":
            raw_html = payload.get("html", "")
            cfg = resolve_config(payload.get("config", {}))
            schema = generate_schema_graph(cfg)
            injected = inject_jsonld_into_html(raw_html, schema)
            return self._send_json({"injected_html": injected}, cors_origin=cors_origin)

        if path == "/api/validate":
            raw_schema = payload.get("schema")
            raw_jsonld = payload.get("jsonld")

            if raw_schema is None and raw_jsonld is None:
                return self._send_json(
                    {"error": "Missing required 'schema' (object) or 'jsonld' (JSON string) field."},
                    status=400,
                    cors_origin=cors_origin,
                )

            schema_obj: Optional[Dict[str, Any]] = None
            if raw_schema is not None:
                if isinstance(raw_schema, dict):
                    schema_obj = raw_schema
                elif isinstance(raw_schema, str):
                    raw_jsonld = raw_schema
                else:
                    return self._send_json(
                        {"error": "'schema' must be a JSON object or JSON-LD string."},
                        status=400,
                        cors_origin=cors_origin,
                    )

            if schema_obj is None and raw_jsonld is not None:
                if not isinstance(raw_jsonld, str) or not raw_jsonld.strip():
                    return self._send_json(
                        {"error": "'jsonld' must be a non-empty JSON string."},
                        status=400,
                        cors_origin=cors_origin,
                    )
                try:
                    parsed_ld = json.loads(raw_jsonld)
                except json.JSONDecodeError as exc:
                    return self._send_json(
                        {"error": f"Invalid JSON-LD syntax: {exc}"},
                        status=400,
                        cors_origin=cors_origin,
                    )
                if not isinstance(parsed_ld, dict):
                    return self._send_json(
                        {"error": "JSON-LD root payload must be a JSON object."},
                        status=400,
                        cors_origin=cors_origin,
                    )
                schema_obj = parsed_ld

            if not schema_obj:
                return self._send_json(
                    {"error": "Empty Schema.org object provided."},
                    status=400,
                    cors_origin=cors_origin,
                )

            report = AEODiagnosticReport("API Validation")
            validate_schema_jsonld_dict(schema_obj, report)
            return self._send_json(report.to_dict(), cors_origin=cors_origin)

        if path == "/api/bot-audit":
            target_url = str(payload.get("url", "")).strip()
            timeout = float(payload.get("timeout", 5.0))
            if not target_url:
                return self._send_json({"error": "Missing 'url' parameter"}, status=400, cors_origin=cors_origin)
            try:
                inspector = BotInspector()
                summary = inspector.inspect_all_bots(target_url, timeout=timeout)
                return self._send_json(summary, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/compare":
            url_a = str(payload.get("url_a", "")).strip()
            url_b = str(payload.get("url_b", "")).strip()
            max_p = max(1, min(10, int(payload.get("max_pages", 5))))
            if not url_a or not url_b:
                return self._send_json({"error": "Missing 'url_a' or 'url_b'"}, status=400, cors_origin=cors_origin)
            try:
                bench = compare_sites(url_a, url_b, max_pages=max_p)
                return self._send_json(bench, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/report":
            scan_data = payload.get("scan_data")
            target_url = str(payload.get("url", "")).strip()
            comp_url = str(payload.get("competitor_url", "")).strip()
            if not scan_data and target_url:
                try:
                    scanner = LiveAEOScanner(target_url, max_pages=3)
                    scan_data = scanner.compute_audit_scores()
                except SSRFBlockedError as exc:
                    return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)
            bench_data = payload.get("benchmark_data")
            if not bench_data and comp_url and target_url:
                try:
                    bench_data = compare_sites(target_url, comp_url, scan_a=scan_data)
                except SSRFBlockedError as exc:
                    return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)
            md_report = generate_markdown_report(scan_data or {}, benchmark_result=bench_data)
            html_report = generate_standalone_html_report(scan_data or {}, benchmark_result=bench_data)
            return self._send_json(
                {
                    "markdown": md_report,
                    "html": html_report,
                    "target_url": target_url or (scan_data or {}).get("target_url") or "https://example.com",
                },
                cors_origin=cors_origin,
            )

        if path == "/api/simulate-citation":
            target = payload.get("url") or payload.get("content") or payload.get("target") or ""
            q_str = payload.get("query")
            brand = payload.get("brand_name")
            dom = payload.get("domain")
            timeout = int(payload.get("timeout", 8))
            try:
                res = simulate_ai_citations(target, query=q_str, brand_name=brand, domain=dom, timeout=timeout)
                return self._send_json(res, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/visualize-schema":
            schema = payload.get("schema")
            fmt = payload.get("format", "both")
            res = visualize_schema_graph(schema_input=schema, format=fmt)
            return self._send_json(res, cors_origin=cors_origin)

        if path == "/api/crawl-sitemap":
            target = str(
                payload.get("sitemap_url") or payload.get("url") or payload.get("domain") or payload.get("target") or ""
            ).strip()
            max_pages = max(1, min(20, int(payload.get("max_pages", 10))))
            timeout = int(payload.get("timeout", 8))
            if not target:
                return self._send_json({"error": "Missing 'sitemap_url' parameter"}, status=400, cors_origin=cors_origin)
            try:
                res = crawl_sitemap_batch(target, max_pages=max_pages, timeout=timeout)
                return self._send_json(res, cors_origin=cors_origin)
            except SSRFBlockedError as exc:
                return self._send_json({"error": str(exc), "blocked": True}, status=403, cors_origin=cors_origin)

        if path == "/api/knowledge-graph":
            content = payload.get("content") or payload.get("text") or payload.get("html") or ""
            schema_data = payload.get("schema")
            base_url = payload.get("base_url", "https://example.com")
            min_conf = float(payload.get("min_confidence", 0.4))
            kg_report = analyze_knowledge_graph(
                content, schema_or_graph=schema_data, base_url=base_url, min_confidence=min_conf
            )
            return self._send_json(kg_report.to_dict(), cors_origin=cors_origin)

        if path in ("/api/claims", "/api/claim-matrix"):
            content = payload.get("content") or payload.get("text") or payload.get("html") or ""
            base_url = payload.get("base_url", "https://example.com")
            title = payload.get("title")
            fmt = payload.get("format", "json")
            matrix = analyze_claim_evidence_matrix(content, base_url=base_url, title=title)
            if fmt == "svg":
                return self._send_json({"svg": matrix.to_svg()}, cors_origin=cors_origin)
            if fmt == "markdown":
                return self._send_json({"markdown": matrix.to_markdown()}, cors_origin=cors_origin)
            return self._send_json(matrix.to_dict(), cors_origin=cors_origin)

        return self._send_not_found(cors_origin)


def start_ui_server(host: str = "127.0.0.1", port: int = 8127) -> ThreadingHTTPServer:
    """Starts the hardened AEO Studio loopback HTTP server."""
    return ThreadingHTTPServer((host, port), AEOStudioHTTPHandler)

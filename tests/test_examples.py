"""
Tests for real-world examples and showcase directories in aeo-graph-engine.
Validates JSON syntax, Schema.org graph structures, llms.txt compliance,
robots.txt AI crawler matrices, HTML embeddings, and documentation completeness.
"""

import json
import re
from pathlib import Path
import pytest

from aeo_graph_engine.validator import (
    validate_aeo_bundle,
    validate_schema_jsonld_dict,
    validate_llms_txt_content,
    validate_ai_txt_content,
    validate_robots_txt_content,
    validate_html_file,
    AEODiagnosticReport,
)

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"


def test_examples_directory_exists():
    """Verify the root examples directory and subdirectories exist."""
    assert EXAMPLES_DIR.exists() and EXAMPLES_DIR.is_dir()
    
    subdirs = [
        "nextjs-app-router",
        "astro-site",
        "vite-react-spa",
        "saas-landing",
        "mcp-clients",
    ]
    for sub in subdirs:
        d = EXAMPLES_DIR / sub
        assert d.exists() and d.is_dir(), f"Expected example directory missing: {sub}"


def test_all_json_files_are_valid():
    """Verify that every single .json file in examples/ parses as valid JSON."""
    json_files = list(EXAMPLES_DIR.glob("**/*.json"))
    assert len(json_files) >= 6, f"Expected at least 6 JSON files, found {len(json_files)}"

    for jf in json_files:
        try:
            with open(jf, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert data is not None, f"JSON file {jf.name} parsed to None"
            assert isinstance(data, (dict, list)), f"JSON file {jf.name} is not a dict or list"
        except Exception as e:
            pytest.fail(f"Failed to parse JSON file {jf}: {e}")


def test_all_markdown_files_have_content():
    """Verify that all markdown files across examples/ exist and have non-empty content."""
    md_files = list(EXAMPLES_DIR.glob("**/*.md"))
    assert len(md_files) >= 6, f"Expected at least 6 markdown files, found {len(md_files)}"

    for mf in md_files:
        content = mf.read_text(encoding="utf-8").strip()
        assert len(content) > 100, f"Markdown file {mf} is too short or empty ({len(content)} chars)"
        assert content.startswith("# "), f"Markdown file {mf} should start with an H1 header"


def test_nextjs_app_router_files():
    """Verify all required Next.js App Router files exist and contain appropriate code."""
    next_dir = EXAMPLES_DIR / "nextjs-app-router"
    
    # 1. layout.tsx
    layout_file = next_dir / "app" / "layout.tsx"
    assert layout_file.exists()
    layout_content = layout_file.read_text(encoding="utf-8")
    assert "application/ld+json" in layout_content
    assert "schemaGraph" in layout_content
    assert "Organization" in layout_content
    assert "WebSite" in layout_content
    assert "SoftwareApplication" in layout_content
    assert "FAQPage" in layout_content
    assert "metadata" in layout_content

    # 2. robots.ts
    robots_file = next_dir / "app" / "robots.ts"
    assert robots_file.exists()
    robots_content = robots_file.read_text(encoding="utf-8")
    assert "MetadataRoute.Robots" in robots_content
    assert "GPTBot" in robots_content
    assert "PerplexityBot" in robots_content
    assert "ClaudeBot" in robots_content
    assert "sitemap" in robots_content.lower()

    # 3. sitemap.ts
    sitemap_file = next_dir / "app" / "sitemap.ts"
    assert sitemap_file.exists()
    sitemap_content = sitemap_file.read_text(encoding="utf-8")
    assert "MetadataRoute.Sitemap" in sitemap_content
    assert "lastModified" in sitemap_content

    # 4. llms.txt route.ts
    llms_route = next_dir / "app" / "llms.txt" / "route.ts"
    assert llms_route.exists()
    llms_route_content = llms_route.read_text(encoding="utf-8")
    assert "export async function GET" in llms_route_content
    assert "text/plain" in llms_route_content
    assert "# CloudPulse AI" in llms_route_content

    # 5. public/ai.txt
    ai_file = next_dir / "public" / "ai.txt"
    assert ai_file.exists()
    ai_report = AEODiagnosticReport(str(ai_file))
    validate_ai_txt_content(ai_file.read_text(encoding="utf-8"), ai_report)
    assert len(ai_report.errors) == 0


def test_astro_site_files():
    """Verify Astro example files and AeoHead component."""
    astro_dir = EXAMPLES_DIR / "astro-site"

    # 1. AeoHead.astro
    head_file = astro_dir / "src" / "components" / "AeoHead.astro"
    assert head_file.exists()
    head_content = head_file.read_text(encoding="utf-8")
    assert "application/ld+json" in head_content
    assert "schemaGraph" in head_content
    assert "canonical" in head_content
    assert "og:title" in head_content

    # 2. public/llms.txt
    llms_file = astro_dir / "public" / "llms.txt"
    assert llms_file.exists()
    llms_report = AEODiagnosticReport(str(llms_file))
    validate_llms_txt_content(llms_file.read_text(encoding="utf-8"), llms_report)
    assert len(llms_report.errors) == 0

    # 3. public/robots.txt
    robots_file = astro_dir / "public" / "robots.txt"
    assert robots_file.exists()
    robots_report = AEODiagnosticReport(str(robots_file))
    validate_robots_txt_content(robots_file.read_text(encoding="utf-8"), robots_report)
    assert len(robots_report.errors) == 0


def test_vite_react_spa_files():
    """Verify Vite + React SPA example files and HTML schema injection."""
    vite_dir = EXAMPLES_DIR / "vite-react-spa"

    # 1. index.html
    html_file = vite_dir / "index.html"
    assert html_file.exists()
    html_report = AEODiagnosticReport(str(html_file))
    validate_html_file(html_file, html_report)
    assert html_report.score >= 90.0
    assert len(html_report.errors) == 0
    assert html_report.artifacts_checked["html_injection"] is True
    assert html_report.artifacts_checked["schema_jsonld"] is True

    # 2. vite.config.ts
    vite_cfg = vite_dir / "vite.config.ts"
    assert vite_cfg.exists()
    vite_cfg_content = vite_cfg.read_text(encoding="utf-8")
    assert "defineConfig" in vite_cfg_content
    assert "aeoPlugin" in vite_cfg_content

    # 3. public/llms.txt
    llms_file = vite_dir / "public" / "llms.txt"
    assert llms_file.exists()
    llms_report = AEODiagnosticReport(str(llms_file))
    validate_llms_txt_content(llms_file.read_text(encoding="utf-8"), llms_report)
    assert len(llms_report.errors) == 0


def test_saas_landing_bundle():
    """Verify full standalone SaaS landing bundle against complete AEO validator."""
    saas_dir = EXAMPLES_DIR / "saas-landing"
    assert saas_dir.exists()

    # 1. Check aeo_config.json
    cfg_file = saas_dir / "aeo_config.json"
    assert cfg_file.exists()
    cfg_data = json.loads(cfg_file.read_text(encoding="utf-8"))
    assert cfg_data["site_name"] == "NexusFlow Cloud"
    assert cfg_data["niche"] == "saas"
    assert len(cfg_data["features"]) >= 3
    assert len(cfg_data["faqs"]) >= 2

    # 2. Validate schema-graph.json directly
    schema_file = saas_dir / "schema-graph.json"
    assert schema_file.exists()
    schema_data = json.loads(schema_file.read_text(encoding="utf-8"))
    schema_report = AEODiagnosticReport(str(schema_file))
    validate_schema_jsonld_dict(schema_data, schema_report)
    assert len(schema_report.errors) == 0
    assert schema_report.artifacts_checked["schema_jsonld"] is True

    # 3. Validate entire directory bundle
    bundle_report = validate_aeo_bundle(saas_dir)
    report_dict = bundle_report.to_dict()
    assert report_dict["score"] >= 90.0
    assert report_dict["status"] in ("EXCELLENT", "GOOD")
    assert report_dict["errors_count"] == 0
    assert report_dict["artifacts_detected"]["schema_jsonld"] is True
    assert report_dict["artifacts_detected"]["llms_txt"] is True
    assert report_dict["artifacts_detected"]["ai_txt"] is True
    assert report_dict["artifacts_detected"]["robots_txt"] is True


def test_mcp_clients_configs():
    """Verify all MCP client configuration presets match standard client structures."""
    mcp_dir = EXAMPLES_DIR / "mcp-clients"
    assert mcp_dir.exists()

    # Claude Desktop
    claude_cfg = json.loads((mcp_dir / "claude_desktop_config.json").read_text(encoding="utf-8"))
    assert "mcpServers" in claude_cfg
    assert "aeo-graph-engine" in claude_cfg["mcpServers"]
    assert claude_cfg["mcpServers"]["aeo-graph-engine"]["command"] == "python3"

    # Cursor
    cursor_cfg = json.loads((mcp_dir / "cursor_mcp.json").read_text(encoding="utf-8"))
    assert "mcpServers" in cursor_cfg
    assert "aeo-graph-engine" in cursor_cfg["mcpServers"]

    # Cline
    cline_cfg = json.loads((mcp_dir / "cline_mcp.json").read_text(encoding="utf-8"))
    assert "mcpServers" in cline_cfg
    assert "aeo-graph-engine" in cline_cfg["mcpServers"]
    assert cline_cfg["mcpServers"]["aeo-graph-engine"]["disabled"] is False

    # Zed
    zed_cfg = json.loads((mcp_dir / "zed_settings.json").read_text(encoding="utf-8"))
    assert "context_servers" in zed_cfg
    assert "aeo-graph-engine" in zed_cfg["context_servers"]
    assert zed_cfg["context_servers"]["aeo-graph-engine"]["command"]["path"] == "python3"

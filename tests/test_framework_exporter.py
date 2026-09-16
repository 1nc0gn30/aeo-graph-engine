"""
Unit tests for framework_exporter.py.
Tests all web framework export formats, file bundles, and auto-remediation generator.
"""

import json
import tempfile
from pathlib import Path
import pytest

from aeo_graph_engine.framework_exporter import (
    FrameworkExporter,
    AEORemediationGenerator,
    export_framework_code,
    generate_remediation_plan,
    get_supported_frameworks,
    normalize_framework_name,
    SUPPORTED_FRAMEWORKS,
)


@pytest.fixture
def sample_config():
    return {
        "domain": "aeo-agent.org",
        "base_url": "https://aeo-agent.org",
        "site_name": "AEO Agent Test",
        "description": "Next-generation answer engine optimization framework.",
        "tagline": "AI Knowledge Graph & AEO Engine",
        "surfaces": [
            {"name": "Docs", "path": "/docs/", "notes": "Developer docs", "indexed": True},
            {"name": "API", "path": "/api/", "notes": "API reference", "indexed": True},
        ],
        "faqs": [
            {"question": "What is AEO?", "answer": "Answer Engine Optimization for LLM discovery."}
        ]
    }


# =============================================================================
# 1. Framework Normalization & Supported List Tests
# =============================================================================

def test_get_supported_frameworks():
    fws = get_supported_frameworks()
    assert isinstance(fws, list)
    assert "nextjs_app" in fws
    assert "astro" in fws
    assert "vite_react" in fws
    assert "sveltekit" in fws
    assert "remix" in fws
    assert "nuxt" in fws
    assert "static" in fws


def test_normalize_framework_name():
    assert normalize_framework_name("NextJS") == "nextjs_app"
    assert normalize_framework_name("next-app") == "nextjs_app"
    assert normalize_framework_name("pages_router") == "nextjs_pages"
    assert normalize_framework_name("Astro") == "astro"
    assert normalize_framework_name("vite") == "vite_react"
    assert normalize_framework_name("react") == "vite_react"
    assert normalize_framework_name("svelte") == "sveltekit"
    assert normalize_framework_name("remix") == "remix"
    assert normalize_framework_name("vue") == "nuxt"
    assert normalize_framework_name("nuxt3") == "nuxt"
    assert normalize_framework_name("html") == "static"
    assert normalize_framework_name("hugo") == "hugo"
    assert normalize_framework_name("jekyll") == "jekyll"
    assert normalize_framework_name("unknown_fw") == "nextjs_app"


# =============================================================================
# 2. Framework Specific Exporter Tests
# =============================================================================

def test_export_nextjs_app(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_nextjs_app()

    assert "app/layout.tsx" in files
    assert "app/robots.ts" in files
    assert "app/sitemap.ts" in files
    assert "app/llms.txt/route.ts" in files
    assert "app/llms-full.txt/route.ts" in files
    assert "app/ai.txt/route.ts" in files

    layout = files["app/layout.tsx"]
    assert "export const metadata: Metadata" in layout
    assert "AEO Agent Test" in layout
    assert "application/ld+json" in layout
    assert "https://aeo-agent.org" in layout

    robots = files["app/robots.ts"]
    assert "GPTBot" in robots
    assert "PerplexityBot" in robots
    assert "ClaudeBot" in robots
    assert "Applebot-Extended" in robots
    assert "Google-Extended" in robots
    assert "sitemap.xml" in robots

    sitemap = files["app/sitemap.ts"]
    assert "export default function sitemap()" in sitemap
    assert "/docs/" in sitemap
    assert "/api/" in sitemap

    llms_route = files["app/llms.txt/route.ts"]
    assert "export const dynamic = \"force-static\";" in llms_route
    assert "text/plain; charset=utf-8" in llms_route


def test_export_nextjs_pages(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_nextjs_pages()

    assert "pages/_document.tsx" in files
    assert "pages/api/llms.txt.ts" in files
    assert "components/AeoHead.tsx" in files

    doc = files["pages/_document.tsx"]
    assert "import Document" in doc
    assert "application/ld+json" in doc
    assert "aeo-schema-graph" in doc

    api = files["pages/api/llms.txt.ts"]
    assert "res.setHeader(\"Content-Type\", \"text/plain; charset=utf-8\")" in api


def test_export_astro(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_astro()

    assert "src/components/AeoHead.astro" in files
    assert "astro.config.mjs" in files
    assert "public/llms.txt" in files
    assert "public/robots.txt" in files
    assert "public/schema-graph.json" in files

    head_astro = files["src/components/AeoHead.astro"]
    assert "set:html={JSON.stringify(schemaGraph)}" in head_astro
    assert "og:title" in head_astro
    assert "twitter:card" in head_astro

    astro_config = files["astro.config.mjs"]
    assert "defineConfig" in astro_config
    assert "@astrojs/sitemap" in astro_config
    assert "https://aeo-agent.org" in astro_config


def test_export_vite_react(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_vite_react()

    assert "index.html" in files
    assert "vite-plugin-aeo.ts" in files
    assert "src/components/AeoMeta.tsx" in files

    index_html = files["index.html"]
    assert "application/ld+json" in index_html
    assert "AEO Agent Test" in index_html
    assert "https://aeo-agent.org" in index_html

    vite_plugin = files["vite-plugin-aeo.ts"]
    assert "export function aeoPlugin(): Plugin" in vite_plugin
    assert "configureServer" in vite_plugin
    assert "generateBundle" in vite_plugin

    meta_tsx = files["src/components/AeoMeta.tsx"]
    assert "export const AeoMeta" in meta_tsx
    assert "aeo-schema-graph" in meta_tsx


def test_export_sveltekit(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_sveltekit()

    assert "src/routes/+layout.svelte" in files
    assert "src/routes/robots.txt/+server.ts" in files
    assert "src/routes/llms.txt/+server.ts" in files
    assert "src/routes/ai.txt/+server.ts" in files

    layout = files["src/routes/+layout.svelte"]
    assert "<svelte:head>" in layout
    assert "application/ld+json" in layout

    robots = files["src/routes/robots.txt/+server.ts"]
    assert "export const GET: RequestHandler" in robots
    assert "GPTBot" in robots


def test_export_remix(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_remix()

    assert "app/root.tsx" in files
    assert "app/routes/robots[.]txt.ts" in files
    assert "app/routes/llms[.]txt.ts" in files

    root = files["app/root.tsx"]
    assert "export const meta: MetaFunction" in root
    assert "application/ld+json" in root


def test_export_nuxt(sample_config):
    exporter = FrameworkExporter(sample_config)
    files = exporter.export_nuxt()

    assert "nuxt.config.ts" in files
    assert "app.vue" in files
    assert "server/routes/llms.txt.ts" in files
    assert "server/routes/robots.txt.ts" in files

    nuxt_conf = files["nuxt.config.ts"]
    assert "defineNuxtConfig" in nuxt_conf
    assert "application/ld+json" in nuxt_conf

    app_vue = files["app.vue"]
    assert "useHead" in app_vue


def test_export_static_hugo_jekyll(sample_config):
    exporter = FrameworkExporter(sample_config)

    static_files = exporter.export_static_html()
    assert "partials/aeo-head.html" in static_files
    assert "llms.txt" in static_files
    assert "schema-graph.json" in static_files

    hugo_files = exporter.export_hugo()
    assert "layouts/partials/aeo-head.html" in hugo_files
    assert "hugo.toml.snippet" in hugo_files

    jekyll_files = exporter.export_jekyll()
    assert "_includes/aeo-head.html" in jekyll_files
    assert "_config.yml.snippet" in jekyll_files


# =============================================================================
# 3. Export All & Bundle Writing Tests
# =============================================================================

def test_export_all_frameworks(sample_config):
    exporter = FrameworkExporter(sample_config)
    all_exports = exporter.export_all()

    for fw in SUPPORTED_FRAMEWORKS:
        assert fw in all_exports
        assert len(all_exports[fw]) > 0


def test_write_framework_bundle(sample_config):
    exporter = FrameworkExporter(sample_config)
    with tempfile.TemporaryDirectory() as tmpdir:
        written = exporter.write_framework_bundle("astro", tmpdir)
        assert "src/components/AeoHead.astro" in written
        assert "astro.config.mjs" in written
        assert "public/llms.txt" in written

        astro_head = Path(written["src/components/AeoHead.astro"])
        assert astro_head.exists()
        assert astro_head.is_file()
        content = astro_head.read_text(encoding="utf-8")
        assert "AEO Agent Test" in content


def test_export_framework_code_convenience(sample_config):
    res = export_framework_code("nextjs_app", sample_config)
    assert "app/layout.tsx" in res
    assert "app/robots.ts" in res


# =============================================================================
# 4. Auto-Remediation Generator Tests
# =============================================================================

def test_remediation_generator_missing_everything():
    mock_scan = {
        "target_url": "https://unoptimized-site.com",
        "origin": "https://unoptimized-site.com",
        "overall_aeo_score": 15.0,
        "root_assets": {
            "llms_txt": {"exists": False, "status": 404},
            "llms_full_txt": {"exists": False, "status": 404},
            "ai_txt": {"exists": False, "status": 404},
            "robots_txt": {"exists": False, "status": 404, "content": ""},
            "sitemap_xml": {"exists": False, "status": 404},
        },
        "pages": [
            {
                "url": "https://unoptimized-site.com",
                "title": "Unoptimized Site",
                "description": "A website lacking AEO elements.",
                "schema_count": 0,
                "schemas": []
            }
        ]
    }

    generator = AEORemediationGenerator(mock_scan, framework="nextjs_app")
    plan = generator.generate_plan()

    assert plan["target_url"] == "https://unoptimized-site.com"
    assert plan["framework"] == "nextjs_app"
    assert plan["overall_score"] == 15.0
    assert plan["total_issues_count"] >= 4
    assert plan["critical_count"] >= 1
    assert plan["high_count"] >= 2

    # Check remediations list
    remediation_ids = [r["id"] for r in plan["remediations"]]
    assert "missing_llms_txt" in remediation_ids
    assert "missing_schema_graph" in remediation_ids
    assert "missing_ai_crawlers_robots" in remediation_ids
    assert "missing_ai_txt" in remediation_ids
    assert "missing_sitemap_xml" in remediation_ids

    # Check files to create
    assert "app/layout.tsx" in plan["all_files_to_create"]
    assert "app/llms.txt/route.ts" in plan["all_files_to_create"]
    assert "app/robots.ts" in plan["all_files_to_create"]

    # Check summary markdown
    assert "# AEO Auto-Remediation Plan" in plan["summary_markdown"]
    assert "| CRITICAL |" in plan["summary_markdown"] or "**CRITICAL**" in plan["summary_markdown"]


def test_remediation_generator_framework_switching():
    mock_scan = {
        "target_url": "https://astro-target.io",
        "root_assets": {
            "llms_txt": {"exists": False},
            "robots_txt": {"exists": True, "content": "User-agent: *\nDisallow: /"},
        },
        "pages": []
    }

    # Test Astro target
    plan_astro = generate_remediation_plan(mock_scan, framework="astro")
    assert plan_astro["framework"] == "astro"
    assert "public/llms.txt" in plan_astro["all_files_to_create"]
    assert "src/components/AeoHead.astro" in plan_astro["all_files_to_create"]

    # Test SvelteKit target
    plan_svelte = generate_remediation_plan(mock_scan, framework="sveltekit")
    assert plan_svelte["framework"] == "sveltekit"
    assert "src/routes/llms.txt/+server.ts" in plan_svelte["all_files_to_create"]
    assert "src/routes/+layout.svelte" in plan_svelte["all_files_to_create"]

    # Test Nuxt target
    plan_nuxt = generate_remediation_plan(mock_scan, framework="nuxt")
    assert plan_nuxt["framework"] == "nuxt"
    assert "server/routes/llms.txt.ts" in plan_nuxt["all_files_to_create"]
    assert "nuxt.config.ts" in plan_nuxt["all_files_to_create"]


def test_remediation_generator_write_files():
    mock_scan = {
        "target_url": "https://test-write.dev",
        "root_assets": {
            "llms_txt": {"exists": False},
            "robots_txt": {"exists": False},
        },
        "pages": []
    }

    generator = AEORemediationGenerator(mock_scan, framework="nextjs_app")
    with tempfile.TemporaryDirectory() as tmpdir:
        created = generator.write_remediations(tmpdir)
        assert "AEO_REMEDIATION_PLAN.md" in created
        assert "app/llms.txt/route.ts" in created

        plan_md = Path(created["AEO_REMEDIATION_PLAN.md"])
        assert plan_md.exists()
        assert "AEO Auto-Remediation Plan" in plan_md.read_text(encoding="utf-8")

        llms_file = Path(created["app/llms.txt/route.ts"])
        assert llms_file.exists()
        assert "force-static" in llms_file.read_text(encoding="utf-8")


def test_remediation_generator_with_mock_scanner_object():
    class MockScanner:
        def compute_audit_scores(self):
            return {
                "target_url": "https://mock-scanner.ai",
                "overall_aeo_score": 40.0,
                "root_assets": {
                    "llms_txt": {"exists": False},
                    "robots_txt": {"exists": False},
                    "ai_txt": {"exists": False},
                    "sitemap_xml": {"exists": False},
                },
                "pages": []
            }

    scanner = MockScanner()
    plan = generate_remediation_plan(scanner, framework="vite_react")
    assert plan["framework"] == "vite_react"
    assert "index.html" in plan["all_files_to_create"]
    assert "public/llms.txt" in plan["all_files_to_create"]

"""
Unit tests for core schema and text artifact generators.
"""

import json
from aeo_graph_engine.core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle
)
from aeo_graph_engine.presets import NICHE_PRESETS, DEFAULT_CONFIG


def test_resolve_config_defaults():
    cfg = resolve_config()
    assert cfg["site_name"] == DEFAULT_CONFIG["site_name"]
    assert cfg["domain"] == DEFAULT_CONFIG["domain"]


def test_resolve_config_niche_override():
    cfg = resolve_config(niche="saas")
    assert cfg["site_name"] == "Nexus SaaS Platform"
    assert "Nexus" in cfg["tagline"] or "Edge" in cfg["tagline"]


def test_resolve_config_user_overrides():
    user_cfg = {"site_name": "Custom Product", "domain": "custom.example.com"}
    cfg = resolve_config(user_cfg, niche="developer_tools")
    assert cfg["site_name"] == "Custom Product"
    assert cfg["base_url"] == "https://custom.example.com"


def test_generate_schema_graph_structure():
    cfg = resolve_config({"site_name": "Test Platform", "domain": "test.com"})
    graph_data = generate_schema_graph(cfg)

    assert "@context" in graph_data
    assert graph_data["@context"] == "https://schema.org"
    assert "@graph" in graph_data

    entities = graph_data["@graph"]
    types = {e["@type"] for e in entities}
    assert "Organization" in types
    assert "WebSite" in types
    assert "SoftwareApplication" in types or "LocalBusiness" in types
    assert "FAQPage" in types
    assert "BreadcrumbList" in types
    assert "ItemList" in types


def test_generate_llms_txt():
    cfg = resolve_config({"site_name": "AI Gateway", "domain": "gateway.ai"})
    content = generate_llms_txt(cfg)

    assert "# AI Gateway" in content
    assert "> " in content
    assert "## Core Capabilities & Architecture" in content
    assert "## Documentation & Key Surfaces" in content
    assert "[Schema.org JSON-LD Graph]" in content


def test_generate_llms_full_txt():
    cfg = resolve_config({"site_name": "AI Gateway", "domain": "gateway.ai"})
    content = generate_llms_full_txt(cfg)

    assert "AI GATEWAY — COMPREHENSIVE SYSTEM KNOWLEDGE BASE" in content
    assert "1. EXECUTIVE OVERVIEW" in content
    assert "2. SYSTEM ARCHITECTURE" in content
    assert "3. INDEXED SURFACES" in content
    assert "4. ANSWER ENGINE ONTOLOGY" in content


def test_generate_ai_txt():
    cfg = resolve_config({"site_name": "AI Gateway", "domain": "gateway.ai"})
    content = generate_ai_txt(cfg)

    assert "User-Agent: *" in content
    assert "Canonical-URL: https://gateway.ai/" in content
    assert "Schema-Org-Graph: https://gateway.ai/schema-graph.json" in content
    assert "LLMs-Txt: https://gateway.ai/llms.txt" in content


def test_generate_robots_txt():
    cfg = resolve_config({"site_name": "AI Gateway", "domain": "gateway.ai"})
    content = generate_robots_txt(cfg)

    assert "User-agent: GPTBot" in content
    assert "User-agent: PerplexityBot" in content
    assert "User-agent: ClaudeBot" in content
    assert "User-agent: Applebot-Extended" in content
    assert "Sitemap: https://gateway.ai/sitemap.xml" in content


def test_write_aeo_bundle(tmp_path):
    cfg = resolve_config()
    res = write_aeo_bundle(tmp_path, cfg)

    assert (tmp_path / "schema-graph.json").exists()
    assert (tmp_path / "llms.txt").exists()
    assert (tmp_path / "llms-full.txt").exists()
    assert (tmp_path / "ai.txt").exists()
    assert (tmp_path / "robots.txt").exists()
    assert len(res) >= 5

"""
Unit tests for Report Generator (aeo_graph_engine.reporter).
"""

import os
from pathlib import Path
import pytest
from aeo_graph_engine.reporter import (
    generate_markdown_report,
    generate_standalone_html_report,
    save_report_to_file,
    _format_score_bar,
    _render_svg_dial,
    _get_grade,
)
from aeo_graph_engine.benchmark import compare_sites


@pytest.fixture
def sample_scan():
    return {
        "target_url": "https://myapp.dev",
        "origin": "https://myapp.dev",
        "overall_aeo_score": 82.5,
        "status": "EXCELLENT",
        "category_scores": {
            "schema_linked_data": {"score": 20.0, "max": 25.0},
            "llms_txt_machine_index": {"score": 25.0, "max": 25.0},
            "ai_crawler_governance": {"score": 16.0, "max": 20.0},
            "semantic_content_grounding": {"score": 11.5, "max": 15.0},
            "technical_seo_foundation": {"score": 10.0, "max": 15.0},
        },
        "root_assets": {
            "robots_txt": {"exists": True, "status": 200},
            "llms_txt": {"exists": True, "status": 200},
            "llms_full_txt": {"exists": True, "status": 200},
            "ai_txt": {"exists": True, "status": 200},
            "sitemap_xml": {"exists": True, "status": 200},
            "schema_graph_json": {"exists": True, "status": 200},
        },
        "pages_audited_count": 2,
        "pages": [
            {
                "url": "https://myapp.dev/",
                "status": 200,
                "title": "MyApp - Intelligent Developer Platform",
                "tagline": "Next-Gen AI Workspace",
                "description": "MyApp provides continuous intelligence and autonomous developer workflows.",
                "headings": ["Overview", "Features", "Pricing"],
                "headings_count": 3,
                "word_count": 920,
                "schemas": [
                    {
                        "@context": "https://schema.org",
                        "@graph": [
                            {"@type": "Organization", "name": "MyApp Inc"},
                            {"@type": "WebSite", "name": "MyApp Portal"},
                            {"@type": "SoftwareApplication", "name": "MyApp Studio"},
                        ],
                    }
                ],
            }
        ],
        "ai_engine_compatibility": {
            "ChatGPT (GPTBot)": {"allowed": True, "has_qa_schema": True},
            "Perplexity AI (PerplexityBot)": {"allowed": True, "has_graph": True},
            "Claude / Anthropic (ClaudeBot)": {"allowed": True, "has_ai_policy": True},
            "Apple Intelligence (Applebot-Extended)": {"allowed": True, "has_app_schema": True},
            "Google AI Overviews (Google-Extended)": {"allowed": True, "has_linked_data": True},
        },
        "action_items": [
            {
                "priority": "HIGH",
                "category": "Schema Graph",
                "issue": "Add FAQPage schema",
                "fix": "Inject FAQPage structured data to increase question-answering coverage.",
            }
        ],
        "backlink_and_distribution_intelligence": {
            "high_authority_citation_hubs": [
                {"platform": "Wikidata", "role": "Entity Anchor", "action": "Link entity"}
            ]
        },
    }


@pytest.fixture
def sample_benchmark(sample_scan):
    scan_b = {
        "target_url": "https://rival.io",
        "origin": "https://rival.io",
        "overall_aeo_score": 52.0,
        "status": "NEEDS_OPTIMIZATION",
        "category_scores": {
            "schema_linked_data": {"score": 5.0, "max": 25.0},
            "llms_txt_machine_index": {"score": 0.0, "max": 25.0},
            "ai_crawler_governance": {"score": 12.0, "max": 20.0},
            "semantic_content_grounding": {"score": 15.0, "max": 15.0},
            "technical_seo_foundation": {"score": 20.0, "max": 15.0},
        },
        "root_assets": {
            "robots_txt": {"exists": True, "status": 200},
            "llms_txt": {"exists": False, "status": 404},
            "llms_full_txt": {"exists": False, "status": 404},
            "ai_txt": {"exists": False, "status": 404},
            "sitemap_xml": {"exists": True, "status": 200},
            "schema_graph_json": {"exists": False, "status": 404},
        },
        "pages_audited_count": 1,
        "pages": [],
        "ai_engine_compatibility": {
            "ChatGPT (GPTBot)": {"allowed": False},
            "Perplexity AI (PerplexityBot)": {"allowed": False},
            "Claude / Anthropic (ClaudeBot)": {"allowed": True},
            "Apple Intelligence (Applebot-Extended)": {"allowed": True},
            "Google AI Overviews (Google-Extended)": {"allowed": True},
        },
    }
    return compare_sites("https://myapp.dev", "https://rival.io", scan_a=sample_scan, scan_b=scan_b)


def test_generate_markdown_report_standalone(sample_scan):
    md = generate_markdown_report(sample_scan)

    assert "# 🌐 AEO & Answer Engine Optimization Audit Report" in md
    assert "https://myapp.dev" in md
    assert "82.5" in md
    assert "## 📊 1. Executive Summary & Category Scorecard" in md
    assert "## 🤖 2. AI Search Engine Bot Compatibility Matrix" in md
    assert "## 📁 3. Root Machine Discovery Assets Status" in md
    assert "## 🧠 4. Schema.org Knowledge Graph & Entity Structure" in md
    assert "```mermaid" in md
    assert "## 🚨 5. Prioritized Action Items & Remediation Roadmap" in md
    assert "## 🛠️ 8. Framework Remediation & Copy-Paste Code" in md
    assert "app/layout.tsx" in md
    assert "public/llms.txt" in md


def test_generate_markdown_report_with_benchmark(sample_scan, sample_benchmark):
    md = generate_markdown_report(sample_scan, benchmark_result=sample_benchmark)

    assert "## ⚔️ 6. Competitive Benchmark & Head-to-Head Analysis" in md
    assert "https://rival.io" in md
    assert "Head-to-Head Category Scores" in md
    assert "Entity & Schema Types Gap Analysis" in md
    assert "Bot Accessibility Delta" in md
    assert "Concrete Strategic Takeaways" in md


def test_generate_standalone_html_report_structure(sample_scan):
    html_doc = generate_standalone_html_report(sample_scan)

    # Validate essential HTML structure
    assert "<!DOCTYPE html>" in html_doc
    assert "<html lang=\"en\" data-theme=\"dark\">" in html_doc
    assert "<head>" in html_doc
    assert "<title>AEO Audit Report" in html_doc
    assert "<style>" in html_doc
    assert "@media print" in html_doc
    assert "<body>" in html_doc
    assert "score-dial" in html_doc
    assert "82.5" in html_doc
    assert "https://myapp.dev" in html_doc
    assert "toggleTheme()" in html_doc
    assert "switchTab(" in html_doc
    assert "copyCode(" in html_doc
    assert "</html>" in html_doc


def test_generate_standalone_html_report_with_benchmark(sample_scan, sample_benchmark):
    html_doc = generate_standalone_html_report(sample_scan, benchmark_result=sample_benchmark)

    assert "Competitor Benchmark Comparison" in html_doc
    assert "https://rival.io" in html_doc
    assert "VS" in html_doc
    assert "Key Strategic Gaps to Beat Competitor" in html_doc


def test_save_report_to_file(tmp_path, sample_scan):
    md = generate_markdown_report(sample_scan)
    report_file = tmp_path / "AEO_AUDIT_REPORT.md"
    saved_path = save_report_to_file(md, report_file)

    assert saved_path.exists()
    assert saved_path.read_text(encoding="utf-8") == md


def test_formatting_helpers():
    bar = _format_score_bar(20.0, 25.0, length=10)
    assert "█" in bar
    assert "80%" in bar

    svg = _render_svg_dial(90.0, size=150, stroke_width=12)
    assert "<svg" in svg
    assert "stroke-dashoffset" in svg
    assert "90.0" in svg

    grade, color, status = _get_grade(95.0)
    assert grade == "A+"
    assert color == "brightgreen"

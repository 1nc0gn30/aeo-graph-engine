"""
Unit tests for command-line interface execution.
"""

import json
from pathlib import Path
from aeo_graph_engine.cli import main, run_internal_tests


def test_cli_internal_tests():
    assert run_internal_tests() == 0


def test_cli_generate_all(tmp_path):
    ret = main([
        "--generate-all",
        "--output-dir", str(tmp_path),
        "--site-name", "CLI Tested App",
        "--domain", "clitest.dev",
        "--niche", "saas"
    ])
    assert ret == 0
    assert (tmp_path / "schema-graph.json").exists()
    assert (tmp_path / "llms.txt").exists()
    assert (tmp_path / "ai.txt").exists()
    assert (tmp_path / "robots.txt").exists()


def test_cli_custom_config(tmp_path):
    cfg_path = tmp_path / "custom.json"
    cfg_path.write_text(json.dumps({
        "site_name": "Custom From JSON",
        "domain": "customjson.io"
    }), encoding="utf-8")

    out_dir = tmp_path / "out"
    ret = main([
        "--config", str(cfg_path),
        "--output-dir", str(out_dir),
        "--generate-all"
    ])
    assert ret == 0
    schema_content = (out_dir / "schema-graph.json").read_text(encoding="utf-8")
    assert "Custom From JSON" in schema_content


def test_cli_validate_command(tmp_path):
    out_dir = tmp_path / "bundle"
    main(["--output-dir", str(out_dir), "--generate-all"])
    ret = main(["--validate", str(out_dir)])
    assert ret == 0


def test_cli_bot_audit_command(monkeypatch, capsys):
    from unittest.mock import MagicMock
    from aeo_graph_engine.bot_inspector import BotInspector

    mock_summary = {
        "target_url": "https://example.com",
        "total_bots": 10,
        "allowed_count": 10,
        "blocked_count": 0,
        "warning_count": 0,
        "waf_detected": False,
        "waf_vendor": None,
        "server_header": "cloudflare",
        "bot_results": [
            {
                "bot_id": "gptbot",
                "bot_name": "GPTBot",
                "operator": "OpenAI",
                "status": "allowed",
                "http_status": 200,
                "latency_ms": 45,
                "details": "Allowed (200 OK)"
            }
        ],
        "recommendations": []
    }

    monkeypatch.setattr(BotInspector, "inspect_all_bots", lambda self, url, timeout=5.0: mock_summary)
    
    # Test JSON output
    ret = main(["bot-audit", "https://example.com", "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert '"allowed_count": 10' in captured

    # Test Text output
    ret = main(["bot-audit", "https://example.com"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "AI SEARCH BOT & WAF INSPECTION RESULTS" in captured


def test_cli_compare_command(monkeypatch, capsys):
    mock_bench = {
        "site_a": {"url": "https://sitea.com", "score": 90},
        "site_b": {"url": "https://siteb.com", "score": 70},
        "score_delta": 20,
        "winners": {"schema": "site_a"},
        "strategic_takeaways": [{"priority": "HIGH", "title": "Lead Advantage", "action": "Maintain schema"}]
    }

    import aeo_graph_engine.cli as cli_module
    monkeypatch.setattr(cli_module, "compare_sites", lambda a, b, max_pages=5: mock_bench)

    ret = main(["compare", "https://sitea.com", "https://siteb.com", "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert '"score_delta": 20' in captured


def test_cli_report_command(monkeypatch, tmp_path):
    mock_scan = {
        "url": "https://mysite.com",
        "overall_aeo_score": 95,
        "category_scores": {"schema": 95, "manifests": 100, "bot_access": 90, "citations": 95, "content": 95},
        "bot_access_matrix": {"GPTBot": {"status": "allowed", "details": "Allowed"}},
        "root_assets": {"llms.txt": {"status": "present", "path": "/llms.txt"}},
        "action_items": [],
        "crawled_pages": [{"url": "https://mysite.com", "http_status": 200, "word_count": 500}],
        "citation_hubs": [],
        "niche_channels": []
    }

    from aeo_graph_engine.scanner import LiveAEOScanner
    monkeypatch.setattr(LiveAEOScanner, "compute_audit_scores", lambda self: mock_scan)

    out_dir = tmp_path / "reports"
    ret = main(["report", "https://mysite.com", "--output-dir", str(out_dir), "--format", "both"])
    assert ret == 0
    assert (out_dir / "AEO_AUDIT_REPORT.md").exists()
    assert (out_dir / "aeo_audit_report.html").exists()


def test_cli_simulate_command(capsys, tmp_path):
    # Test with local text/HTML string
    html_content = """
    <html>
      <head><title>QuantumDB - Fast Vector Database</title></head>
      <body>
        <h1>QuantumDB</h1>
        <p>QuantumDB is an open-source vector database built for high-throughput AI search.</p>
        <p>It supports sub-millisecond similarity search across billions of vectors.</p>
      </body>
    </html>
    """
    f = tmp_path / "page.html"
    f.write_text(html_content, encoding="utf-8")

    # 1. Text format
    ret = main(["simulate", str(f), "--query", "What is QuantumDB?"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "AI SEARCH ENGINE CITATION & EXTRACTABILITY SIMULATION" in out
    assert "QuantumDB" in out
    assert "Extractability Score" in out
    assert "Perplexity AI" in out

    # 2. JSON format
    ret_json = main(["simulate", str(f), "--json"])
    assert ret_json == 0
    out_json = capsys.readouterr().out
    parsed = json.loads(out_json)
    assert parsed["brand_name"] == "QuantumDB"
    assert "extractability_score" in parsed
    assert "extracted_quotes" in parsed
    assert len(parsed["extracted_quotes"]) >= 1


def test_cli_visual_command(capsys, tmp_path):
    schema_data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": "https://solarcloud.io/#org",
                "name": "SolarCloud Inc",
                "url": "https://solarcloud.io"
            },
            {
                "@type": "WebSite",
                "@id": "https://solarcloud.io/#site",
                "name": "SolarCloud",
                "publisher": {"@id": "https://solarcloud.io/#org"}
            },
            {
                "@type": "SoftwareApplication",
                "@id": "https://solarcloud.io/#app",
                "name": "Solar Engine",
                "author": {"@id": "https://solarcloud.io/#org"}
            }
        ]
    }
    schema_file = tmp_path / "schema-graph.json"
    schema_file.write_text(json.dumps(schema_data), encoding="utf-8")

    # 1. Format: mermaid
    ret_mermaid = main(["visual", str(schema_file), "--format", "mermaid"])
    assert ret_mermaid == 0
    out_mermaid = capsys.readouterr().out
    assert "graph TD" in out_mermaid
    assert "SolarCloud Inc" in out_mermaid

    # 2. Format: ascii
    ret_ascii = main(["visual", str(schema_file), "--format", "ascii"])
    assert ret_ascii == 0
    out_ascii = capsys.readouterr().out
    assert "Schema.org Knowledge Graph" in out_ascii
    assert "SolarCloud Inc" in out_ascii

    # 3. Format: both with alias `visualize`
    ret_both = main(["visualize", str(schema_file), "--format", "both"])
    assert ret_both == 0
    out_both = capsys.readouterr().out
    assert "SCHEMA.ORG ENTITY KNOWLEDGE GRAPH" in out_both
    assert "graph TD" in out_both
    assert "Schema.org Knowledge Graph" in out_both


def test_cli_crawl_command(capsys, tmp_path, monkeypatch):
    mock_crawl_result = {
        "sitemap_target": "https://acme.org/sitemap.xml",
        "sitemaps_discovered": ["https://acme.org/sitemap.xml"],
        "total_urls_in_sitemap": 2,
        "pages_audited_count": 2,
        "overall_sitemap_aeo_score": 94.0,
        "status": "EXCELLENT",
        "coverage_metrics": {
            "schema_coverage_pct": 100,
            "faq_coverage_pct": 50,
            "h1_coverage_pct": 100,
            "canonical_coverage_pct": 100
        },
        "pages": [
            {
                "url": "https://acme.org/",
                "status": 200,
                "title": "Acme Home",
                "h1": "Welcome to Acme",
                "word_count": 420,
                "schema_count": 3,
                "schema_types": ["Organization", "WebSite", "SoftwareApplication"],
                "aeo_score": 98.0,
                "issues": []
            },
            {
                "url": "https://acme.org/docs",
                "status": 200,
                "title": "Acme Docs",
                "h1": "Documentation",
                "word_count": 650,
                "schema_count": 1,
                "schema_types": ["TechArticle"],
                "aeo_score": 90.0,
                "issues": ["Missing FAQPage schema"]
            }
        ],
        "action_items": [
            {
                "priority": "MEDIUM",
                "category": "Schema",
                "issue": "Add FAQPage schema to https://acme.org/docs",
                "fix": "Embed FAQPage schema to boost Answer Engine extractability."
            }
        ]
    }

    import aeo_graph_engine.cli as cli_module
    monkeypatch.setattr(cli_module, "crawl_sitemap_batch", lambda target, max_pages=10, timeout=8: mock_crawl_result)

    # 1. Text format
    ret_text = main(["crawl", "https://acme.org/sitemap.xml", "--max-pages", "5"])
    assert ret_text == 0
    out_text = capsys.readouterr().out
    assert "SITEMAP & MULTI-PAGE AEO AUDIT REPORT" in out_text
    assert "https://acme.org/sitemap.xml" in out_text
    assert "94.0 / 100" in out_text
    assert "https://acme.org/" in out_text
    assert "https://acme.org/docs" in out_text

    # 2. JSON format
    ret_json = main(["crawl", "https://acme.org/sitemap.xml", "--json"])
    assert ret_json == 0
    out_json = capsys.readouterr().out
    parsed = json.loads(out_json)
    assert parsed["overall_sitemap_aeo_score"] == 94.0
    assert len(parsed["pages"]) == 2
    assert parsed["coverage_metrics"]["schema_coverage_pct"] == 100


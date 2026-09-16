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


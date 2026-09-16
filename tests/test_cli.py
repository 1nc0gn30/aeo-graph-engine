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

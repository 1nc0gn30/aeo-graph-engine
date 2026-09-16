"""
Unit tests for AEO CI/CD Quality Gate, GitHub Actions formatting, and automated enforcement.
"""

import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from aeo_graph_engine.ci_gate import (
    run_ci_check,
    format_github_annotation,
    write_github_step_summary,
    main as ci_main,
)
from aeo_graph_engine.core import write_aeo_bundle, resolve_config
from aeo_graph_engine.cli import main as cli_main


def _create_valid_bundle(dest_dir: Path) -> Path:
    """Helper to generate a complete valid AEO bundle."""
    cfg = resolve_config({"site_name": "Gate Test App", "domain": "gatetest.io"}, niche="developer_tools")
    write_aeo_bundle(dest_dir, cfg, niche="developer_tools")
    return dest_dir


def test_format_github_annotation():
    ann_err = format_github_annotation("error", "Missing entity", title="Schema Error", file="public/schema.json", line=10)
    assert "::error file=public/schema.json,line=10,title=Schema Error::Missing entity" in ann_err

    ann_warn = format_github_annotation("warning", "No FAQPage found", title="AEO Warning")
    assert "::warning title=AEO Warning::No FAQPage found" in ann_warn

    ann_notice = format_github_annotation("notice", "Audit complete", title="Success")
    assert "::notice title=Success::Audit complete" in ann_notice


def test_write_github_step_summary(tmp_path, monkeypatch):
    summary_file = tmp_path / "step_summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary_file))

    report = {
        "target": "dist",
        "score": 92.5,
        "passed": ["Schema valid", "llms.txt valid"],
        "warnings": ["Consider adding FAQs"],
        "errors": [],
        "artifacts_detected": {
            "schema_jsonld": True,
            "llms_txt": True,
            "ai_txt": True,
            "robots_txt": True,
        }
    }
    write_github_step_summary(report, passed=True, min_score=80, reasons=[])

    assert summary_file.exists()
    content = summary_file.read_text(encoding="utf-8")
    assert "AEO Quality Gate Summary" in content
    assert "92.5/100" in content
    assert "✅ PASSED" in content


def test_ci_gate_pass_valid_bundle(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=80,
        fail_on_missing_llms=True,
        output_format="text"
    )
    assert passed is True
    assert report["passed_gate"] is True
    assert report["score"] >= 80
    assert report["status"] == "PASSED"
    assert report["artifacts_detected"]["llms_txt"] is True
    assert "PASSED ✅" in formatted


def test_ci_gate_fail_score_below_threshold(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    # Set impossible min_score of 101 to trigger failure
    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=101,
        fail_on_missing_llms=True,
        output_format="text"
    )
    assert passed is False
    assert report["passed_gate"] is False
    assert any("below required minimum threshold" in r for r in report["failure_reasons"])
    assert "FAILED ❌" in formatted


def test_ci_gate_fail_missing_llms_txt(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    # Delete llms.txt
    (bundle_dir / "llms.txt").unlink()

    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=50,
        fail_on_missing_llms=True,
        output_format="text"
    )
    assert passed is False
    assert report["artifacts_detected"]["llms_txt"] is False
    assert any("llms.txt machine knowledge manifest is missing" in r for r in report["failure_reasons"])


def test_ci_gate_pass_missing_llms_when_fail_on_missing_disabled(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    (bundle_dir / "llms.txt").unlink()

    # When fail_on_missing_llms is False and min_score is low enough, check passes
    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=60,
        fail_on_missing_llms=False,
        output_format="text"
    )
    assert passed is True
    assert report["passed_gate"] is True


def test_ci_gate_github_format_annotations(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=80,
        fail_on_missing_llms=True,
        output_format="github"
    )
    assert passed is True
    assert "::notice title=AEO CI Gate PASSED::" in formatted


def test_ci_gate_github_format_annotations_on_failure(tmp_path):
    bundle_dir = tmp_path / "empty_dir"
    bundle_dir.mkdir()

    passed, report, formatted = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=80,
        fail_on_missing_llms=True,
        output_format="github"
    )
    assert passed is False
    assert "::error title=" in formatted


def test_ci_gate_json_output_format(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    passed, report, formatted_json = run_ci_check(
        target_url_or_path=str(bundle_dir),
        min_score=80,
        output_format="json"
    )
    data = json.loads(formatted_json)
    assert data["passed_gate"] is True
    assert "score" in data
    assert "artifacts_detected" in data
    assert data["artifacts_detected"]["schema_jsonld"] is True


def test_ci_gate_nonexistent_path(tmp_path):
    bad_path = tmp_path / "does_not_exist"
    passed, report, formatted = run_ci_check(str(bad_path), min_score=80)
    assert passed is False
    assert report["score"] == 0.0
    assert any("does not exist" in err for err in report["errors"])


def test_ci_gate_live_url_mocked():
    mock_scan_data = {
        "target_url": "https://example.com",
        "overall_aeo_score": 91.0,
        "status": "EXCELLENT",
        "root_assets": {
            "schema_org": {"exists": True, "status": "200 OK"},
            "llms_txt": {"exists": True, "status": "200 OK"},
            "llms_full_txt": {"exists": False, "status": "404 Not Found"},
            "ai_txt": {"exists": True, "status": "200 OK"},
            "robots_txt": {"exists": True, "status": "200 OK"},
        },
        "action_items": []
    }

    with patch("aeo_graph_engine.ci_gate.LiveAEOScanner") as mock_scanner_cls:
        mock_instance = MagicMock()
        mock_instance.compute_audit_scores.return_value = mock_scan_data
        mock_scanner_cls.return_value = mock_instance

        passed, report, formatted = run_ci_check("https://example.com", min_score=80)
        assert passed is True
        assert report["score"] == 91.0
        assert report["artifacts_detected"]["llms_txt"] is True
        assert report["artifacts_detected"]["schema_jsonld"] is True


def test_ci_gate_cli_module_runner(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    
    # Success exit code 0
    ret_pass = ci_main([str(bundle_dir), "--min-score", "80"])
    assert ret_pass == 0

    # Failure exit code 1
    ret_fail = ci_main([str(bundle_dir), "--min-score", "101"])
    assert ret_fail == 1


def test_cli_check_subcommand(tmp_path):
    bundle_dir = _create_valid_bundle(tmp_path / "bundle")
    
    # Run via aeo check <dir>
    ret = cli_main(["check", str(bundle_dir), "--min-score", "80", "--format", "text"])
    assert ret == 0

    # Run via aeo check <dir> with high min score
    ret_high = cli_main(["check", str(bundle_dir), "--min-score", "101"])
    assert ret_high == 1

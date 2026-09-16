"""
Unit tests for AEO validator and readiness scoring.
"""

from pathlib import Path
from aeo_graph_engine.validator import validate_aeo_bundle
from aeo_graph_engine.core import write_aeo_bundle, resolve_config


def test_validate_complete_bundle(tmp_path):
    cfg = resolve_config({"site_name": "Val App", "domain": "val.ai"})
    write_aeo_bundle(tmp_path, cfg)

    report = validate_aeo_bundle(tmp_path)
    res = report.to_dict()

    assert res["score"] >= 90.0
    assert res["status"] in ("EXCELLENT", "GOOD")
    assert res["errors_count"] == 0
    assert len(res["passed"]) > 5


def test_validate_single_schema_file(tmp_path):
    schema_file = tmp_path / "schema.json"
    schema_file.write_text("""{
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": "https://test.com/#org", "name": "Test Org"},
            {"@type": "WebSite", "@id": "https://test.com/#site", "name": "Test Site"}
        ]
    }""", encoding="utf-8")

    report = validate_aeo_bundle(schema_file)
    assert report.score >= 80.0
    assert report.artifacts_checked["schema_jsonld"] is True


def test_validate_missing_context(tmp_path):
    bad_file = tmp_path / "bad.json"
    bad_file.write_text('{"foo": "bar"}', encoding="utf-8")

    report = validate_aeo_bundle(bad_file)
    assert report.score < 80.0
    assert len(report.errors) > 0


def test_validate_nonexistent_path():
    report = validate_aeo_bundle("/non/existent/path/for/sure")
    assert report.score == 0.0
    assert len(report.errors) > 0

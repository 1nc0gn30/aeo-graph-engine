"""
Tests for cryptographic integrity and manifest generation in AEO Graph Engine.
"""

import json
from pathlib import Path
from aeo_graph_engine.crypto import (
    canonicalize_jsonld,
    compute_sha256,
    compute_manifest_hashes,
    generate_cryptographic_manifest,
    verify_cryptographic_manifest,
)


def test_canonicalize_jsonld():
    payload_a = {"name": "Test", "version": "1.0", "items": [3, 2, 1]}
    payload_b = {"version": "1.0", "name": "Test", "items": [3, 2, 1]}
    assert canonicalize_jsonld(payload_a) == canonicalize_jsonld(payload_b)


def test_compute_sha256():
    data = "exact-equilibrium"
    digest = compute_sha256(data)
    assert len(digest) == 64
    assert digest == compute_sha256(data.encode("utf-8"))


def test_manifest_generation_and_verification(tmp_path: Path):
    schema_file = tmp_path / "schema.jsonld"
    schema_file.write_text('{"@context": "https://schema.org"}', encoding="utf-8")
    llms_file = tmp_path / "llms.txt"
    llms_file.write_text("# LLMs documentation", encoding="utf-8")

    manifest = generate_cryptographic_manifest(tmp_path, root_entity="https://example.com/#org")
    assert manifest["version"] == "1.0.0"
    assert manifest["artifact_count"] == 2
    assert "schema.jsonld" in manifest["artifacts"]
    assert "llms.txt" in manifest["artifacts"]
    assert len(manifest["composite_root_sha256"]) == 64

    is_valid, discrepancies = verify_cryptographic_manifest(tmp_path, manifest)
    assert is_valid is True
    assert len(discrepancies) == 0

    # Modify an artifact and verify discrepancy detection
    llms_file.write_text("# Altered documentation", encoding="utf-8")
    is_valid_modified, discrepancies_mod = verify_cryptographic_manifest(tmp_path, manifest)
    assert is_valid_modified is False
    assert any("Checksum mismatch for llms.txt" in d for d in discrepancies_mod)

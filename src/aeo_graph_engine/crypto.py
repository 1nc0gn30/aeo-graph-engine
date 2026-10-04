"""
Cryptographic integrity, canonical hashing, and provenance verification for AEO Graph Engine.
Ensures exact equilibrium and deterministic verification of Knowledge Graph manifests,
llms.txt bundles, Schema.org declarations, and citation matrices.

Zero external dependencies (pure Python standard library: hashlib, json).
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple


def canonicalize_jsonld(data: Union[Dict[str, Any], List[Any]]) -> str:
    """
    Produces deterministic, canonical JSON representation (RFC 8785 inspired)
    with sorted keys and compact UTF-8 encoding.
    """
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def compute_sha256(content: Union[str, bytes]) -> str:
    """Computes SHA-256 hex digest of string or binary payload."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_manifest_hashes(bundle_dir: Union[str, Path]) -> Dict[str, str]:
    """
    Traverses an AEO bundle directory and returns SHA-256 hashes of standard AEO artifacts.
    Standard artifacts:
      - schema.jsonld / schema.json
      - llms.txt
      - llms-full.txt
      - ai.txt
      - robots.txt
      - claim_evidence_matrix.json
      - ai-config.json
    """
    path = Path(bundle_dir).resolve()
    if not path.is_dir():
        raise NotADirectoryError(f"Target bundle path is not a directory: {path}")

    target_files = [
        "schema.jsonld",
        "schema.json",
        "llms.txt",
        "llms-full.txt",
        "ai.txt",
        "robots.txt",
        "claim_evidence_matrix.json",
        "ai-config.json",
    ]

    hashes: Dict[str, str] = {}
    for filename in target_files:
        f = path / filename
        if f.is_file():
            hashes[filename] = compute_sha256(f.read_bytes())
    return hashes


def generate_cryptographic_manifest(
    bundle_dir: Union[str, Path],
    root_entity: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates a cryptographic equilibrium manifest proving the exact hash state
    and canonical identity of the AEO Knowledge Graph bundle.
    """
    path = Path(bundle_dir).resolve()
    artifact_hashes = compute_manifest_hashes(path)
    
    # Deterministic composite hash of all present artifact hashes
    composite_input = "".join(f"{k}:{v};" for k, v in sorted(artifact_hashes.items()))
    composite_root = compute_sha256(composite_input) if artifact_hashes else ""

    manifest = {
        "version": "1.0.0",
        "standard": "AEO-Cryptographic-Equilibrium-v1",
        "root_entity": root_entity or "urn:aeo:graph:root",
        "composite_root_sha256": composite_root,
        "artifact_count": len(artifact_hashes),
        "artifacts": artifact_hashes,
    }
    return manifest


def verify_cryptographic_manifest(
    bundle_dir: Union[str, Path],
    manifest: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Verifies that the target directory conforms exactly to the cryptographic manifest.
    Returns (is_valid, discrepancies).
    """
    path = Path(bundle_dir).resolve()
    discrepancies: List[str] = []
    current_hashes = compute_manifest_hashes(path)

    expected_artifacts = manifest.get("artifacts", {})
    
    # Check for missing or altered expected artifacts
    for filename, expected_hash in expected_artifacts.items():
        if filename not in current_hashes:
            discrepancies.append(f"Missing artifact: {filename}")
        elif current_hashes[filename] != expected_hash:
            discrepancies.append(
                f"Checksum mismatch for {filename}: expected {expected_hash}, got {current_hashes[filename]}"
            )

    # Check for unexpected extra standard artifacts
    for filename in current_hashes:
        if filename not in expected_artifacts:
            discrepancies.append(f"Untracked standard artifact present: {filename}")

    # Check composite root
    current_composite = generate_cryptographic_manifest(path, manifest.get("root_entity"))["composite_root_sha256"]
    if manifest.get("composite_root_sha256") and current_composite != manifest.get("composite_root_sha256"):
        discrepancies.append(
            f"Composite root mismatch: expected {manifest.get('composite_root_sha256')}, computed {current_composite}"
        )

    return len(discrepancies) == 0, discrepancies

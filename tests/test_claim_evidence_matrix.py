"""
Unit and integration tests for Atomic Claim-Evidence Matrix and Scroll-to-Text Citation Fragments.
Zero external runtime dependencies (100% Python Standard Library).
"""

from __future__ import annotations

import io
import json
import os
from pathlib import Path

import pytest

from aeo_graph_engine.claim_evidence_matrix import (
    AtomicClaim,
    ClaimCategory,
    ClaimEvidenceMatrix,
    analyze_claim_evidence_matrix,
)
from aeo_graph_engine.cli import main as cli_main
from aeo_graph_engine.mcp_server import MCPServer
from aeo_graph_engine.ui_server import AEOStudioHTTPHandler


SAMPLE_TECH_DOC = """
# QuantumGraph Database Engine

QuantumGraph delivers 5.4x higher query throughput with zero external dependencies.
The engine conforms strictly to the W3C RDF and Schema.org standards.
Developers might possibly consider using it over LegacyDB for distributed clusters.
Every query executes in less than 2.5ms across 10,000 nodes.
Our core clustering algorithm is 30% faster than standard Raft consensus.
"""

SAMPLE_HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
  <title>Apex Vector Cloud | High Performance AI Search</title>
</head>
<body>
  <script>const ignoreMe = true;</script>
  <h1>Apex Vector Cloud</h1>
  <p>Apex Vector Cloud answers embedding queries in under 1.2ms with 99.99% availability.</p>
  <p>The platform supports JSON-LD Schema.org and Model Context Protocol stdio pipelines.</p>
  <p>Some engineers think that maybe it could scale better than traditional elastic search.</p>
</body>
</html>"""


def test_claim_evidence_matrix_basic_extraction():
    """Verify claim extraction, categorization, and scoring from technical doc."""
    matrix = analyze_claim_evidence_matrix(SAMPLE_TECH_DOC, base_url="https://quantumgraph.io", title="QuantumGraph Whitepaper")

    assert isinstance(matrix, ClaimEvidenceMatrix)
    assert matrix.url_or_title == "QuantumGraph Whitepaper"
    assert matrix.total_claims >= 4
    assert matrix.mean_quotability_score > 50.0
    assert matrix.quotability_grade in ("A+", "A", "B", "C")
    assert matrix.quantitative_density > 0.3
    assert matrix.high_quotability_count >= 2

    # Check categories
    cats = matrix.category_counts
    assert cats[ClaimCategory.QUANTITATIVE.value] >= 2
    assert cats[ClaimCategory.ARCHITECTURAL.value] >= 1

    # Check atomic claim details
    claims = matrix.claims
    first_claim = claims[0]
    assert isinstance(first_claim, AtomicClaim)
    assert len(first_claim.quote_hash) == 8
    assert first_claim.text_fragment.startswith("#:~:text=")
    assert len(first_claim.metrics) > 0


def test_html_stripping_and_title_extraction():
    """Verify HTML cleanup, script removal, and title extraction."""
    matrix = analyze_claim_evidence_matrix(SAMPLE_HTML_PAGE, base_url="https://apexvector.ai")

    assert matrix.url_or_title == "Apex Vector Cloud | High Performance AI Search"
    # Ensure script content was not extracted as a claim
    claim_texts = [c.text for c in matrix.claims]
    assert not any("ignoreMe" in t for t in claim_texts)

    # Check quantitative claim with metrics
    metric_claims = [c for c in matrix.claims if c.category == ClaimCategory.QUANTITATIVE.value]
    assert len(metric_claims) >= 1
    assert any("1.2ms" in c.text or "99.99%" in c.text for c in metric_claims)


def test_hedging_penalty_and_quotability_score():
    """Verify that hedging words trigger penalty and actionable recommendations."""
    hedged_doc = "We think that maybe our server might execute requests faster."
    matrix = analyze_claim_evidence_matrix(hedged_doc, base_url="https://test.com")

    assert matrix.total_claims == 1
    claim = matrix.claims[0]
    assert len(claim.hedging_words) > 0
    # Base 50 - 20 (hedging) - 10 (short) = 20
    assert claim.quotability_score <= 40.0
    assert "hedging" in claim.recommendation.lower()


def test_schema_org_linked_data_generation():
    """Verify Schema.org ClaimReview / Statement linked data structure."""
    matrix = analyze_claim_evidence_matrix(SAMPLE_TECH_DOC, base_url="https://quantumgraph.io")
    schema = matrix.schema_org_claim_review

    assert schema["@context"] == "https://schema.org"
    assert schema["@type"] == "WebPage"
    assert "hasPart" in schema
    assert len(schema["hasPart"]) >= 4

    item = schema["hasPart"][0]
    assert item["@type"] == "Statement"
    assert item["@id"].startswith("https://quantumgraph.io/#quote-")
    assert "text" in item
    assert "url" in item


def test_markdown_and_svg_export():
    """Verify Markdown and SVG rendering methods."""
    matrix = analyze_claim_evidence_matrix(SAMPLE_TECH_DOC, base_url="https://quantumgraph.io", title="QuantumGraph Whitepaper")

    # 1. Markdown
    md = matrix.to_markdown()
    assert "# 🎯 Atomic Claim-Evidence & Citation Matrix" in md
    assert "QuantumGraph Whitepaper" in md
    assert "| Category | Count |" in md

    # 2. SVG
    svg = matrix.to_svg()
    assert "<svg" in svg
    assert "</svg>" in svg
    assert "Atomic Claim-Evidence" in svg
    assert "QUOTABILITY SCORE" in svg


def test_cli_claims_subcommand(tmp_path, capsys):
    """Verify CLI `aeo claims` execution with various output formats."""
    doc_path = tmp_path / "sample_doc.md"
    doc_path.write_text(SAMPLE_TECH_DOC, encoding="utf-8")

    out_json = tmp_path / "claims.json"
    out_svg = tmp_path / "claims.svg"

    # 1. Default summary output
    ret1 = cli_main(["claims", str(doc_path)])
    assert ret1 == 0
    captured1 = capsys.readouterr()
    assert "ATOMIC CLAIM-EVIDENCE & CITATION MATRIX" in captured1.out

    # 2. JSON output to file
    ret2 = cli_main(["claims", str(doc_path), "--format", "json", "-o", str(out_json)])
    assert ret2 == 0
    assert out_json.exists()
    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert "total_claims" in data
    assert data["total_claims"] >= 4

    # 3. SVG output to file
    ret3 = cli_main(["claims", str(doc_path), "--format", "svg", "-o", str(out_svg)])
    assert ret3 == 0
    assert out_svg.exists()
    assert "<svg" in out_svg.read_text(encoding="utf-8")


def test_mcp_claims_tools():
    """Verify MCP tools `aeo_analyze_claims` and `aeo_generate_claim_matrix`."""
    from aeo_graph_engine.mcp_server import TOOLS_DEFINITIONS
    server = MCPServer()
    server.is_initialized = True
    defs = {t["name"]: t for t in TOOLS_DEFINITIONS}
    assert "aeo_analyze_claims" in defs
    assert "aeo_generate_claim_matrix" in defs

    # 1. Analyze claims
    req1 = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "aeo_analyze_claims",
            "arguments": {
                "content": SAMPLE_TECH_DOC,
                "base_url": "https://test.dev"
            }
        }
    }
    resp1 = server.process_jsonrpc_request(req1)
    assert resp1 is not None
    assert resp1["id"] == 101
    res1 = resp1["result"]
    assert res1["isError"] is False
    assert len(res1["content"]) == 2
    parsed_json = json.loads(res1["content"][1]["text"])
    assert parsed_json["total_claims"] >= 4

    # 2. Generate claim matrix in markdown format
    req2 = {
        "jsonrpc": "2.0",
        "id": 102,
        "method": "tools/call",
        "params": {
            "name": "aeo_generate_claim_matrix",
            "arguments": {
                "content": SAMPLE_TECH_DOC,
                "format": "markdown"
            }
        }
    }
    resp2 = server.process_jsonrpc_request(req2)
    assert resp2 is not None
    res2 = resp2["result"]
    assert res2["isError"] is False
    assert "🎯 Atomic Claim-Evidence & Citation Matrix" in res2["content"][0]["text"]

    # 3. Generate claim matrix in SVG format
    req3 = {
        "jsonrpc": "2.0",
        "id": 103,
        "method": "tools/call",
        "params": {
            "name": "aeo_generate_claim_matrix",
            "arguments": {
                "content": SAMPLE_TECH_DOC,
                "format": "svg"
            }
        }
    }
    resp3 = server.process_jsonrpc_request(req3)
    assert resp3 is not None
    res3 = resp3["result"]
    assert res3["isError"] is False
    assert "<svg" in res3["content"][0]["text"]


def test_ui_server_claims_endpoints():
    """Verify REST endpoints for claims extraction and demo."""
    from unittest.mock import MagicMock

    handler = AEOStudioHTTPHandler.__new__(AEOStudioHTTPHandler)
    handler.headers = {"Content-Length": "0"}
    handler.send_response = MagicMock()
    handler.send_header = MagicMock()
    handler.end_headers = MagicMock()

    # 1. GET /api/claims/demo
    handler.path = "/api/claims/demo"
    handler.wfile = io.BytesIO()
    handler.do_GET()
    demo_resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert "total_claims" in demo_resp
    assert demo_resp["total_claims"] >= 2

    # 2. POST /api/claims
    post_body = json.dumps({
        "content": SAMPLE_TECH_DOC,
        "base_url": "https://quantumgraph.io"
    }).encode("utf-8")
    handler.headers = {"Content-Length": str(len(post_body))}
    handler.rfile = io.BytesIO(post_body)
    handler.path = "/api/claims"
    handler.wfile = io.BytesIO()

    handler.do_POST()
    post_resp = json.loads(handler.wfile.getvalue().decode("utf-8"))
    assert post_resp["total_claims"] >= 4
    assert post_resp["quotability_grade"] in ("A+", "A", "B", "C")

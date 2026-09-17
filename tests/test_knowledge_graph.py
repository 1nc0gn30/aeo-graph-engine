"""Tests for Semantic Triplet & Knowledge Graph Entity Resolver Engine.

Validates:
1. Deterministic linguistic triplet extraction heuristics.
2. Topological PageRank centrality and entity salience computation.
3. Schema.org alignment, entity coverage scoring, and orphan concept detection.
4. RDF N-Triples and Turtle knowledge graph serialization.
5. High-level analysis facade, MCP tool integration, CLI subcommand, and UI endpoint.

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict

import pytest

from aeo_graph_engine.knowledge_graph import (
    EntityNode,
    KnowledgeGraphReport,
    SemanticTriplet,
    analyze_knowledge_graph,
    audit_knowledge_graph_schema_alignment,
    build_entity_graph,
    compute_pagerank,
    export_rdf_ntriples,
    export_turtle,
    extract_semantic_triplets,
)
from aeo_graph_engine.mcp_server import MCPServer
from aeo_graph_engine.ui_server import start_ui_server
from aeo_graph_engine.cli import build_parser, main as cli_main


SAMPLE_TEXT = """
NullAI is a cutting-edge autonomous AI developer tools studio.
NullAI was founded by Alice Vance in San Francisco.
NullAI is maintained by 757tech Team.
NullAI features automated answer engine optimization and schema synthesis.
NullAI supports Python and TypeScript.
NullAI integrates with Next.js, Astro, and GitHub Actions.
NullAI depends on Python 3.9.
NullAI is built on Schema.org standards.
NullAI enables rapid LLM citation distribution across Perplexity and SearchGPT.
NullAI is located in San Francisco.
"""

SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head><title>NullAI Studio</title></head>
<body>
  <h1>NullAI is a cutting-edge autonomous AI developer tools studio.</h1>
  <p>NullAI was created by Alice Vance.</p>
  <div>
    <h2>Features & Integrations</h2>
    <p>NullAI features automated schema synthesis.</p>
    <p>NullAI supports Python and TypeScript.</p>
    <p>NullAI integrates with Next.js and Astro.</p>
  </div>
</body>
</html>
"""

SAMPLE_SCHEMA = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@type": "SoftwareApplication",
            "@id": "https://example.com/#software",
            "name": "NullAI",
            "operatingSystem": "Python",
            "creator": {
                "@type": "Person",
                "name": "Alice Vance",
            },
        },
        {
            "@type": "Organization",
            "@id": "https://example.com/#org",
            "name": "757tech Team",
        },
    ],
}


def test_extract_semantic_triplets_from_text():
    """Verify semantic triplet extraction across various linguistic patterns."""
    triplets = extract_semantic_triplets(SAMPLE_TEXT)
    assert len(triplets) >= 5

    subjects = {t.subject.lower() for t in triplets}
    predicates = {t.predicate for t in triplets}

    assert "nullai" in subjects
    assert "is_a" in predicates or "founded_by" in predicates or "supports" in predicates

    # Check triplet fields
    t0 = triplets[0]
    assert isinstance(t0.subject, str)
    assert isinstance(t0.predicate, str)
    assert isinstance(t0.object, str)
    assert 0.0 <= t0.confidence <= 1.0
    assert t0.inferred_schema_property is not None


def test_extract_semantic_triplets_from_html():
    """Verify HTML stripping and extraction from markup structure."""
    triplets = extract_semantic_triplets(SAMPLE_HTML)
    assert len(triplets) >= 3
    preds = [t.predicate for t in triplets]
    assert any(p in ("is_a", "developed_by", "supports", "integrates_with", "features", "provides") for p in preds)


def test_pagerank_computation():
    """Verify power-iteration PageRank calculation on cyclic and dangling graphs."""
    nodes = ["A", "B", "C"]
    # A -> B, B -> C, C -> A (cyclic triangle)
    adj = {"a": ["b"], "b": ["c"], "c": ["a"]}
    ranks = compute_pagerank(["a", "b", "c"], adj)
    assert len(ranks) == 3
    # In symmetric ring, ranks should be approximately equal (1/3 each)
    assert pytest.approx(ranks["a"], rel=1e-2) == 1.0 / 3.0
    assert pytest.approx(ranks["b"], rel=1e-2) == 1.0 / 3.0
    assert pytest.approx(ranks["c"], rel=1e-2) == 1.0 / 3.0

    # Single node edge case
    single_rank = compute_pagerank(["solo"], {})
    assert single_rank == {"solo": 1.0}

    # Empty graph
    assert compute_pagerank([], {}) == {}


def test_build_entity_graph_salience_and_density():
    """Verify entity graph construction, salience ranking, and density calculation."""
    triplets = extract_semantic_triplets(SAMPLE_TEXT)
    entities, adj, density = build_entity_graph(triplets)

    assert len(entities) > 0
    assert isinstance(density, float)
    assert density >= 0.0

    # NullAI should be the primary subject with highest salience
    top_entity = entities[0]
    assert top_entity.name.lower() == "nullai"
    assert top_entity.salience > 0.0
    assert top_entity.degree > 0
    assert top_entity.frequency > 0

    # Wikidata authority mapping check
    py_entities = [e for e in entities if e.name.lower() == "python"]
    if py_entities:
        assert py_entities[0].wikidata_id == "https://www.wikidata.org/wiki/Q28865"
        assert len(py_entities[0].same_as) > 0


def test_audit_knowledge_graph_schema_alignment():
    """Verify Schema.org alignment, entity coverage scoring, and orphan detection."""
    triplets = extract_semantic_triplets(SAMPLE_TEXT)
    entities, _, _ = build_entity_graph(triplets)

    report = audit_knowledge_graph_schema_alignment(
        triplets=triplets,
        entities=entities,
        schema_or_graph=SAMPLE_SCHEMA,
        base_url="https://example.com",
    )

    assert isinstance(report, KnowledgeGraphReport)
    assert report.triplets_count == len(triplets)
    assert report.entities_count == len(entities)
    assert 0.0 <= report.entity_coverage_score <= 100.0

    # NullAI and Alice Vance are in the schema
    matched = [e for e in report.entities if e.in_schema]
    assert len(matched) >= 1

    # Unmatched entities with high salience should appear in orphan_entities or patches
    assert isinstance(report.orphan_entities, list)
    assert isinstance(report.suggested_schema_patches, list)
    if report.suggested_schema_patches:
        patch = report.suggested_schema_patches[0]
        assert "@type" in patch
        assert "name" in patch


def test_export_rdf_and_turtle():
    """Verify serialization to W3C RDF N-Triples and Turtle syntax."""
    triplets = [
        SemanticTriplet(
            subject="NullAI",
            predicate="supports",
            object="Python",
            confidence=0.8,
            inferred_schema_property="knowsAbout",
        ),
        SemanticTriplet(
            subject="NullAI",
            predicate="developed_by",
            object="Alice Vance",
            confidence=0.9,
            inferred_schema_property="creator",
        ),
    ]

    ntriples = export_rdf_ntriples(triplets, base_url="https://example.com")
    assert "<https://example.com/resource/NullAI>" in ntriples
    assert "<https://schema.org/knowsAbout>" in ntriples
    assert '"Python" .' in ntriples

    turtle = export_turtle(triplets, base_url="https://example.com")
    assert "@prefix schema: <https://schema.org/> ." in turtle
    assert "res:NullAI schema:knowsAbout \"Python\" ." in turtle


def test_analyze_knowledge_graph_facade():
    """Verify the high-level facade function."""
    report = analyze_knowledge_graph(SAMPLE_TEXT, schema_or_graph=SAMPLE_SCHEMA)
    assert isinstance(report, KnowledgeGraphReport)
    res_dict = report.to_dict()
    assert "triplets_count" in res_dict
    assert "entities_count" in res_dict
    assert "entity_coverage_score" in res_dict
    assert "rdf_ntriples" in res_dict
    assert "turtle" in res_dict


def test_mcp_tool_aeo_extract_knowledge_graph():
    """Verify MCP protocol handling for aeo_extract_knowledge_graph tool."""
    mcp = MCPServer()

    # 1. Verification of tool schema registration
    tools_res = mcp.process_jsonrpc_request({"jsonrpc": "2.0", "id": 10, "method": "tools/list"})
    tool_names = [t["name"] for t in tools_res["result"]["tools"]]
    assert "aeo_extract_knowledge_graph" in tool_names

    # 2. Tool invocation
    call_req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "aeo_extract_knowledge_graph",
            "arguments": {
                "content": SAMPLE_TEXT,
                "schema_json": SAMPLE_SCHEMA,
                "base_url": "https://nullai.dev",
            },
        },
    }
    call_res = mcp.process_jsonrpc_request(call_req)
    assert not call_res.get("isError")
    contents = call_res["result"]["content"]
    assert len(contents) == 2
    summary_text = contents[0]["text"]
    assert "AEO KNOWLEDGE GRAPH & TRIPLETS REPORT" in summary_text

    data = json.loads(contents[1]["text"])
    assert data["triplets_count"] > 0
    assert data["entities_count"] > 0
    assert "entity_coverage_score" in data


def test_cli_knowledge_graph_subcommand(capsys):
    """Verify CLI execution of `aeo knowledge-graph`."""
    parser = build_parser()
    args = parser.parse_args(["knowledge-graph", SAMPLE_TEXT, "--format", "json"])
    assert args.subcommand == "knowledge-graph"
    assert args.format == "json"

    # Test running CLI entrypoint
    ret = cli_main(["knowledge-graph", SAMPLE_TEXT, "--format", "json"])
    assert ret == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert "triplets_count" in payload
    assert payload["triplets_count"] > 0


def test_ui_api_knowledge_graph_endpoint():
    """Verify POST /api/knowledge-graph on ephemeral HTTP server."""
    server = start_ui_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}/api/knowledge-graph"

    th = threading.Thread(target=server.serve_forever, daemon=True)
    th.start()
    time.sleep(0.05)

    try:
        body = json.dumps({
            "content": SAMPLE_TEXT,
            "schema": SAMPLE_SCHEMA,
            "base_url": "https://nullai.dev",
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert "triplets_count" in data
            assert data["triplets_count"] > 0
            assert "entity_coverage_score" in data
    finally:
        server.shutdown()
        server.server_close()
        th.join(timeout=1.0)

"""
Comprehensive Unit Tests for AEO Graph Engine MCP Server.
Tests JSON-RPC 2.0 protocol handling, tool schemas, tool execution, client config generation,
and stdio streaming workflows.
"""

import json
import io
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from typing import Dict, Any

from aeo_graph_engine.mcp_server import (
    AEOMCPServer,
    generate_mcp_client_config,
    get_framework_snippets,
    simulate_ai_citations,
    visualize_schema_graph,
    crawl_sitemap_batch,
    main as mcp_main,
    TOOLS_DEFINITIONS,
    SERVER_NAME,
    SERVER_VERSION,
    PROTOCOL_VERSION,
    PARSE_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    INVALID_PARAMS,
)


@pytest.fixture
def mcp_server():
    return AEOMCPServer()


# ==============================================================================
# 1. MCP Initialization and Lifecycle Handshake Tests
# ==============================================================================

def test_mcp_initialize(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0.0"}
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp is not None
    assert resp["jsonrpc"] == "2.0"
    assert resp["id"] == 1
    assert "result" in resp

    result = resp["result"]
    assert result["serverInfo"]["name"] == SERVER_NAME
    assert result["serverInfo"]["version"] == SERVER_VERSION
    assert result["protocolVersion"] == PROTOCOL_VERSION
    assert "tools" in result["capabilities"]
    assert mcp_server.is_initialized is True


def test_mcp_notifications_initialized(mcp_server):
    # Notification with no id should return None
    notification = {
        "jsonrpc": "2.0",
        "method": "notifications/initialized",
        "params": {}
    }
    resp = mcp_server.process_jsonrpc_request(notification)
    assert resp is None
    assert mcp_server.is_initialized is True

    # Call with id (if client sends as request)
    req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "initialized",
        "params": {}
    }
    resp_req = mcp_server.process_jsonrpc_request(req)
    assert resp_req is not None
    assert resp_req["id"] == 2
    assert resp_req["result"] == {}


def test_mcp_ping(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "ping"
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp is not None
    assert resp["id"] == 3
    assert resp["result"] == {}


# ==============================================================================
# 2. Tools Listing and Schema Inspection Tests
# ==============================================================================

def test_mcp_tools_list(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/list"
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp is not None
    assert resp["id"] == 4
    tools = resp["result"]["tools"]

    tool_names = [t["name"] for t in tools]
    expected_tools = [
        "aeo_scan_site",
        "aeo_synthesize_prompt",
        "aeo_generate_bundle",
        "aeo_inject_html",
        "aeo_validate",
        "aeo_get_framework_snippets",
        "aeo_simulate_citation",
        "aeo_visualize_schema",
        "aeo_crawl_sitemap"
    ]

    for expected in expected_tools:
        assert expected in tool_names, f"Missing tool: {expected}"

    # Verify each tool has valid MCP schema
    for t in tools:
        assert "name" in t
        assert "description" in t
        assert "inputSchema" in t
        assert t["inputSchema"]["type"] == "object"
        assert "properties" in t["inputSchema"]


# ==============================================================================
# 3. Tool Execution Tests via tools/call
# ==============================================================================

def test_tool_call_aeo_scan_site_mocked(mcp_server):
    mock_report = {
        "target_url": "https://example.com",
        "base_origin": "https://example.com",
        "overall_aeo_score": 92.5,
        "status": "EXCELLENT",
        "category_scores": {
            "schema_linked_data": {"score": 25.0, "max": 25.0},
            "llms_txt_machine_index": {"score": 25.0, "max": 25.0},
            "ai_crawler_governance": {"score": 20.0, "max": 20.0},
            "semantic_content_grounding": {"score": 12.5, "max": 15.0},
            "technical_seo_foundation": {"score": 10.0, "max": 15.0}
        },
        "root_assets": {
            "robots_txt": {"exists": True, "status": 200},
            "llms_txt": {"exists": True, "status": 200},
            "ai_txt": {"exists": True, "status": 200},
            "sitemap_xml": {"exists": True, "status": 200}
        },
        "pages_audited_count": 3,
        "ai_engine_compatibility": {
            "GPTBot (OpenAI / ChatGPT)": {"allowed": True},
            "PerplexityBot": {"allowed": True},
            "ClaudeBot": {"allowed": True}
        },
        "action_items": [
            {"priority": "LOW", "category": "SEO", "issue": "Missing canonical link", "fix": "Add canonical link"}
        ]
    }

    with patch("aeo_graph_engine.mcp_server.LiveAEOScanner") as mock_scanner_cls:
        mock_instance = MagicMock()
        mock_instance.compute_audit_scores.return_value = mock_report
        mock_scanner_cls.return_value = mock_instance

        req = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "aeo_scan_site",
                "arguments": {"url": "https://example.com", "max_pages": 3}
            }
        }
        resp = mcp_server.process_jsonrpc_request(req)
        assert resp["result"]["isError"] is False
        assert len(resp["result"]["content"]) == 2
        text_out = resp["result"]["content"][0]["text"]
        assert "LIVE AEO AUDIT REPORT" in text_out
        assert "92.5/100" in text_out


def test_tool_call_aeo_synthesize_prompt(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 10,
        "method": "tools/call",
        "params": {
            "name": "aeo_synthesize_prompt",
            "arguments": {
                "prompt": "Autonomous multi-agent research swarm called AgentIQ on agentiq.ai",
                "base_niche": "ai_swarm"
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp is not None
    assert resp["id"] == 10
    result = resp["result"]
    assert result["isError"] is False
    assert len(result["content"]) > 0
    text_out = result["content"][0]["text"]
    assert "AgentIQ" in text_out
    assert "agentiq.ai" in text_out


def test_tool_call_aeo_generate_bundle_in_memory(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 11,
        "method": "tools/call",
        "params": {
            "name": "aeo_generate_bundle",
            "arguments": {
                "config": {
                    "site_name": "TestMCP App",
                    "domain": "testmcp.dev"
                },
                "niche": "developer_tools"
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp is not None
    result = resp["result"]
    assert result["isError"] is False

    # Second content element contains structured JSON
    data = json.loads(result["content"][1]["text"])
    assert data["site_name"] == "TestMCP App"
    assert data["domain"] == "testmcp.dev"
    assert "schema_graph" in data["artifacts"]
    assert "@graph" in data["artifacts"]["schema_graph"]
    assert "# TestMCP App" in data["artifacts"]["llms_txt"]
    assert "GPTBot" in data["artifacts"]["robots_txt"]


def test_tool_call_aeo_generate_bundle_to_disk(mcp_server, tmp_path):
    out_dir = tmp_path / "mcp_bundle_output"
    req = {
        "jsonrpc": "2.0",
        "id": 12,
        "method": "tools/call",
        "params": {
            "name": "aeo_generate_bundle",
            "arguments": {
                "config": {"site_name": "Disk App", "domain": "diskapp.io"},
                "output_dir": str(out_dir)
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False

    assert (out_dir / "schema-graph.json").exists()
    assert (out_dir / "llms.txt").exists()
    assert (out_dir / "llms-full.txt").exists()
    assert (out_dir / "ai.txt").exists()
    assert (out_dir / "robots.txt").exists()


def test_tool_call_aeo_inject_html_string(mcp_server):
    sample_html = "<html><head><title>Original Page</title></head><body>Hello</body></html>"
    req = {
        "jsonrpc": "2.0",
        "id": 13,
        "method": "tools/call",
        "params": {
            "name": "aeo_inject_html",
            "arguments": {
                "html_content": sample_html,
                "config": {"site_name": "Injected Brand", "domain": "injected.com"}
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False
    injected_html = resp["result"]["content"][1]["text"]
    assert '<script type="application/ld+json">' in injected_html
    assert "Injected Brand" in injected_html
    assert "</head>" in injected_html


def test_tool_call_aeo_inject_html_file(mcp_server, tmp_path):
    html_file = tmp_path / "index.html"
    html_file.write_text("<html><head><title>Disk Test</title></head><body>Content</body></html>", encoding="utf-8")

    req = {
        "jsonrpc": "2.0",
        "id": 14,
        "method": "tools/call",
        "params": {
            "name": "aeo_inject_html",
            "arguments": {
                "html_file_path": str(html_file),
                "config": {"site_name": "File Injected Brand", "domain": "fileinject.com"},
                "backup": True
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False

    # Check updated file content and backup
    updated = html_file.read_text(encoding="utf-8")
    assert '<script type="application/ld+json">' in updated
    assert (tmp_path / "index.html.bak").exists()


def test_tool_call_aeo_validate_in_memory_schema(mcp_server):
    valid_schema = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": "https://test.com/#org", "name": "Org"},
            {"@type": "WebSite", "@id": "https://test.com/#site", "name": "Site"},
            {"@type": "SoftwareApplication", "@id": "https://test.com/#app", "name": "App"},
            {"@type": "FAQPage", "@id": "https://test.com/#faq", "name": "FAQ"}
        ]
    }
    req = {
        "jsonrpc": "2.0",
        "id": 15,
        "method": "tools/call",
        "params": {
            "name": "aeo_validate",
            "arguments": {
                "schema_data": valid_schema
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False
    report_data = json.loads(resp["result"]["content"][1]["text"])
    assert report_data["score"] >= 80
    assert report_data["errors_count"] == 0


def test_tool_call_aeo_validate_in_memory_manifests(mcp_server):
    # Validate llms.txt content
    llms_sample = "# My Tool\n\n> A fast tool\n\n- [Docs](https://mytool.dev/docs)\n- [API](https://mytool.dev/api)\n- [Schema](https://mytool.dev/schema)\n"
    req_llms = {
        "jsonrpc": "2.0",
        "id": 151,
        "method": "tools/call",
        "params": {
            "name": "aeo_validate",
            "arguments": {
                "content": llms_sample,
                "artifact_type": "llms_txt"
            }
        }
    }
    resp_llms = mcp_server.process_jsonrpc_request(req_llms)
    assert resp_llms["result"]["isError"] is False
    report_llms = json.loads(resp_llms["result"]["content"][1]["text"])
    assert report_llms["score"] >= 90

    # Validate robots.txt content
    robots_sample = "User-agent: *\nAllow: /\nUser-agent: GPTBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nUser-agent: ClaudeBot\nAllow: /\nSitemap: https://mytool.dev/sitemap.xml\n"
    req_robots = {
        "jsonrpc": "2.0",
        "id": 152,
        "method": "tools/call",
        "params": {
            "name": "aeo_validate",
            "arguments": {
                "content": robots_sample,
                "artifact_type": "robots_txt"
            }
        }
    }
    resp_robots = mcp_server.process_jsonrpc_request(req_robots)
    assert resp_robots["result"]["isError"] is False


def test_tool_call_aeo_validate_target_path(mcp_server, tmp_path):
    # Create valid bundle
    from aeo_graph_engine.core import write_aeo_bundle
    write_aeo_bundle(tmp_path)

    req = {
        "jsonrpc": "2.0",
        "id": 16,
        "method": "tools/call",
        "params": {
            "name": "aeo_validate",
            "arguments": {
                "target_path": str(tmp_path)
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False
    report_data = json.loads(resp["result"]["content"][1]["text"])
    assert report_data["score"] >= 90
    assert report_data["status"] == "EXCELLENT"


def test_tool_call_aeo_get_framework_snippets(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 17,
        "method": "tools/call",
        "params": {
            "name": "aeo_get_framework_snippets",
            "arguments": {
                "framework": "all",
                "config": {"site_name": "Snippets App", "domain": "snippets.app"}
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False
    data = json.loads(resp["result"]["content"][1]["text"])

    assert "nextjs" in data
    assert "astro" in data
    assert "vite" in data
    assert "remix" in data
    assert "nuxt" in data
    assert "sveltekit" in data
    assert "html" in data

    # Test single framework query
    req_single = {
        "jsonrpc": "2.0",
        "id": 18,
        "method": "tools/call",
        "params": {
            "name": "aeo_get_framework_snippets",
            "arguments": {"framework": "astro"}
        }
    }
    resp_single = mcp_server.process_jsonrpc_request(req_single)
    single_data = json.loads(resp_single["result"]["content"][1]["text"])
    assert len(single_data) == 1
    assert "astro" in single_data
    assert "set:html" in single_data["astro"]["code"]


def test_tool_call_aeo_simulate_citation(mcp_server):
    sample_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>ApexGraph - Fast Graph Neural Network Library</title>
        <link rel="canonical" href="https://apexgraph.ai/" />
        <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "SoftwareApplication",
          "name": "ApexGraph",
          "applicationCategory": "DeveloperApplication",
          "description": "High-performance GPU graph neural network framework."
        }
        </script>
      </head>
      <body>
        <h1>ApexGraph</h1>
        <p>ApexGraph is an ultra-scalable Python library for graph neural networks and node classification. It enables fast graph processing at scale.</p>
        <p>It achieves 10x faster inference speed on GPUs using custom CUDA kernels for tensor operations.</p>
      </body>
    </html>
    """
    req = {
        "jsonrpc": "2.0",
        "id": 19,
        "method": "tools/call",
        "params": {
            "name": "aeo_simulate_citation",
            "arguments": {
                "url_or_content": sample_html,
                "query": "What is ApexGraph?"
            }
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is False
    assert len(resp["result"]["content"]) == 2
    text_out = resp["result"]["content"][0]["text"]
    assert "AI CITATION SIMULATION REPORT" in text_out
    assert "ApexGraph" in text_out

    sim_data = json.loads(resp["result"]["content"][1]["text"])
    assert sim_data["brand_name"] == "ApexGraph"
    assert sim_data["extractability_score"] >= 60
    assert "extracted_quotes" in sim_data
    assert len(sim_data["extracted_quotes"]) >= 1
    assert "engines" in sim_data
    assert "perplexity" in sim_data["engines"]
    assert "chatgpt" in sim_data["engines"]
    assert "gemini" in sim_data["engines"]


def test_tool_call_aeo_visualize_schema(mcp_server, tmp_path):
    schema_dict = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "Organization", "@id": "https://acme.org/#org", "name": "Acme Inc"},
            {"@type": "WebSite", "@id": "https://acme.org/#site", "name": "Acme Site", "publisher": {"@id": "https://acme.org/#org"}},
            {"@type": "SoftwareApplication", "@id": "https://acme.org/#app", "name": "Acme App", "author": {"@id": "https://acme.org/#org"}}
        ]
    }

    # 1. Format: mermaid
    req_m = {
        "jsonrpc": "2.0",
        "id": 20,
        "method": "tools/call",
        "params": {
            "name": "aeo_visualize_schema",
            "arguments": {
                "schema_data": schema_dict,
                "format": "mermaid"
            }
        }
    }
    resp_m = mcp_server.process_jsonrpc_request(req_m)
    assert resp_m["result"]["isError"] is False
    m_data = json.loads(resp_m["result"]["content"][1]["text"])
    assert "mermaid" in m_data
    assert "graph TD" in m_data["mermaid"]
    assert "Acme Inc" in m_data["mermaid"]
    assert m_data["entities_count"] == 3

    # 2. Format: ascii with schema file on disk
    schema_file = tmp_path / "schema-graph.json"
    schema_file.write_text(json.dumps(schema_dict), encoding="utf-8")
    req_a = {
        "jsonrpc": "2.0",
        "id": 21,
        "method": "tools/call",
        "params": {
            "name": "aeo_visualize_schema",
            "arguments": {
                "schema_file": str(schema_file),
                "format": "ascii"
            }
        }
    }
    resp_a = mcp_server.process_jsonrpc_request(req_a)
    assert resp_a["result"]["isError"] is False
    a_data = json.loads(resp_a["result"]["content"][1]["text"])
    assert "ascii" in a_data
    assert "Schema.org Knowledge Graph" in a_data["ascii"]
    assert "Acme Inc" in a_data["ascii"]


def test_tool_call_aeo_crawl_sitemap(mcp_server, monkeypatch):
    mock_sitemap_report = {
        "sitemap_target": "https://testdomain.com/sitemap.xml",
        "sitemaps_discovered": ["https://testdomain.com/sitemap.xml"],
        "total_urls_in_sitemap": 3,
        "pages_audited_count": 3,
        "overall_sitemap_aeo_score": 96.0,
        "status": "EXCELLENT",
        "coverage_metrics": {
            "schema_coverage_pct": 100,
            "faq_coverage_pct": 67,
            "h1_coverage_pct": 100,
            "canonical_coverage_pct": 100
        },
        "pages": [
            {
                "url": "https://testdomain.com/",
                "status": 200,
                "title": "Home",
                "h1": "Welcome",
                "word_count": 300,
                "schema_count": 2,
                "schema_types": ["Organization", "WebSite"],
                "aeo_score": 98.0,
                "issues": []
            }
        ],
        "action_items": []
    }

    with patch("aeo_graph_engine.mcp_server.crawl_sitemap_batch", return_value=mock_sitemap_report):
        req = {
            "jsonrpc": "2.0",
            "id": 22,
            "method": "tools/call",
            "params": {
                "name": "aeo_crawl_sitemap",
                "arguments": {
                    "sitemap_url_or_domain": "https://testdomain.com/sitemap.xml",
                    "max_pages": 5
                }
            }
        }
        resp = mcp_server.process_jsonrpc_request(req)
        assert resp["result"]["isError"] is False
        assert len(resp["result"]["content"]) == 2
        text_out = resp["result"]["content"][0]["text"]
        assert "SITEMAP AEO CRAWL REPORT" in text_out
        assert "96.0/100" in text_out
        data_out = json.loads(resp["result"]["content"][1]["text"])
        assert data_out["overall_sitemap_aeo_score"] == 96.0


def test_direct_helper_functions(tmp_path):
    # 1. Test simulate_ai_citations
    sim = simulate_ai_citations("<html><head><title>Direct Test</title></head><body><h1>Hello</h1><p>A fast AI tool.</p></body></html>")
    assert sim["brand_name"] == "Direct Test"
    assert "extractability_score" in sim
    assert len(sim["extracted_quotes"]) >= 1

    # 2. Test visualize_schema_graph
    vis = visualize_schema_graph({
        "@graph": [
            {"@type": "Organization", "@id": "https://x.org/#org", "name": "Org X"},
            {"@type": "WebSite", "@id": "https://x.org/#site", "name": "Site X"}
        ]
    }, format="both")
    assert "graph TD" in vis["mermaid"]
    assert "Schema.org Knowledge Graph" in vis["ascii"]

    # 3. Test crawl_sitemap_batch with local sitemap.xml
    sitemap_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
      <url><loc>https://example.com/</loc></url>
      <url><loc>https://example.com/about</loc></url>
    </urlset>
    """
    sitemap_file = tmp_path / "sitemap.xml"
    sitemap_file.write_text(sitemap_xml, encoding="utf-8")

    # Patch urllib to avoid live requests during batch test
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.read.return_value = b"<html><head><title>Local Page</title></head><body><h1>Title</h1><p>Words here</p></body></html>"
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        crawl = crawl_sitemap_batch(str(sitemap_file), max_pages=2)
        assert crawl["total_urls_in_sitemap"] == 2
        assert crawl["pages_audited_count"] == 2
        assert "coverage_metrics" in crawl


# ==============================================================================
# 4. Error Handling and Edge Case Tests
# ==============================================================================

def test_mcp_unknown_method(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 99,
        "method": "non_existent_method"
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["error"]["code"] == METHOD_NOT_FOUND
    assert "Method not found" in resp["error"]["message"]


def test_mcp_unknown_tool(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 100,
        "method": "tools/call",
        "params": {
            "name": "unknown_tool_xyz",
            "arguments": {}
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is True
    assert "Unknown tool name" in resp["result"]["content"][0]["text"]


def test_mcp_missing_tool_params(mcp_server):
    req = {
        "jsonrpc": "2.0",
        "id": 101,
        "method": "tools/call",
        "params": {
            "name": "aeo_synthesize_prompt",
            "arguments": {} # Missing required 'prompt'
        }
    }
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["result"]["isError"] is True
    assert "'prompt' parameter is required" in resp["result"]["content"][0]["text"]


def test_mcp_invalid_jsonrpc_structure(mcp_server):
    # Missing method field
    req = {"jsonrpc": "2.0", "id": 102}
    resp = mcp_server.process_jsonrpc_request(req)
    assert resp["error"]["code"] == INVALID_REQUEST

    # Non-dict object
    resp2 = mcp_server.process_jsonrpc_request("not-a-json-object")
    assert resp2["error"]["code"] == INVALID_REQUEST


# ==============================================================================
# 5. MCP Client Config Generator Tests
# ==============================================================================

def test_generate_mcp_client_config_all_clients():
    # Claude Desktop
    claude_cfg = generate_mcp_client_config("claude_desktop", python_path="/usr/bin/python3")
    assert "mcpServers" in claude_cfg
    assert "aeo-graph-engine" in claude_cfg["mcpServers"]
    assert claude_cfg["mcpServers"]["aeo-graph-engine"]["command"] == "/usr/bin/python3"
    assert claude_cfg["mcpServers"]["aeo-graph-engine"]["args"] == ["-m", "aeo_graph_engine.mcp_server"]

    # Cursor
    cursor_cfg = generate_mcp_client_config("cursor")
    assert "mcpServers" in cursor_cfg
    assert "aeo-graph-engine" in cursor_cfg["mcpServers"]

    # Cline
    cline_cfg = generate_mcp_client_config("cline")
    assert "mcpServers" in cline_cfg
    assert cline_cfg["mcpServers"]["aeo-graph-engine"]["disabled"] is False

    # Zed
    zed_cfg = generate_mcp_client_config("zed")
    assert "context_servers" in zed_cfg
    assert "aeo-graph-engine" in zed_cfg["context_servers"]
    assert zed_cfg["context_servers"]["aeo-graph-engine"]["command"]["path"] == "python3"

    # Generic
    generic_cfg = generate_mcp_client_config("generic")
    assert generic_cfg["name"] == SERVER_NAME
    assert generic_cfg["transport"] == "stdio"
    assert generic_cfg["protocol_version"] == PROTOCOL_VERSION


def test_generate_mcp_client_config_with_project_root():
    proj_path = "/workspace/my-project"
    cfg = generate_mcp_client_config("claude_desktop", project_root=proj_path)
    env = cfg["mcpServers"]["aeo-graph-engine"]["env"]
    assert "PYTHONPATH" in env
    resolved_root = str(Path(proj_path).resolve())
    assert resolved_root in env["PYTHONPATH"]


def test_generate_mcp_client_config_invalid():
    with pytest.raises(ValueError) as exc:
        generate_mcp_client_config("unsupported_client_abc")
    assert "Unsupported MCP client" in str(exc.value)


# ==============================================================================
# 6. CLI Entrypoint Tests for mcp_server
# ==============================================================================

def test_mcp_cli_help(capsys):
    ret = mcp_main(["--help"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "AEO Graph Engine MCP Server" in captured.out


def test_mcp_cli_tools_listing(capsys):
    ret = mcp_main(["--tools"])
    assert ret == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert len(parsed) == len(TOOLS_DEFINITIONS)


def test_mcp_cli_config_generator(capsys):
    ret = mcp_main(["--config", "cursor"])
    assert ret == 0
    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert "mcpServers" in parsed


# ==============================================================================
# 7. Full Stdio Stream End-to-End Test (Single & Batch & Parse Error)
# ==============================================================================

def test_mcp_stdio_stream_conversation(tmp_path):
    server = AEOMCPServer()

    # Create sequence of JSON-RPC commands
    messages = [
        # 1. Initialize
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        # 2. Initialized notification (no output expected)
        {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}},
        # 3. Ping
        {"jsonrpc": "2.0", "id": 2, "method": "ping"},
        # 4. List tools
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list"},
        # 5. Call tool
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "aeo_synthesize_prompt",
                "arguments": {"prompt": "A modern analytics engine called PulseMetrics on pulse.dev"}
            }
        }
    ]

    input_lines = "\n".join(json.dumps(m) for m in messages) + "\n"
    in_stream = io.StringIO(input_lines)
    out_stream = io.StringIO()

    server.serve_stdio(input_stream=in_stream, output_stream=out_stream)

    out_lines = [l.strip() for l in out_stream.getvalue().splitlines() if l.strip()]
    
    # 4 responses expected (initialize, ping, tools/list, tools/call)
    assert len(out_lines) == 4

    resp_init = json.loads(out_lines[0])
    assert resp_init["id"] == 1
    assert resp_init["result"]["serverInfo"]["name"] == SERVER_NAME

    resp_ping = json.loads(out_lines[1])
    assert resp_ping["id"] == 2
    assert resp_ping["result"] == {}

    resp_tools = json.loads(out_lines[2])
    assert resp_tools["id"] == 3
    assert len(resp_tools["result"]["tools"]) == len(TOOLS_DEFINITIONS)

    resp_call = json.loads(out_lines[3])
    assert resp_call["id"] == 4
    assert resp_call["result"]["isError"] is False
    assert "PulseMetrics" in resp_call["result"]["content"][0]["text"]


def test_mcp_stdio_stream_batch_and_parse_error():
    server = AEOMCPServer()

    # Line 1: Malformed JSON
    # Line 2: Batch request [ping, tools/list]
    input_text = "NOT_VALID_JSON\n" + json.dumps([
        {"jsonrpc": "2.0", "id": 10, "method": "ping"},
        {"jsonrpc": "2.0", "id": 11, "method": "tools/list"}
    ]) + "\n"

    in_stream = io.StringIO(input_text)
    out_stream = io.StringIO()

    server.serve_stdio(input_stream=in_stream, output_stream=out_stream)

    lines = [l.strip() for l in out_stream.getvalue().splitlines() if l.strip()]
    assert len(lines) == 2

    # Line 1 response: parse error
    resp_err = json.loads(lines[0])
    assert resp_err["error"]["code"] == PARSE_ERROR

    # Line 2 response: batch array
    resp_batch = json.loads(lines[1])
    assert isinstance(resp_batch, list)
    assert len(resp_batch) == 2
    assert resp_batch[0]["id"] == 10
    assert resp_batch[1]["id"] == 11

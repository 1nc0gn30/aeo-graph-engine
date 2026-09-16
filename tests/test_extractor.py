"""
Unit tests for HTML metadata extraction and project discovery.
"""

from pathlib import Path
from aeo_graph_engine.extractor import extract_metadata_from_html, extract_from_file
from aeo_graph_engine.discovery import discover_project_metadata


def test_extract_metadata_from_html():
    sample_html = """<!DOCTYPE html>
    <html lang="en">
    <head>
        <title>OmniCloud — High Performance Cloud</title>
        <meta name="description" content="Serverless edge computing with sub-millisecond cold starts.">
        <meta property="og:site_name" content="OmniCloud">
        <meta property="og:image" content="https://omnicloud.io/og.png">
        <link rel="canonical" href="https://omnicloud.io/">
        <script type="application/ld+json">
        {"@context": "https://schema.org", "@type": "SoftwareApplication", "name": "OmniCloud Engine"}
        </script>
    </head>
    <body>
        <h1>Next-Gen Cloud Mesh</h1>
        <h2>Features</h2>
    </body>
    </html>"""

    res = extract_metadata_from_html(sample_html)

    assert res["site_name"] == "OmniCloud"
    assert "Serverless edge computing" in res["description"]
    assert res["canonical_url"] == "https://omnicloud.io/"
    assert res["domain"] == "omnicloud.io"
    assert res["og_image_url"] == "https://omnicloud.io/og.png"
    assert len(res["existing_jsonld"]) == 1
    assert res["existing_jsonld"][0]["name"] == "OmniCloud Engine"
    assert len(res["headings"]) >= 2


def test_extract_from_file(tmp_path):
    html_file = tmp_path / "sample.html"
    html_file.write_text("<html><head><title>File Platform</title></head><body><h1>Hi</h1></body></html>", encoding="utf-8")

    res = extract_from_file(html_file)
    assert res["site_name"] == "File Platform"
    assert res["source_file"] == str(html_file.resolve())


def test_discover_project_metadata(tmp_path):
    pkg_file = tmp_path / "package.json"
    pkg_file.write_text('{"name": "agent-orchestrator", "description": "AI Agent Mesh", "dependencies": {"next": "15.0.0"}}', encoding="utf-8")

    res = discover_project_metadata(tmp_path)
    assert "Agent Orchestrator" in res["site_name"]
    assert res["description"] == "AI Agent Mesh"
    assert res["framework"] == "nextjs"

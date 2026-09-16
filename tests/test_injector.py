"""
Unit tests for HTML injection and updater functionality.
"""

from pathlib import Path
from aeo_graph_engine.injector import inject_jsonld_into_html, inject_file
from aeo_graph_engine.core import generate_schema_graph


def test_inject_jsonld_into_html_basic():
    html = "<!DOCTYPE html><html><head><title>Demo</title></head><body><h1>Hello</h1></body></html>"
    payload = {"@context": "https://schema.org", "@type": "Organization", "name": "Acme Corp"}

    result = inject_jsonld_into_html(html, payload)

    assert '<script type="application/ld+json">' in result
    assert '"Organization"' in result
    assert '"Acme Corp"' in result
    assert '</head>' in result


def test_inject_jsonld_idempotent_replace():
    html = """<!DOCTYPE html>
<html>
<head>
  <title>Demo</title>
  <script type="application/ld+json">
  {"@context": "https://schema.org", "@type": "OldEntity"}
  </script>
</head>
<body><h1>Hello</h1></body>
</html>"""
    new_payload = {"@context": "https://schema.org", "@type": "NewEntity"}
    result = inject_jsonld_into_html(html, new_payload)

    assert '"NewEntity"' in result
    assert '"OldEntity"' not in result
    assert result.count('<script type="application/ld+json">') == 1


def test_inject_jsonld_fallback_no_head():
    html = "<html><body><h1>Hello World</h1></body></html>"
    payload = {"@context": "https://schema.org", "@type": "WebSite"}
    result = inject_jsonld_into_html(html, payload)

    assert '<script type="application/ld+json">' in result
    assert '<body>' in result


def test_inject_file(tmp_path):
    html_file = tmp_path / "page.html"
    html_file.write_text("<html><head><title>Test</title></head><body>Content</body></html>", encoding="utf-8")

    graph = generate_schema_graph({"site_name": "Injected App"})
    success = inject_file(html_file, graph, backup=True)

    assert success is True
    updated_content = html_file.read_text(encoding="utf-8")
    assert '<script type="application/ld+json">' in updated_content
    assert '"Injected App"' in updated_content
    assert (tmp_path / "page.html.bak").exists()

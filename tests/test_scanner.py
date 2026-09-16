"""
Unit tests for LiveAEOScanner and AI distribution intelligence.
"""

import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from aeo_graph_engine.scanner import LiveAEOScanner, HTMLLinkExtractor


class MockSiteHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/robots.txt":
            content = "User-agent: GPTBot\nAllow: /\nUser-agent: PerplexityBot\nAllow: /\nSitemap: http://127.0.0.1/sitemap.xml\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        if self.path == "/llms.txt":
            content = "# Demo Site\n\n> A test platform\n\n- [Docs](http://127.0.0.1/docs): API reference\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(content.encode("utf-8"))
            return

        if self.path in ("/", "/index.html"):
            html = """<!DOCTYPE html>
<html>
<head>
    <title>Mock Testing Portal</title>
    <meta name="description" content="A live test site for AEO scanner">
    <link rel="canonical" href="http://127.0.0.1/">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {"@type": "Organization", "@id": "http://127.0.0.1/#org", "name": "Mock Org"},
        {"@type": "WebSite", "@id": "http://127.0.0.1/#site", "name": "Mock Portal"}
      ]
    }
    </script>
</head>
<body>
    <h1>Welcome to Testing</h1>
    <p>This is a test paragraph with multiple words to test the live crawler parsing.</p>
    <a href="/about">About Us</a>
    <a href="/docs">Documentation</a>
</body>
</html>"""
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if self.path == "/about":
            html = "<html><head><title>About</title></head><body><h1>About</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        if self.path == "/docs":
            html = "<html><head><title>Docs</title></head><body><h1>Documentation</h1></body></html>"
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
            return

        self.send_response(404)
        self.end_headers()


def test_live_scanner_execution():
    server = ThreadingHTTPServer(("127.0.0.1", 0), MockSiteHandler)
    host, port = server.server_address
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()

    try:
        url = f"http://{host}:{port}/"
        scanner = LiveAEOScanner(url, max_pages=3, timeout=5)
        report = scanner.compute_audit_scores()

        assert report["overall_aeo_score"] > 0
        assert report["pages_audited_count"] >= 1
        assert report["root_assets"]["robots_txt"]["exists"] is True
        assert report["root_assets"]["llms_txt"]["exists"] is True
        assert "ai_engine_compatibility" in report
        assert "backlink_and_distribution_intelligence" in report

        bot_matrix = report["ai_engine_compatibility"]
        assert bot_matrix["ChatGPT (GPTBot)"]["allowed"] is True

        strategy = report["backlink_and_distribution_intelligence"]
        assert len(strategy["high_authority_citation_hubs"]) >= 3
    finally:
        server.shutdown()
        server.server_close()


def test_html_link_extractor():
    base = "https://example.com/blog/article-1"
    parser = HTMLLinkExtractor(base)
    html = """
    <a href="/about">About</a>
    <a href="https://example.com/pricing">Pricing</a>
    <a href="https://external.com/partner">External</a>
    <a href="#section">Fragment</a>
    """
    parser.feed(html)

    assert "https://example.com/about" in parser.internal_links
    assert "https://example.com/pricing" in parser.internal_links
    assert "https://external.com/partner" in parser.external_links

"""
Unit tests for Sitemap Crawler & Multi-Page AEO Auditor.
Tests XML namespace parsing, sitemap index traversal, internal link fallback crawling,
latency measurements, and site-wide AEO coverage metric calculations.
"""

from unittest.mock import MagicMock, patch
import pytest

from aeo_graph_engine.crawler import (
    HTMLLinkExtractor,
    parse_sitemap_xml,
    SitemapCrawler,
    crawl_sitemap_or_site,
)

SAMPLE_STANDARD_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
    <url>
        <loc>https://example.com/</loc>
        <lastmod>2026-09-16</lastmod>
        <priority>1.0</priority>
    </url>
    <url>
        <loc>https://example.com/docs</loc>
        <lastmod>2026-09-15</lastmod>
        <priority>0.8</priority>
    </url>
    <url>
        <loc>https://example.com/pricing</loc>
        <lastmod>2026-09-14</lastmod>
        <priority>0.7</priority>
    </url>
</urlset>
"""

SAMPLE_SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://example.com/sitemaps/pages.xml</loc>
        <lastmod>2026-09-16</lastmod>
    </sitemap>
    <sitemap>
        <loc>https://example.com/sitemaps/posts.xml</loc>
        <lastmod>2026-09-15</lastmod>
    </sitemap>
</sitemapindex>
"""

HOMEPAGE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Example Home</title>
    <meta name="description" content="Official home page with high-speed indexing">
    <script type="application/ld+json">
    {"@context": "https://schema.org", "@type": "WebSite", "name": "Example"}
    </script>
</head>
<body>
    <h1>Welcome to Example</h1>
    <p>This is the main platform landing page with comprehensive documentation.</p>
    <a href="/features">Features</a>
    <a href="/about">About Us</a>
    <a href="https://external-site.org/resource">External Link</a>
</body>
</html>
"""

FEATURES_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Features</title>
</head>
<body>
    <h1>Our Features</h1>
    <p>We provide high performance structured metadata extraction.</p>
</body>
</html>
"""


class TestSitemapXMLParser:
    """Tests XML namespace handling and sitemap index parsing."""

    def test_parses_standard_sitemap_with_namespaces(self):
        result = parse_sitemap_xml(SAMPLE_STANDARD_SITEMAP)
        assert result["is_index"] is False
        assert len(result["urls"]) == 3
        assert "https://example.com/" in result["urls"]
        assert "https://example.com/docs" in result["urls"]
        assert "https://example.com/pricing" in result["urls"]

    def test_parses_sitemap_index(self):
        result = parse_sitemap_xml(SAMPLE_SITEMAP_INDEX)
        assert result["is_index"] is True
        assert len(result["child_sitemaps"]) == 2
        assert "https://example.com/sitemaps/pages.xml" in result["child_sitemaps"]

    def test_handles_empty_or_malformed_xml(self):
        empty_res = parse_sitemap_xml("")
        assert empty_res["urls"] == []
        assert empty_res["is_index"] is False

        malformed = "<urlset><url><loc>https://example.com/broken</loc></urlset>"
        malformed_res = parse_sitemap_xml(malformed)
        assert "https://example.com/broken" in malformed_res["urls"]


class TestHTMLLinkExtractor:
    """Tests discovery of internal and external links from HTML."""

    def test_extracts_internal_and_external_links(self):
        extractor = HTMLLinkExtractor("https://example.com/")
        extractor.feed(HOMEPAGE_HTML)

        assert "https://example.com/features" in extractor.internal_links
        assert "https://example.com/about" in extractor.internal_links
        assert "https://external-site.org/resource" in extractor.external_links


class TestSitemapCrawler:
    """Tests multi-page crawling, metric computation, and fallback link discovery."""

    @patch.object(SitemapCrawler, "_fetch")
    def test_crawl_with_sitemap_success(self, mock_fetch):
        def fake_fetch(url: str):
            if "sitemap.xml" in url:
                return 200, SAMPLE_STANDARD_SITEMAP, "application/xml", 25.0
            elif url == "https://example.com/":
                return 200, HOMEPAGE_HTML, "text/html", 15.0
            elif "docs" in url or "pricing" in url:
                return 200, FEATURES_HTML, "text/html", 20.0
            elif "llms.txt" in url:
                return 200, "# Example\n> Summary", "text/plain", 10.0
            elif "robots.txt" in url:
                return 200, "User-agent: *\nAllow: /", "text/plain", 10.0
            return 404, "", None, 10.0

        mock_fetch.side_effect = fake_fetch

        crawler = SitemapCrawler("https://example.com/sitemap.xml", max_pages=5)
        metrics = crawler.crawl_and_audit()

        assert metrics["sitemap_detected"] is True
        assert metrics["pages_crawled_count"] >= 3
        assert metrics["successful_pages_count"] >= 3
        assert metrics["schema_coverage_pct"] > 0.0
        assert metrics["avg_word_count"] > 0.0
        assert metrics["avg_latency_ms"] > 0.0
        assert metrics["overall_aeo_health_score"] > 50.0

    @patch.object(SitemapCrawler, "_fetch")
    def test_crawl_fallback_when_sitemap_missing(self, mock_fetch):
        def fake_fetch(url: str):
            if "sitemap" in url:
                return 404, "", None, 10.0
            elif url == "https://example.com" or url == "https://example.com/":
                return 200, HOMEPAGE_HTML, "text/html", 15.0
            elif "features" in url:
                return 200, FEATURES_HTML, "text/html", 18.0
            elif "about" in url:
                return 200, "<html><body><h1>About</h1><p>About page content.</p></body></html>", "text/html", 12.0
            return 404, "", None, 10.0

        mock_fetch.side_effect = fake_fetch

        res = crawl_sitemap_or_site("example.com", max_pages=3)

        assert res["sitemap_detected"] is False
        assert res["pages_crawled_count"] >= 2
        assert "missing_elements" in res
        assert "recommendations" in res

    @patch.object(SitemapCrawler, "_fetch")
    def test_crawl_sitemap_index_fetches_child_sitemaps(self, mock_fetch):
        def fake_fetch(url: str):
            if url.endswith("sitemap.xml"):
                return 200, SAMPLE_SITEMAP_INDEX, "application/xml", 20.0
            elif "sitemaps/pages.xml" in url:
                return 200, "<urlset><url><loc>https://example.com/page1</loc></url></urlset>", "application/xml", 15.0
            elif "page1" in url:
                return 200, "<html><head><title>P1</title></head><body><h1>P1</h1><p>Page 1 content.</p></body></html>", "text/html", 10.0
            return 404, "", None, 10.0

        mock_fetch.side_effect = fake_fetch

        crawler = SitemapCrawler("https://example.com/sitemap.xml", max_pages=2)
        metrics = crawler.crawl_and_audit()

        assert metrics["sitemap_detected"] is True
        assert any(p["url"] == "https://example.com/page1" for p in metrics["pages"])
        assert "pages_missing_schema" in metrics["missing_elements"]

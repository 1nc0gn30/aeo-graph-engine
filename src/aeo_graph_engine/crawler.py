"""
High-Performance Sitemap Crawler & Multi-Page AEO Auditor for AEO Graph Engine.
Parses sitemap.xml, sitemap_index.xml, discovers internal links, and runs
lightweight AEO/GEO audits computing site-wide coverage metrics.
Zero external runtime dependencies (Python standard library urllib, xml.etree, html.parser).
"""

import re
import json
import time
import urllib.request
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from .extractor import extract_metadata_from_html
from .validator import validate_schema_jsonld_dict, AEODiagnosticReport


class HTMLLinkExtractor(HTMLParser):
    """Extracts internal and external links from HTML for crawler discovery."""

    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.parsed_base = urllib.parse.urlparse(base_url)
        self.internal_links: Set[str] = set()
        self.external_links: Set[str] = set()

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        if tag.lower() == "a":
            for k, v in attrs:
                if k.lower() == "href" and v:
                    href = v.strip()
                    if href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
                        continue
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    parsed_full = urllib.parse.urlparse(full_url)

                    if parsed_full.scheme not in ("http", "https"):
                        continue

                    # Normalize by stripping fragment and query parameters
                    clean_url = urllib.parse.urlunparse((
                        parsed_full.scheme,
                        parsed_full.netloc,
                        parsed_full.path or "/",
                        "", "", ""
                    ))

                    if parsed_full.netloc == self.parsed_base.netloc:
                        self.internal_links.add(clean_url)
                    else:
                        self.external_links.add(clean_url)


def parse_sitemap_xml(xml_content: str) -> Dict[str, Any]:
    """
    Parses sitemap.xml or sitemap_index.xml with clean XML namespace stripping.
    Supports standard sitemaps, sitemap indexes, and news/image sitemaps.
    Returns {"is_index": bool, "urls": List[str], "child_sitemaps": List[str]}.
    """
    urls: List[str] = []
    child_sitemaps: List[str] = []
    is_index = False

    if not xml_content or not xml_content.strip():
        return {"is_index": False, "urls": [], "child_sitemaps": []}

    # Method 1: ElementTree with namespace removal
    try:
        # Strip default XML namespaces for clean tag matching
        clean_xml = re.sub(r'\sxmlns(?::\w+)?="[^"]+"', '', xml_content, count=0)
        root = ET.fromstring(clean_xml)

        root_tag = root.tag.lower().split("}")[-1]

        if "sitemapindex" in root_tag:
            is_index = True
            for sitemap_node in root.findall(".//sitemap"):
                loc = sitemap_node.find("loc")
                if loc is not None and loc.text and loc.text.strip():
                    child_sitemaps.append(loc.text.strip())
        else:
            for url_node in root.findall(".//url"):
                loc = url_node.find("loc")
                if loc is not None and loc.text and loc.text.strip():
                    urls.append(loc.text.strip())

    except Exception:
        # Method 2: Robust Regex Fallback
        if "<sitemapindex" in xml_content.lower():
            is_index = True
            child_matches = re.findall(r'<sitemap[^>]*>\s*<loc>([^<]+)</loc>', xml_content, re.IGNORECASE)
            child_sitemaps = [m.strip() for m in child_matches if m.strip()]
        else:
            loc_matches = re.findall(r'<loc>([^<]+)</loc>', xml_content, re.IGNORECASE)
            urls = [m.strip() for m in loc_matches if m.strip()]

    return {
        "is_index": is_index,
        "urls": urls,
        "child_sitemaps": child_sitemaps
    }


class SitemapCrawler:
    """
    High-performance AEO/GEO crawler and sitemap auditor.
    Fetches sitemaps, discovers internal links, and computes site-wide AEO metrics.
    """

    USER_AGENT = "Mozilla/5.0 (compatible; AEOGraphEngine-Crawler/1.0; +https://github.com/1nc0gn30/aeo-graph-engine)"

    def __init__(self, target_url_or_domain: str, max_pages: int = 15, timeout: float = 5.0):
        raw = target_url_or_domain.strip()
        if not raw.startswith(("http://", "https://")):
            raw = "https://" + raw

        self.initial_target = raw
        self.parsed_root = urllib.parse.urlparse(raw)
        self.base_origin = f"{self.parsed_root.scheme}://{self.parsed_root.netloc}"
        self.max_pages = max(1, max_pages)
        self.timeout = timeout

        self.crawled_pages: Dict[str, Dict[str, Any]] = {}
        self.discovered_urls: Set[str] = set()
        self.sitemap_urls_found: List[str] = []
        self.sitemap_detected: bool = False
        self.root_assets: Dict[str, Dict[str, Any]] = {
            "robots_txt": {"exists": False, "status": 0, "content": ""},
            "llms_txt": {"exists": False, "status": 0, "content": ""},
            "llms_full_txt": {"exists": False, "status": 0, "content": ""},
            "ai_txt": {"exists": False, "status": 0, "content": ""},
            "sitemap_xml": {"exists": False, "status": 0, "content": ""},
            "schema_graph_json": {"exists": False, "status": 0, "content": ""}
        }

    def _fetch(self, url: str) -> Tuple[int, str, Optional[str], float]:
        """Fetches a URL, measures latency in milliseconds, and handles HTTP errors."""
        start_time = time.perf_counter()
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,text/plain;q=0.8,*/*;q=0.7"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                raw_bytes = response.read(2_000_000)
                elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
                text = raw_bytes.decode("utf-8", errors="replace")
                return status, text, content_type, elapsed_ms
        except urllib.error.HTTPError as e:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return e.code, "", None, elapsed_ms
        except Exception:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return 0, "", None, elapsed_ms

    def inspect_root_assets(self) -> None:
        """Inspects root AI discovery manifests and sitemaps."""
        endpoints = {
            "robots_txt": f"{self.base_origin}/robots.txt",
            "llms_txt": f"{self.base_origin}/llms.txt",
            "llms_full_txt": f"{self.base_origin}/llms-full.txt",
            "ai_txt": f"{self.base_origin}/ai.txt",
            "sitemap_xml": f"{self.base_origin}/sitemap.xml",
            "schema_graph_json": f"{self.base_origin}/schema-graph.json"
        }

        for key, ep in endpoints.items():
            status, text, _, _ = self._fetch(ep)
            if status == 200 and text.strip():
                self.root_assets[key]["exists"] = True
                self.root_assets[key]["status"] = status
                self.root_assets[key]["content"] = text
            else:
                self.root_assets[key]["status"] = status

    def discover_sitemap_urls(self) -> List[str]:
        """Discovers and parses sitemaps or sitemap index files."""
        # Determine candidate sitemap endpoint
        candidate_url = self.initial_target if self.initial_target.endswith(".xml") else f"{self.base_origin}/sitemap.xml"

        status, content, _, _ = self._fetch(candidate_url)
        if status != 200 or not content.strip():
            # Try /sitemap_index.xml
            candidate_url = f"{self.base_origin}/sitemap_index.xml"
            status, content, _, _ = self._fetch(candidate_url)

        if status != 200 or not content.strip():
            return []

        self.sitemap_detected = True
        self.root_assets["sitemap_xml"]["exists"] = True
        self.root_assets["sitemap_xml"]["status"] = 200
        self.root_assets["sitemap_xml"]["content"] = content

        parsed = parse_sitemap_xml(content)
        collected_urls: List[str] = []

        if parsed["is_index"] and parsed["child_sitemaps"]:
            # Fetch child sitemaps up to 3 sub-sitemaps
            for child_sm in parsed["child_sitemaps"][:3]:
                c_status, c_content, _, _ = self._fetch(child_sm)
                if c_status == 200 and c_content.strip():
                    child_parsed = parse_sitemap_xml(c_content)
                    collected_urls.extend(child_parsed["urls"])
        else:
            collected_urls.extend(parsed["urls"])

        # Filter to same domain
        valid_urls = []
        for u in collected_urls:
            p = urllib.parse.urlparse(u)
            if p.netloc == self.parsed_root.netloc:
                valid_urls.append(u)

        self.sitemap_urls_found = valid_urls
        return valid_urls

    def crawl_and_audit(self) -> Dict[str, Any]:
        """Runs multi-page sitemap crawl or internal link crawler with AEO metrics."""
        self.inspect_root_assets()
        sitemap_urls = self.discover_sitemap_urls()

        # Seed queue
        queue: List[str] = []
        if self.initial_target.endswith(".xml"):
            homepage = f"{self.base_origin}/"
            queue.append(homepage)
        else:
            queue.append(self.initial_target)

        for su in sitemap_urls:
            if su not in queue:
                queue.append(su)

        visited: Set[str] = set()

        while queue and len(visited) < self.max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            self.discovered_urls.add(current_url)

            status, html_text, ctype, latency_ms = self._fetch(current_url)

            if status != 200 or not html_text:
                self.crawled_pages[current_url] = {
                    "url": current_url,
                    "status": status,
                    "latency_ms": latency_ms,
                    "error": f"HTTP status {status}" if status != 200 else "Empty response",
                    "has_schema": False,
                    "schema_count": 0,
                    "word_count": 0
                }
                continue

            # Extract metadata and schemas
            meta = extract_metadata_from_html(html_text)

            # Discover internal links if we need more pages
            link_parser = HTMLLinkExtractor(current_url)
            try:
                link_parser.feed(html_text)
            except Exception:
                pass

            for new_link in link_parser.internal_links:
                self.discovered_urls.add(new_link)
                if new_link not in visited and new_link not in queue:
                    queue.append(new_link)

            # Analyze page Schema.org JSON-LD
            schemas_found = meta.get("existing_jsonld", [])
            schema_report = AEODiagnosticReport(current_url)
            for sch in schemas_found:
                if isinstance(sch, dict):
                    validate_schema_jsonld_dict(sch, schema_report)

            # Word count estimation
            plain_text = re.sub(r'<[^>]+>', ' ', html_text)
            words = len(plain_text.split())

            # Detect headings
            headings = meta.get("headings", [])
            h1s = [h for h in headings if h.get("tag") == "h1"]

            self.crawled_pages[current_url] = {
                "url": current_url,
                "status": status,
                "latency_ms": latency_ms,
                "title": meta.get("site_name") or meta.get("tagline") or "",
                "tagline": meta.get("tagline") or "",
                "description": meta.get("description") or "",
                "canonical_url": meta.get("canonical_url"),
                "headings_count": len(headings),
                "h1_count": len(h1s),
                "headings": headings[:8],
                "word_count": words,
                "has_schema": len(schemas_found) > 0,
                "schema_count": len(schemas_found),
                "schemas": schemas_found,
                "schema_score": round(schema_report.score, 1),
                "schema_errors": schema_report.errors,
                "schema_warnings": schema_report.warnings,
                "internal_links_count": len(link_parser.internal_links),
                "external_links_count": len(link_parser.external_links)
            }

        return self.compute_site_metrics()

    def compute_site_metrics(self) -> Dict[str, Any]:
        """Computes comprehensive site-wide AEO coverage metrics and diagnostics."""
        pages = list(self.crawled_pages.values())
        successful_pages = [p for p in pages if p.get("status") == 200]
        total_crawled = len(pages)
        total_successful = len(successful_pages)

        # Status distribution
        status_dist: Dict[str, int] = {}
        for p in pages:
            s_code = str(p.get("status", 0))
            status_dist[s_code] = status_dist.get(s_code, 0) + 1

        # Metrics calculation
        if total_successful > 0:
            pages_with_schema = [p for p in successful_pages if p.get("has_schema")]
            schema_coverage_pct = round((len(pages_with_schema) / total_successful) * 100, 1)
            avg_word_count = round(sum(p.get("word_count", 0) for p in successful_pages) / total_successful, 1)
            avg_latency_ms = round(sum(p.get("latency_ms", 0.0) for p in pages) / max(1, total_crawled), 1)
        else:
            schema_coverage_pct = 0.0
            avg_word_count = 0.0
            avg_latency_ms = round(sum(p.get("latency_ms", 0.0) for p in pages) / max(1, total_crawled), 1) if pages else 0.0

        # Missing element diagnostics
        missing_schema_urls = [p["url"] for p in successful_pages if not p.get("has_schema")]
        missing_meta_desc_urls = [p["url"] for p in successful_pages if not p.get("description")]
        missing_h1_urls = [p["url"] for p in successful_pages if p.get("h1_count", 0) == 0]
        thin_content_urls = [p["url"] for p in successful_pages if p.get("word_count", 0) < 150]

        # Overall Site AEO Health Score (0-100)
        # 1. Schema Coverage (30 pts)
        score_schema = (schema_coverage_pct / 100.0) * 30.0
        # 2. AI Manifests & Root Assets (25 pts)
        score_manifests = 0.0
        if self.root_assets["llms_txt"]["exists"]:
            score_manifests += 12.0
        if self.root_assets["robots_txt"]["exists"]:
            score_manifests += 5.0
        if self.root_assets["ai_txt"]["exists"]:
            score_manifests += 4.0
        if self.root_assets["sitemap_xml"]["exists"]:
            score_manifests += 4.0
        # 3. Content Depth & Meta Quality (25 pts)
        score_content = 0.0
        if total_successful > 0:
            meta_ratio = (total_successful - len(missing_meta_desc_urls)) / total_successful
            h1_ratio = (total_successful - len(missing_h1_urls)) / total_successful
            depth_ratio = (total_successful - len(thin_content_urls)) / total_successful
            score_content = (meta_ratio * 8.0) + (h1_ratio * 8.0) + (depth_ratio * 9.0)
        # 4. Latency & HTTP Health (20 pts)
        score_health = 0.0
        if total_crawled > 0:
            success_ratio = total_successful / total_crawled
            score_health += success_ratio * 12.0
            if avg_latency_ms <= 300.0:
                score_health += 8.0
            elif avg_latency_ms <= 800.0:
                score_health += 5.0
            elif avg_latency_ms <= 2000.0:
                score_health += 2.0

        overall_aeo_score = min(100.0, round(score_schema + score_manifests + score_content + score_health, 1))

        # Recommendations
        recommendations: List[Dict[str, Any]] = []
        if schema_coverage_pct < 100.0:
            recommendations.append({
                "priority": "HIGH",
                "category": "Schema.org",
                "issue": f"{len(missing_schema_urls)} pages missing Schema.org structured data ({schema_coverage_pct}% coverage)",
                "fix": "Inject connected Schema.org @graph JSON-LD into all missing pages."
            })
        if not self.root_assets["llms_txt"]["exists"]:
            recommendations.append({
                "priority": "HIGH",
                "category": "Machine Discovery",
                "issue": "Missing root llms.txt manifest",
                "fix": "Generate and place llms.txt at the site root."
            })
        if missing_meta_desc_urls:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Metadata",
                "issue": f"{len(missing_meta_desc_urls)} pages missing meta description",
                "fix": "Add descriptive meta tags for standalone AI snippet indexing."
            })
        if thin_content_urls:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Content Depth",
                "issue": f"{len(thin_content_urls)} pages with thin content (<150 words)",
                "fix": "Expand thin pages with FAQ Q&A blocks and clear feature definitions."
            })

        return {
            "target": self.initial_target,
            "origin": self.base_origin,
            "sitemap_detected": self.sitemap_detected,
            "total_indexed_urls": len(self.discovered_urls) if self.discovered_urls else len(self.sitemap_urls_found),
            "pages_crawled_count": total_crawled,
            "successful_pages_count": total_successful,
            "schema_coverage_pct": schema_coverage_pct,
            "avg_word_count": avg_word_count,
            "avg_latency_ms": avg_latency_ms,
            "overall_aeo_health_score": overall_aeo_score,
            "status_code_distribution": status_dist,
            "root_assets": {k: {"exists": v["exists"], "status": v["status"]} for k, v in self.root_assets.items()},
            "missing_elements": {
                "pages_missing_schema": missing_schema_urls,
                "pages_missing_meta_description": missing_meta_desc_urls,
                "pages_missing_h1": missing_h1_urls,
                "pages_thin_content": thin_content_urls
            },
            "pages": pages,
            "recommendations": recommendations
        }


def crawl_sitemap_or_site(sitemap_url_or_domain: str, max_pages: int = 15, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Primary API entrypoint:
    Crawls a sitemap XML URL or falls back to domain link crawling up to `max_pages`,
    running lightweight AEO audits across all pages and computing site-wide coverage metrics.

    Zero external runtime dependencies.
    """
    crawler = SitemapCrawler(
        target_url_or_domain=sitemap_url_or_domain,
        max_pages=max_pages,
        timeout=timeout
    )
    return crawler.crawl_and_audit()

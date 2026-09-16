"""
Live Site AEO/GEO Crawler, Multi-Page Auditor, and AI Distribution Intelligence Engine.
Fetches live URLs, sitemaps, robots.txt, llms.txt, and subpages to compute accurate
AEO Readiness scores, AI bot compatibility metrics, and targeted backlink strategies.
Zero external runtime dependencies (Python standard library urllib, json, html.parser).
"""

import sys
import os
import re
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Set, Tuple

from .extractor import extract_metadata_from_html
from .validator import validate_schema_jsonld_dict, AEODiagnosticReport


class HTMLLinkExtractor(HTMLParser):
    """Extracts internal links from HTML for crawler discovery."""

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
                    if href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:") or href.startswith("tel:"):
                        continue
                    full_url = urllib.parse.urljoin(self.base_url, href)
                    parsed_full = urllib.parse.urlparse(full_url)

                    # Only HTTP/HTTPS
                    if parsed_full.scheme not in ("http", "https"):
                        continue

                    # Strip fragment and query for crawling
                    clean_url = urllib.parse.urlunparse((
                        parsed_full.scheme,
                        parsed_full.netloc,
                        parsed_full.path,
                        "", "", ""
                    ))

                    if parsed_full.netloc == self.parsed_base.netloc:
                        self.internal_links.add(clean_url)
                    else:
                        self.external_links.add(clean_url)


class LiveAEOScanner:
    """
    High-efficiency multi-page live website auditor and AEO/GEO strategy analyzer.
    """

    USER_AGENT = "Mozilla/5.0 (compatible; AEOGraphEngine/1.0; +https://github.com/1nc0gn30/aeo-graph-engine)"

    def __init__(self, target_url: str, max_pages: int = 5, timeout: int = 8):
        # Normalize target URL
        if not target_url.startswith("http://") and not target_url.startswith("https://"):
            target_url = "https://" + target_url

        self.target_url = target_url.rstrip("/")
        self.parsed_root = urllib.parse.urlparse(self.target_url)
        self.base_origin = f"{self.parsed_root.scheme}://{self.parsed_root.netloc}"
        self.max_pages = max_pages
        self.timeout = timeout

        self.crawled_pages: Dict[str, Dict[str, Any]] = {}
        self.root_assets: Dict[str, Dict[str, Any]] = {
            "robots_txt": {"exists": False, "status": 0, "content": ""},
            "llms_txt": {"exists": False, "status": 0, "content": ""},
            "llms_full_txt": {"exists": False, "status": 0, "content": ""},
            "ai_txt": {"exists": False, "status": 0, "content": ""},
            "sitemap_xml": {"exists": False, "status": 0, "content": ""},
            "schema_graph_json": {"exists": False, "status": 0, "content": ""}
        }

    def _fetch_url(self, url: str) -> Tuple[int, str, Optional[str]]:
        """Fetches a URL safely with timeouts and redirects."""
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": "text/html,application/xhtml+xml,application/xml,text/plain;q=0.9,*/*;q=0.8"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                status = response.status
                content_type = response.headers.get("Content-Type", "")
                raw_bytes = response.read(2_000_000) # Read up to 2MB max
                text = raw_bytes.decode("utf-8", errors="replace")
                return status, text, content_type
        except urllib.error.HTTPError as e:
            return e.code, "", None
        except Exception:
            return 0, "", None

    def scan_root_assets(self) -> None:
        """Inspects root machine discovery assets (robots.txt, llms.txt, ai.txt, sitemap.xml)."""
        asset_endpoints = {
            "robots_txt": f"{self.base_origin}/robots.txt",
            "llms_txt": f"{self.base_origin}/llms.txt",
            "llms_full_txt": f"{self.base_origin}/llms-full.txt",
            "ai_txt": f"{self.base_origin}/ai.txt",
            "sitemap_xml": f"{self.base_origin}/sitemap.xml",
            "schema_graph_json": f"{self.base_origin}/schema-graph.json"
        }

        for key, ep in asset_endpoints.items():
            status, text, ctype = self._fetch_url(ep)
            if status == 200 and text.strip():
                self.root_assets[key]["exists"] = True
                self.root_assets[key]["status"] = status
                self.root_assets[key]["content"] = text
            else:
                self.root_assets[key]["status"] = status

    def extract_sitemap_urls(self) -> List[str]:
        """Extracts URLs listed in sitemap.xml if available."""
        sitemap_content = self.root_assets["sitemap_xml"]["content"]
        if not sitemap_content:
            return []
        locs = re.findall(r'<loc>(https?://[^<]+)</loc>', sitemap_content, re.IGNORECASE)
        # Filter to same domain
        internal_locs = [
            loc.strip() for loc in locs
            if urllib.parse.urlparse(loc.strip()).netloc == self.parsed_root.netloc
        ]
        return internal_locs

    def crawl_site(self) -> None:
        """Crawls site up to max_pages discovering pages and extracting deep metrics."""
        # 1. Scan root discovery files first
        self.scan_root_assets()

        # 2. Seed URLs queue
        queue: List[str] = [self.target_url]
        sitemap_urls = self.extract_sitemap_urls()
        for su in sitemap_urls:
            if su not in queue:
                queue.append(su)

        visited: Set[str] = set()

        while queue and len(visited) < self.max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue

            visited.add(current_url)
            status, html_text, ctype = self._fetch_url(current_url)

            if status != 200 or not html_text:
                self.crawled_pages[current_url] = {
                    "url": current_url,
                    "status": status,
                    "error": f"HTTP status {status}" if status != 200 else "Empty response"
                }
                continue

            # Extract metadata and schemas
            meta = extract_metadata_from_html(html_text)

            # Discover internal links
            link_parser = HTMLLinkExtractor(current_url)
            try:
                link_parser.feed(html_text)
            except Exception:
                pass

            for new_link in link_parser.internal_links:
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

            self.crawled_pages[current_url] = {
                "url": current_url,
                "status": status,
                "title": meta.get("site_name") or meta.get("tagline"),
                "tagline": meta.get("tagline"),
                "description": meta.get("description"),
                "canonical_url": meta.get("canonical_url"),
                "headings_count": len(meta.get("headings", [])),
                "headings": meta.get("headings", [])[:10],
                "word_count": words,
                "schema_count": len(schemas_found),
                "schemas": schemas_found,
                "schema_score": round(schema_report.score, 1),
                "schema_errors": schema_report.errors,
                "schema_warnings": schema_report.warnings,
                "internal_links_count": len(link_parser.internal_links),
                "external_links_count": len(link_parser.external_links)
            }

    def compute_audit_scores(self) -> Dict[str, Any]:
        """Calculates precise scores matching current 2026 AEO search engine standards."""
        if not self.crawled_pages:
            self.crawl_site()

        total_pages = len(self.crawled_pages)
        successful_pages = [p for p in self.crawled_pages.values() if p.get("status") == 200]

        # 1. Schema.org Linked Data Score (0 - 25 pts)
        schema_pts = 0.0
        pages_with_schema = [p for p in successful_pages if p.get("schema_count", 0) > 0]
        if pages_with_schema:
            ratio = len(pages_with_schema) / max(1, len(successful_pages))
            schema_pts += ratio * 15.0 # Up to 15 pts for schema coverage

            # Bonus for @graph connected structures and FAQPage
            for p in pages_with_schema:
                for sch in p.get("schemas", []):
                    if isinstance(sch, dict):
                        if "@graph" in sch:
                            schema_pts += 5.0
                            break
                        if "FAQPage" in str(sch):
                            schema_pts += 5.0
                            break
        schema_pts = min(25.0, schema_pts)

        # 2. llms.txt & Machine Discovery Score (0 - 25 pts)
        llms_pts = 0.0
        if self.root_assets["llms_txt"]["exists"]:
            llms_pts += 15.0
            content = self.root_assets["llms_txt"]["content"]
            if ">" in content and "[" in content:
                llms_pts += 5.0
        if self.root_assets["llms_full_txt"]["exists"]:
            llms_pts += 5.0
        llms_pts = min(25.0, llms_pts)

        # 3. AI Search Bot Governance (0 - 20 pts)
        crawler_pts = 0.0
        robots_content = self.root_assets["robots_txt"]["content"].lower()
        if self.root_assets["robots_txt"]["exists"]:
            crawler_pts += 5.0
            if "gptbot" in robots_content:
                crawler_pts += 4.0
            if "perplexitybot" in robots_content:
                crawler_pts += 4.0
            if "claudebot" in robots_content:
                crawler_pts += 4.0
            if "applebot" in robots_content or "google-extended" in robots_content:
                crawler_pts += 3.0
        if self.root_assets["ai_txt"]["exists"]:
            crawler_pts += 5.0
        crawler_pts = min(20.0, crawler_pts)

        # 4. Semantic Content & Grounding (0 - 15 pts)
        semantic_pts = 0.0
        for p in successful_pages:
            if p.get("headings_count", 0) >= 3:
                semantic_pts += 5.0 / max(1, len(successful_pages))
            if p.get("description"):
                semantic_pts += 5.0 / max(1, len(successful_pages))
            if p.get("word_count", 0) >= 200:
                semantic_pts += 5.0 / max(1, len(successful_pages))
        semantic_pts = min(15.0, semantic_pts)

        # 5. Technical SEO & Discovery Foundation (0 - 15 pts)
        tech_pts = 0.0
        if self.parsed_root.scheme == "https":
            tech_pts += 5.0
        if self.root_assets["sitemap_xml"]["exists"]:
            tech_pts += 5.0
        canonical_count = sum(1 for p in successful_pages if p.get("canonical_url"))
        if canonical_count > 0:
            tech_pts += 5.0 * (canonical_count / max(1, len(successful_pages)))
        tech_pts = min(15.0, tech_pts)

        total_score = round(schema_pts + llms_pts + crawler_pts + semantic_pts + tech_pts, 1)

        # AI Bot Compatibility matrix
        bot_compatibility = {
            "ChatGPT (GPTBot)": {
                "allowed": "gptbot" in robots_content or (not robots_content and self.root_assets["robots_txt"]["status"] != 403),
                "has_qa_schema": any("FAQ" in str(p.get("schemas", [])) for p in successful_pages),
                "indexed_via_llms": self.root_assets["llms_txt"]["exists"]
            },
            "Perplexity AI (PerplexityBot)": {
                "allowed": "perplexitybot" in robots_content or (not robots_content),
                "has_deep_index": self.root_assets["llms_full_txt"]["exists"] or self.root_assets["llms_txt"]["exists"],
                "has_graph": any("@graph" in str(p.get("schemas", [])) for p in successful_pages)
            },
            "Claude / Anthropic (ClaudeBot)": {
                "allowed": "claudebot" in robots_content or "anthropic-ai" in robots_content,
                "has_ai_policy": self.root_assets["ai_txt"]["exists"]
            },
            "Apple Intelligence (Applebot-Extended)": {
                "allowed": "applebot" in robots_content or (not robots_content),
                "has_app_schema": any("SoftwareApplication" in str(p.get("schemas", [])) or "Organization" in str(p.get("schemas", [])) for p in successful_pages)
            },
            "Google AI Overviews (Google-Extended)": {
                "allowed": "google-extended" in robots_content or (not robots_content),
                "has_linked_data": any(p.get("schema_count", 0) > 0 for p in successful_pages)
            }
        }

        # Determine Niche & Backlink Strategy
        detected_text = " ".join([p.get("title", "") + " " + p.get("description", "") for p in successful_pages]).lower()
        backlink_strategy = self._generate_distribution_and_backlink_strategy(detected_text)

        # Generate Actionable Fixes
        action_items = []
        if not self.root_assets["llms_txt"]["exists"]:
            action_items.append({
                "priority": "HIGH",
                "category": "Machine Discovery",
                "issue": "Missing llms.txt standard manifest",
                "fix": "Generate and place a standardized llms.txt at the root of your site (llmstxt.org specification) to allow ChatGPT & Perplexity to ingest docs in <50 tokens."
            })
        if not pages_with_schema:
            action_items.append({
                "priority": "CRITICAL",
                "category": "Knowledge Graph",
                "issue": "Zero Schema.org JSON-LD structured data detected",
                "fix": "Inject a connected Schema.org @graph (Organization, WebSite, App/Service, FAQPage) into your <head> to anchor entity authority in AI vector models."
            })
        if "gptbot" not in robots_content:
            action_items.append({
                "priority": "HIGH",
                "category": "Crawler Policies",
                "issue": "robots.txt lacks explicit permissions for modern AI bots",
                "fix": "Add explicit 'User-agent: GPTBot', 'User-agent: PerplexityBot', 'User-agent: ClaudeBot' directives allowing access."
            })
        if not self.root_assets["ai_txt"]["exists"]:
            action_items.append({
                "priority": "MEDIUM",
                "category": "AI Policy",
                "issue": "Missing ai.txt policy manifest",
                "fix": "Create an ai.txt manifest declaring canonical attribution format and citation permissions."
            })

        return {
            "target_url": self.target_url,
            "origin": self.base_origin,
            "overall_aeo_score": total_score,
            "status": "EXCELLENT" if total_score >= 85 else "GOOD" if total_score >= 65 else "NEEDS_OPTIMIZATION",
            "category_scores": {
                "schema_linked_data": {"score": round(schema_pts, 1), "max": 25.0},
                "llms_txt_machine_index": {"score": round(llms_pts, 1), "max": 25.0},
                "ai_crawler_governance": {"score": round(crawler_pts, 1), "max": 20.0},
                "semantic_content_grounding": {"score": round(semantic_pts, 1), "max": 15.0},
                "technical_seo_foundation": {"score": round(tech_pts, 1), "max": 15.0}
            },
            "root_assets": {k: {"exists": v["exists"], "status": v["status"]} for k, v in self.root_assets.items()},
            "pages_audited_count": len(self.crawled_pages),
            "pages": list(self.crawled_pages.values()),
            "ai_engine_compatibility": bot_compatibility,
            "action_items": action_items,
            "backlink_and_distribution_intelligence": backlink_strategy
        }

    def _generate_distribution_and_backlink_strategy(self, content_text: str) -> Dict[str, Any]:
        """
        Generates genuine, high-authority backlink, citation, and posting opportunities
        tailored to how AI search companies ingest training and retrieval data.
        """
        # Universal AI Citation Hubs
        universal_citation_hubs = [
            {
                "platform": "llmstxt.org Directory & Awesome-LLMS-Txt",
                "role": "Direct LLM Discovery",
                "action": "Submit your canonical /llms.txt URL to the community llms.txt registry for direct crawler seeding."
            },
            {
                "platform": "Wikidata & Wikipedia Entity Linking",
                "role": "Knowledge Graph Anchor",
                "action": "Create or link your brand / software entity on Wikidata. Google AI Overviews and ChatGPT rely heavily on Wikidata for disambiguation."
            },
            {
                "platform": "GitHub Official Organization & README",
                "role": "High-Weight Developer Index",
                "action": "Maintain an active GitHub repository with linked releases and clean README. Code repositories are heavily weighted by Claude, Cursor, and Perplexity."
            },
            {
                "platform": "Hugging Face Hub / Model & Dataset Cards",
                "role": "AI Research Ingestion",
                "action": "Publish model/dataset/space cards. Hugging Face is an authoritative domain indexed continuously by AI web crawlers."
            }
        ]

        # Domain Specific Channels
        niche_channels = []
        if "crypto" in content_text or "defi" in content_text or "solana" in content_text:
            niche_channels = [
                {"platform": "DefiLlama / CoinGecko", "action": "List protocol TVL, contracts, and canonical documentation for automated financial LLM lookups."},
                {"platform": "Farcaster / Crypto Twitter (X)", "action": "Post architectural breakdowns using markdown threads that get indexed by Perplexity Finance."},
                {"platform": "Ethresear.ch / Solana Forum", "action": "Publish technical design specifications linking back to your canonical documentation."}
            ]
        elif "security" in content_text or "osint" in content_text or "vault" in content_text:
            niche_channels = [
                {"platform": "Awesome-Security / Awesome-OSINT GitHub", "action": "Submit PR to curated Awesome lists; AI search treats these as primary index references."},
                {"platform": "Packet Storm / Exploit-DB / CVE", "action": "Reference security advisories and tooling whitepapers."},
                {"platform": "Hacker News (Show HN)", "action": "Post detailed technical launch story linking to your deep documentation."}
            ]
        else:
            niche_channels = [
                {"platform": "Product Hunt & Dev.to", "action": "Publish launch posts with exact technical architecture descriptions and canonical links."},
                {"platform": "Reddit (r/technology, r/programming, r/LocalLLaMA)", "action": "Share open-source tool implementations and benchmark results."},
                {"platform": "Crunchbase & Official Social Profiles", "action": "Ensure all company profiles link back to the canonical domain and are referenced in Schema 'sameAs'."}
            ]

        return {
            "ai_crawler_research_methods": {
                "OpenAI_ChatGPT_Search": "Combines live Bing search API results with direct fetches of root llms.txt, robots.txt, and FAQPage JSON-LD structures.",
                "Perplexity_AI": "Scans root sitemaps, indexes full-text deep research pages (llms-full.txt), and verifies factual claims against Wikidata and GitHub.",
                "Anthropic_Claude": "Relying on clean structured documentation, markdown formats without layout clutter, and explicit ai.txt citation directives.",
                "Google_Gemini_AI_Overviews": "Matches queries against the Google Knowledge Graph. Requires Schema.org @graph linking Organization to WebSite to Product."
            },
            "high_authority_citation_hubs": universal_citation_hubs,
            "vertical_specific_distribution": niche_channels
        }

"""
Competitor Benchmark & Comparative AEO/GEO Intelligence Engine.
Computes side-by-side AEO score comparisons, entity depth deltas,
AI crawler governance differences, keyword coverage, and actionable
strategic gaps to outperform competitors in generative search engines.

Zero external runtime dependencies (pure Python standard library).
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional, Set, Tuple, Union

from .scanner import LiveAEOScanner


# Standard English stop words for keyword extraction
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down",
    "during", "each", "few", "for", "from", "further", "had", "hadn't", "has",
    "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her",
    "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's",
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it",
    "it's", "its", "itself", "let's", "me", "more", "most", "mustn't", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other",
    "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't",
    "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "https", "http", "www", "com", "org", "net", "io",
    "page", "site", "website", "home", "get", "use", "using", "free", "best", "new"
}


def _extract_schema_types_recursive(obj: Any, collected: Set[str]) -> None:
    """Recursively traverses schema dictionaries and lists to gather all @type definitions."""
    if isinstance(obj, dict):
        if "@type" in obj:
            t = obj["@type"]
            if isinstance(t, str):
                collected.add(t.strip())
            elif isinstance(t, list):
                for item in t:
                    if isinstance(item, str):
                        collected.add(item.strip())
        if "@graph" in obj and isinstance(obj["@graph"], list):
            for child in obj["@graph"]:
                _extract_schema_types_recursive(child, collected)
        for k, v in obj.items():
            if k not in ("@type", "@graph"):
                _extract_schema_types_recursive(v, collected)
    elif isinstance(obj, list):
        for item in obj:
            _extract_schema_types_recursive(item, collected)


def _extract_all_schema_info(pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Extracts schema types, entity count, and graph structure from audited pages."""
    types: Set[str] = set()
    total_schemas = 0
    has_graph = False

    for p in pages:
        schemas = p.get("schemas", [])
        total_schemas += len(schemas)
        for s in schemas:
            if isinstance(s, dict):
                if "@graph" in s:
                    has_graph = True
                _extract_schema_types_recursive(s, types)

    return {
        "types": sorted(list(types)),
        "total_schemas": total_schemas,
        "has_graph": has_graph,
        "unique_types_count": len(types),
    }


def _extract_keywords_from_pages(pages: List[Dict[str, Any]], top_n: int = 20) -> List[Tuple[str, int]]:
    """Extracts high-frequency topical keywords from page titles, descriptions, and headings."""
    text_corpus = []
    for p in pages:
        text_corpus.append(str(p.get("title") or ""))
        text_corpus.append(str(p.get("tagline") or ""))
        text_corpus.append(str(p.get("description") or ""))
        for h in p.get("headings", []):
            text_corpus.append(str(h))

    full_text = " ".join(text_corpus).lower()
    # Match words of 3+ letters
    tokens = re.findall(r'\b[a-z]{3,}\b', full_text)
    
    freq: Dict[str, int] = {}
    for token in tokens:
        if token not in STOP_WORDS:
            freq[token] = freq.get(token, 0) + 1

    sorted_keywords = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return sorted_keywords[:top_n]


def _determine_winner(score_a: float, score_b: float, tolerance: float = 0.5) -> str:
    """Returns 'site_a', 'site_b', or 'tie' based on score delta."""
    if score_a > score_b + tolerance:
        return "site_a"
    if score_b > score_a + tolerance:
        return "site_b"
    return "tie"


class CompetitorBenchmark:
    """
    Computes rigorous side-by-side AEO benchmarks between two websites.
    """

    def __init__(
        self,
        url_a: str,
        url_b: str,
        scan_a: Optional[Dict[str, Any]] = None,
        scan_b: Optional[Dict[str, Any]] = None,
        max_pages: int = 5,
        timeout: int = 8
    ):
        self.url_a = url_a.strip()
        self.url_b = url_b.strip()
        self.max_pages = max_pages
        self.timeout = timeout

        self.scan_a = scan_a
        self.scan_b = scan_b

    def _ensure_scans(self) -> None:
        """Executes live scans if scan payloads were not provided."""
        if self.scan_a is None:
            scanner_a = LiveAEOScanner(self.url_a, max_pages=self.max_pages, timeout=self.timeout)
            self.scan_a = scanner_a.compute_audit_scores()

        if self.scan_b is None:
            scanner_b = LiveAEOScanner(self.url_b, max_pages=self.max_pages, timeout=self.timeout)
            self.scan_b = scanner_b.compute_audit_scores()

    def compare(self) -> Dict[str, Any]:
        """Runs full comparative audit and returns structured benchmark result."""
        self._ensure_scans()
        assert self.scan_a is not None
        assert self.scan_b is not None

        # 1. Overall Score & Category Scores
        score_a = float(self.scan_a.get("overall_aeo_score", 0.0))
        score_b = float(self.scan_b.get("overall_aeo_score", 0.0))
        score_delta = round(score_a - score_b, 1)
        overall_winner = _determine_winner(score_a, score_b)

        winner_url = self.url_a if overall_winner == "site_a" else (
            self.url_b if overall_winner == "site_b" else "Tie"
        )

        # Category comparisons
        cat_scores_a = self.scan_a.get("category_scores", {})
        cat_scores_b = self.scan_b.get("category_scores", {})
        all_cats = [
            "schema_linked_data",
            "llms_txt_machine_index",
            "ai_crawler_governance",
            "semantic_content_grounding",
            "technical_seo_foundation",
        ]

        category_comparison = {}
        for cat in all_cats:
            sa = float(cat_scores_a.get(cat, {}).get("score", 0.0))
            sb = float(cat_scores_b.get(cat, {}).get("score", 0.0))
            m = float(cat_scores_a.get(cat, {}).get("max", 25.0) or cat_scores_b.get(cat, {}).get("max", 25.0))
            d = round(sa - sb, 1)
            w = _determine_winner(sa, sb, tolerance=0.2)
            category_comparison[cat] = {
                "score_a": sa,
                "score_b": sb,
                "max": m,
                "delta": d,
                "winner": w,
            }

        # 2. Schema & Entity Depth Comparison
        pages_a = self.scan_a.get("pages", [])
        pages_b = self.scan_b.get("pages", [])
        schema_info_a = _extract_all_schema_info(pages_a)
        schema_info_b = _extract_all_schema_info(pages_b)

        types_set_a = set(schema_info_a["types"])
        types_set_b = set(schema_info_b["types"])
        shared_types = sorted(list(types_set_a.intersection(types_set_b)))
        unique_to_a = sorted(list(types_set_a - types_set_b))
        unique_to_b = sorted(list(types_set_b - types_set_a))

        schema_score_a = category_comparison.get("schema_linked_data", {}).get("score_a", 0.0)
        schema_score_b = category_comparison.get("schema_linked_data", {}).get("score_b", 0.0)
        winner_schema = _determine_winner(schema_score_a, schema_score_b)
        if winner_schema == "tie":
            winner_schema = _determine_winner(len(types_set_a), len(types_set_b), tolerance=0)

        schema_comparison = {
            "total_schemas_a": schema_info_a["total_schemas"],
            "total_schemas_b": schema_info_b["total_schemas"],
            "types_a": schema_info_a["types"],
            "types_b": schema_info_b["types"],
            "shared_types": shared_types,
            "unique_to_a": unique_to_a,
            "unique_to_b": unique_to_b,
            "missing_in_a": unique_to_b,
            "missing_in_b": unique_to_a,
            "has_graph_a": schema_info_a["has_graph"],
            "has_graph_b": schema_info_b["has_graph"],
            "winner": winner_schema,
        }

        # 3. Bot Accessibility Matrix Delta
        bots_a = self.scan_a.get("ai_engine_compatibility", {})
        bots_b = self.scan_b.get("ai_engine_compatibility", {})
        all_bot_names = sorted(list(set(bots_a.keys()).union(set(bots_b.keys()))))
        if not all_bot_names:
            all_bot_names = [
                "ChatGPT (GPTBot)",
                "Perplexity AI (PerplexityBot)",
                "Claude / Anthropic (ClaudeBot)",
                "Apple Intelligence (Applebot-Extended)",
                "Google AI Overviews (Google-Extended)",
            ]

        bot_matrix_rows = []
        allowed_count_a = 0
        allowed_count_b = 0
        bots_where_a_wins = []
        bots_where_b_wins = []

        for bot in all_bot_names:
            info_a = bots_a.get(bot, {})
            info_b = bots_b.get(bot, {})
            allow_a = bool(info_a.get("allowed", False))
            allow_b = bool(info_b.get("allowed", False))

            if allow_a:
                allowed_count_a += 1
            if allow_b:
                allowed_count_b += 1

            if allow_a and allow_b:
                status = "BOTH_ALLOWED"
                adv = "equal"
            elif not allow_a and not allow_b:
                status = "BOTH_BLOCKED"
                adv = "equal"
            elif allow_a and not allow_b:
                status = "A_ALLOWED_B_BLOCKED"
                adv = "site_a"
                bots_where_a_wins.append(bot)
            else:
                status = "B_ALLOWED_A_BLOCKED"
                adv = "site_b"
                bots_where_b_wins.append(bot)

            bot_matrix_rows.append({
                "bot_name": bot,
                "site_a_allowed": allow_a,
                "site_b_allowed": allow_b,
                "status": status,
                "advantage": adv,
                "features_a": {k: v for k, v in info_a.items() if k != "allowed"},
                "features_b": {k: v for k, v in info_b.items() if k != "allowed"},
            })

        winner_bot_access = _determine_winner(allowed_count_a, allowed_count_b, tolerance=0)
        bot_comparison = {
            "bots": bot_matrix_rows,
            "total_allowed_a": allowed_count_a,
            "total_allowed_b": allowed_count_b,
            "bots_where_a_wins": bots_where_a_wins,
            "bots_where_b_wins": bots_where_b_wins,
            "bots_blocked_on_a": [b["bot_name"] for b in bot_matrix_rows if not b["site_a_allowed"]],
            "bots_blocked_on_b": [b["bot_name"] for b in bot_matrix_rows if not b["site_b_allowed"]],
            "winner": winner_bot_access,
        }

        # 4. Manifests & Machine Discovery Comparison
        assets_a = self.scan_a.get("root_assets", {})
        assets_b = self.scan_b.get("root_assets", {})
        standard_assets = [
            "robots_txt",
            "llms_txt",
            "llms_full_txt",
            "ai_txt",
            "sitemap_xml",
            "schema_graph_json",
        ]

        manifest_rows = []
        manifest_count_a = 0
        manifest_count_b = 0
        missing_on_a = []
        missing_on_b = []

        for asset in standard_assets:
            ex_a = bool(assets_a.get(asset, {}).get("exists", False))
            ex_b = bool(assets_b.get(asset, {}).get("exists", False))

            if ex_a:
                manifest_count_a += 1
            else:
                missing_on_a.append(asset)

            if ex_b:
                manifest_count_b += 1
            else:
                missing_on_b.append(asset)

            if ex_a and ex_b:
                st = "BOTH_EXIST"
                adv = "equal"
            elif not ex_a and not ex_b:
                st = "BOTH_MISSING"
                adv = "equal"
            elif ex_a and not ex_b:
                st = "A_EXISTS_B_MISSING"
                adv = "site_a"
            else:
                st = "B_EXISTS_A_MISSING"
                adv = "site_b"

            manifest_rows.append({
                "asset": asset,
                "site_a_exists": ex_a,
                "site_b_exists": ex_b,
                "status": st,
                "advantage": adv,
            })

        winner_manifests = _determine_winner(manifest_count_a, manifest_count_b, tolerance=0)
        manifests_comparison = {
            "assets": manifest_rows,
            "manifests_count_a": manifest_count_a,
            "manifests_count_b": manifest_count_b,
            "missing_on_a": missing_on_a,
            "missing_on_b": missing_on_b,
            "winner": winner_manifests,
        }

        # 5. Content Density & Keywords Comparison
        words_a = sum(int(p.get("word_count", 0)) for p in pages_a)
        words_b = sum(int(p.get("word_count", 0)) for p in pages_b)
        count_pages_a = max(1, len(pages_a))
        count_pages_b = max(1, len(pages_b))
        avg_words_a = round(words_a / count_pages_a, 1)
        avg_words_b = round(words_b / count_pages_b, 1)
        headings_a = sum(int(p.get("headings_count", len(p.get("headings", [])))) for p in pages_a)
        headings_b = sum(int(p.get("headings_count", len(p.get("headings", [])))) for p in pages_b)

        top_kw_a = _extract_keywords_from_pages(pages_a, top_n=15)
        top_kw_b = _extract_keywords_from_pages(pages_b, top_n=15)

        kw_names_a = [k for k, _ in top_kw_a]
        kw_names_b = [k for k, _ in top_kw_b]
        shared_kw = [k for k in kw_names_a if k in kw_names_b]
        unique_kw_b = [k for k in kw_names_b if k not in kw_names_a]
        unique_kw_a = [k for k in kw_names_a if k not in kw_names_b]

        content_score_a = category_comparison.get("semantic_content_grounding", {}).get("score_a", 0.0)
        content_score_b = category_comparison.get("semantic_content_grounding", {}).get("score_b", 0.0)
        winner_content = _determine_winner(content_score_a + (avg_words_a / 100.0), content_score_b + (avg_words_b / 100.0), tolerance=0.5)

        content_comparison = {
            "total_words_a": words_a,
            "total_words_b": words_b,
            "avg_words_per_page_a": avg_words_a,
            "avg_words_per_page_b": avg_words_b,
            "headings_count_a": headings_a,
            "headings_count_b": headings_b,
            "top_keywords_a": top_kw_a,
            "top_keywords_b": top_kw_b,
            "shared_keywords": shared_kw,
            "keywords_unique_to_b": unique_kw_b,
            "keywords_unique_to_a": unique_kw_a,
            "winner": winner_content,
        }

        # 6. Citations / Grounding winner
        cit_score_a = (category_comparison.get("semantic_content_grounding", {}).get("score_a", 0.0) +
                       category_comparison.get("technical_seo_foundation", {}).get("score_a", 0.0))
        cit_score_b = (category_comparison.get("semantic_content_grounding", {}).get("score_b", 0.0) +
                       category_comparison.get("technical_seo_foundation", {}).get("score_b", 0.0))
        winner_citations = _determine_winner(cit_score_a, cit_score_b, tolerance=0.2)

        # Aggregate Category Winners
        category_winners = {
            "schema": winner_schema,
            "manifests": winner_manifests,
            "bot_access": winner_bot_access,
            "citations": winner_citations,
            "content": winner_content,
            "overall": overall_winner,
        }

        # 7. Actionable Strategic Takeaways
        takeaways = self._generate_strategic_takeaways(
            score_delta=score_delta,
            schema_comp=schema_comparison,
            bot_comp=bot_comparison,
            manifest_comp=manifests_comparison,
            content_comp=content_comparison,
            category_comp=category_comparison,
        )

        return {
            "site_a": {
                "url": self.url_a,
                "origin": self.scan_a.get("origin", self.url_a),
                "overall_score": score_a,
                "status": self.scan_a.get("status", "UNKNOWN"),
                "pages_audited": len(pages_a),
            },
            "site_b": {
                "url": self.url_b,
                "origin": self.scan_b.get("origin", self.url_b),
                "overall_score": score_b,
                "status": self.scan_b.get("status", "UNKNOWN"),
                "pages_audited": len(pages_b),
            },
            "summary": {
                "score_a": score_a,
                "score_b": score_b,
                "score_delta": score_delta,
                "overall_winner": overall_winner,
                "overall_winner_url": winner_url,
                "lead_description": (
                    f"Site A leads competitor by +{score_delta} points" if score_delta > 0
                    else f"Site A trails competitor by {abs(score_delta)} points" if score_delta < 0
                    else "Both sites are tied in overall AEO readiness"
                ),
            },
            "category_scores": category_comparison,
            "category_winners": category_winners,
            "schema_comparison": schema_comparison,
            "bot_matrix_comparison": bot_comparison,
            "manifests_comparison": manifests_comparison,
            "content_comparison": content_comparison,
            "takeaways": takeaways,
            "raw_scan_a": self.scan_a,
            "raw_scan_b": self.scan_b,
        }

    def _generate_strategic_takeaways(
        self,
        score_delta: float,
        schema_comp: Dict[str, Any],
        bot_comp: Dict[str, Any],
        manifest_comp: Dict[str, Any],
        content_comp: Dict[str, Any],
        category_comp: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Synthesizes high-impact strategic actions for Site A to beat or extend lead against Site B."""
        takeaways: List[Dict[str, Any]] = []

        # 1. Schema gaps
        missing_schemas = schema_comp.get("missing_in_a", [])
        if missing_schemas:
            types_str = ", ".join(missing_schemas[:4])
            takeaways.append({
                "priority": "CRITICAL",
                "category": "Schema & Knowledge Graph",
                "competitor_advantage": f"Competitor implements structured entities you lack: [{types_str}].",
                "action": f"Inject Schema.org @graph JSON-LD defining {types_str} to establish entity parity in LLM vector indices.",
                "impact": "+10 to +20 pts score increase & inclusion in AI summary carousels.",
            })

        if not schema_comp.get("has_graph_a") and schema_comp.get("has_graph_b"):
            takeaways.append({
                "priority": "HIGH",
                "category": "Knowledge Graph",
                "competitor_advantage": "Competitor connects entities into a single cohesive @graph structure.",
                "action": "Consolidate isolated JSON-LD script tags into a unified @graph array linking WebSite, Organization, and Software/Service.",
                "impact": "Eliminates entity ambiguity in Google AI Overviews and Claude citation pipelines.",
            })

        # 2. Manifest gaps
        if "llms_txt" in manifest_comp.get("missing_on_a", []) and not ("llms_txt" in manifest_comp.get("missing_on_b", [])):
            takeaways.append({
                "priority": "CRITICAL",
                "category": "Machine Discovery",
                "competitor_advantage": "Competitor provides /llms.txt for sub-50ms ingestion by ChatGPT and Perplexity.",
                "action": "Deploy a standardized /llms.txt manifest following the llmstxt.org specification.",
                "impact": "+15 pts AEO score & immediate indexing in Perplexity/ChatGPT deep search.",
            })
        elif "llms_full_txt" in manifest_comp.get("missing_on_a", []) and not ("llms_full_txt" in manifest_comp.get("missing_on_b", [])):
            takeaways.append({
                "priority": "HIGH",
                "category": "Deep Research Grounding",
                "competitor_advantage": "Competitor serves a complete knowledge corpus via /llms-full.txt.",
                "action": "Generate and publish /llms-full.txt to serve full-text documentation to AI reasoning models (o3, Gemini Pro).",
                "impact": "+5 pts AEO score and rich citations in complex multi-step user prompts.",
            })

        if "ai_txt" in manifest_comp.get("missing_on_a", []):
            takeaways.append({
                "priority": "MEDIUM",
                "category": "AI Attribution Policy",
                "competitor_advantage": "Missing formal /ai.txt permissions manifest.",
                "action": "Deploy an /ai.txt manifest specifying canonical attribution requirements and training license terms.",
                "impact": "+5 pts score and protected brand attribution across generative responses.",
            })

        # 3. Crawler governance gaps
        blocked_bots = bot_comp.get("bots_blocked_on_a", [])
        if blocked_bots:
            bots_str = ", ".join(blocked_bots[:3])
            takeaways.append({
                "priority": "CRITICAL",
                "category": "AI Crawler Governance",
                "competitor_advantage": f"Your site blocks key AI bots ({bots_str}) that competitor allows.",
                "action": f"Update robots.txt to explicitly allow User-agents: {bots_str} without restrictions on public docs.",
                "impact": "Restores live retrieval visibility in ChatGPT Search, Perplexity, and Apple Intelligence.",
            })

        # 4. Content & Keyword gaps
        unique_b_kw = content_comp.get("keywords_unique_to_b", [])
        if unique_b_kw:
            kw_sample = ", ".join(f"'{k}'" for k in unique_b_kw[:5])
            takeaways.append({
                "priority": "HIGH",
                "category": "Topical Semantic Coverage",
                "competitor_advantage": f"Competitor covers high-frequency semantic entities you omit: {kw_sample}.",
                "action": f"Incorporate contextual sections addressing {kw_sample} into your main documentation and FAQ schema.",
                "impact": "Closes embedding space gap during vector similarity retrieval.",
            })

        avg_a = content_comp.get("avg_words_per_page_a", 0)
        avg_b = content_comp.get("avg_words_per_page_b", 0)
        if avg_b > avg_a * 1.4 and avg_b > 300:
            takeaways.append({
                "priority": "MEDIUM",
                "category": "Content Depth",
                "competitor_advantage": f"Competitor pages average {avg_b} words vs your {avg_a} words per page.",
                "action": "Enrich key landing pages with detailed technical explanations, FAQ sections, and architecture overviews.",
                "impact": "Increases chunk density for LLM RAG pipelines.",
            })

        # 5. Winning site positive advice
        if score_delta >= 10.0:
            takeaways.append({
                "priority": "MAINTAIN",
                "category": "Competitive Advantage",
                "competitor_advantage": "Site A holds a dominant AEO readiness lead over competitor.",
                "action": "Maintain lead by syncing /llms-full.txt with code releases and submitting to the official llmstxt.org registry.",
                "impact": "Solidifies long-term authoritative domain grounding in AI search engines.",
            })
        elif not takeaways:
            takeaways.append({
                "priority": "MEDIUM",
                "category": "Continuous Optimization",
                "competitor_advantage": "Both sites have similar baseline AEO configurations.",
                "action": "Expand structured schema coverage with FAQPage and HowTo entities, and secure Wikidata entity links.",
                "impact": "Breaks tie to gain primary citation placement in Google AI Overviews.",
            })

        return takeaways


def compare_sites(
    url_a: str,
    url_b: str,
    scan_a: Optional[Dict[str, Any]] = None,
    scan_b: Optional[Dict[str, Any]] = None,
    max_pages: int = 5,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    Public entrypoint to compare two websites for AEO/GEO readiness and generative search dominance.

    Args:
        url_a: Primary target website URL.
        url_b: Competitor website URL.
        scan_a: Optional pre-computed scan dictionary for URL A (avoids network requests).
        scan_b: Optional pre-computed scan dictionary for URL B (avoids network requests).
        max_pages: Crawl depth limit if performing live scan.
        timeout: Network request timeout in seconds.

    Returns:
        Structured dictionary containing side-by-side scores, category winners,
        schema diffs, bot matrix deltas, keyword coverage, and strategic takeaways.
    """
    bench = CompetitorBenchmark(
        url_a=url_a,
        url_b=url_b,
        scan_a=scan_a,
        scan_b=scan_b,
        max_pages=max_pages,
        timeout=timeout,
    )
    return bench.compare()

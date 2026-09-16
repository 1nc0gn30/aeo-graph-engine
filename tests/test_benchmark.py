"""
Unit tests for Competitor Benchmark Engine (aeo_graph_engine.benchmark).
"""

import pytest
from aeo_graph_engine.benchmark import (
    compare_sites,
    CompetitorBenchmark,
    _extract_all_schema_info,
    _extract_keywords_from_pages,
    _determine_winner,
)


def create_sample_scan_a():
    return {
        "target_url": "https://alpha.example.com",
        "origin": "https://alpha.example.com",
        "overall_aeo_score": 88.5,
        "status": "EXCELLENT",
        "category_scores": {
            "schema_linked_data": {"score": 24.0, "max": 25.0},
            "llms_txt_machine_index": {"score": 25.0, "max": 25.0},
            "ai_crawler_governance": {"score": 18.0, "max": 20.0},
            "semantic_content_grounding": {"score": 11.5, "max": 15.0},
            "technical_seo_foundation": {"score": 10.0, "max": 15.0},
        },
        "root_assets": {
            "robots_txt": {"exists": True, "status": 200},
            "llms_txt": {"exists": True, "status": 200},
            "llms_full_txt": {"exists": True, "status": 200},
            "ai_txt": {"exists": True, "status": 200},
            "sitemap_xml": {"exists": True, "status": 200},
            "schema_graph_json": {"exists": True, "status": 200},
        },
        "pages_audited_count": 2,
        "pages": [
            {
                "url": "https://alpha.example.com/",
                "status": 200,
                "title": "Alpha Platform - NextGen AI Engine",
                "tagline": "Autonomous Search Optimization",
                "description": "Alpha platform provides high performance developer tools and machine learning APIs.",
                "headings": ["Features", "Quickstart", "API Reference", "Benchmarks"],
                "headings_count": 4,
                "word_count": 850,
                "schemas": [
                    {
                        "@context": "https://schema.org",
                        "@graph": [
                            {"@type": "Organization", "name": "Alpha Corp"},
                            {"@type": "WebSite", "name": "Alpha Portal"},
                            {"@type": "SoftwareApplication", "name": "Alpha Engine"},
                            {"@type": "FAQPage", "mainEntity": []},
                        ],
                    }
                ],
            },
            {
                "url": "https://alpha.example.com/docs",
                "status": 200,
                "title": "Alpha Documentation",
                "tagline": "Architecture Guide",
                "description": "Comprehensive developer documentation and integration tutorials.",
                "headings": ["Installation", "Authentication", "SDK Usage"],
                "headings_count": 3,
                "word_count": 1200,
                "schemas": [],
            },
        ],
        "ai_engine_compatibility": {
            "ChatGPT (GPTBot)": {"allowed": True, "has_qa_schema": True, "indexed_via_llms": True},
            "Perplexity AI (PerplexityBot)": {"allowed": True, "has_deep_index": True, "has_graph": True},
            "Claude / Anthropic (ClaudeBot)": {"allowed": True, "has_ai_policy": True},
            "Apple Intelligence (Applebot-Extended)": {"allowed": True, "has_app_schema": True},
            "Google AI Overviews (Google-Extended)": {"allowed": True, "has_linked_data": True},
        },
        "action_items": [],
        "backlink_and_distribution_intelligence": {
            "high_authority_citation_hubs": [
                {"platform": "llmstxt.org", "role": "Discovery", "action": "Submit URL"}
            ]
        },
    }


def create_sample_scan_b():
    return {
        "target_url": "https://beta.competitor.com",
        "origin": "https://beta.competitor.com",
        "overall_aeo_score": 45.0,
        "status": "NEEDS_OPTIMIZATION",
        "category_scores": {
            "schema_linked_data": {"score": 5.0, "max": 25.0},
            "llms_txt_machine_index": {"score": 0.0, "max": 25.0},
            "ai_crawler_governance": {"score": 10.0, "max": 20.0},
            "semantic_content_grounding": {"score": 15.0, "max": 15.0},
            "technical_seo_foundation": {"score": 15.0, "max": 15.0},
        },
        "root_assets": {
            "robots_txt": {"exists": True, "status": 200},
            "llms_txt": {"exists": False, "status": 404},
            "llms_full_txt": {"exists": False, "status": 404},
            "ai_txt": {"exists": False, "status": 404},
            "sitemap_xml": {"exists": True, "status": 200},
            "schema_graph_json": {"exists": False, "status": 404},
        },
        "pages_audited_count": 1,
        "pages": [
            {
                "url": "https://beta.competitor.com/",
                "status": 200,
                "title": "Beta Competitor - Legacy Analytics",
                "tagline": "Traditional Web Analytics",
                "description": "Beta competitor delivers enterprise analytics metrics, tracking, dashboards, and reporting.",
                "headings": ["Overview", "Pricing", "Enterprise Solutions", "Cloud Integration"],
                "headings_count": 4,
                "word_count": 1600,
                "schemas": [
                    {
                        "@context": "https://schema.org",
                        "@type": "WebPage",
                        "name": "Beta Home",
                    }
                ],
            }
        ],
        "ai_engine_compatibility": {
            "ChatGPT (GPTBot)": {"allowed": False, "has_qa_schema": False, "indexed_via_llms": False},
            "Perplexity AI (PerplexityBot)": {"allowed": False, "has_deep_index": False, "has_graph": False},
            "Claude / Anthropic (ClaudeBot)": {"allowed": True, "has_ai_policy": False},
            "Apple Intelligence (Applebot-Extended)": {"allowed": True, "has_app_schema": False},
            "Google AI Overviews (Google-Extended)": {"allowed": True, "has_linked_data": True},
        },
        "action_items": [
            {"priority": "CRITICAL", "category": "Discovery", "issue": "Missing llms.txt", "fix": "Add llms.txt"}
        ],
    }


def test_compare_sites_score_and_delta():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)

    assert res["summary"]["score_a"] == 88.5
    assert res["summary"]["score_b"] == 45.0
    assert res["summary"]["score_delta"] == 43.5
    assert res["summary"]["overall_winner"] == "site_a"
    assert res["summary"]["overall_winner_url"] == "https://alpha.example.com"
    assert "leads" in res["summary"]["lead_description"].lower()


def test_category_winners():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)

    cat_winners = res["category_winners"]
    assert cat_winners["schema"] == "site_a"
    assert cat_winners["manifests"] == "site_a"
    assert cat_winners["bot_access"] == "site_a"
    assert cat_winners["citations"] == "site_b"
    assert cat_winners["overall"] == "site_a"


def test_schema_comparison_entity_depth():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)
    schema_comp = res["schema_comparison"]

    assert "SoftwareApplication" in schema_comp["types_a"]
    assert "Organization" in schema_comp["types_a"]
    assert "FAQPage" in schema_comp["types_a"]
    assert "WebPage" in schema_comp["types_b"]

    assert "SoftwareApplication" in schema_comp["unique_to_a"]
    assert "WebPage" in schema_comp["unique_to_b"]
    assert "WebPage" in schema_comp["missing_in_a"]

    assert schema_comp["has_graph_a"] is True
    assert schema_comp["has_graph_b"] is False
    assert schema_comp["winner"] == "site_a"


def test_bot_accessibility_matrix_delta():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)
    bot_comp = res["bot_matrix_comparison"]

    assert bot_comp["total_allowed_a"] == 5
    assert bot_comp["total_allowed_b"] == 3
    assert bot_comp["winner"] == "site_a"
    assert "ChatGPT (GPTBot)" in bot_comp["bots_where_a_wins"]
    assert "Perplexity AI (PerplexityBot)" in bot_comp["bots_where_a_wins"]
    assert len(bot_comp["bots_blocked_on_b"]) == 2


def test_manifests_comparison():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)
    manifest_comp = res["manifests_comparison"]

    assert manifest_comp["manifests_count_a"] == 6
    assert manifest_comp["manifests_count_b"] == 2
    assert "llms_txt" in manifest_comp["missing_on_b"]
    assert "ai_txt" in manifest_comp["missing_on_b"]
    assert len(manifest_comp["missing_on_a"]) == 0
    assert manifest_comp["winner"] == "site_a"


def test_content_and_keyword_coverage():
    scan_a = create_sample_scan_a()
    scan_b = create_sample_scan_b()

    res = compare_sites("https://alpha.example.com", "https://beta.competitor.com", scan_a=scan_a, scan_b=scan_b)
    content_comp = res["content_comparison"]

    assert content_comp["total_words_a"] == 2050
    assert content_comp["total_words_b"] == 1600
    assert content_comp["headings_count_a"] == 7

    # Check extracted keywords
    top_kw_a = [k for k, _ in content_comp["top_keywords_a"]]
    top_kw_b = [k for k, _ in content_comp["top_keywords_b"]]

    assert "alpha" in top_kw_a
    assert "analytics" in top_kw_b or "enterprise" in top_kw_b


def test_actionable_takeaways_generation():
    # Test when Site A is trailing
    scan_a = create_sample_scan_b() # Lower score
    scan_b = create_sample_scan_a() # Higher score

    res = compare_sites("https://beta.competitor.com", "https://alpha.example.com", scan_a=scan_a, scan_b=scan_b)
    takeaways = res["takeaways"]

    assert len(takeaways) >= 2
    priorities = [t["priority"] for t in takeaways]
    assert "CRITICAL" in priorities or "HIGH" in priorities

    # Missing schema gap
    categories = [t["category"] for t in takeaways]
    assert any("Schema" in c or "Knowledge" in c for c in categories)


def test_helper_functions():
    assert _determine_winner(85.0, 70.0) == "site_a"
    assert _determine_winner(50.0, 80.0) == "site_b"
    assert _determine_winner(75.0, 75.2, tolerance=0.5) == "tie"

    pages = [
        {
            "title": "Machine Learning API Platform",
            "tagline": "AI Search Engine",
            "description": "Super fast deep retrieval engine",
            "headings": ["Installation", "Python SDK Guide"],
        }
    ]
    kw = _extract_keywords_from_pages(pages, top_n=5)
    kw_words = [w for w, _ in kw]
    assert "machine" in kw_words or "learning" in kw_words or "engine" in kw_words

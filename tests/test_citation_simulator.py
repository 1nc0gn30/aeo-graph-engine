"""
Unit tests for AEO AI Citation Simulator & Extractability Engine.
Tests HTML structural parsing, 5-pillar Citation Extractability scoring,
simulated AI answer previews across 5 engines, and optimization tips.
"""

import json
from unittest.mock import MagicMock, patch
import pytest

from aeo_graph_engine.citation_simulator import (
    HTMLStructureParser,
    extract_html_structure,
    calculate_citation_extractability_score,
    generate_engine_previews,
    generate_optimization_tips,
    simulate_ai_citation,
)


SAMPLE_RICH_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AEO Graph Engine — Next-Generation Answer Engine Optimization Platform</title>
    <meta name="description" content="AEO Graph Engine is an open-source system that generates connected Schema.org knowledge graphs and llms.txt manifests with 99.8% extraction accuracy.">
    <link rel="canonical" href="https://aeo-engine.dev/docs/intro">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@id": "https://aeo-engine.dev/#organization",
          "@type": "Organization",
          "name": "NullAI Technologies",
          "url": "https://aeo-engine.dev/"
        },
        {
          "@id": "https://aeo-engine.dev/#application",
          "@type": "SoftwareApplication",
          "name": "AEO Graph Engine",
          "applicationCategory": "DeveloperApplication",
          "softwareVersion": "v1.0.0",
          "operatingSystem": "Linux, macOS, Windows",
          "creator": {"@id": "https://aeo-engine.dev/#organization"}
        },
        {
          "@id": "https://aeo-engine.dev/#faq",
          "@type": "FAQPage",
          "mainEntity": [
            {
              "@type": "Question",
              "name": "What is AEO Graph Engine?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "AEO Graph Engine is a high-performance framework for Answer Engine Optimization and Schema.org knowledge graph compilation."
              }
            },
            {
              "@type": "Question",
              "name": "How fast does the engine compile schemas?",
              "acceptedAnswer": {
                "@type": "Answer",
                "text": "The engine compiles full entity graphs in under 5ms with zero external runtime dependencies."
              }
            }
          ]
        }
      ]
    }
    </script>
</head>
<body>
    <h1>AEO Graph Engine Documentation</h1>
    <p><strong>AEO Graph Engine</strong> is an open-source framework designed for <b>Answer Engine Optimization</b> and machine-readable data generation.</p>

    <h2>Core Architecture and Capabilities</h2>
    <p>The system provides automated Schema.org entity graph synthesis, yielding 10x faster indexing in modern AI search crawlers.</p>

    <ul>
        <li>Automated Schema.org @graph compilation with cross-entity references.</li>
        <li>Standards-compliant llms.txt and llms-full.txt generation.</li>
        <li>AI crawler governance with fine-grained robots.txt policies.</li>
    </ul>

    <h2>Performance Benchmarks</h2>
    <p>Benchmark tests demonstrate sub-5ms latency across 1000 iterations on standard hardware.</p>

    <table>
        <thead>
            <tr>
                <th>Metric</th>
                <th>AEO Graph Engine</th>
                <th>Legacy Tools</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Latency</td>
                <td>3.2ms</td>
                <td>45.0ms</td>
            </tr>
            <tr>
                <td>Memory Usage</td>
                <td>12MB</td>
                <td>120MB</td>
            </tr>
        </tbody>
    </table>

    <blockquote>
        AEO Graph Engine provides the definitive reference architecture for answer engine discovery.
    </blockquote>

    <pre><code class="language-python">
from aeo_graph_engine import generate_schema_graph
graph = generate_schema_graph()
    </code></pre>
</body>
</html>
"""

SAMPLE_POOR_HTML = """
<html>
<body>
    <div>Just some random text without structure.</div>
</body>
</html>
"""


class TestHTMLStructureParser:
    """Tests zero-dependency HTML parsing and component extraction."""

    def test_parses_headings_hierarchy(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        headings = structure["headings"]
        assert len(headings) >= 3
        assert headings[0]["level"] == 1
        assert headings[0]["text"] == "AEO Graph Engine Documentation"
        assert headings[1]["level"] == 2
        assert headings[1]["text"] == "Core Architecture and Capabilities"

    def test_parses_tables_and_headers(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        tables = structure["tables"]
        assert len(tables) == 1
        tbl = tables[0]
        assert tbl["headers"] == ["Metric", "AEO Graph Engine", "Legacy Tools"]
        assert len(tbl["rows"]) == 2
        assert tbl["rows"][0][0] == "Latency"

    def test_parses_lists_and_items(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        lists = structure["lists"]
        assert len(lists) == 1
        assert lists[0]["item_count"] == 3
        assert "Automated Schema.org" in lists[0]["items"][0]

    def test_parses_jsonld_schemas_and_faqs(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        schemas = structure["schemas"]
        assert len(schemas) == 1
        assert "@graph" in schemas[0]
        faq_blocks = structure["faq_blocks"]
        assert len(faq_blocks) >= 2
        assert faq_blocks[0]["question"] == "What is AEO Graph Engine?"

    def test_parses_bold_terms_and_blockquotes(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        assert len(structure["bold_terms"]) >= 1
        assert len(structure["blockquotes"]) == 1
        assert "definitive reference architecture" in structure["blockquotes"][0]["text"]


class TestCitationScoring:
    """Tests 5-pillar Citation Extractability scoring algorithm."""

    def test_rich_html_receives_high_score(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        result = calculate_citation_extractability_score(structure)

        assert result["total_score"] >= 75.0
        assert result["grade"] in ("A+", "A", "B")
        assert result["status"] in ("EXCELLENT", "VERY_STRONG", "STRONG")

        sub = result["sub_scores"]
        assert "heading_hierarchy" in sub
        assert "claim_clarity" in sub
        assert "entity_precision" in sub
        assert "structured_data_anchoring" in sub
        assert "quotability" in sub

        assert sub["heading_hierarchy"]["score"] > 10.0
        assert sub["structured_data_anchoring"]["score"] > 10.0
        assert sub["entity_precision"]["score"] > 10.0

    def test_poor_html_receives_low_score(self):
        structure = extract_html_structure(SAMPLE_POOR_HTML)
        result = calculate_citation_extractability_score(structure)

        assert result["total_score"] < 40.0
        assert result["grade"] in ("D", "F")
        assert result["status"] in ("NEEDS_OPTIMIZATION", "POOR")


class TestSimulatedEnginePreviews:
    """Tests simulated answer generation for all 5 major AI answer engines."""

    def test_generates_all_5_engine_previews(self):
        structure = extract_html_structure(SAMPLE_RICH_HTML)
        previews = generate_engine_previews(structure, query="What is AEO Graph Engine?")

        assert "perplexity" in previews
        assert "chatgpt" in previews
        assert "gemini" in previews
        assert "claude" in previews
        assert "apple_intelligence" in previews

        # Perplexity check
        pplx = previews["perplexity"]
        assert pplx["engine"] == "Perplexity AI"
        assert "[1]" in pplx["synthesis"]
        assert len(pplx["citations"]) >= 1
        assert pplx["citations"][0]["confidence_score"] >= 0.9

        # ChatGPT check
        gpt = previews["chatgpt"]
        assert gpt["engine"] == "ChatGPT Search"
        assert "source_pill" in gpt
        assert "attribution_format" in gpt

        # Gemini check
        gemini = previews["gemini"]
        assert gemini["engine"] == "Google Gemini / AI Overviews"
        assert "overview_box" in gemini
        assert "knowledge_graph_card" in gemini["overview_box"]

        # Claude check
        claude = previews["claude"]
        assert claude["engine"] == "Anthropic Claude"
        assert ">" in claude["synthesis"]

        # Apple Intelligence check
        apple = previews["apple_intelligence"]
        assert apple["engine"] == "Apple Intelligence"
        assert "summary_capsule" in apple
        assert len(apple["summary_capsule"]["key_facts"]) >= 1


class TestOptimizationTips:
    """Tests concrete, actionable recommendation generation."""

    def test_poor_html_triggers_comprehensive_tips(self):
        structure = extract_html_structure(SAMPLE_POOR_HTML)
        score_res = calculate_citation_extractability_score(structure)
        tips = generate_optimization_tips(score_res["sub_scores"], structure)

        assert len(tips) >= 3
        pillars = {t["pillar"] for t in tips}
        assert any("Heading" in p for p in pillars)
        assert any("Structured Data" in p for p in pillars)


class TestSimulateAICitationEntrypoint:
    """Tests primary simulate_ai_citation function with various inputs."""

    def test_simulate_with_raw_html(self):
        res = simulate_ai_citation(SAMPLE_RICH_HTML)
        assert res["source_type"] == "raw_html"
        assert res["citation_score"] > 50.0
        assert "simulated_citations" in res
        assert "optimization_tips" in res
        assert "key_extractable_quotes" in res

    def test_simulate_with_file_path(self, tmp_path):
        html_file = tmp_path / "page.html"
        html_file.write_text(SAMPLE_RICH_HTML, encoding="utf-8")

        res = simulate_ai_citation(str(html_file))
        assert res["source_type"] == "file"
        assert res["citation_score"] > 50.0

    @patch("urllib.request.urlopen")
    def test_simulate_with_mocked_url(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = SAMPLE_RICH_HTML.encode("utf-8")
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        res = simulate_ai_citation("https://aeo-engine.dev/docs")
        assert res["source_type"] == "url"
        assert res["source_location"] == "https://aeo-engine.dev/docs"
        assert res["citation_score"] > 50.0

    def test_custom_query_override(self):
        res = simulate_ai_citation(SAMPLE_RICH_HTML, query="How does AEO Graph Engine handle robots.txt?")
        assert res["target_query"] == "How does AEO Graph Engine handle robots.txt?"
        assert res["simulated_citations"]["perplexity"]["simulated_query"] == "How does AEO Graph Engine handle robots.txt?"

    def test_parses_details_summary_and_dt_dd_faqs(self):
        faq_html = """
        <html>
        <body>
            <details>
                <summary>Is this free?</summary>
                Yes, it is open source and free under MIT.
            </details>
            <dl>
                <dt>What languages are supported?</dt>
                <dd>Python, JavaScript, TypeScript, and Go.</dd>
            </dl>
        </body>
        </html>
        """
        structure = extract_html_structure(faq_html)
        assert len(structure["faq_blocks"]) == 2
        assert structure["faq_blocks"][0]["question"] == "Is this free?"
        assert structure["faq_blocks"][1]["question"] == "What languages are supported?"

    def test_handles_empty_and_broken_html(self):
        res = simulate_ai_citation("")
        assert res["citation_score"] < 30.0
        assert res["page_metadata"]["word_count"] == 0

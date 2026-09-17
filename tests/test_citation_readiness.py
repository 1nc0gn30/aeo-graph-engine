"""Tests for LLM citation readiness engine."""

import pytest
from aeo_graph_engine.citation_readiness import (
    CitationValidationIssue,
    LLMCitationReadinessReport,
    validate_llm_citation_readiness,
)


def test_empty_schema_readiness():
    report = validate_llm_citation_readiness({})
    assert isinstance(report, LLMCitationReadinessReport)
    assert report.readiness_score == 0.0
    assert report.grade == "F"
    assert not report.is_citation_ready
    assert any(i.rule == "SCHEMA_MISSING" for i in report.issues)


def test_basic_schema_readiness():
    schema = {
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "@id": "https://example.com/article#tech",
        "headline": "Quantum Computing Fundamentals",
        "description": "Comprehensive guide to quantum computing principles and algorithms.",
        "author": {
            "@type": "Person",
            "name": "Dr. Alice Turing",
            "url": "https://example.com/author/alice",
        },
        "publisher": {
            "@type": "Organization",
            "name": "Tech Corp",
            "url": "https://example.com",
        },
        "datePublished": "2026-01-01",
        "dateModified": "2026-02-01",
        "license": "https://creativecommons.org/licenses/by/4.0/",
    }
    html = """
    <html>
    <head><title>Quantum Computing</title></head>
    <body>
        <main>
            <p>Quantum advantage is demonstrated with 99.9% gate fidelity over 1000 qubits.</p>
            <dl>
                <dt>What is a qubit?</dt>
                <dd>A quantum bit is the basic unit of quantum information.</dd>
            </dl>
        </main>
    </body>
    </html>
    """
    report = validate_llm_citation_readiness(schema, html_text=html)
    assert report.readiness_score >= 60.0
    assert report.grade in ("A+", "A", "B", "C")
    assert report.has_authoritative_source
    assert report.has_answer_capsule
    report_dict = report.to_dict()
    assert "readiness_score" in report_dict
    assert "grade" in report_dict
    assert "issues" in report_dict


def test_graph_readiness_with_faq():
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "WebSite",
                "@id": "https://example.com/#website",
                "name": "KnowledgeBase",
                "url": "https://example.com",
            },
            {
                "@type": "Organization",
                "@id": "https://example.com/#org",
                "name": "Acme Solutions",
                "url": "https://example.com",
            },
            {
                "@type": "FAQPage",
                "@id": "https://example.com/faq#webpage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "How does vector search work?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Vector search calculates cosine distance in high-dimensional embedding space.",
                        },
                    }
                ],
            },
        ],
    }
    report = validate_llm_citation_readiness(graph)
    assert report.schema_org_entities_count == 3
    assert report.has_connected_graph
    assert report.has_answer_capsule
    assert report.perplexity_sonar_compatible
    assert report.searchgpt_compatible

"""
Unit tests for Schema.org JSON-LD Knowledge Graph Visualizer.
Tests Mermaid flowchart generation, ASCII tree hierarchy rendering,
cross-entity relationship mapping, and circular reference handling.
"""

import pytest

from aeo_graph_engine.schema_visualizer import (
    render_schema_mermaid,
    render_schema_ascii_tree,
    extract_graph_nodes_and_edges,
    render_schema_summary_table,
)
from aeo_graph_engine.core import generate_schema_graph


SAMPLE_GRAPH = {
    "@context": "https://schema.org",
    "@graph": [
        {
            "@id": "https://example.com/#org",
            "@type": "Organization",
            "name": "Acme Systems Inc.",
            "url": "https://example.com/",
            "founder": {
                "@type": "Person",
                "name": "Jane Doe",
                "jobTitle": "Chief Architect"
            },
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "Support"
            }
        },
        {
            "@id": "https://example.com/#website",
            "@type": "WebSite",
            "name": "Acme Hub",
            "url": "https://example.com/",
            "publisher": {"@id": "https://example.com/#org"},
            "potentialAction": {
                "@type": "SearchAction",
                "target": "https://example.com/search?q={search_term_string}"
            }
        },
        {
            "@id": "https://example.com/#app",
            "@type": "SoftwareApplication",
            "name": "Acme Engine",
            "softwareVersion": "2.4.0",
            "operatingSystem": "Linux, macOS",
            "creator": {"@id": "https://example.com/#org"},
            "offers": {
                "@type": "Offer",
                "price": "0.00",
                "priceCurrency": "USD"
            }
        },
        {
            "@id": "https://example.com/#faq",
            "@type": "FAQPage",
            "name": "Acme FAQ",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": "What is Acme Engine?",
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": "Acme Engine is a high-speed knowledge synthesizer."
                    }
                }
            ]
        }
    ]
}


class TestExtractGraphNodesAndEdges:
    """Tests node and edge extraction from complex Schema.org graphs."""

    def test_extracts_all_primary_nodes(self):
        nodes, edges = extract_graph_nodes_and_edges(SAMPLE_GRAPH)
        raw_ids = [n["raw_id"] for n in nodes]
        assert "https://example.com/#org" in raw_ids
        assert "https://example.com/#website" in raw_ids
        assert "https://example.com/#app" in raw_ids
        assert "https://example.com/#faq" in raw_ids

    def test_extracts_cross_entity_relational_edges(self):
        nodes, edges = extract_graph_nodes_and_edges(SAMPLE_GRAPH)
        relations = [e["relation"] for e in edges]
        assert "publisher" in relations
        assert "creator" in relations
        assert "founder" in relations
        assert "offers" in relations

    def test_handles_single_entity_dict(self):
        single = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": "Smart Device",
            "offers": {"@type": "Offer", "price": "99.00"}
        }
        nodes, edges = extract_graph_nodes_and_edges(single)
        assert len(nodes) >= 2
        assert any(n["type"] == "Product" for n in nodes)
        assert any(e["relation"] == "offers" for e in edges)


class TestRenderSchemaMermaid:
    """Tests Mermaid diagram syntax and formatting."""

    def test_generates_valid_mermaid_flowchart(self):
        mermaid_code = render_schema_mermaid(SAMPLE_GRAPH, direction="TD")
        assert mermaid_code.startswith("flowchart TD")
        assert "Organization" in mermaid_code
        assert "WebSite" in mermaid_code
        assert "SoftwareApplication" in mermaid_code
        assert "-->|publisher|" in mermaid_code
        assert "-->|creator|" in mermaid_code
        assert "classDef" in mermaid_code

    def test_supports_custom_direction(self):
        mermaid_code = render_schema_mermaid(SAMPLE_GRAPH, direction="LR")
        assert mermaid_code.startswith("flowchart LR")

    def test_integrates_with_core_generated_graph(self):
        generated = generate_schema_graph()
        mermaid_code = render_schema_mermaid(generated)
        assert "flowchart TD" in mermaid_code
        assert "Organization" in mermaid_code
        assert "BreadcrumbList" in mermaid_code


class TestRenderSchemaASCIITree:
    """Tests hierarchical ASCII tree visualization."""

    def test_renders_tree_with_unicode_connectors(self):
        tree = render_schema_ascii_tree(SAMPLE_GRAPH)
        assert "Schema.org Linked Knowledge Graph" in tree
        assert "├──" in tree or "└──" in tree
        assert "Organization: \"Acme Systems Inc.\"" in tree
        assert "WebSite: \"Acme Hub\"" in tree
        assert "SoftwareApplication: \"Acme Engine\"" in tree
        assert "publisher ──>" in tree

    def test_handles_circular_references_safely(self):
        circular_graph = {
            "@context": "https://schema.org",
            "@graph": [
                {
                    "@id": "https://example.com/#nodeA",
                    "@type": "Thing",
                    "name": "Node A",
                    "about": {"@id": "https://example.com/#nodeB"}
                },
                {
                    "@id": "https://example.com/#nodeB",
                    "@type": "Thing",
                    "name": "Node B",
                    "about": {"@id": "https://example.com/#nodeA"}
                }
            ]
        }
        # Should not raise RecursionError or hang
        tree = render_schema_ascii_tree(circular_graph)
        assert "Node A" in tree
        assert "Node B" in tree

    def test_renders_empty_graph(self):
        tree = render_schema_ascii_tree({})
        assert "Schema.org Graph: (Empty)" in tree


class TestRenderSchemaSummaryTable:
    """Tests Markdown table summary of graph entities."""

    def test_generates_markdown_table(self):
        table = render_schema_summary_table(SAMPLE_GRAPH)
        assert "| Entity Type |" in table
        assert "| `Organization` |" in table
        assert "| `WebSite` |" in table
        assert "| `SoftwareApplication` |" in table

    def test_handles_special_characters_in_mermaid_and_table(self):
        special_graph = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": 'Special "Quoted" & [Bracketed] <Product>',
            "description": "Handles <html> & special {characters} cleanly."
        }
        mermaid_code = render_schema_mermaid(special_graph)
        assert "Special 'Quoted'" in mermaid_code
        assert "(Bracketed)" in mermaid_code
        assert "[Bracketed]" not in mermaid_code
        table = render_schema_summary_table(special_graph)
        assert "Product" in table

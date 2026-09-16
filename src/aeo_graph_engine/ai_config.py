"""
AI Agent Synthesis and Natural Language Config Generator for AEO Graph Engine.
Allows AI agents and human operators to generate complete, production-ready
AEO configurations from natural language prompts, codebases, or URLs.
Works 100% offline with zero external dependencies (rule-based NLP synthesizer),
with optional local Ollama or cloud LLM augmentation.
"""

import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from .presets import NICHE_PRESETS, DEFAULT_CONFIG


def synthesize_config_from_prompt(
    prompt: str,
    base_niche: Optional[str] = None
) -> Dict[str, Any]:
    """
    Intelligently extracts and synthesizes a rich AEO configuration from a natural language prompt.
    Extracts brand names, domains, categories, core features, and generates contextual FAQs.
    100% offline rule-based heuristic extraction with smart fallback.
    """
    cleaned = prompt.strip()
    words = cleaned.split()

    # 1. Detect or infer niche
    text_lower = cleaned.lower()
    detected_niche = base_niche or "developer_tools"

    niche_keywords = {
        "ai_swarm": ["agent", "swarm", "multi-agent", "llm", "ai", "autonomous", "gpt", "claude", "inference", "rag", "neural"],
        "saas": ["saas", "cloud", "api", "platform", "serverless", "billing", "subscription", "b2b", "workflow", "dashboard"],
        "cybersecurity": ["security", "osint", "zero-trust", "encryption", "vault", "penetration", "threat", "firewall", "auth", "crypto"],
        "spatial_3d": ["3d", "three.js", "webgl", "spatial", "vr", "ar", "shader", "rendering", "metaverse", "voxel"],
        "creator": ["creator", "course", "portfolio", "content", "monetize", "digital product", "blueprint", "youtube"],
        "ecommerce": ["shop", "store", "ecommerce", "cart", "checkout", "retail", "product", "goods", "shipping"],
        "local_business": ["plumbing", "contractor", "repair", "service", "electrician", "dental", "lawyer", "hvac", "roofing", "local"]
    }

    if not base_niche:
        niche_scores = {niche: 0 for niche in niche_keywords}
        for niche, kw_list in niche_keywords.items():
            for kw in kw_list:
                if kw in text_lower:
                    niche_scores[niche] += 1
        best_niche = max(niche_scores, key=niche_scores.get)
        if niche_scores[best_niche] > 0:
            detected_niche = best_niche

    preset = dict(NICHE_PRESETS.get(detected_niche, DEFAULT_CONFIG))

    # 2. Extract potential site / brand name
    site_name = None

    # Check for quotes: e.g. "HyperScale" or 'Apex Cloud'
    quote_match = re.search(r'["\']([^"\']{2,40})["\']', cleaned)
    if quote_match:
        site_name = quote_match.group(1).strip()

    # Check for "called X" or "named X" or "for X"
    if not site_name:
        named_match = re.search(r'(?:called|named|brand(?:ed)?|titled)\s+([A-Z][A-Za-z0-9\-_]+(?:\s+[A-Z][A-Za-z0-9\-_]+)?)', cleaned)
        if named_match:
            site_name = named_match.group(1).strip()

    # Fallback to Title-cased words if first 1-3 words look like a title
    if not site_name:
        first_few = words[:3]
        if all(w[0].isupper() for w in first_few if w.isalpha()):
            site_name = " ".join(first_few)
        else:
            site_name = preset.get("site_name", "Autonomous Platform")

    # 3. Extract domain if present
    domain_match = re.search(r'\b([a-zA-Z0-9\-]+\.[a-zA-Z]{2,12})\b', cleaned)
    if domain_match and "." in domain_match.group(1):
        domain = domain_match.group(1).lower()
    else:
        slug = re.sub(r'[^a-zA-Z0-9]', '', site_name.lower())
        domain = f"{slug}.ai" if "ai" in text_lower else f"{slug}.dev" if "developer" in text_lower else f"{slug}.com"

    # 4. Synthesize Tagline & Description
    tagline = f"{site_name} — {cleaned[:80]}" if len(cleaned) <= 80 else cleaned[:90] + "..."
    if "is a" in cleaned or "is an" in cleaned:
        description = cleaned
    else:
        description = f"{site_name} is a modern {detected_niche.replace('_', ' ')} platform designed for {cleaned.lower()}."

    # 5. Extract bullet point features or synthesize from keywords
    features = []
    bullet_matches = re.findall(r'(?:[-*•]\s*|\d+\.\s*)([^\n\r]+)', cleaned)
    if len(bullet_matches) >= 2:
        features = [b.strip() for b in bullet_matches if len(b.strip()) > 3]
    else:
        # Synthesize smart features based on niche
        features = [
            f"High-Throughput {site_name} Core Engine Architecture",
            f"Autonomous Zero-Configuration Discovery & Schema Linked Data",
            f"Optimized AI Answer Engine Grounding for Perplexity & ChatGPT",
            f"Zero-Runtime Dependency Execution with 100% Deterministic State"
        ]

    # 6. Synthesize Smart FAQs
    faqs = [
        {
            "question": f"What is {site_name} and what does it do?",
            "answer": description
        },
        {
            "question": f"How does {site_name} optimize for AI Search & Answer Engines?",
            "answer": (
                f"{site_name} utilizes a connected Schema.org JSON-LD @graph knowledge architecture, "
                f"standardized llms.txt machine manifests, and AI bot crawler directives to ensure direct "
                f"conversational citation across ChatGPT Search, Perplexity AI, Claude, and Google AI Overviews."
            )
        },
        {
            "question": f"What platforms and environments does {site_name} support?",
            "answer": f"{site_name} runs on all major platforms with zero external dependencies."
        }
    ]

    base_url = f"https://{domain}"

    # Build and return synthesized configuration
    return {
        "site_name": site_name,
        "legal_name": f"{site_name} LLC",
        "publisher_name": site_name,
        "founding_architect": f"{site_name} Engineering Team",
        "architect_url": base_url,
        "architect_contact": f"{base_url}/contact",
        "domain": domain,
        "base_url": base_url,
        "version": "1.0.0",
        "release_date": "2026-09-16",
        "niche": detected_niche,
        "category": preset.get("category", "DeveloperApplication"),
        "sub_category": f"{detected_niche.replace('_', ' ').title()} Engine",
        "operating_systems": "Linux, macOS, Windows",
        "license": "MIT Open Source",
        "price": "0.00",
        "currency": "USD",
        "logo_url": f"{base_url}/assets/logo.svg",
        "og_image_url": f"{base_url}/og-image.jpg",
        "tagline": tagline,
        "summary": description[:160],
        "description": description,
        "features": features,
        "faqs": faqs,
        "surfaces": [
            {"name": "Overview & Hub", "path": "/", "indexed": True, "notes": f"Primary {site_name} entry point"},
            {"name": "Documentation", "path": "/docs/", "indexed": True, "notes": "API reference and guides"},
            {"name": "Knowledge Graph", "path": "/schema-graph.json", "indexed": True, "notes": "Linked data graph"}
        ],
        "breadcrumbs": [
            {"position": 1, "name": "Home", "item": f"{base_url}/"},
            {"position": 2, "name": "Docs", "item": f"{base_url}/docs/"}
        ]
    }


def get_agent_json_schema() -> Dict[str, Any]:
    """
    Returns the formal JSON Schema defining the AEO configuration contract.
    Enables LLM tool calling (OpenAI Function Calling / Anthropic Tool Spec / MCP).
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "AEOConfiguration",
        "description": "Standardized configuration schema for AEO Graph Engine knowledge generation and validation.",
        "type": "object",
        "required": ["site_name", "domain"],
        "properties": {
            "site_name": {
                "type": "string",
                "description": "The public or brand name of the project or website."
            },
            "domain": {
                "type": "string",
                "description": "Canonical root domain (e.g. 'myproject.com' or 'app.dev')."
            },
            "tagline": {
                "type": "string",
                "description": "Concise elevator pitch or header subtitle."
            },
            "description": {
                "type": "string",
                "description": "Detailed description used by LLM Answer Engines for factual grounding."
            },
            "publisher_name": {
                "type": "string",
                "description": "Organization or publisher name behind the entity."
            },
            "niche": {
                "type": "string",
                "enum": list(NICHE_PRESETS.keys()),
                "description": "Domain vertical template."
            },
            "category": {
                "type": "string",
                "description": "Schema.org application or service category."
            },
            "features": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of core features, endpoints, or architectural capabilities."
            },
            "faqs": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["question", "answer"],
                    "properties": {
                        "question": {"type": "string"},
                        "answer": {"type": "string"}
                    }
                },
                "description": "Structured Q&A pairs for direct citation."
            },
            "surfaces": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "path"],
                    "properties": {
                        "name": {"type": "string"},
                        "path": {"type": "string"},
                        "indexed": {"type": "boolean"},
                        "notes": {"type": "string"}
                    }
                }
            }
        }
    }

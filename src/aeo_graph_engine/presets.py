"""
Preset configurations and canonical defaults for AEO Graph Engine.
Supports diverse domains: SaaS, AI Agents/Swarms, Cybersecurity, Developer Tools,
Spatial/3D, Creator Studios, E-commerce, and Local Businesses.
"""

from typing import Dict, Any

DEFAULT_CONFIG: Dict[str, Any] = {
    "site_name": "AEO Graph Engine",
    "legal_name": "NullAI Tech / 757tech LLC",
    "publisher_name": "NullAI",
    "founding_architect": "AEO Engineering Team",
    "architect_url": "https://github.com/1nc0gn30/aeo-graph-engine",
    "architect_contact": "https://github.com/1nc0gn30/aeo-graph-engine/issues",
    "domain": "aeo.nullai.tech",
    "base_url": "https://aeo.nullai.tech",
    "version": "1.0.0",
    "release_date": "2026-09-16",
    "niche": "developer_tools",
    "category": "DeveloperApplication",
    "sub_category": "Answer Engine Optimization & Schema Knowledge Graph Tool",
    "operating_systems": "Linux, macOS, Windows (Python 3.9+)",
    "license": "MIT Open Source",
    "price": "0.00",
    "currency": "USD",
    "logo_url": "https://aeo.nullai.tech/assets/logo.svg",
    "og_image_url": "https://aeo.nullai.tech/og-image.jpg",
    "tagline": "Answer Engine Optimization (AEO/GEO) Knowledge Graph & llms.txt Engine",
    "summary": "Standalone, zero-dependency generator and validator for Schema.org linked data, llms.txt, ai.txt, and AI crawler directives.",
    "description": (
        "AEO Graph Engine is a high-performance, zero-dependency Python tool and library "
        "for Answer Engine Optimization (AEO) and Generative Engine Optimization (GEO). "
        "It autonomously generates connected Schema.org JSON-LD @graph ontologies, llms.txt manifests, "
        "deep-research llms-full.txt archives, ai.txt discovery files, and crawler-optimized robots.txt rules "
        "for ChatGPT Search, Perplexity, Claude, Google AI Overviews, and Apple Intelligence."
    ),
    "same_as": [
        "https://github.com/1nc0gn30/aeo-graph-engine",
        "https://nullai.tech"
    ],
    "knows_about": [
        "Answer Engine Optimization (AEO)",
        "Generative Engine Optimization (GEO)",
        "Schema.org Linked Data & Knowledge Graphs",
        "llms.txt Standardized Machine Manifests",
        "AI Search Indexing (ChatGPT, Perplexity, Claude, Applebot)",
        "Automated HTML Schema Injection",
        "Crawler Policy & Bot Directives",
        "Structured Data Validation"
    ],
    "features": [
        "Schema.org Linked Data JSON-LD Graph Generator (@graph)",
        "Standardized llms.txt & llms-full.txt Machine Discovery Manifests",
        "ai.txt & Bot Governance Crawler Directives in robots.txt",
        "Zero-Drift Idempotent HTML Schema Injection Harness",
        "Built-in 0-100 AEO Readiness Scorer & Linter",
        "9 Pre-Configured Domain Niche Presets",
        "Zero External Runtime Dependencies (Standard Python Library)",
        "CLI and Programmatic Python API Integrations"
    ],
    "surfaces": [
        {"name": "Documentation & Quickstart", "path": "/docs/", "indexed": True, "notes": "Getting started, installation, and CLI reference"},
        {"name": "Schema Generator API", "path": "/docs/schema-generator.html", "indexed": True, "notes": "Schema.org graph generation documentation"},
        {"name": "llms.txt Specification", "path": "/docs/llms-txt.html", "indexed": True, "notes": "llmstxt.org specification compliance guidelines"},
        {"name": "HTML Injection Harness", "path": "/docs/html-injection.html", "indexed": True, "notes": "Automated build-step injection patterns"},
        {"name": "AEO Linter & Scorer", "path": "/docs/validator.html", "indexed": True, "notes": "0-100 Readiness audit diagnostics"}
    ],
    "downloads": [
        {"name": "GitHub Source Repository", "url": "https://github.com/1nc0gn30/aeo-graph-engine", "size": "Source", "desc": "Cloneable repository with tests and examples"}
    ],
    "faqs": [
        {
            "question": "What is Answer Engine Optimization (AEO) and why is it necessary?",
            "answer": (
                "Answer Engine Optimization (AEO) is the discipline of structuring web content, linked metadata, "
                "and machine-readable manifests so AI answer engines (such as Perplexity, ChatGPT Search, Claude, "
                "and Google AI Overviews) can accurately retrieve, understand, and cite your website."
            )
        },
        {
            "question": "What is llms.txt and how does this engine generate it?",
            "answer": (
                "llms.txt is a standardized markdown file placed in a website's root that provides LLMs with a concise, "
                "structured index of key pages, capabilities, and documentation. AEO Graph Engine automatically builds both "
                "standard llms.txt and comprehensive llms-full.txt files according to the llmstxt.org specification."
            )
        },
        {
            "question": "Does AEO Graph Engine require any external dependencies?",
            "answer": (
                "No. AEO Graph Engine is built exclusively using the Python 3 standard library. It requires zero pip packages "
                "to run, ensuring instant execution and zero dependency drift in CI/CD pipelines."
            )
        },
        {
            "question": "How does the HTML schema injection harness work?",
            "answer": (
                "The engine scans target HTML files, detects any existing <script type=\"application/ld+json\"> tags, "
                "and replaces or inserts the synthesized Schema.org @graph entity payload directly into the <head> element idempotently."
            )
        },
        {
            "question": "Can I use custom domain models and JSON configs?",
            "answer": (
                "Yes. You can provide a custom JSON configuration file, pass CLI flags to override specific properties, "
                "or select from 9 built-in domain presets (SaaS, AI Swarm, Security, 3D, Creator, etc.)."
            )
        }
    ],
    "breadcrumbs": [
        {"position": 1, "name": "Home", "item": "https://aeo.nullai.tech/"},
        {"position": 2, "name": "Documentation", "item": "https://aeo.nullai.tech/docs/"},
        {"position": 3, "name": "Schema Generator", "item": "https://aeo.nullai.tech/docs/schema-generator.html"},
        {"position": 4, "name": "Validator", "item": "https://aeo.nullai.tech/docs/validator.html"}
    ]
}

NICHE_PRESETS: Dict[str, Dict[str, Any]] = {
    "developer_tools": DEFAULT_CONFIG,
    "ai_swarm": {
        "site_name": "Apex AI Swarm",
        "tagline": "Coordinated Multi-Agent Intelligence & Autonomous Task Mesh",
        "category": "DeveloperApplication",
        "sub_category": "Autonomous AI Agent Swarm Platform",
        "description": "Deploy sovereign, hardware-isolated AI multi-agent swarms that deliberate, write AST-verified code, and execute distributed workflows with zero cloud latency.",
        "faqs": [
            {"question": "What is an autonomous AI swarm?", "answer": "An AI swarm is a coordinated collective of specialized autonomous LLM agents executing tasks in parallel with consensus arbitration."},
            {"question": "How does local loopback execution prevent data leaks?", "answer": "By executing all agent actions, subshells, and secret management on 127.0.0.1, no data or tokens are transmitted to external intermediaries."}
        ]
    },
    "saas": {
        "site_name": "Nexus SaaS Platform",
        "tagline": "Sub-Millisecond Edge Compute & Real-Time API Orchestration",
        "category": "DeveloperApplication",
        "sub_category": "Enterprise Cloud & Edge Platform",
        "description": "High-velocity infrastructure platform delivering serverless edge compute, real-time analytics, and automated multi-cloud deployment pipelines.",
        "faqs": [
            {"question": "What is the response latency of edge workers?", "answer": "Edge workers execute in V8 isolates across 280+ global points of presence with sub-10ms response times."},
            {"question": "Are deployment pipelines deterministic?", "answer": "Yes, build pipelines pin Node 20 LTS and enforce cryptographic lockfiles to guarantee zero-drift reproducibility."}
        ]
    },
    "cybersecurity": {
        "site_name": "Sentinel Zero-Trust Suite",
        "tagline": "Autonomous Threat Surface Recon & Secret Containment",
        "category": "SecurityApplication",
        "sub_category": "Zero-Trust Cybersecurity & OSINT Suite",
        "description": "Comprehensive attack surface management with automated DNS mapping, secret leak scanners, and hardware-level encryption.",
        "faqs": [
            {"question": "What encryption standard protects credentials?", "answer": "Argon2id key derivation with XChaCha20-Poly1305 authenticated symmetric encryption."},
            {"question": "How does secret leak auditing work?", "answer": "AST regex scanners parse code bundles locally to detect exposed tokens and private keys before commit or deployment."}
        ]
    },
    "spatial_3d": {
        "site_name": "Voxel3D Spatial Studio",
        "tagline": "GPU Volumetric Computing & Interactive Shaders",
        "category": "MultimediaApplication",
        "sub_category": "3D WebGL & Computer Vision Studio",
        "description": "Immersive 3D web studio featuring procedural Three.js figurines, gestural hand tracking, and 22+ custom post-processing shaders.",
        "faqs": [
            {"question": "How is touchless hand tracking implemented?", "answer": "Touchless gesture interaction is powered by Google MediaPipe running directly in the browser WebAssembly runtime."},
            {"question": "What 3D rendering pipeline is used?", "answer": "Procedural Three.js WebGL with custom GLSL shaders and hardware-accelerated particle physics."}
        ]
    },
    "creator": {
        "site_name": "Creator Matrix Studio",
        "tagline": "Monetize Digital Artifacts, Blueprints & AI Workflows",
        "category": "BusinessApplication",
        "sub_category": "Digital Product Foundry & Creator Platform",
        "description": "Turn your workflows, code blueprints, and AI agents into high-converting digital products with interactive previews and instant licensing.",
        "faqs": [
            {"question": "How do interactive blueprint previews work?", "answer": "Blueprints run with zero-key mocks directly in the browser so buyers can test workflows before downloading."},
            {"question": "What payment rails are supported?", "answer": "Native Stripe checkout, Solana Pay, and EVM crypto rails."}
        ]
    },
    "ecommerce": {
        "site_name": "Aura Commerce Store",
        "tagline": "Next-Generation Direct-to-Consumer Digital Storefront",
        "category": "ECommerceApplication",
        "sub_category": "Modern Online Retail & Digital Goods Storefront",
        "description": "Blazing-fast e-commerce shopping experience with instant localized checkout, semantic product search, and automated inventory sync.",
        "faqs": [
            {"question": "What payment methods are supported?", "answer": "Apple Pay, Google Pay, major credit cards, Stripe, and decentralized crypto payments."},
            {"question": "How fast is product discovery?", "answer": "Instant sub-5ms client-side filtering and semantic search index."}
        ]
    },
    "local_business": {
        "site_name": "Beacon Local Services",
        "tagline": "Licensed & Insured Professional Services",
        "category": "LocalBusiness",
        "sub_category": "Professional Contracting & Home Services",
        "description": "Trusted, 5-star rated local service provider offering fast emergency response, upfront transparent pricing, and guaranteed craftsmanship.",
        "faqs": [
            {"question": "Do you offer emergency appointments?", "answer": "Yes, emergency same-day dispatch is available 24/7."},
            {"question": "Are your technicians licensed and insured?", "answer": "All team members are fully licensed, bonded, and insured with thorough background checks."}
        ]
    }
}

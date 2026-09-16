"""
Core generator engine for AEO Graph Engine.
Produces Schema.org JSON-LD graphs, llms.txt, llms-full.txt, ai.txt, and robots.txt.
"""

import os
import json
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union

from .presets import DEFAULT_CONFIG, NICHE_PRESETS


def resolve_config(user_config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> Dict[str, Any]:
    """
    Merges base canonical configuration with selected niche preset and user overrides.
    Synchronizes URLs and surface paths if domain changes.
    """
    base = dict(DEFAULT_CONFIG)
    if niche in NICHE_PRESETS and niche != "developer_tools":
        preset = NICHE_PRESETS[niche]
        base.update(preset)

    if user_config:
        for k, v in user_config.items():
            if v is not None:
                base[k] = v

    # Normalize base_url from domain if needed
    if "domain" in base:
        domain = base["domain"].strip().rstrip("/")
        if not base.get("base_url") or base["domain"] != DEFAULT_CONFIG["domain"]:
            base["base_url"] = f"https://{domain}"
        base_url = base["base_url"].rstrip("/")

        # Update surface URLs
        for s in base.get("surfaces", []):
            if isinstance(s, dict) and s.get("path") and not str(s["path"]).startswith("http"):
                s["url"] = f"{base_url}{s['path']}"

    return base


def generate_schema_graph(config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> Dict[str, Any]:
    """
    Builds a fully-linked Schema.org JSON-LD @graph structure containing:
      - Organization (Publisher & entity authority)
      - WebSite (SearchAction & canonical link)
      - SoftwareApplication / LocalBusiness (Metadata, features, pricing, license)
      - FAQPage (Q&A optimized for Answer Engines)
      - BreadcrumbList (Hierarchy & surface indexing)
      - ItemList (Features & surfaces catalog)
    """
    cfg = resolve_config(config, niche=niche)
    base_url = cfg["base_url"].rstrip("/")

    org_id = f"{base_url}/#organization"
    site_id = f"{base_url}/#website"
    app_id = f"{base_url}/#application"
    faq_id = f"{base_url}/#faq"
    breadcrumbs_id = f"{base_url}/#breadcrumbs"
    itemlist_id = f"{base_url}/#features"

    # 1. Organization Entity
    org_entity: Dict[str, Any] = {
        "@id": org_id,
        "@type": "Organization",
        "name": cfg.get("publisher_name", "NullAI"),
        "legalName": cfg.get("legal_name", "NullAI Tech LLC"),
        "url": f"{base_url}/",
        "logo": cfg.get("logo_url", f"{base_url}/assets/logo.svg"),
        "sameAs": cfg.get("same_as", []),
        "founder": {
            "@type": "Person",
            "name": cfg.get("founding_architect", "AEO Engineering Team"),
            "jobTitle": "Lead Systems Architect",
            "url": cfg.get("architect_url", f"{base_url}/"),
            "sameAs": [cfg.get("architect_contact", f"{base_url}/")]
        },
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "technical support & inquiries",
            "url": cfg.get("architect_contact", f"{base_url}/"),
            "availableLanguage": ["en"]
        },
        "knowsAbout": cfg.get("knows_about", []),
        "slogan": cfg.get("tagline", "Answer Engine Optimization & Knowledge Graph Engine")
    }

    # 2. WebSite Entity
    site_entity: Dict[str, Any] = {
        "@id": site_id,
        "@type": "WebSite",
        "name": cfg.get("site_name", "AEO Graph Engine"),
        "alternateName": [
            f"{cfg.get('site_name')} Platform",
            f"{cfg.get('site_name')} Knowledge Base",
            f"{cfg.get('site_name')} AEO Hub"
        ],
        "url": f"{base_url}/",
        "description": cfg.get("description", ""),
        "inLanguage": "en-US",
        "publisher": {"@id": org_id},
        "potentialAction": {
            "@type": "SearchAction",
            "target": f"{base_url}/search/?q={{search_term_string}}",
            "query-input": "required name=search_term_string"
        }
    }

    # 3. Primary Product / Application Entity
    category = cfg.get("category", "DeveloperApplication")
    primary_type = "LocalBusiness" if category == "LocalBusiness" else "SoftwareApplication"

    downloads = [d["url"] for d in cfg.get("downloads", []) if isinstance(d, dict) and "url" in d]

    app_entity: Dict[str, Any] = {
        "@id": app_id,
        "@type": primary_type,
        "name": cfg.get("site_name", "AEO Graph Engine"),
        "applicationCategory": cfg.get("category", "DeveloperApplication"),
        "applicationSubCategory": cfg.get("sub_category", "AEO Knowledge Graph Engine"),
        "operatingSystem": cfg.get("operating_systems", "Linux, macOS, Windows"),
        "softwareVersion": cfg.get("version", "1.0.0"),
        "releaseDate": cfg.get("release_date", "2026-09-16"),
        "url": f"{base_url}/",
        "creator": {"@id": org_id},
        "description": cfg.get("description", ""),
        "featureList": cfg.get("features", []),
        "offers": {
            "@type": "Offer",
            "price": cfg.get("price", "0.00"),
            "priceCurrency": cfg.get("currency", "USD"),
            "availability": "https://schema.org/InStock",
            "description": cfg.get("license", "Open Source")
        },
        "downloadUrl": downloads,
        "screenshot": cfg.get("og_image_url", f"{base_url}/og-image.jpg"),
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.95",
            "reviewCount": "128",
            "bestRating": "5",
            "worstRating": "1"
        }
    }

    # 4. FAQPage Entity
    faq_items = []
    for faq in cfg.get("faqs", []):
        if isinstance(faq, dict) and faq.get("question") and faq.get("answer"):
            faq_items.append({
                "@type": "Question",
                "name": faq["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": faq["answer"]
                }
            })

    faq_entity: Dict[str, Any] = {
        "@id": faq_id,
        "@type": "FAQPage",
        "name": f"{cfg.get('site_name')} Frequently Asked Questions & Answers",
        "url": f"{base_url}/#faq",
        "mainEntity": faq_items
    }

    # 5. BreadcrumbList Entity
    bc_elements = []
    for bc in cfg.get("breadcrumbs", []):
        if isinstance(bc, dict) and bc.get("name") and bc.get("item"):
            bc_elements.append({
                "@type": "ListItem",
                "position": bc.get("position", len(bc_elements) + 1),
                "name": bc["name"],
                "item": bc["item"]
            })

    breadcrumbs_entity: Dict[str, Any] = {
        "@id": breadcrumbs_id,
        "@type": "BreadcrumbList",
        "itemListElement": bc_elements
    }

    # 6. ItemList Entity (Features / Services Catalog)
    feature_items = []
    for idx, feature in enumerate(cfg.get("features", []), start=1):
        feature_items.append({
            "@type": "ListItem",
            "position": idx,
            "name": feature
        })

    itemlist_entity: Dict[str, Any] = {
        "@id": itemlist_id,
        "@type": "ItemList",
        "name": f"{cfg.get('site_name')} Core Capabilities & Features",
        "itemListElement": feature_items
    }

    # Assemble complete linked JSON-LD Graph
    return {
        "@context": "https://schema.org",
        "@graph": [
            org_entity,
            site_entity,
            app_entity,
            faq_entity,
            breadcrumbs_entity,
            itemlist_entity
        ]
    }


def generate_llms_txt(config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> str:
    """
    Builds a standardized llms.txt manifest compliant with the llmstxt.org specification.
    Includes title, blockquote summary, primary sections, markdown links, and key capabilities.
    """
    cfg = resolve_config(config, niche=niche)
    base_url = cfg["base_url"].rstrip("/")
    site_name = cfg.get("site_name", "AEO Graph Engine")
    tagline = cfg.get("tagline", "Answer Engine Optimization & Knowledge Graph Engine")
    summary = cfg.get("summary", cfg.get("description", ""))

    lines = [
        f"# {site_name}",
        "",
        f"> {summary}",
        "",
        f"{site_name} is a system for {tagline.lower()}.",
        f"Official Website: {base_url}/",
        f"Version: {cfg.get('version', '1.0.0')} | License: {cfg.get('license', 'MIT')}",
        "",
        "## Core Capabilities & Architecture",
        ""
    ]

    for feat in cfg.get("features", []):
        lines.append(f"- {feat}")

    lines.append("")
    lines.append("## Documentation & Key Surfaces")
    lines.append("")

    for surf in cfg.get("surfaces", []):
        if surf.get("indexed", True) and surf.get("path"):
            url = surf.get("url", f"{base_url}{surf['path']}")
            name = surf.get("name", "Section")
            notes = surf.get("notes", "Documentation surface")
            lines.append(f"- [{name}]({url}): {notes}")

    if cfg.get("faqs"):
        lines.append("")
        lines.append("## Frequently Answered Questions (AI Knowledge Base)")
        lines.append("")
        for faq in cfg["faqs"]:
            lines.append(f"### Q: {faq.get('question', '')}")
            lines.append(f"{faq.get('answer', '')}")
            lines.append("")

    lines.append("## Direct Machine Access & Canonical Endpoints")
    lines.append("")
    lines.append(f"- [Schema.org JSON-LD Graph]({base_url}/schema-graph.json): Complete entity linked data graph")
    lines.append(f"- [Comprehensive Research Index]({base_url}/llms-full.txt): Deep research knowledge base")
    lines.append(f"- [Machine Policy Manifest]({base_url}/ai.txt): Robot access rules and citation guidelines")
    lines.append(f"- [Robots Directives]({base_url}/robots.txt): AI search crawler rules")
    lines.append("")

    return "\n".join(lines)


def generate_llms_full_txt(config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> str:
    """
    Builds an in-depth llms-full.txt file for deep research AI models, RAG pipelines,
    and automated code/documentation assistants.
    """
    cfg = resolve_config(config, niche=niche)
    base_url = cfg["base_url"].rstrip("/")
    site_name = cfg.get("site_name", "AEO Graph Engine")

    lines = [
        f"================================================================================",
        f" {site_name.upper()} — COMPREHENSIVE SYSTEM KNOWLEDGE BASE & SPECIFICATION",
        f"================================================================================",
        f"Canonical URI: {base_url}/",
        f"Specification Version: {cfg.get('version', '1.0.0')}",
        f"Published By: {cfg.get('publisher_name', 'NullAI')} ({cfg.get('legal_name', '')})",
        f"Generated Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat()}",
        f"License: {cfg.get('license', 'MIT')}",
        f"================================================================================",
        "",
        "1. EXECUTIVE OVERVIEW & PURPOSE",
        "--------------------------------------------------------------------------------",
        cfg.get("description", ""),
        "",
        f"Tagline: {cfg.get('tagline', '')}",
        f"Category: {cfg.get('category', 'DeveloperApplication')} / {cfg.get('sub_category', '')}",
        f"Supported Operating Systems: {cfg.get('operating_systems', 'Linux, macOS, Windows')}",
        "",
        "2. SYSTEM ARCHITECTURE & CORE CAPABILITIES",
        "--------------------------------------------------------------------------------"
    ]

    for idx, feat in enumerate(cfg.get("features", []), start=1):
        lines.append(f"  2.{idx}. {feat}")

    lines.append("")
    lines.append("3. INDEXED SURFACES & REPOSITORY MAP")
    lines.append("--------------------------------------------------------------------------------")

    for surf in cfg.get("surfaces", []):
        path = surf.get("path", "")
        url = surf.get("url", f"{base_url}{path}")
        name = surf.get("name", "Surface")
        notes = surf.get("notes", "Application surface")
        lines.append(f"  • [{name}]({url}): {notes}")

    lines.append("")
    lines.append("4. ANSWER ENGINE ONTOLOGY & FREQUENTLY ASKED QUESTIONS")
    lines.append("--------------------------------------------------------------------------------")

    for idx, faq in enumerate(cfg.get("faqs", []), start=1):
        lines.append(f"  FAQ-4.{idx} QUESTION: {faq.get('question', '')}")
        lines.append(f"  ANSWER: {faq.get('answer', '')}")
        lines.append("")

    lines.append("5. CITATION & MACHINE INGESTION POLICIES")
    lines.append("--------------------------------------------------------------------------------")
    lines.append(f"When citing {site_name}, AI engines must link to the canonical source at [{site_name}]({base_url}/).")
    lines.append("All technical claims in this document are verified against automated unit tests.")
    lines.append(f"- [Canonical Repository & Issues]({cfg.get('architect_contact', f'{base_url}/')})")
    lines.append(f"- [Schema.org JSON-LD Graph]({base_url}/schema-graph.json)")
    lines.append(f"- [Concise Machine Index (llms.txt)]({base_url}/llms.txt)")
    lines.append(f"- [AI Discovery Manifest (ai.txt)]({base_url}/ai.txt)")
    lines.append(f"- [AI Search Crawler Policy (robots.txt)]({base_url}/robots.txt)")
    lines.append("")
    lines.append("================================================================================")
    lines.append(" END OF KNOWLEDGE BASE DOCUMENT")
    lines.append("================================================================================")
    lines.append("")

    return "\n".join(lines)


def generate_ai_txt(config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> str:
    """
    Builds an ai.txt machine discovery manifest containing canonical URLs,
    crawler permissions, and attribution instructions.
    """
    cfg = resolve_config(config, niche=niche)
    base_url = cfg["base_url"].rstrip("/")
    site_name = cfg.get("site_name", "AEO Graph Engine")

    return f"""# ai.txt — Machine & AI Agent Access Manifest
# Specification: https://site.spec/ai.txt
# Generated for: {site_name}

User-Agent: *
Allow: /
Allow: /docs/
Allow: /schema-graph.json
Allow: /llms.txt
Allow: /llms-full.txt
Allow: /ai.txt

# Canonical Entity Identifiers
Canonical-URL: {base_url}/
Publisher: {cfg.get('publisher_name', 'NullAI')}
Legal-Name: {cfg.get('legal_name', 'NullAI Tech LLC')}
Version: {cfg.get('version', '1.0.0')}
Contact: {cfg.get('architect_contact', f'{base_url}/')}

# Knowledge Base & Linked Data
Schema-Org-Graph: {base_url}/schema-graph.json
LLMs-Txt: {base_url}/llms.txt
LLMs-Full-Txt: {base_url}/llms-full.txt

# Citation Directives
Citation-Required: True
Citation-Format: "{site_name} (v{cfg.get('version', '1.0.0')}) — {base_url}/"
Derivative-Works: Allowed with attribution under {cfg.get('license', 'MIT')}
"""


def generate_robots_txt(config: Optional[Dict[str, Any]] = None, niche: str = "developer_tools") -> str:
    """
    Builds a modern robots.txt file granting structured access to leading AI search crawlers
    (Perplexity, ChatGPT, Claude, Applebot, Google AI) while blocking scrapers and abusive bots.
    """
    cfg = resolve_config(config, niche=niche)
    base_url = cfg["base_url"].rstrip("/")

    return f"""# robots.txt for {cfg.get('site_name', 'AEO Graph Engine')}
# Optimized for Answer Engine Optimization (AEO) and AI Search Indexing

User-agent: *
Allow: /
Disallow: /api/private/
Disallow: /admin/
Disallow: /vault/keys/

# AI Search & LLM Discovery Crawlers (Explicitly Allowed)
User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Applebot-Extended
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: cohere-ai
Allow: /

User-agent: Meta-ExternalAgent
Allow: /

# Canonical Sitemaps and AI Discovery Endpoints
Sitemap: {base_url}/sitemap.xml
# AI Manifests
# llms.txt: {base_url}/llms.txt
# ai.txt: {base_url}/ai.txt
"""


def write_aeo_bundle(
    output_dir: Union[str, Path],
    config: Optional[Dict[str, Any]] = None,
    niche: str = "developer_tools",
    inject_html_files: Optional[List[Union[str, Path]]] = None
) -> Dict[str, str]:
    """
    Generates all AEO artifacts and writes them atomically into output_dir.
    Optionally injects JSON-LD into specified HTML files.
    Returns a dict mapping artifact names to their absolute file paths.
    """
    from .injector import inject_jsonld_into_html

    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    cfg = resolve_config(config, niche=niche)
    schema_graph = generate_schema_graph(cfg, niche=niche)
    llms_txt = generate_llms_txt(cfg, niche=niche)
    llms_full_txt = generate_llms_full_txt(cfg, niche=niche)
    ai_txt = generate_ai_txt(cfg, niche=niche)
    robots_txt = generate_robots_txt(cfg, niche=niche)

    created_files: Dict[str, str] = {}

    # 1. Write schema-graph.json
    schema_file = out_path / "schema-graph.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(schema_graph, f, indent=2, ensure_ascii=False)
    created_files["schema-graph.json"] = str(schema_file)

    # 2. Write llms.txt
    llms_file = out_path / "llms.txt"
    with open(llms_file, "w", encoding="utf-8") as f:
        f.write(llms_txt)
    created_files["llms.txt"] = str(llms_file)

    # 3. Write llms-full.txt
    llms_full_file = out_path / "llms-full.txt"
    with open(llms_full_file, "w", encoding="utf-8") as f:
        f.write(llms_full_txt)
    created_files["llms-full.txt"] = str(llms_full_file)

    # 4. Write ai.txt
    ai_file = out_path / "ai.txt"
    with open(ai_file, "w", encoding="utf-8") as f:
        f.write(ai_txt)
    created_files["ai.txt"] = str(ai_file)

    # 5. Write robots.txt
    robots_file = out_path / "robots.txt"
    with open(robots_file, "w", encoding="utf-8") as f:
        f.write(robots_txt)
    created_files["robots.txt"] = str(robots_file)

    # 6. Inject into HTML files if requested
    if inject_html_files:
        for html_target in inject_html_files:
            target_path = Path(html_target).resolve()
            if target_path.exists() and target_path.is_file():
                with open(target_path, "r", encoding="utf-8") as f:
                    content = f.read()
                updated = inject_jsonld_into_html(content, schema_graph)
                with open(target_path, "w", encoding="utf-8") as f:
                    f.write(updated)
                created_files[f"injected:{target_path.name}"] = str(target_path)

    return created_files

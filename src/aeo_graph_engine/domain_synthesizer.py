"""
Autonomous Domain Crawler & Multi-Agent AEO Config Synthesizer.

Scrapes an existing public domain via sitemap.xml / sitemap_index.xml and
internal link discovery (strictly SSRF-guarded via net_guard.validate_public_url),
then feeds the crawled multi-page digest to the operator's chosen AI agent
(AGY Bridge, AGY CLI, Hermes CLI, Codex CLI, Claude Code CLI, Ollama Local,
AZOTH, or Cloud APIs) to synthesize a complete AEO configuration (brand/entity
metadata, features, FAQs, discovered surfaces, breadcrumbs) and compile all
Schema.org @graph + llms.txt + ai.txt + robots.txt artifacts.

Zero external runtime dependencies (Python standard library only).
"""

from __future__ import annotations

import json
import re
import time
import urllib.parse
from typing import Any, Dict, List, Optional

from .ai_gateway import AIGateway, _normalize_provider
from .core import (
    generate_ai_txt,
    generate_llms_full_txt,
    generate_llms_txt,
    generate_robots_txt,
    generate_schema_graph,
    resolve_config,
)
from .crawler import SitemapCrawler
from .net_guard import validate_public_url
from .presets import NICHE_PRESETS
from .validator import AEODiagnosticReport, validate_schema_jsonld_dict

VALID_NICHES = tuple(NICHE_PRESETS.keys())
VALID_CATEGORIES = (
    "DeveloperApplication",
    "SoftwareApplication",
    "SecurityApplication",
    "MultimediaApplication",
    "BusinessApplication",
    "LocalBusiness",
)


def _infer_niche_and_category(text: str) -> tuple[str, str]:
    lower = text.lower()
    if any(k in lower for k in ("agent", "swarm", "llm", "neural", "inference", "mcp")):
        return "ai_swarm", "DeveloperApplication"
    if any(k in lower for k in ("security", "zero-trust", "vault", "osint", "firewall", "cipher")):
        return "cybersecurity", "SecurityApplication"
    if any(k in lower for k in ("3d", "webgl", "shader", "spatial", "three.js")):
        return "spatial_3d", "MultimediaApplication"
    if any(k in lower for k in ("shop", "store", "cart", "checkout", "apparel", "ecommerce")):
        return "ecommerce", "BusinessApplication"
    if any(k in lower for k in ("dental", "plumbing", "clinic", "roofing", "hvac", "local service")):
        return "local_business", "LocalBusiness"
    if any(k in lower for k in ("saas", "cloud", "workflow", "dashboard", "analytics", "platform")):
        return "saas", "SoftwareApplication"
    return "developer_tools", "DeveloperApplication"


def _clean_site_title(raw_title: str, fallback_host: str) -> str:
    if not raw_title:
        return fallback_host
    for sep in (" | ", " — ", " - ", " :: ", " // "):
        if sep in raw_title:
            head = raw_title.split(sep, 1)[0].strip()
            if len(head) >= 2:
                return head[:80]
    return raw_title.strip()[:80] or fallback_host


def _page_h1(page: Dict[str, Any]) -> str:
    if page.get("h1"):
        return str(page["h1"]).strip()
    for h in page.get("headings") or []:
        if isinstance(h, dict) and str(h.get("tag", "")).lower() == "h1" and h.get("text"):
            return str(h["text"]).strip()
    return ""


def _build_deterministic_config_from_crawl(
    crawl_report: Dict[str, Any],
    origin: str,
    hostname: str,
) -> Dict[str, Any]:
    """Derives a clean, grounded AEO config directly from scraped pages."""
    pages = crawl_report.get("pages") or []
    ok_pages = [p for p in pages if p.get("status") == 200]
    root_page = ok_pages[0] if ok_pages else (pages[0] if pages else {})

    raw_title = str(root_page.get("title") or "").strip()
    site_name = _clean_site_title(raw_title, hostname)
    h1 = _page_h1(root_page)
    description = str(root_page.get("description") or "").strip()

    if not description:
        titles = [str(p.get("title") or "").strip() for p in ok_pages[:4] if p.get("title")]
        description = (
            f"{site_name} ({hostname}) — structured web platform covering {', '.join(titles)}."
            if titles
            else f"{site_name} official website and documentation at {origin}."
        )

    tagline = h1 if (h1 and len(h1) <= 110) else (raw_title[:110] or f"{site_name} Official Hub")
    corpus = " ".join(
        f"{p.get('title', '')} {_page_h1(p)} {p.get('description', '')}" for p in ok_pages[:10]
    )
    niche, category = _infer_niche_and_category(corpus)

    # Build real discovered surfaces from scraped pages
    surfaces: List[Dict[str, Any]] = []
    seen_paths = set()
    for p in ok_pages[:12]:
        purl = str(p.get("url") or "")
        parsed = urllib.parse.urlparse(purl)
        path = parsed.path or "/"
        if path in seen_paths:
            continue
        seen_paths.add(path)
        ptitle = _clean_site_title(str(p.get("title") or ""), path)
        pdesc = str(p.get("description") or _page_h1(p) or f"Discovered page at {path}").strip()[:160]
        surfaces.append({"name": ptitle, "path": path, "url": purl, "indexed": True, "notes": pdesc})

    if not surfaces:
        surfaces = [{"name": "Home", "path": "/", "url": f"{origin}/", "indexed": True, "notes": tagline}]

    # Extract concrete features from page H1s / titles
    features: List[str] = []
    for p in ok_pages[:8]:
        cand = (_page_h1(p) or str(p.get("title") or "")).strip()
        if cand and cand not in features and len(cand) >= 4:
            features.append(cand[:110])
    if len(features) < 3:
        features.extend([
            f"Canonical web surface at {origin}/",
            f"Multi-page semantic structure ({len(ok_pages)} crawled page(s))",
            "Structured Schema.org JSON-LD @graph & llms.txt discovery",
        ])

    # Build grounded FAQs
    faqs = [
        {
            "question": f"What is {site_name}?",
            "answer": description,
        },
        {
            "question": f"What key pages and resources are available on {hostname}?",
            "answer": "Primary indexed sections include: "
            + ", ".join(f"{s['name']} ({s['path']})" for s in surfaces[:5])
            + ".",
        },
        {
            "question": f"How can AI search engines and developers access {site_name}?",
            "answer": f"Visit {origin}/ or ingest {origin}/llms.txt and {origin}/schema-graph.json for machine-readable entity grounding.",
        },
    ]

    breadcrumbs = [
        {"position": idx, "name": s["name"], "item": s["url"]}
        for idx, s in enumerate(surfaces[:4], start=1)
    ]

    return {
        "site_name": site_name,
        "domain": hostname,
        "base_url": origin,
        "publisher_name": site_name,
        "legal_name": site_name,
        "tagline": tagline,
        "summary": description[:160],
        "description": description,
        "niche": niche,
        "category": category,
        "features": features[:8],
        "faqs": faqs,
        "surfaces": surfaces,
        "breadcrumbs": breadcrumbs,
        "same_as": [f"{origin}/"],
    }


def _extract_json_object(raw_text: str) -> Optional[Dict[str, Any]]:
    if not raw_text:
        return None
    cleaned = raw_text.strip()
    # Strip markdown code fences if present
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def generate_aeo_from_domain(
    target_url: str,
    *,
    provider: str = "agy_bridge",
    model: Optional[str] = None,
    max_pages: int = 6,
    timeout: float = 6.0,
    allow_private: bool = False,
) -> Dict[str, Any]:
    """
    Crawls a public domain via sitemap.xml and link discovery, then runs the
    requested AI agent (AGY, Hermes, Codex, Claude Code, Ollama, etc.) to
    synthesize a complete AEO configuration and compile all AEO artifacts.
    """
    validated_url = validate_public_url(target_url, allow_private=allow_private)
    parsed_root = urllib.parse.urlparse(validated_url)
    origin = f"{parsed_root.scheme}://{parsed_root.netloc}"
    hostname = parsed_root.netloc

    clamped_pages = max(1, min(15, int(max_pages)))
    crawl_t0 = time.time()
    crawler = SitemapCrawler(validated_url, max_pages=clamped_pages, timeout=timeout, allow_private=allow_private)
    crawl_report = crawler.crawl_and_audit()
    crawl_ms = round((time.time() - crawl_t0) * 1000.0, 1)

    base_cfg = _build_deterministic_config_from_crawl(crawl_report, origin, hostname)

    pages = crawl_report.get("pages") or []
    pages_digest_lines: List[str] = []
    for p in pages[:clamped_pages]:
        schema_types = [
            str(s.get("@type")) for s in (p.get("schemas") or []) if isinstance(s, dict) and s.get("@type")
        ]
        pages_digest_lines.append(
            f"- URL: {p.get('url')} | HTTP {p.get('status')} | Title: {p.get('title') or '(none)'} "
            f"| H1: {_page_h1(p) or '(none)'} | Words: {p.get('word_count', 0)} "
            f"| Schemas: {', '.join(schema_types) or 'none'} "
            f"| Desc: {str(p.get('description') or '')[:140]}"
        )

    norm_provider = _normalize_provider(provider)
    agent_exec: Dict[str, Any] = {
        "requested_provider": provider,
        "used_provider": "heuristic",
        "model": "crawl-extractor-v2",
        "mode": "crawl_deterministic",
        "latency_ms": 0.0,
        "notice": "Synthesized deterministically from crawled sitemap and page metadata.",
    }

    if norm_provider != "heuristic":
        gateway = AIGateway()
        agent_prompt = (
            f"You scraped the website {origin} (sitemap_detected={crawl_report.get('sitemap_detected')}, "
            f"sitemap_urls={crawl_report.get('total_indexed_urls', 0)}, pages_crawled={len(pages)}).\n\n"
            f"Scraped Pages Digest:\n" + ("\n".join(pages_digest_lines) or f"- {origin}/ (no HTML content returned)") + "\n\n"
            f"Generate a complete, factual Answer Engine Optimization (AEO) configuration grounded strictly in these scraped pages.\n"
            f"Return ONLY a single valid JSON object (no markdown fences, no commentary) with exact keys:\n"
            f"{{\n"
            f'  "site_name": "Brand or Site Name",\n'
            f'  "publisher_name": "Organization or Publisher Name",\n'
            f'  "tagline": "Concise 1-line tagline (<=100 chars)",\n'
            f'  "description": "Concrete 2-sentence factual overview (60-260 chars)",\n'
            f'  "niche": one of {list(VALID_NICHES)},\n'
            f'  "category": one of {list(VALID_CATEGORIES)},\n'
            f'  "features": ["4 to 6 concrete capabilities/topics found on the site"],\n'
            f'  "faqs": [{{"question": "...", "answer": "..."}} (3 to 4 factual Q&As grounded in the site)]\n'
            f"}}"
        )
        llm_res = gateway.complete_prompt(
            agent_prompt,
            system_prompt="You are an AEO/Schema.org compiler agent. Return strictly valid JSON with no markdown prose.",
            provider=norm_provider,
            model=model,
            timeout=45,
        )
        if llm_res.get("success") and llm_res.get("content"):
            parsed_ai = _extract_json_object(llm_res["content"])
            if parsed_ai:
                for key in ("site_name", "publisher_name", "tagline", "description"):
                    val = parsed_ai.get(key)
                    if isinstance(val, str) and val.strip():
                        base_cfg[key] = val.strip()
                if parsed_ai.get("niche") in VALID_NICHES:
                    base_cfg["niche"] = parsed_ai["niche"]
                if parsed_ai.get("category") in VALID_CATEGORIES:
                    base_cfg["category"] = parsed_ai["category"]
                if isinstance(parsed_ai.get("features"), list):
                    clean_feats = [str(x).strip() for x in parsed_ai["features"] if str(x).strip()][:8]
                    if clean_feats:
                        base_cfg["features"] = clean_feats
                if isinstance(parsed_ai.get("faqs"), list):
                    clean_faqs = []
                    for item in parsed_ai["faqs"][:6]:
                        if isinstance(item, dict) and item.get("question") and item.get("answer"):
                            clean_faqs.append({
                                "question": str(item["question"]).strip(),
                                "answer": str(item["answer"]).strip(),
                            })
                    if clean_faqs:
                        base_cfg["faqs"] = clean_faqs
                base_cfg["summary"] = base_cfg["description"][:160]
                base_cfg["legal_name"] = base_cfg["publisher_name"]

                agent_exec = {
                    "requested_provider": provider,
                    "used_provider": llm_res["provider"],
                    "model": llm_res["model"],
                    "mode": "live_agent",
                    "latency_ms": llm_res["latency_ms"],
                    "notice": f"Synthesized via live AI agent '{llm_res['provider']}' ({llm_res['model']}) from {len(pages)} crawled page(s).",
                }
            else:
                agent_exec["mode"] = "crawl_deterministic_fallback"
                agent_exec["latency_ms"] = llm_res.get("latency_ms", 0.0)
                agent_exec["notice"] = (
                    f"Agent '{llm_res['provider']}' responded without parseable JSON; populated inputs from real crawled page metadata."
                )
        else:
            agent_exec["mode"] = "crawl_deterministic_fallback"
            agent_exec["latency_ms"] = llm_res.get("latency_ms", 0.0)
            agent_exec["notice"] = (
                f"Agent '{provider}' unavailable ({llm_res.get('error', 'unreachable')}); populated inputs from real crawled page metadata."
            )

    # Compile full AEO artifacts & compute real validation score
    niche = base_cfg.get("niche", "developer_tools")
    resolved = resolve_config(base_cfg, niche=niche)
    schema = generate_schema_graph(resolved, niche=niche)
    llms_txt = generate_llms_txt(resolved, niche=niche)
    llms_full_txt = generate_llms_full_txt(resolved, niche=niche)
    ai_txt = generate_ai_txt(resolved, niche=niche)
    robots_txt = generate_robots_txt(resolved, niche=niche)

    val_report = AEODiagnosticReport(origin)
    validate_schema_jsonld_dict(schema, val_report)

    return {
        "target_url": validated_url,
        "origin": origin,
        "config": {
            "site_name": resolved["site_name"],
            "domain": resolved["domain"],
            "publisher_name": resolved["publisher_name"],
            "tagline": resolved["tagline"],
            "description": resolved["description"],
            "niche": niche,
            "category": resolved["category"],
            "features": resolved.get("features", []),
            "faqs": resolved.get("faqs", []),
            "surfaces": resolved.get("surfaces", []),
            "breadcrumbs": resolved.get("breadcrumbs", []),
            "same_as": resolved.get("same_as", []),
        },
        "crawl_summary": {
            "origin": origin,
            "crawl_ms": crawl_ms,
            "sitemap_detected": bool(crawl_report.get("sitemap_detected")),
            "sitemap_urls_found": int(crawl_report.get("total_indexed_urls", 0)),
            "pages_scraped": len(pages),
            "existing_aeo_score": crawl_report.get("overall_aeo_health_score", 0),
            "pages": [
                {
                    "url": p.get("url"),
                    "status": p.get("status"),
                    "title": p.get("title") or "",
                    "h1": _page_h1(p),
                    "word_count": p.get("word_count", 0),
                    "schema_count": p.get("schema_count", 0),
                }
                for p in pages
            ],
        },
        "agent_execution": agent_exec,
        "artifacts": {
            "schema": schema,
            "llms_txt": llms_txt,
            "llms_full_txt": llms_full_txt,
            "ai_txt": ai_txt,
            "robots_txt": robots_txt,
            "score": round(val_report.score, 1),
            "validation": val_report.to_dict(),
        },
    }

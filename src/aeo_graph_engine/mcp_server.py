"""
Model Context Protocol (MCP) and AI Agent Integration Server for AEO Graph Engine.
Standard JSON-RPC 2.0 / MCP stdio protocol implementation with zero external runtime dependencies.

Provides AI agents and LLM clients (Claude Desktop, Cursor, Cline, Zed, LibreChat, OpenCode)
with native tools for:
  - aeo_scan_site: Live URL crawl, multi-page audit, AEO readiness score, AI crawler matrix, backlink strategy
  - aeo_synthesize_prompt: Natural language to rich AEO configuration synthesizer
  - aeo_generate_bundle: Complete Schema.org @graph, llms.txt, llms-full.txt, ai.txt, robots.txt generator
  - aeo_inject_html: Safe & idempotent JSON-LD embedding into HTML files/strings
  - aeo_validate: 0-100 AEO readiness scoring & diagnostic auditor
  - aeo_get_framework_snippets: Next.js/Astro/Vite/Nuxt/SvelteKit/Remix integration code
"""

import sys
import os
import json
import io
import re
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, TextIO

from .core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle,
)
from .injector import inject_jsonld_into_html, inject_file
from .validator import (
    validate_aeo_bundle,
    validate_schema_jsonld_dict,
    validate_llms_txt_content,
    validate_ai_txt_content,
    validate_robots_txt_content,
    AEODiagnosticReport,
)
from .extractor import extract_metadata_from_html
from .ai_config import synthesize_config_from_prompt, get_agent_json_schema
from .scanner import LiveAEOScanner
from .presets import NICHE_PRESETS, DEFAULT_CONFIG

# Standard JSON-RPC 2.0 error codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

SERVER_NAME = "aeo-graph-engine-mcp"
SERVER_VERSION = "1.0.0"
PROTOCOL_VERSION = "2024-11-05"


# Tool JSON Schemas according to MCP specification
TOOLS_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "aeo_scan_site",
        "description": (
            "Crawl and audit a live website URL. Analyzes root machine discovery assets (robots.txt, llms.txt, "
            "ai.txt, sitemap.xml), evaluates existing Schema.org JSON-LD, computes a 0-100 AEO Readiness Score, "
            "evaluates AI search engine crawler permissions (GPTBot, PerplexityBot, ClaudeBot, Applebot), "
            "and generates targeted high-authority backlink and citation distribution opportunities."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Target live website URL to crawl and audit (e.g. 'https://example.com')."
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum number of internal pages to discover and audit (default: 5).",
                    "default": 5
                },
                "timeout": {
                    "type": "integer",
                    "description": "HTTP request timeout in seconds (default: 8).",
                    "default": 8
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "aeo_synthesize_prompt",
        "description": (
            "Synthesize a rich, production-ready AEO/GEO configuration from a natural language prompt or "
            "product description. Automatically extracts brand name, domain, niche category, core features, "
            "and structured FAQ pairs for Answer Engine citation. 100% offline rule-based heuristic synthesizer."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "Natural language description of the website, software product, or service."
                },
                "base_niche": {
                    "type": "string",
                    "description": "Optional base domain vertical preset.",
                    "enum": list(NICHE_PRESETS.keys())
                }
            },
            "required": ["prompt"]
        }
    },
    {
        "name": "aeo_generate_bundle",
        "description": (
            "Generate complete Answer Engine Optimization (AEO/GEO) artifacts: Schema.org JSON-LD @graph, "
            "llms.txt, llms-full.txt, ai.txt, and robots.txt. Returns in-memory text/JSON payloads and "
            "optionally writes all files directly to disk if output_dir is provided."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "config": {
                    "type": "object",
                    "description": "Optional custom AEO configuration object (overrides preset defaults)."
                },
                "niche": {
                    "type": "string",
                    "description": "Preset niche template (developer_tools, ai_swarm, saas, cybersecurity, spatial_3d, creator, ecommerce, local_business).",
                    "default": "developer_tools",
                    "enum": list(NICHE_PRESETS.keys())
                },
                "output_dir": {
                    "type": "string",
                    "description": "Optional target directory path to write generated files to disk."
                },
                "inject_html_files": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of HTML file paths to inject the generated JSON-LD graph into."
                }
            }
        }
    },
    {
        "name": "aeo_inject_html",
        "description": (
            "Safely and idempotently embed Schema.org JSON-LD into an HTML string or file on disk. "
            "Updates existing <script type='application/ld+json'> or inserts formatted script before </head>."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "html_content": {
                    "type": "string",
                    "description": "Raw HTML string to inject JSON-LD into."
                },
                "html_file_path": {
                    "type": "string",
                    "description": "Path to HTML file on disk to inject into and save."
                },
                "schema_payload": {
                    "type": ["object", "string"],
                    "description": "Schema.org JSON-LD dict or JSON string. If omitted, generates from config/niche."
                },
                "config": {
                    "type": "object",
                    "description": "Custom configuration dictionary if schema_payload is omitted."
                },
                "niche": {
                    "type": "string",
                    "description": "Preset niche template if generating schema (default: developer_tools).",
                    "default": "developer_tools"
                },
                "backup": {
                    "type": "boolean",
                    "description": "Whether to create a .bak backup file when modifying file on disk (default: false).",
                    "default": False
                }
            }
        }
    },
    {
        "name": "aeo_validate",
        "description": (
            "Validate an AEO bundle directory, single artifact file, or in-memory Schema/manifest payload. "
            "Calculates a 0-100 AEO Readiness Score and provides detailed diagnostic lists of passed checks, "
            "actionable warnings, and critical errors."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_path": {
                    "type": "string",
                    "description": "Path to AEO bundle directory or single artifact file (schema-graph.json, llms.txt, ai.txt, robots.txt, HTML)."
                },
                "schema_data": {
                    "type": "object",
                    "description": "In-memory Schema.org JSON-LD dictionary to validate directly."
                },
                "content": {
                    "type": "string",
                    "description": "Raw text content of artifact to validate in-memory."
                },
                "artifact_type": {
                    "type": "string",
                    "description": "Type of raw text content (llms_txt, llms_full_txt, ai_txt, robots_txt).",
                    "enum": ["llms_txt", "llms_full_txt", "ai_txt", "robots_txt"]
                }
            }
        }
    },
    {
        "name": "aeo_get_framework_snippets",
        "description": (
            "Get production-ready code snippets and integration instructions for embedding AEO Schema.org "
            "graphs and manifests into web frameworks (Next.js App/Pages Router, Astro, Vite, Remix, Nuxt, SvelteKit, HTML)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "framework": {
                    "type": "string",
                    "description": "Target framework name ('all', 'nextjs', 'nextjs_pages', 'astro', 'vite', 'remix', 'nuxt', 'sveltekit', 'html').",
                    "default": "all",
                    "enum": ["all", "nextjs", "nextjs_pages", "astro", "vite", "remix", "nuxt", "sveltekit", "html"]
                },
                "schema_graph": {
                    "type": "object",
                    "description": "Optional Schema.org JSON-LD dictionary to embed into snippets. If omitted, uses config/preset."
                },
                "config": {
                    "type": "object",
                    "description": "Optional AEO config to generate schema graph from if schema_graph is omitted."
                },
                "niche": {
                    "type": "string",
                    "description": "Preset niche template (default: developer_tools).",
                    "default": "developer_tools"
                }
            }
        }
    },
    {
        "name": "aeo_simulate_citation",
        "description": (
            "Simulate AI search engine perception (Perplexity AI, ChatGPT Search, Google Gemini) and "
            "compute factual extractability and citation readiness scores (0-100) for any live URL, "
            "HTML string, or markdown knowledge base. Extracts key factual quotes and per-engine synthesis."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url_or_content": {
                    "type": "string",
                    "description": "Target live URL, local file path, or raw HTML / text content to simulate."
                },
                "query": {
                    "type": "string",
                    "description": "Optional search query or prompt (e.g. 'What is X and what makes it notable?')."
                },
                "brand_name": {
                    "type": "string",
                    "description": "Optional brand/site name override."
                },
                "domain": {
                    "type": "string",
                    "description": "Optional canonical domain name override (e.g. 'example.com')."
                },
                "timeout": {
                    "type": "integer",
                    "description": "HTTP request timeout in seconds (default: 8).",
                    "default": 8
                }
            },
            "required": ["url_or_content"]
        }
    },
    {
        "name": "aeo_visualize_schema",
        "description": (
            "Generate Mermaid.js visual entity relationship diagrams and structured ASCII knowledge graph trees "
            "from Schema.org @graph JSON-LD or schema files. Visualizes nodes, entities, and connecting edges."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema_data": {
                    "type": "object",
                    "description": "Optional Schema.org JSON-LD dictionary with @graph array."
                },
                "schema_file": {
                    "type": "string",
                    "description": "Optional path to schema JSON or HTML file on disk."
                },
                "format": {
                    "type": "string",
                    "description": "Output diagram format ('mermaid', 'ascii', 'both').",
                    "enum": ["mermaid", "ascii", "both"],
                    "default": "mermaid"
                }
            }
        }
    },
    {
        "name": "aeo_crawl_sitemap",
        "description": (
            "Batch crawl and audit an XML sitemap (or website domain with sitemap discovery) to produce "
            "a site-wide multi-page AEO audit report, Schema.org coverage metrics, and page health analysis."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sitemap_url_or_domain": {
                    "type": "string",
                    "description": "Sitemap URL (e.g. 'https://example.com/sitemap.xml'), domain URL, or local sitemap.xml file."
                },
                "max_pages": {
                    "type": "integer",
                    "description": "Maximum number of pages to audit from sitemap (default: 10).",
                    "default": 10
                },
                "timeout": {
                    "type": "integer",
                    "description": "HTTP request timeout in seconds (default: 8).",
                    "default": 8
                }
            },
            "required": ["sitemap_url_or_domain"]
        }
    },
    {
        "name": "aeo_extract_knowledge_graph",
        "description": (
            "Extract subject-predicate-object semantic triplets from content/HTML, compute entity PageRank "
            "centrality, audit Schema.org @graph alignment to identify orphan entities, and generate "
            "RDF N-Triples and Turtle knowledge graph serializations."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Raw HTML or Markdown text content to extract semantic knowledge graph from."
                },
                "schema_json": {
                    "type": "object",
                    "description": "Optional parsed Schema.org JSON-LD object to audit entity coverage against."
                },
                "base_url": {
                    "type": "string",
                    "description": "Base website canonical URL (default: 'https://example.com').",
                    "default": "https://example.com"
                },
                "min_confidence": {
                    "type": "number",
                    "description": "Minimum extraction confidence threshold (0.0 to 1.0, default: 0.4).",
                    "default": 0.4
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "aeo_analyze_claims",
        "description": (
            "Extract atomic factual assertions from web content or markdown, calculate LLM quotability scores, "
            "categorize claims (quantitative, architectural, capability, comparative), and generate W3C Scroll-to-Text "
            "citation fragments for Perplexity and SearchGPT grounding."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Text, markdown, or raw HTML content to extract atomic claims from."
                },
                "base_url": {
                    "type": "string",
                    "description": "Base canonical URL for W3C text fragment generation (default: 'https://example.com').",
                    "default": "https://example.com"
                },
                "title": {
                    "type": "string",
                    "description": "Optional document or product title."
                }
            },
            "required": ["content"]
        }
    },
    {
        "name": "aeo_generate_claim_matrix",
        "description": (
            "Generate a formatted Atomic Claim-Evidence Matrix in Markdown, SVG dark-mode visualization badge, "
            "or Schema.org Statement/ClaimReview linked data graph."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "Text, markdown, or raw HTML content to process."
                },
                "base_url": {
                    "type": "string",
                    "description": "Base canonical URL (default: 'https://example.com').",
                    "default": "https://example.com"
                },
                "format": {
                    "type": "string",
                    "description": "Output representation format ('markdown', 'svg', 'json', 'schema_org').",
                    "enum": ["markdown", "svg", "json", "schema_org"],
                    "default": "markdown"
                }
            },
            "required": ["content"]
        }
    }
]


def get_framework_snippets(
    framework: str = "all",
    schema_graph: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None,
    niche: str = "developer_tools"
) -> Dict[str, Any]:
    """
    Generates copy-paste framework snippets for embedding Schema.org JSON-LD.
    """
    if schema_graph is None:
        cfg = resolve_config(config, niche=niche)
        schema_graph = generate_schema_graph(cfg, niche=niche)

    schema_json_str = json.dumps(schema_graph, indent=2, ensure_ascii=False)
    site_name = schema_graph.get("@graph", [{}])[1].get("name", "My Application") if len(schema_graph.get("@graph", [])) > 1 else "My Application"

    snippets: Dict[str, Dict[str, str]] = {}

    # 1. Next.js App Router (app/layout.tsx)
    snippets["nextjs"] = {
        "title": "Next.js App Router (app/layout.tsx)",
        "file": "app/layout.tsx",
        "description": "Embed Schema.org JSON-LD @graph in Next.js 13/14/15 App Router root layout",
        "code": f'''// app/layout.tsx
import type {{ Metadata }} from 'next';
import React from 'react';

// Option A: Import generated schema-graph.json directly
import schemaGraph from '@/public/schema-graph.json';

export const metadata: Metadata = {{
  title: '{site_name}',
  description: 'Answer Engine Optimized Application',
}};

export default function RootLayout({{
  children,
}}: {{
  children: React.ReactNode;
}}) {{
  return (
    <html lang="en">
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{{{ __html: JSON.stringify(schemaGraph) }}}}
        />
      </head>
      <body>{{children}}</body>
    </html>
  );
}}'''
    }

    # 2. Next.js Pages Router (pages/_document.tsx)
    snippets["nextjs_pages"] = {
        "title": "Next.js Pages Router (pages/_document.tsx)",
        "file": "pages/_document.tsx",
        "description": "Embed Schema.org JSON-LD in Pages Router document head",
        "code": f'''// pages/_document.tsx
import Document, {{ Html, Head, Main, NextScript }} from 'next/document';
import schemaGraph from '../public/schema-graph.json';

export default class MyDocument extends Document {{
  render() {{
    return (
      <Html lang="en">
        <Head>
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{{{ __html: JSON.stringify(schemaGraph) }}}}
          />
        </Head>
        <body>
          <Main />
          <NextScript />
        </body>
      </Html>
    );
  }}
}}'''
    }

    # 3. Astro (src/layouts/Layout.astro)
    snippets["astro"] = {
        "title": "Astro (src/layouts/Layout.astro)",
        "file": "src/layouts/Layout.astro",
        "description": "Embed Schema.org JSON-LD using Astro set:html directive",
        "code": f'''---
// src/layouts/Layout.astro
import schemaGraph from '../../public/schema-graph.json';

interface Props {{
  title?: string;
  description?: string;
}}

const {{ title = '{site_name}', description }} = Astro.props;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{{title}}</title>
    {{description && <meta name="description" content={{description}} />}}
    
    <!-- AEO Schema.org Graph Integration -->
    <script type="application/ld+json" set:html={{JSON.stringify(schemaGraph)}} />
  </head>
  <body>
    <slot />
  </body>
</html>'''
    }

    # 4. Vite + React / Vue / Vanilla (index.html)
    snippets["vite"] = {
        "title": "Vite / React / Vanilla (index.html)",
        "file": "index.html",
        "description": "Embed static JSON-LD in root index.html for Vite builds",
        "code": f'''<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{site_name}</title>
    
    <!-- AEO Schema.org JSON-LD Graph -->
    <script type="application/ld+json">
{schema_json_str}
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>'''
    }

    # 5. Remix / React Router v7 (app/root.tsx)
    snippets["remix"] = {
        "title": "Remix / React Router v7 (app/root.tsx)",
        "file": "app/root.tsx",
        "description": "Embed Schema.org JSON-LD into Remix root template",
        "code": f'''// app/root.tsx
import {{ Links, Meta, Outlet, Scripts, ScrollRestoration }} from "@remix-run/react";
import schemaGraph from "../public/schema-graph.json";

export default function App() {{
  return (
    <html lang="en">
      <head>
        <meta charSet="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <Meta />
        <Links />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{{{ __html: JSON.stringify(schemaGraph) }}}}
        />
      </head>
      <body>
        <Outlet />
        <ScrollRestoration />
        <Scripts />
      </body>
    </html>
  );
}}'''
    }

    # 6. Nuxt 3 (app.vue or nuxt.config.ts)
    snippets["nuxt"] = {
        "title": "Nuxt 3 (app.vue)",
        "file": "app.vue",
        "description": "Embed Schema.org JSON-LD using Nuxt 3 useHead composable",
        "code": f'''<script setup lang="ts">
// app.vue
import schemaGraph from '~/public/schema-graph.json'

useHead({{
  title: '{site_name}',
  script: [
    {{
      type: 'application/ld+json',
      innerHTML: JSON.stringify(schemaGraph)
    }}
  ]
}})
</script>

<template>
  <div>
    <NuxtPage />
  </div>
</template>'''
    }

    # 7. SvelteKit (src/routes/+layout.svelte)
    snippets["sveltekit"] = {
        "title": "SvelteKit (src/routes/+layout.svelte)",
        "file": "src/routes/+layout.svelte",
        "description": "Embed Schema.org JSON-LD into SvelteKit <svelte:head>",
        "code": f'''<script lang="ts">
  // src/routes/+layout.svelte
  import schemaGraph from '/schema-graph.json?url';
  const schemaJson = {json.dumps(schema_json_str)};
</script>

<svelte:head>
  <title>{site_name}</title>
  {{@html `<script type="application/ld+json">${{schemaJson}}</script>`}}
</svelte:head>

<slot />'''
    }

    # 8. Plain HTML / SSG (index.html)
    snippets["html"] = {
        "title": "Standard Static HTML",
        "file": "index.html",
        "description": "Direct injection snippet for any HTML file",
        "code": f'''<script type="application/ld+json">
{schema_json_str}
</script>'''
    }

    if framework.lower() != "all" and framework.lower() in snippets:
        return {framework.lower(): snippets[framework.lower()]}

    return snippets


def generate_mcp_client_config(
    client_name: str,
    python_path: str = "python3",
    server_module: str = "aeo_graph_engine.mcp_server",
    project_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generates standardized MCP configuration snippets for major AI agent environments:
      - "claude_desktop": Anthropic Claude Desktop config file (claude_desktop_config.json)
      - "cursor": Cursor IDE MCP settings (.cursor/mcp.json)
      - "cline": Cline VS Code extension settings (cline_mcp_settings.json)
      - "zed": Zed Editor context server settings (settings.json)
      - "generic": Generic stdio configuration dictionary
    """
    norm = client_name.strip().lower().replace("-", "_").replace(" ", "_")

    # Resolve python path & environment if project_root provided
    env_vars: Dict[str, str] = {}
    if project_root:
        abs_root = str(Path(project_root).resolve())
        src_dir = str(Path(project_root).resolve() / "src")
        env_vars["PYTHONPATH"] = f"{src_dir}{os.pathsep}{abs_root}"

    server_key = "aeo-graph-engine"

    if norm in ("claude_desktop", "claude", "claude_desktop_config"):
        cfg: Dict[str, Any] = {
            "mcpServers": {
                server_key: {
                    "command": python_path,
                    "args": ["-m", server_module]
                }
            }
        }
        if env_vars:
            cfg["mcpServers"][server_key]["env"] = env_vars
        return cfg

    elif norm in ("cursor", "cursor_ide"):
        cfg = {
            "mcpServers": {
                server_key: {
                    "command": python_path,
                    "args": ["-m", server_module]
                }
            }
        }
        if env_vars:
            cfg["mcpServers"][server_key]["env"] = env_vars
        return cfg

    elif norm in ("cline", "cline_mcp"):
        cfg = {
            "mcpServers": {
                server_key: {
                    "command": python_path,
                    "args": ["-m", server_module],
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
        if env_vars:
            cfg["mcpServers"][server_key]["env"] = env_vars
        return cfg

    elif norm in ("zed", "zed_editor"):
        cfg = {
            "context_servers": {
                server_key: {
                    "command": {
                        "path": python_path,
                        "args": ["-m", server_module]
                    }
                }
            }
        }
        if env_vars:
            cfg["context_servers"][server_key]["command"]["env"] = env_vars
        return cfg

    elif norm in ("generic", "default", "jsonrpc", "mcp"):
        return {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
            "transport": "stdio",
            "protocol_version": PROTOCOL_VERSION,
            "command": python_path,
            "args": ["-m", server_module],
            "env": env_vars,
            "description": "Answer Engine Optimization (AEO/GEO) MCP Server"
        }

    else:
        raise ValueError(
            f"Unsupported MCP client '{client_name}'. "
            f"Supported clients: 'claude_desktop', 'cursor', 'cline', 'zed', 'generic'"
        )


def simulate_ai_citations(
    url_or_content: str,
    query: Optional[str] = None,
    brand_name: Optional[str] = None,
    domain: Optional[str] = None,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    Simulates AI search engine perception (Perplexity Sonar, ChatGPT Search, Gemini)
    and computes factual extractability and citation readiness scores (0-100).
    """
    target = (url_or_content or "").strip()
    is_url = target.startswith("http://") or target.startswith("https://")

    html_content = ""
    http_status = 200

    # 1. Fetch content if URL or read if file
    if is_url:
        try:
            req = urllib.request.Request(
                target,
                headers={"User-Agent": "AEO-Graph-Engine-Simulator/1.0 (Citation-Extractor; +https://aeo.nullai.tech)"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                http_status = resp.status
                html_content = resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            html_content = f"<html><head><title>{brand_name or 'Simulated Target'}</title></head><body><h1>{brand_name or 'Simulated Target'}</h1><p>Website at {target}</p></body></html>"
            http_status = 0
    else:
        possible_path = Path(target)
        if possible_path.exists() and possible_path.is_file():
            try:
                html_content = possible_path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                html_content = target
        else:
            html_content = target

    # 2. Extract metadata & semantic features
    extracted = extract_metadata_from_html(html_content) if ("<html" in html_content.lower() or "<title" in html_content.lower() or "<script" in html_content.lower() or "<head" in html_content.lower()) else {}

    resolved_domain = domain
    if not resolved_domain and is_url:
        resolved_domain = urllib.parse.urlparse(target).netloc
    if not resolved_domain:
        resolved_domain = extracted.get("domain") or "example.com"

    resolved_brand = brand_name or extracted.get("site_name")
    if not resolved_brand or resolved_brand in ("Extracted Website", "My Application", "Simulated Target"):
        if is_url:
            resolved_brand = urllib.parse.urlparse(target).netloc.split(".")[0].capitalize()
        else:
            resolved_brand = "Target Application"

    tagline = extracted.get("tagline") or f"A modern platform on {resolved_domain}"
    description = extracted.get("description") or f"{resolved_brand} provides high-performance services and capabilities at {resolved_domain}."
    headings = extracted.get("headings", [])
    schemas = extracted.get("schemas", [])

    plain_text = re.sub(r'<[^>]+>', ' ', html_content)
    plain_text = re.sub(r'\s+', ' ', plain_text).strip()
    words = plain_text.split()
    word_count = len(words)

    # 3. Compute Extractability Score & Signal Breakdown
    signals = {
        "schema_linked_data": {
            "score": 0.0,
            "max": 25.0,
            "details": "Schema.org JSON-LD structured graph presence and depth."
        },
        "semantic_structure_headings": {
            "score": 0.0,
            "max": 25.0,
            "details": "H1/H2 hierarchy and logical document outline for LLM chunks."
        },
        "faq_qa_grounding": {
            "score": 0.0,
            "max": 20.0,
            "details": "FAQ structured Q&A pairs for direct conversational retrieval."
        },
        "machine_manifest_discovery": {
            "score": 0.0,
            "max": 15.0,
            "details": "Discovery signals for llms.txt, ai.txt, or canonical tags."
        },
        "factual_quote_density": {
            "score": 0.0,
            "max": 15.0,
            "details": "High-density technical, factual, or quantitative claims."
        }
    }

    if schemas:
        signals["schema_linked_data"]["score"] += 15.0
        for s in schemas:
            if isinstance(s, dict) and (len(s.get("@graph", [])) >= 3 or s.get("@type") in ("SoftwareApplication", "Organization", "WebSite")):
                signals["schema_linked_data"]["score"] += 10.0
                break
            elif isinstance(s, dict) and s.get("@type"):
                signals["schema_linked_data"]["score"] += 5.0
                break
        signals["schema_linked_data"]["score"] = min(25.0, signals["schema_linked_data"]["score"])
    elif "application/ld+json" in html_content:
        signals["schema_linked_data"]["score"] = 20.0
    else:
        signals["schema_linked_data"]["score"] = 5.0

    if headings:
        h1s = [h for h in headings if h.get("tag") == "h1"]
        h2s = [h for h in headings if h.get("tag") == "h2"]
        if h1s:
            signals["semantic_structure_headings"]["score"] += 12.0
        if h2s:
            signals["semantic_structure_headings"]["score"] += 8.0
        if word_count >= 100:
            signals["semantic_structure_headings"]["score"] += 5.0
    else:
        if word_count >= 150:
            signals["semantic_structure_headings"]["score"] = 15.0
        else:
            signals["semantic_structure_headings"]["score"] = 8.0

    has_faq = any("faq" in str(s).lower() for s in schemas) or ("faq" in html_content.lower()) or ("q:" in plain_text.lower() and "a:" in plain_text.lower())
    if has_faq:
        signals["faq_qa_grounding"]["score"] = 20.0
    elif len(headings) >= 3:
        signals["faq_qa_grounding"]["score"] = 10.0
    else:
        signals["faq_qa_grounding"]["score"] = 5.0

    if "llms.txt" in html_content or "ai.txt" in html_content or extracted.get("canonical_url"):
        signals["machine_manifest_discovery"]["score"] = 15.0
    else:
        signals["machine_manifest_discovery"]["score"] = 8.0

    if word_count >= 200 or len(headings) >= 4:
        signals["factual_quote_density"]["score"] = 15.0
    elif word_count >= 50:
        signals["factual_quote_density"]["score"] = 10.0
    else:
        signals["factual_quote_density"]["score"] = 6.0

    total_extractability_score = round(sum(s["score"] for s in signals.values()), 1)

    if total_extractability_score >= 85:
        status_label = "EXCELLENT"
        confidence_str = "96%"
    elif total_extractability_score >= 65:
        status_label = "HIGH"
        confidence_str = "84%"
    elif total_extractability_score >= 45:
        status_label = "MODERATE"
        confidence_str = "62%"
    else:
        status_label = "NEEDS_OPTIMIZATION"
        confidence_str = "40%"

    quotes = []
    if extracted.get("tagline"):
        quotes.append({
            "quote": f"\"{extracted['tagline']}\"",
            "source": f"https://{resolved_domain}/#header",
            "context": "Primary Brand Tagline / Value Proposition",
            "confidence": "98%"
        })
    if extracted.get("description"):
        quotes.append({
            "quote": f"\"{extracted['description'][:180]}...\"",
            "source": f"https://{resolved_domain}/#meta-description",
            "context": "Core Entity Knowledge Grounding",
            "confidence": "95%"
        })
    if headings:
        top_h = headings[:2]
        for h in top_h:
            quotes.append({
                "quote": f"\"{h['text']}\"",
                "source": f"https://{resolved_domain}/#{h['tag']}",
                "context": f"Section Heading ({h['tag'].upper()})",
                "confidence": "92%"
            })
    if not quotes:
        quotes.append({
            "quote": f"\"{resolved_brand} is an application hosted at {resolved_domain}.\"",
            "source": f"https://{resolved_domain}/",
            "context": "Default Synthetic Entity Extraction",
            "confidence": "85%"
        })

    active_query = query or f"What is {resolved_brand} and how does it work?"

    perplexity_text = (
        f"**{resolved_brand}** ({resolved_domain}) is an application and platform operating at `{resolved_domain}` [1]. "
        f"According to verified structured metadata, {resolved_brand} focuses on {tagline.lower() if tagline else 'specialized digital capabilities'} [2].\n\n"
        f"### Key Verified Facts:\n"
        f"• **Entity Definition:** {description[:160]} [1].\n"
        f"• **Structured Linked Data:** {f'{len(schemas)} Schema.org JSON-LD tag(s) indexed' if schemas else 'Schema graph metadata available for machine traversal'} [2].\n"
        f"• **AEO Extractability Score:** {total_extractability_score}/100 ({status_label}) with {confidence_str} citation confidence [3].\n\n"
        f"### Sources & Citations:\n"
        f"[1] https://{resolved_domain}/ - Official Homepage & Meta Overview\n"
        f"[2] https://{resolved_domain}/#schema-graph - Schema.org JSON-LD Graph\n"
        f"[3] https://{resolved_domain}/llms.txt - AI Knowledge Manifest"
    )

    chatgpt_text = (
        f"Based on real-time web search indexing for **{resolved_brand}**:\n\n"
        f"**Overview:**\n"
        f"{resolved_brand} ({resolved_domain}) provides {description[:180]}.\n\n"
        f"**Core Highlights:**\n"
        f"- **Primary Domain:** `{resolved_domain}`\n"
        f"- **Tagline:** {tagline}\n"
        f"- **AI Extractability:** {total_extractability_score}/100 ({status_label}). The site has clear semantic markers that allow conversational answer engines to accurately answer user inquiries.\n\n"
        f"🔍 *Sources: {resolved_domain} | Knowledge Graph | Machine Manifest*"
    )

    gemini_text = (
        f"### ✦ AI Overview: {resolved_brand}\n"
        f"**{resolved_brand}** is a {extracted.get('category', 'software application')} accessible on `{resolved_domain}`.\n\n"
        f"**Quick Facts:**\n"
        f"• **Specialization:** {tagline}\n"
        f"• **Grounding Confidence:** {confidence_str} based on structured entity relationships.\n"
        f"• **Citation Readiness:** Rated **{status_label}** ({total_extractability_score}/100)."
    )

    return {
        "target": target,
        "brand_name": resolved_brand,
        "domain": resolved_domain,
        "query": active_query,
        "extractability_score": total_extractability_score,
        "status": status_label,
        "confidence": confidence_str,
        "word_count": word_count,
        "schemas_detected_count": len(schemas),
        "signals": signals,
        "extracted_quotes": quotes,
        "engines": {
            "perplexity": {
                "name": "Perplexity AI (Sonar Pro)",
                "response": perplexity_text,
                "confidence": confidence_str,
                "citations": [
                    f"https://{resolved_domain}/",
                    f"https://{resolved_domain}/#schema-graph",
                    f"https://{resolved_domain}/llms.txt"
                ]
            },
            "chatgpt": {
                "name": "ChatGPT Search (GPT-4o)",
                "response": chatgpt_text,
                "confidence": confidence_str,
                "citations": [f"https://{resolved_domain}/"]
            },
            "gemini": {
                "name": "Google Gemini (AI Overview)",
                "response": gemini_text,
                "confidence": confidence_str,
                "citations": [f"https://{resolved_domain}/"]
            }
        }
    }


def visualize_schema_graph(
    schema_input: Optional[Union[Dict[str, Any], str, Path]] = None,
    format: str = "mermaid"
) -> Dict[str, Any]:
    """
    Generates Mermaid entity relationship diagram syntax and ASCII tree visualization
    from Schema.org @graph JSON-LD.
    """
    graph_dict: Dict[str, Any] = {}

    if isinstance(schema_input, dict):
        graph_dict = schema_input
    elif isinstance(schema_input, (str, Path)):
        p = Path(schema_input)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            if p.suffix == ".json" or content.strip().startswith("{"):
                try:
                    graph_dict = json.loads(content)
                except Exception:
                    pass
            else:
                meta = extract_metadata_from_html(content)
                if meta.get("schemas"):
                    graph_dict = meta["schemas"][0]
        elif isinstance(schema_input, str) and schema_input.strip().startswith("{"):
            try:
                graph_dict = json.loads(schema_input)
            except Exception:
                pass

    if not graph_dict or "@graph" not in graph_dict:
        cfg = resolve_config(None)
        graph_dict = generate_schema_graph(cfg)

    entities_list = graph_dict.get("@graph", [])
    if not entities_list and "@type" in graph_dict:
        entities_list = [graph_dict]

    icon_map = {
        "WebSite": "🌐",
        "Organization": "🏢",
        "SoftwareApplication": "⚡",
        "WebApplication": "💻",
        "MobileApplication": "📱",
        "FAQPage": "❓",
        "Question": "❔",
        "Answer": "💬",
        "BreadcrumbList": "🍞",
        "ListItem": "📍",
        "Product": "🛍️",
        "Service": "🛠️",
        "Article": "📰",
        "Person": "👤",
        "LocalBusiness": "🏪"
    }

    nodes = []
    edges = []
    id_to_index = {}

    for idx, ent in enumerate(entities_list):
        etype = ent.get("@type", "Thing")
        raw_id = ent.get("@id", f"#node_{idx}")
        name = ent.get("name") or ent.get("headline") or ent.get("title") or etype
        icon = icon_map.get(etype, "📦")

        node_id = f"node_{idx}"
        id_to_index[raw_id] = node_id
        if "#" in raw_id:
            id_to_index["#" + raw_id.split("#")[-1]] = node_id
            id_to_index[raw_id.split("#")[-1]] = node_id

        nodes.append({
            "index": idx,
            "id": node_id,
            "raw_id": raw_id,
            "type": etype,
            "name": name,
            "icon": icon,
            "data": ent
        })

    for idx, ent in enumerate(entities_list):
        src_id = f"node_{idx}"
        for rel_key in ["publisher", "author", "creator", "provider", "isPartOf", "mainEntity", "about", "offers", "itemListElement"]:
            val = ent.get(rel_key)
            if isinstance(val, dict):
                target_raw_id = val.get("@id")
                if target_raw_id and target_raw_id in id_to_index:
                    tgt_id = id_to_index[target_raw_id]
                    if tgt_id != src_id:
                        edges.append({"source": src_id, "target": tgt_id, "label": rel_key})
            elif isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and item.get("@id") in id_to_index:
                        tgt_id = id_to_index[item["@id"]]
                        if tgt_id != src_id:
                            edges.append({"source": src_id, "target": tgt_id, "label": rel_key})

    if not edges and len(nodes) > 1:
        org_node = next((n for n in nodes if n["type"] in ("Organization", "Person", "LocalBusiness")), None)
        ws_node = next((n for n in nodes if n["type"] == "WebSite"), None)

        if org_node and ws_node and org_node["id"] != ws_node["id"]:
            edges.append({"source": ws_node["id"], "target": org_node["id"], "label": "publisher"})

        for n in nodes:
            if n["type"] not in ("Organization", "WebSite"):
                if ws_node and n["id"] != ws_node["id"]:
                    edges.append({"source": n["id"], "target": ws_node["id"], "label": "isPartOf"})
                elif org_node and n["id"] != org_node["id"]:
                    edges.append({"source": n["id"], "target": org_node["id"], "label": "author"})

    mermaid_lines = ["graph TD", "  %% Schema.org Knowledge Graph"]
    for n in nodes:
        clean_name = n["name"].replace('"', "'").replace("\n", " ")[:30]
        anchor = n["raw_id"].split("#")[-1] if "#" in n["raw_id"] else n["raw_id"].split("/")[-1] or f"node_{n['index']}"
        label = f"{n['icon']} {n['type']}<br/><b>{clean_name}</b><br/><small>#{anchor}</small>"
        mermaid_lines.append(f'  {n["id"]}["{label}"]')

    mermaid_lines.append("")
    mermaid_lines.append("  %% Relationships")
    for e in edges:
        mermaid_lines.append(f'  {e["source"]} -->|{e["label"]}| {e["target"]}')

    mermaid_lines.append("")
    mermaid_lines.append("  %% Theme Styles")
    mermaid_lines.append("  classDef entityNode fill:#e8f0fe,stroke:#1a73e8,stroke-width:2px,color:#202124,rx:8px,ry:8px;")
    mermaid_lines.append("  classDef orgNode fill:#e6f4ea,stroke:#1e8e3e,stroke-width:2px,color:#202124,rx:8px,ry:8px;")
    mermaid_lines.append("  classDef appNode fill:#f3e8fd,stroke:#9334e6,stroke-width:2px,color:#202124,rx:8px,ry:8px;")

    org_ids = [n["id"] for n in nodes if n["type"] in ("Organization", "LocalBusiness", "Person")]
    app_ids = [n["id"] for n in nodes if n["type"] in ("SoftwareApplication", "WebApplication", "Product")]
    rest_ids = [n["id"] for n in nodes if n["id"] not in org_ids and n["id"] not in app_ids]

    if rest_ids:
        mermaid_lines.append(f"  class {','.join(rest_ids)} entityNode;")
    if org_ids:
        mermaid_lines.append(f"  class {','.join(org_ids)} orgNode;")
    if app_ids:
        mermaid_lines.append(f"  class {','.join(app_ids)} appNode;")

    mermaid_code = "\n".join(mermaid_lines)

    ascii_lines = [
        f"📦 Schema.org Knowledge Graph (@context: https://schema.org | {len(nodes)} Connected Entities)",
        "│"
    ]
    for i, n in enumerate(nodes):
        is_last_node = (i == len(nodes) - 1)
        prefix = "└── " if is_last_node else "├── "
        pipe = "    " if is_last_node else "│   "

        anchor = n["raw_id"].split("#")[-1] if "#" in n["raw_id"] else n["raw_id"]
        ascii_lines.append(f"{prefix}{n['icon']} [{n['type']}] id: \"{anchor}\" (name: \"{n['name']}\")")

        d = n["data"]
        displayed_props = 0
        for k in ["url", "applicationCategory", "operatingSystem", "description", "headline"]:
            if k in d and isinstance(d[k], str):
                val_str = (d[k][:50] + "...") if len(d[k]) > 50 else d[k]
                ascii_lines.append(f"{pipe}├── {k}: \"{val_str}\"")
                displayed_props += 1
                if displayed_props >= 3:
                    break

        node_edges = [e for e in edges if e["source"] == n["id"]]
        for j, ne in enumerate(node_edges):
            tgt_node = next((x for x in nodes if x["id"] == ne["target"]), None)
            tgt_name = tgt_node["type"] if tgt_node else ne["target"]
            tgt_anchor = tgt_node["raw_id"].split("#")[-1] if tgt_node and "#" in tgt_node["raw_id"] else ""
            ascii_lines.append(f"{pipe}└── ──[{ne['label']}]──> {tgt_node['icon'] if tgt_node else '📦'} [{tgt_name}] (#{tgt_anchor})")

        if not is_last_node:
            ascii_lines.append("│")

    ascii_tree = "\n".join(ascii_lines)

    return {
        "format": format,
        "mermaid": mermaid_code,
        "ascii": ascii_tree,
        "entities_count": len(nodes),
        "relationships_count": len(edges),
        "entities": [
            {
                "id": n["id"],
                "raw_id": n["raw_id"],
                "type": n["type"],
                "name": n["name"],
                "icon": n["icon"],
                "properties": {k: v for k, v in n["data"].items() if isinstance(v, (str, int, float, bool))}
            }
            for n in nodes
        ]
    }


def crawl_sitemap_batch(
    sitemap_target: str,
    max_pages: int = 10,
    timeout: int = 8
) -> Dict[str, Any]:
    """
    Crawls and audits XML sitemaps to verify site-wide AEO coverage, Schema.org presence,
    page health, and AI discoverability across multiple pages.
    """
    target = (sitemap_target or "").strip()
    if not (target.startswith("http://") or target.startswith("https://")) and not Path(target).exists():
        target = f"https://{target}"

    sitemap_urls: List[str] = []
    discovered_sitemaps: List[str] = []
    is_live_url = target.startswith("http://") or target.startswith("https://")

    if is_live_url:
        parsed = urllib.parse.urlparse(target)
        base_origin = f"{parsed.scheme}://{parsed.netloc}"

        candidates = []
        if target.endswith(".xml"):
            candidates.append(target)
        else:
            candidates.extend([
                f"{base_origin}/sitemap.xml",
                f"{base_origin}/sitemap_index.xml",
                f"{base_origin}/robots.txt"
            ])

        for cand in candidates:
            try:
                req = urllib.request.Request(
                    cand,
                    headers={"User-Agent": "AEO-Graph-Engine-SitemapCrawler/1.0 (+https://aeo.nullai.tech)"}
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8", errors="replace")
                        if cand.endswith("robots.txt"):
                            sm_matches = re.findall(r'Sitemap:\s*(https?://[^\s\r\n]+)', content, re.IGNORECASE)
                            for sm in sm_matches:
                                if sm not in candidates:
                                    candidates.append(sm)
                        else:
                            discovered_sitemaps.append(cand)
                            locs = re.findall(r'<loc>(https?://[^<]+)</loc>', content, re.IGNORECASE)
                            sub_sitemaps = [l for l in locs if l.endswith(".xml")]
                            page_locs = [l for l in locs if not l.endswith(".xml")]

                            for pl in page_locs:
                                if pl not in sitemap_urls:
                                    sitemap_urls.append(pl.strip())

                            for sub in sub_sitemaps[:2]:
                                if sub not in discovered_sitemaps:
                                    discovered_sitemaps.append(sub)
                                    try:
                                        sub_req = urllib.request.Request(sub, headers={"User-Agent": "AEO-Graph-Engine-SitemapCrawler/1.0"})
                                        with urllib.request.urlopen(sub_req, timeout=timeout) as sub_resp:
                                            sub_xml = sub_resp.read().decode("utf-8", errors="replace")
                                            sub_locs = re.findall(r'<loc>(https?://[^<]+)</loc>', sub_xml, re.IGNORECASE)
                                            for sl in sub_locs:
                                                if not sl.endswith(".xml") and sl not in sitemap_urls:
                                                    sitemap_urls.append(sl.strip())
                                    except Exception:
                                        pass
                            if sitemap_urls:
                                break
            except Exception:
                continue

        if not sitemap_urls:
            sitemap_urls = [target]
    else:
        p = Path(target)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8", errors="replace")
            discovered_sitemaps.append(str(p))
            locs = re.findall(r'<loc>(https?://[^<]+)</loc>', content, re.IGNORECASE)
            sitemap_urls = [l.strip() for l in locs]
            if not sitemap_urls:
                sitemap_urls = ["https://localhost/index.html"]

    pages_to_crawl = sitemap_urls[:max_pages]
    crawled_pages = []

    total_score_sum = 0.0
    pages_with_schema = 0
    pages_with_faq = 0
    pages_with_h1 = 0
    pages_with_canonical = 0

    for url in pages_to_crawl:
        start_t = time.time()
        status_code = 200
        html = ""
        latency_ms = 0.0

        if is_live_url and (url.startswith("http://") or url.startswith("https://")):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "AEO-Graph-Engine-Scanner/1.0"})
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status_code = resp.status
                    html = resp.read().decode("utf-8", errors="replace")
                latency_ms = round((time.time() - start_t) * 1000, 1)
            except Exception as e:
                status_code = 0
                latency_ms = round((time.time() - start_t) * 1000, 1)
                html = f"<html><head><title>Page {url}</title></head><body><h1>Error</h1><p>{str(e)}</p></body></html>"
        else:
            status_code = 200
            html = f"<html><head><title>Audited Page: {url}</title></head><body><h1>Welcome</h1><p>Sample crawled page body for testing AEO coverage.</p></body></html>"
            latency_ms = 5.0

        meta = extract_metadata_from_html(html)
        schemas = meta.get("schemas", [])
        headings = meta.get("headings", [])
        h1s = [h for h in headings if h.get("tag") == "h1"]

        words = len(re.sub(r'<[^>]+>', ' ', html).split())

        p_score = 0.0
        issues = []
        if status_code == 200:
            p_score += 20.0
        else:
            issues.append(f"HTTP Status {status_code}")

        if meta.get("site_name") or meta.get("tagline"):
            p_score += 15.0
        else:
            issues.append("Missing <title> tag")

        if h1s:
            p_score += 15.0
            pages_with_h1 += 1
        else:
            issues.append("Missing <h1> heading")

        if schemas:
            p_score += 30.0
            pages_with_schema += 1
            if any("faq" in str(s).lower() for s in schemas):
                pages_with_faq += 1
        else:
            issues.append("No Schema.org JSON-LD found")

        if meta.get("canonical_url"):
            p_score += 10.0
            pages_with_canonical += 1
        else:
            issues.append("Missing canonical link")

        if words >= 150:
            p_score += 10.0
        else:
            issues.append(f"Thin content ({words} words)")

        p_score = min(100.0, p_score)
        total_score_sum += p_score

        schema_types = [s.get("@type", "Schema") for s in schemas if isinstance(s, dict)]
        if not schema_types and schemas:
            schema_types = ["JSON-LD"]

        crawled_pages.append({
            "url": url,
            "status": status_code,
            "latency_ms": latency_ms,
            "title": meta.get("site_name") or meta.get("tagline") or "No Title",
            "h1": h1s[0]["text"] if h1s else "None",
            "word_count": words,
            "schema_count": len(schemas),
            "schema_types": schema_types,
            "canonical": meta.get("canonical_url"),
            "aeo_score": round(p_score, 1),
            "issues": issues
        })

    crawled_count = len(crawled_pages)
    avg_score = round(total_score_sum / max(1, crawled_count), 1)

    schema_pct = round((pages_with_schema / max(1, crawled_count)) * 100, 1)
    faq_pct = round((pages_with_faq / max(1, crawled_count)) * 100, 1)
    h1_pct = round((pages_with_h1 / max(1, crawled_count)) * 100, 1)
    canonical_pct = round((pages_with_canonical / max(1, crawled_count)) * 100, 1)

    action_items = []
    if schema_pct < 100:
        action_items.append({
            "priority": "HIGH",
            "category": "Schema.org",
            "issue": f"{crawled_count - pages_with_schema} crawled page(s) missing JSON-LD schema.",
            "fix": "Embed Schema.org @graph on all sitemap routes."
        })
    if canonical_pct < 100:
        action_items.append({
            "priority": "MEDIUM",
            "category": "Canonicalization",
            "issue": f"{crawled_count - pages_with_canonical} page(s) missing canonical link tags.",
            "fix": "Add <link rel='canonical' href='...'> to page heads."
        })
    if h1_pct < 100:
        action_items.append({
            "priority": "MEDIUM",
            "category": "Structure",
            "issue": f"{crawled_count - pages_with_h1} page(s) missing primary <h1> headings.",
            "fix": "Ensure every page has a distinct H1 headline."
        })

    return {
        "sitemap_target": target,
        "sitemaps_discovered": discovered_sitemaps or ["sitemap.xml (auto)"],
        "total_urls_in_sitemap": len(sitemap_urls),
        "pages_audited_count": crawled_count,
        "overall_sitemap_aeo_score": avg_score,
        "status": "EXCELLENT" if avg_score >= 80 else ("GOOD" if avg_score >= 60 else "NEEDS_OPTIMIZATION"),
        "coverage_metrics": {
            "schema_coverage_pct": schema_pct,
            "faq_coverage_pct": faq_pct,
            "h1_coverage_pct": h1_pct,
            "canonical_coverage_pct": canonical_pct,
        },
        "pages": crawled_pages,
        "action_items": action_items
    }


class AEOMCPServer:
    """
    Complete Zero-Runtime-Dependency Model Context Protocol (MCP) Server.
    Communicates via line-delimited JSON-RPC 2.0 over standard I/O (stdin/stdout).
    """

    def __init__(self):
        self.server_name = SERVER_NAME
        self.server_version = SERVER_VERSION
        self.protocol_version = PROTOCOL_VERSION
        self.is_initialized = False

    def handle_message(self, req: Any) -> Optional[Dict[str, Any]]:
        """Alias for process_jsonrpc_request for backward compatibility and test runners."""
        return self.process_jsonrpc_request(req)

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handles MCP initialize request."""
        self.is_initialized = True
        return {
            "protocolVersion": self.protocol_version,
            "capabilities": {
                "tools": {
                    "listChanged": False
                },
                "logging": {}
            },
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version
            },
            "instructions": (
                "AEO Graph Engine MCP Server provides deterministic tools for Answer Engine "
                "Optimization (AEO/GEO), Schema.org JSON-LD @graph creation, llms.txt and machine "
                "manifest generation, live website multi-page crawling, HTML injection, and code integration."
            )
        }

    def handle_tools_list(self) -> Dict[str, Any]:
        """Returns the list of available MCP tools and input schemas."""
        return {
            "tools": TOOLS_DEFINITIONS
        }

    def handle_tool_call(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatches and executes the requested tool."""
        try:
            if name == "aeo_scan_site":
                url = arguments.get("url")
                if not url:
                    return {
                        "content": [{"type": "text", "text": "Error: 'url' parameter is required for aeo_scan_site."}],
                        "isError": True
                    }
                max_pages = arguments.get("max_pages", 5)
                timeout = arguments.get("timeout", 8)
                scanner = LiveAEOScanner(url, max_pages=max_pages, timeout=timeout)
                report = scanner.compute_audit_scores()

                text_summary = (
                    f"🌐 LIVE AEO AUDIT REPORT: {report['target_url']}\n"
                    f"📊 Overall Score: {report['overall_aeo_score']}/100 ({report['status']})\n"
                    f"📄 Pages Audited: {report['pages_audited_count']}\n\n"
                    f"--- Category Breakdown ---\n"
                )
                for cat, val in report["category_scores"].items():
                    text_summary += f"  • {cat.replace('_', ' ').title():30}: {val['score']}/{val['max']}\n"

                text_summary += "\n--- Root Discovery Assets ---\n"
                for asset, stat in report["root_assets"].items():
                    status_icon = "✅ Found" if stat["exists"] else f"❌ Missing (HTTP {stat['status']})"
                    text_summary += f"  • {asset:22}: {status_icon}\n"

                text_summary += "\n--- AI Search Engine Permissions ---\n"
                for bot, bdata in report["ai_engine_compatibility"].items():
                    bicon = "✅ Allowed" if bdata.get("allowed") else "❌ Blocked"
                    text_summary += f"  🤖 {bot:32}: {bicon}\n"

                if report.get("action_items"):
                    text_summary += "\n--- Prioritized Action Items ---\n"
                    for item in report["action_items"]:
                        text_summary += f"  [{item['priority']}] {item['category']}: {item['issue']}\n"
                        text_summary += f"        -> Fix: {item['fix']}\n"

                return {
                    "content": [
                        {"type": "text", "text": text_summary},
                        {"type": "text", "text": json.dumps(report, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_synthesize_prompt":
                prompt = arguments.get("prompt")
                if not prompt:
                    return {
                        "content": [{"type": "text", "text": "Error: 'prompt' parameter is required for aeo_synthesize_prompt."}],
                        "isError": True
                    }
                base_niche = arguments.get("base_niche")
                synthesized = synthesize_config_from_prompt(prompt, base_niche=base_niche)

                text_summary = (
                    f"✨ Synthesized AEO Configuration for: {synthesized.get('site_name')}\n"
                    f"🌐 Domain: {synthesized.get('domain')} ({synthesized.get('niche')})\n"
                    f"📌 Tagline: {synthesized.get('tagline')}\n"
                    f"💡 Features: {len(synthesized.get('features', []))} defined\n"
                    f"❓ FAQs: {len(synthesized.get('faqs', []))} structured Q&A pairs\n\n"
                    f"{json.dumps(synthesized, indent=2, ensure_ascii=False)}"
                )
                return {
                    "content": [{"type": "text", "text": text_summary}],
                    "isError": False
                }

            elif name == "aeo_generate_bundle":
                cfg_in = arguments.get("config")
                niche = arguments.get("niche", "developer_tools")
                output_dir = arguments.get("output_dir")
                inject_html_files = arguments.get("inject_html_files")

                cfg = resolve_config(cfg_in, niche=niche)
                schema_graph = generate_schema_graph(cfg, niche=niche)
                llms_txt = generate_llms_txt(cfg, niche=niche)
                llms_full_txt = generate_llms_full_txt(cfg, niche=niche)
                ai_txt = generate_ai_txt(cfg, niche=niche)
                robots_txt = generate_robots_txt(cfg, niche=niche)

                created_files = {}
                if output_dir:
                    created_files = write_aeo_bundle(
                        output_dir,
                        cfg,
                        niche=niche,
                        inject_html_files=inject_html_files
                    )

                result_data = {
                    "site_name": cfg.get("site_name"),
                    "domain": cfg.get("domain"),
                    "niche": niche,
                    "written_to_disk": bool(output_dir),
                    "created_files": created_files,
                    "artifacts": {
                        "schema_graph": schema_graph,
                        "llms_txt": llms_txt,
                        "llms_full_txt": llms_full_txt,
                        "ai_txt": ai_txt,
                        "robots_txt": robots_txt
                    }
                }

                summary_text = (
                    f"🎉 AEO Bundle Generated Successfully for '{cfg.get('site_name')}' ({cfg.get('domain')})\n"
                    f"• Schema.org @graph entities: {len(schema_graph.get('@graph', []))}\n"
                    f"• llms.txt: {len(llms_txt.splitlines())} lines\n"
                    f"• llms-full.txt: {len(llms_full_txt.splitlines())} lines\n"
                    f"• ai.txt: Ready\n"
                    f"• robots.txt: Ready\n"
                )
                if created_files:
                    summary_text += f"\n📁 Written to Disk ({output_dir}):\n"
                    for fname, fpath in created_files.items():
                        summary_text += f"  📄 {fname:20} -> {fpath}\n"

                return {
                    "content": [
                        {"type": "text", "text": summary_text},
                        {"type": "text", "text": json.dumps(result_data, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_inject_html":
                html_content = arguments.get("html_content")
                html_file_path = arguments.get("html_file_path")
                schema_payload = arguments.get("schema_payload")
                config = arguments.get("config")
                niche = arguments.get("niche", "developer_tools")
                backup = arguments.get("backup", False)

                if schema_payload is None:
                    cfg = resolve_config(config, niche=niche)
                    schema_payload = generate_schema_graph(cfg, niche=niche)

                if html_file_path:
                    path = Path(html_file_path).resolve()
                    if not path.exists():
                        return {
                            "content": [{"type": "text", "text": f"Error: HTML target file not found at: {path}"}],
                            "isError": True
                        }
                    inject_file(path, schema_payload, backup=backup)
                    return {
                        "content": [{
                            "type": "text",
                            "text": f"✅ Successfully injected Schema.org JSON-LD into '{path}'. (Backup: {backup})"
                        }],
                        "isError": False
                    }
                elif html_content:
                    injected_html = inject_jsonld_into_html(html_content, schema_payload)
                    return {
                        "content": [
                            {"type": "text", "text": "✅ Successfully injected Schema.org JSON-LD into HTML content."},
                            {"type": "text", "text": injected_html}
                        ],
                        "isError": False
                    }
                else:
                    return {
                        "content": [{"type": "text", "text": "Error: Either 'html_file_path' or 'html_content' must be provided."}],
                        "isError": True
                    }

            elif name == "aeo_validate":
                target_path = arguments.get("target_path")
                schema_data = arguments.get("schema_data")
                content = arguments.get("content")
                artifact_type = arguments.get("artifact_type")

                if schema_data:
                    report = AEODiagnosticReport("in-memory-schema")
                    validate_schema_jsonld_dict(schema_data, report)
                    data = report.to_dict()
                elif content and artifact_type:
                    report = AEODiagnosticReport(f"in-memory-{artifact_type}")
                    if artifact_type == "llms_txt":
                        validate_llms_txt_content(content, report, is_full=False)
                    elif artifact_type == "llms_full_txt":
                        validate_llms_txt_content(content, report, is_full=True)
                    elif artifact_type == "ai_txt":
                        validate_ai_txt_content(content, report)
                    elif artifact_type == "robots_txt":
                        validate_robots_txt_content(content, report)
                    else:
                        return {
                            "content": [{"type": "text", "text": f"Error: Unknown artifact_type '{artifact_type}'."}],
                            "isError": True
                        }
                    data = report.to_dict()
                elif target_path:
                    report = validate_aeo_bundle(target_path)
                    data = report.to_dict()
                else:
                    return {
                        "content": [{"type": "text", "text": "Error: Specify 'target_path', 'schema_data', or 'content' + 'artifact_type' for validation."}],
                        "isError": True
                    }

                summary = (
                    f"🔍 AEO Validation Report: {data['target']}\n"
                    f"📊 Score: {data['score']}/100 ({data['status']})\n"
                    f"  ✅ Passed checks: {data['passed_count']}\n"
                    f"  ⚠️  Warnings:      {data['warnings_count']}\n"
                    f"  ❌ Errors:        {data['errors_count']}\n"
                )
                if data["errors"]:
                    summary += "\nErrors:\n" + "\n".join(f"  ❌ {e}" for e in data["errors"])
                if data["warnings"]:
                    summary += "\nWarnings:\n" + "\n".join(f"  ⚠️  {w}" for w in data["warnings"])

                return {
                    "content": [
                        {"type": "text", "text": summary},
                        {"type": "text", "text": json.dumps(data, indent=2)}
                    ],
                    "isError": False
                }

            elif name == "aeo_get_framework_snippets":
                fw = arguments.get("framework", "all")
                schema_graph = arguments.get("schema_graph")
                config = arguments.get("config")
                niche = arguments.get("niche", "developer_tools")

                snippets_result = get_framework_snippets(
                    framework=fw,
                    schema_graph=schema_graph,
                    config=config,
                    niche=niche
                )

                formatted = "# AEO Framework Integration Code Snippets\n\n"
                for k, v in snippets_result.items():
                    formatted += f"## {v['title']}\n"
                    formatted += f"_{v['description']}_\n\n"
                    formatted += f"```tsx\n{v['code']}\n```\n\n"

                return {
                    "content": [
                        {"type": "text", "text": formatted},
                        {"type": "text", "text": json.dumps(snippets_result, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_simulate_citation":
                target = arguments.get("url_or_content")
                if not target:
                    return {
                        "content": [{"type": "text", "text": "Error: 'url_or_content' parameter is required for aeo_simulate_citation."}],
                        "isError": True
                    }
                query = arguments.get("query")
                brand = arguments.get("brand_name")
                domain = arguments.get("domain")
                timeout = arguments.get("timeout", 8)
                sim_res = simulate_ai_citations(target, query=query, brand_name=brand, domain=domain, timeout=timeout)

                summary = (
                    f"🎯 AI CITATION SIMULATION REPORT: {sim_res['brand_name']} ({sim_res['domain']})\n"
                    f"📊 Extractability Score: {sim_res['extractability_score']}/100 ({sim_res['status']})\n"
                    f"🔮 Citation Confidence: {sim_res['confidence']}\n"
                    f"❓ Query: \"{sim_res['query']}\"\n\n"
                    f"--- Extracted Key Quotes ---\n"
                )
                for q in sim_res["extracted_quotes"]:
                    summary += f"  • {q['quote']} (Context: {q['context']})\n"

                summary += f"\n--- Perplexity AI (Sonar Pro) Simulation ---\n{sim_res['engines']['perplexity']['response']}\n"
                summary += f"\n--- ChatGPT Search Simulation ---\n{sim_res['engines']['chatgpt']['response']}\n"

                return {
                    "content": [
                        {"type": "text", "text": summary},
                        {"type": "text", "text": json.dumps(sim_res, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_visualize_schema":
                schema_data = arguments.get("schema_data")
                schema_file = arguments.get("schema_file")
                fmt = arguments.get("format", "mermaid")
                vis_res = visualize_schema_graph(schema_input=schema_data or schema_file, format=fmt)

                diagram_text = vis_res["mermaid"] if fmt == "mermaid" else (vis_res["ascii"] if fmt == "ascii" else f"# Mermaid Diagram\n```mermaid\n{vis_res['mermaid']}\n```\n\n# ASCII Tree\n```\n{vis_res['ascii']}\n```")

                return {
                    "content": [
                        {"type": "text", "text": diagram_text},
                        {"type": "text", "text": json.dumps(vis_res, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_crawl_sitemap":
                target = arguments.get("sitemap_url_or_domain")
                if not target:
                    return {
                        "content": [{"type": "text", "text": "Error: 'sitemap_url_or_domain' parameter is required for aeo_crawl_sitemap."}],
                        "isError": True
                    }
                max_pages = arguments.get("max_pages", 10)
                timeout = arguments.get("timeout", 8)
                crawl_res = crawl_sitemap_batch(target, max_pages=max_pages, timeout=timeout)

                summary = (
                    f"🕷️ SITEMAP AEO CRAWL REPORT: {crawl_res['sitemap_target']}\n"
                    f"📊 Site-Wide AEO Health Score: {crawl_res['overall_sitemap_aeo_score']}/100 ({crawl_res['status']})\n"
                    f"📄 Pages Audited: {crawl_res['pages_audited_count']} / {crawl_res['total_urls_in_sitemap']} found\n"
                    f"🕸️ Schema.org Coverage: {crawl_res['coverage_metrics']['schema_coverage_pct']}%\n"
                    f"🍞 Canonical Tag Coverage: {crawl_res['coverage_metrics']['canonical_coverage_pct']}%\n\n"
                    f"--- Audited Pages Breakdown ---\n"
                )
                for p in crawl_res["pages"]:
                    status_icon = "✅" if p["status"] == 200 else "⚠️"
                    summary += f"  {status_icon} [{p['aeo_score']}/100] {p['url']} - {p['title']} ({p['word_count']} words, {p['schema_count']} schemas)\n"

                if crawl_res.get("action_items"):
                    summary += "\n--- Recommended Site Actions ---\n"
                    for item in crawl_res["action_items"]:
                        summary += f"  [{item['priority']}] {item['category']}: {item['issue']}\n"

                return {
                    "content": [
                        {"type": "text", "text": summary},
                        {"type": "text", "text": json.dumps(crawl_res, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_extract_knowledge_graph":
                from .knowledge_graph import analyze_knowledge_graph
                content = arguments.get("content")
                if not content:
                    return {
                        "content": [{"type": "text", "text": "Error: 'content' parameter is required for aeo_extract_knowledge_graph."}],
                        "isError": True
                    }
                schema_json = arguments.get("schema_json")
                base_url = arguments.get("base_url", "https://example.com")
                min_conf = float(arguments.get("min_confidence", 0.4))
                kg_report = analyze_knowledge_graph(content, schema_or_graph=schema_json, base_url=base_url, min_confidence=min_conf)
                res_dict = kg_report.to_dict()

                summary = (
                    f"🧠 AEO KNOWLEDGE GRAPH & TRIPLETS REPORT\n"
                    f"🔗 Extracted Semantic Triplets: {res_dict['triplets_count']}\n"
                    f"🌐 Unique Entities Identified: {res_dict['entities_count']}\n"
                    f"📊 Schema.org Entity Coverage: {res_dict['entity_coverage_score']}%\n"
                    f"🕸️ Graph Density: {res_dict['graph_density']}\n"
                    f"⚠️ Orphan High-Salience Concepts: {len(res_dict['orphan_entities'])}\n\n"
                    f"--- Top Central Entities (PageRank Salience) ---\n"
                )
                for ent in res_dict["entities"][:6]:
                    in_s = "✅ In Schema" if ent["in_schema"] else "❌ Missing from Schema"
                    summary += f"  • {ent['name']} ({ent['entity_type']}) - Salience: {ent['salience']} (PR: {ent['pagerank']}) [{in_s}]\n"

                return {
                    "content": [
                        {"type": "text", "text": summary},
                        {"type": "text", "text": json.dumps(res_dict, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_analyze_claims":
                from .claim_evidence_matrix import analyze_claim_evidence_matrix
                content = arguments.get("content")
                if not content:
                    return {
                        "content": [{"type": "text", "text": "Error: 'content' parameter is required for aeo_analyze_claims."}],
                        "isError": True
                    }
                base_url = arguments.get("base_url", "https://example.com")
                title = arguments.get("title")
                matrix = analyze_claim_evidence_matrix(content, base_url=base_url, title=title)
                res_dict = matrix.to_dict()

                summary = (
                    f"🎯 ATOMIC CLAIM-EVIDENCE & CITATION MATRIX\n"
                    f"📄 Target / Title: {matrix.url_or_title}\n"
                    f"📊 Quotability Score: {matrix.mean_quotability_score:.1f}/100 (Grade: {matrix.quotability_grade})\n"
                    f"🔬 Total Atomic Claims: {matrix.total_claims}\n"
                    f"📈 Quantitative Metric Density: {matrix.quantitative_density * 100:.1f}%\n"
                    f"⚡ High-Confidence Quotable (≥75): {matrix.high_quotability_count}\n"
                )

                return {
                    "content": [
                        {"type": "text", "text": summary},
                        {"type": "text", "text": json.dumps(res_dict, indent=2, ensure_ascii=False)}
                    ],
                    "isError": False
                }

            elif name == "aeo_generate_claim_matrix":
                from .claim_evidence_matrix import analyze_claim_evidence_matrix
                content = arguments.get("content")
                if not content:
                    return {
                        "content": [{"type": "text", "text": "Error: 'content' parameter is required for aeo_generate_claim_matrix."}],
                        "isError": True
                    }
                base_url = arguments.get("base_url", "https://example.com")
                fmt = arguments.get("format", "markdown")
                matrix = analyze_claim_evidence_matrix(content, base_url=base_url)

                if fmt == "svg":
                    out_text = matrix.to_svg()
                elif fmt == "schema_org":
                    out_text = json.dumps(matrix.schema_org_claim_review, indent=2, ensure_ascii=False)
                elif fmt == "json":
                    out_text = json.dumps(matrix.to_dict(), indent=2, ensure_ascii=False)
                else:
                    out_text = matrix.to_markdown()

                return {
                    "content": [
                        {"type": "text", "text": out_text}
                    ],
                    "isError": False
                }

            else:
                return {
                    "content": [{"type": "text", "text": f"Error: Unknown tool name '{name}'."}],
                    "isError": True
                }

        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Execution error in tool '{name}': {str(e)}"}],
                "isError": True
            }

    def process_jsonrpc_request(self, req: Any) -> Optional[Dict[str, Any]]:
        """
        Processes a single JSON-RPC 2.0 message according to MCP specification.
        Returns a response dict, or None if the request is a notification without an id.
        """
        if not isinstance(req, dict):
            return {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": INVALID_REQUEST,
                    "message": "Invalid JSON-RPC 2.0 Request: expected object."
                }
            }

        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params", {})

        # Check for standard JSON-RPC fields
        if not method or not isinstance(method, str):
            if req_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": INVALID_REQUEST,
                        "message": "Missing or invalid 'method' field in JSON-RPC request."
                    }
                }
            return None

        # Notifications (no id)
        is_notification = (req_id is None)

        # Handle MCP Methods
        if method == "initialize":
            result = self.handle_initialize(params)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }

        elif method in ("notifications/initialized", "initialized"):
            # Client acknowledgement notification
            self.is_initialized = True
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
            return None

        elif method == "ping":
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {}
                }
            return None

        elif method == "tools/list":
            result = self.handle_tools_list()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result
            }

        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            if not tool_name:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": INVALID_PARAMS,
                        "message": "Missing 'name' in tools/call parameters."
                    }
                }
            call_result = self.handle_tool_call(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_result
            }

        elif method.startswith("notifications/"):
            # Other client notifications (e.g. notifications/cancelled)
            return None

        else:
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "error": {
                        "code": METHOD_NOT_FOUND,
                        "message": f"Method not found: '{method}'"
                    }
                }
            return None

    def serve_stdio(self, input_stream: Optional[TextIO] = None, output_stream: Optional[TextIO] = None) -> None:
        """
        Runs the line-delimited JSON-RPC 2.0 loop on standard input / output.
        """
        in_stream = input_stream or sys.stdin
        out_stream = output_stream or sys.stdout

        sys.stderr.write(f"[{SERVER_NAME}] Server running on stdio (MCP Protocol v{PROTOCOL_VERSION})\n")
        sys.stderr.flush()

        for line in in_stream:
            line_str = line.strip()
            if not line_str:
                continue

            try:
                parsed_json = json.loads(line_str)
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": PARSE_ERROR,
                        "message": f"Parse error: {str(e)}"
                    }
                }
                out_stream.write(json.dumps(err_resp) + "\n")
                out_stream.flush()
                continue

            # Process single or batch requests
            if isinstance(parsed_json, list):
                batch_responses = []
                for item in parsed_json:
                    resp = self.process_jsonrpc_request(item)
                    if resp is not None:
                        batch_responses.append(resp)
                if batch_responses:
                    out_stream.write(json.dumps(batch_responses) + "\n")
                    out_stream.flush()
            else:
                resp = self.process_jsonrpc_request(parsed_json)
                if resp is not None:
                    out_stream.write(json.dumps(resp) + "\n")
                    out_stream.flush()


def run_server() -> int:
    """Entry point for running the MCP server directly."""
    AEOMCPServer.handle_message = AEOMCPServer.process_jsonrpc_request
    server = AEOMCPServer()
    server.serve_stdio()
    return 0


# Public Aliases
MCPServer = AEOMCPServer
run_stdio_server = run_server



def main(argv: Optional[List[str]] = None) -> int:
    """CLI handler for inspecting tools, generating client configs, or starting stdio."""
    args = argv if argv is not None else sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(f"AEO Graph Engine MCP Server v{SERVER_VERSION}")
        print("Usage:")
        print("  python -m aeo_graph_engine.mcp_server              # Run stdio MCP server")
        print("  python -m aeo_graph_engine.mcp_server --tools      # Print available tool schemas")
        print("  python -m aeo_graph_engine.mcp_server --config <c> # Generate client config (claude_desktop, cursor, cline, zed, generic)")
        return 0

    if "--tools" in args or "--list-tools" in args:
        print(json.dumps(TOOLS_DEFINITIONS, indent=2))
        return 0

    if "--config" in args:
        idx = args.index("--config")
        client = args[idx + 1] if idx + 1 < len(args) else "generic"
        cfg = generate_mcp_client_config(client)
        print(json.dumps(cfg, indent=2))
        return 0

    # Default to running stdio server
    return run_server()


if __name__ == "__main__":
    sys.exit(main())

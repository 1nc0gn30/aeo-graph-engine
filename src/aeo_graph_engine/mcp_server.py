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
        env_vars["PYTHONPATH"] = f"{src_dir}:{abs_root}"

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

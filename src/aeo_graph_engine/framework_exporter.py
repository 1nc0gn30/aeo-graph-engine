"""
Framework Exporter & AEO Remediation Engine.
Generates copy-pasteable, production-ready integration code and auto-remediation
fixes for all modern web frameworks: Next.js (App & Pages router), Astro, Vite/React,
SvelteKit, Remix, Nuxt/Vue, and Static HTML / Hugo / Jekyll.

Zero external dependencies (pure Python standard library).
"""

import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Set

from .presets import DEFAULT_CONFIG, NICHE_PRESETS
from .core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
)


SUPPORTED_FRAMEWORKS = [
    "nextjs_app",
    "nextjs_pages",
    "astro",
    "vite_react",
    "sveltekit",
    "remix",
    "nuxt",
    "static",
    "hugo",
    "jekyll",
]


def normalize_framework_name(name: str) -> str:
    """Normalizes various aliases to canonical framework names."""
    n = name.lower().strip().replace("-", "_").replace(" ", "_")
    if n in ("next", "nextjs", "next_app", "nextjs_app_router", "app_router", "nextjs_app"):
        return "nextjs_app"
    if n in ("next_pages", "nextjs_pages", "pages_router", "next_page", "pages"):
        return "nextjs_pages"
    if n in ("astro", "astrojs"):
        return "astro"
    if n in ("vite", "react", "vite_react", "vite_spa", "spa", "cra"):
        return "vite_react"
    if n in ("svelte", "sveltekit", "svelte_kit"):
        return "sveltekit"
    if n in ("remix", "remix_run"):
        return "remix"
    if n in ("nuxt", "nuxt3", "nuxtjs", "vue", "vuejs"):
        return "nuxt"
    if n in ("static", "html", "vanilla", "plain"):
        return "static"
    if n in ("hugo", "gohugo"):
        return "hugo"
    if n in ("jekyll", "github_pages"):
        return "jekyll"
    return "nextjs_app"


def get_supported_frameworks() -> List[str]:
    """Returns list of all canonical supported framework identifiers."""
    return list(SUPPORTED_FRAMEWORKS)


class FrameworkExporter:
    """
    Generates complete, production-grade integration files for modern web frameworks
    to embed Answer Engine Optimization (AEO), Schema.org graphs, llms.txt, and AI crawler rules.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        niche: str = "developer_tools"
    ):
        self.config = resolve_config(config, niche=niche)
        self.niche = niche
        self.base_url = self.config.get("base_url", "https://example.com").rstrip("/")
        self.site_name = self.config.get("site_name", "AEO Graph Engine")
        self.description = self.config.get("description", "")
        self.tagline = self.config.get("tagline", "")
        self.og_image_url = self.config.get("og_image_url", f"{self.base_url}/og-image.png")

        # Core AEO artifacts
        self.schema_graph = generate_schema_graph(self.config, niche=niche)
        self.llms_txt = generate_llms_txt(self.config, niche=niche)
        self.llms_full_txt = generate_llms_full_txt(self.config, niche=niche)
        self.ai_txt = generate_ai_txt(self.config, niche=niche)
        self.robots_txt = generate_robots_txt(self.config, niche=niche)

    # -------------------------------------------------------------------------
    # 1. Next.js App Router
    # -------------------------------------------------------------------------
    def export_nextjs_app(self) -> Dict[str, str]:
        """
        Generates Next.js App Router integration files:
          - app/layout.tsx (with Metadata & Schema.org JSON-LD script)
          - app/robots.ts (with AI crawler rules)
          - app/sitemap.ts (dynamic sitemap)
          - app/llms.txt/route.ts (static route handler)
          - app/llms-full.txt/route.ts (deep research route handler)
          - app/ai.txt/route.ts (AI policy route handler)
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        # Sitemap items
        surfaces = self.config.get("surfaces", [])
        sitemap_items = []
        for s in surfaces:
            if isinstance(s, dict) and s.get("path"):
                path = s["path"]
                if not path.startswith("/"):
                    path = "/" + path
                sitemap_items.append(f"""    {{
      url: `${{baseUrl}}{path}`,
      lastModified,
      changeFrequency: "weekly" as const,
      priority: 0.8,
    }},""")
        sitemap_entries = "\n".join(sitemap_items)

        # app/layout.tsx
        layout_tsx = f"""import type {{ Metadata }} from "next";
import "./globals.css";

export const metadata: Metadata = {{
  title: {json.dumps(self.site_name)},
  description: {json.dumps(self.description)},
  metadataBase: new URL("{self.base_url}"),
  alternates: {{
    canonical: "/",
  }},
  openGraph: {{
    title: {json.dumps(self.site_name)},
    description: {json.dumps(self.description)},
    url: "{self.base_url}/",
    siteName: {json.dumps(self.site_name)},
    images: [
      {{
        url: "{self.og_image_url}",
        width: 1200,
        height: 630,
        alt: {json.dumps(self.site_name)},
      }},
    ],
    locale: "en_US",
    type: "website",
  }},
  twitter: {{
    card: "summary_large_image",
    title: {json.dumps(self.site_name)},
    description: {json.dumps(self.description)},
    images: ["{self.og_image_url}"],
  }},
  robots: {{
    index: true,
    follow: true,
    googleBot: {{
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    }},
  }},
}};

const jsonLd = {json_ld_str};

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
          dangerouslySetInnerHTML={{{{ __html: JSON.stringify(jsonLd) }}}}
        />
      </head>
      <body>{{children}}</body>
    </html>
  );
}}
"""

        # app/robots.ts
        robots_ts = f"""import type {{ MetadataRoute }} from "next";

export default function robots(): MetadataRoute.Robots {{
  const baseUrl = "{self.base_url}";

  return {{
    rules: [
      {{
        userAgent: "*",
        allow: "/",
        disallow: ["/api/private/", "/admin/", "/vault/keys/"],
      }},
      {{
        userAgent: [
          "GPTBot",
          "ChatGPT-User",
          "PerplexityBot",
          "ClaudeBot",
          "anthropic-ai",
          "Applebot-Extended",
          "Google-Extended",
          "cohere-ai",
          "Meta-ExternalAgent",
        ],
        allow: "/",
      }},
    ],
    sitemap: `${{baseUrl}}/sitemap.xml`,
  }};
}}
"""

        # app/sitemap.ts
        sitemap_ts = f"""import type {{ MetadataRoute }} from "next";

export default function sitemap(): MetadataRoute.Sitemap {{
  const baseUrl = "{self.base_url}";
  const lastModified = new Date();

  return [
    {{
      url: `${{baseUrl}}/`,
      lastModified,
      changeFrequency: "weekly",
      priority: 1.0,
    }},
{sitemap_entries}
  ];
}}
"""

        # app/llms.txt/route.ts
        llms_route_ts = f"""export const dynamic = "force-static";

export async function GET() {{
  const content = {json.dumps(self.llms_txt)};

  return new Response(content, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
    }},
  }});
}}
"""

        # app/llms-full.txt/route.ts
        llms_full_route_ts = f"""export const dynamic = "force-static";

export async function GET() {{
  const content = {json.dumps(self.llms_full_txt)};

  return new Response(content, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
    }},
  }});
}}
"""

        # app/ai.txt/route.ts
        ai_route_ts = f"""export const dynamic = "force-static";

export async function GET() {{
  const content = {json.dumps(self.ai_txt)};

  return new Response(content, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400, stale-while-revalidate=3600",
    }},
  }});
}}
"""

        return {
            "app/layout.tsx": layout_tsx,
            "app/robots.ts": robots_ts,
            "app/sitemap.ts": sitemap_ts,
            "app/llms.txt/route.ts": llms_route_ts,
            "app/llms-full.txt/route.ts": llms_full_route_ts,
            "app/ai.txt/route.ts": ai_route_ts,
        }

    # -------------------------------------------------------------------------
    # 2. Next.js Pages Router
    # -------------------------------------------------------------------------
    def export_nextjs_pages(self) -> Dict[str, str]:
        """
        Generates Next.js Pages Router integration files:
          - pages/_document.tsx (with custom document JSON-LD)
          - pages/api/llms.txt.ts (API route)
          - components/AeoHead.tsx (Head component)
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        doc_tsx = f"""import Document, {{ Html, Head, Main, NextScript, DocumentContext }} from "next/document";

const schemaGraph = {json_ld_str};

class MyDocument extends Document {{
  static async getInitialProps(ctx: DocumentContext) {{
    const initialProps = await Document.getInitialProps(ctx);
    return {{ ...initialProps }};
  }}

  render() {{
    return (
      <Html lang="en">
        <Head>
          <link rel="canonical" href="{self.base_url}/" />
          <meta name="description" content={json.dumps(self.description)} />
          <meta property="og:title" content={json.dumps(self.site_name)} />
          <meta property="og:description" content={json.dumps(self.description)} />
          <meta property="og:url" content="{self.base_url}/" />
          <meta property="og:type" content="website" />
          <meta property="og:image" content="{self.og_image_url}" />
          <meta name="twitter:card" content="summary_large_image" />
          <meta name="twitter:title" content={json.dumps(self.site_name)} />
          <meta name="twitter:description" content={json.dumps(self.description)} />
          <meta name="twitter:image" content="{self.og_image_url}" />
          <script
            id="aeo-schema-graph"
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
}}

export default MyDocument;
"""

        api_llms_ts = f"""import type {{ NextApiRequest, NextApiResponse }} from "next";

const llmsTxtContent = {json.dumps(self.llms_txt)};

export default function handler(req: NextApiRequest, res: NextApiResponse) {{
  res.setHeader("Content-Type", "text/plain; charset=utf-8");
  res.setHeader("Cache-Control", "public, max-age=86400, stale-while-revalidate=3600");
  res.status(200).send(llmsTxtContent);
}}
"""

        head_component_tsx = f"""import React from "react";
import Head from "next/head";

interface AeoHeadProps {{
  title?: string;
  description?: string;
  canonicalUrl?: string;
}}

const schemaGraph = {json_ld_str};

export const AeoHead: React.FC<AeoHeadProps> = ({{
  title = {json.dumps(self.site_name)},
  description = {json.dumps(self.description)},
  canonicalUrl = "{self.base_url}/",
}}) => {{
  return (
    <Head>
      <title>{{title}}</title>
      <meta name="description" content={{description}} />
      <link rel="canonical" href={{canonicalUrl}} />
      <meta property="og:title" content={{title}} />
      <meta property="og:description" content={{description}} />
      <meta property="og:url" content={{canonicalUrl}} />
      <meta property="og:type" content="website" />
      <meta name="twitter:card" content="summary_large_image" />
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{{{ __html: JSON.stringify(schemaGraph) }}}}
      />
    </Head>
  );
}};

export default AeoHead;
"""

        return {
            "pages/_document.tsx": doc_tsx,
            "pages/api/llms.txt.ts": api_llms_ts,
            "components/AeoHead.tsx": head_component_tsx,
        }

    # -------------------------------------------------------------------------
    # 3. Astro
    # -------------------------------------------------------------------------
    def export_astro(self) -> Dict[str, str]:
        """
        Generates Astro integration files:
          - src/components/AeoHead.astro
          - astro.config.mjs (sitemap + site url)
          - public/llms.txt
          - public/llms-full.txt
          - public/ai.txt
          - public/robots.txt
          - public/schema-graph.json
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        aeo_head_astro = f"""---
export interface Props {{
  title?: string;
  description?: string;
  canonical?: string;
  ogImage?: string;
}}

const {{
  title = {json.dumps(self.site_name)},
  description = {json.dumps(self.description)},
  canonical = "{self.base_url}/",
  ogImage = "{self.og_image_url}"
}} = Astro.props;

const schemaGraph = {json_ld_str};
---

<!-- Canonical & Primary Meta -->
<link rel="canonical" href={{canonical}} />
<meta name="description" content={{description}} />

<!-- Open Graph / AI Search Indexing -->
<meta property="og:type" content="website" />
<meta property="og:url" content={{canonical}} />
<meta property="og:title" content={{title}} />
<meta property="og:description" content={{description}} />
<meta property="og:image" content={{ogImage}} />

<!-- Twitter Card -->
<meta property="twitter:card" content="summary_large_image" />
<meta property="twitter:url" content={{canonical}} />
<meta property="twitter:title" content={{title}} />
<meta property="twitter:description" content={{description}} />
<meta property="twitter:image" content={{ogImage}} />

<!-- Answer Engine Optimization (AEO) JSON-LD Linked Data Graph -->
<script type="application/ld+json" set:html={{JSON.stringify(schemaGraph)}} />
"""

        astro_config_mjs = f"""import {{ defineConfig }} from 'astro/config';
import sitemap from '@astrojs/sitemap';

// https://astro.build/config
export default defineConfig({{
  site: '{self.base_url}',
  integrations: [
    sitemap({{
      changefreq: 'weekly',
      priority: 0.8,
      lastmod: new Date(),
    }}),
  ],
}});
"""

        return {
            "src/components/AeoHead.astro": aeo_head_astro,
            "astro.config.mjs": astro_config_mjs,
            "public/llms.txt": self.llms_txt,
            "public/llms-full.txt": self.llms_full_txt,
            "public/ai.txt": self.ai_txt,
            "public/robots.txt": self.robots_txt,
            "public/schema-graph.json": json.dumps(self.schema_graph, indent=2, ensure_ascii=False),
        }

    # -------------------------------------------------------------------------
    # 4. Vite + React / SPA
    # -------------------------------------------------------------------------
    def export_vite_react(self) -> Dict[str, str]:
        """
        Generates Vite + React / SPA integration files:
          - index.html injection snippet
          - vite-plugin-aeo.ts (Vite plugin to bundle/serve llms.txt & schema-graph)
          - src/components/AeoMeta.tsx (React Helmet / Meta component)
        """
        json_ld_indented = json.dumps(self.schema_graph, indent=4, ensure_ascii=False)

        index_html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/logo.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{self.site_name}</title>
    <meta name="description" content="{self.description}" />
    <link rel="canonical" href="{self.base_url}/" />

    <!-- Open Graph & Social Cards -->
    <meta property="og:title" content="{self.site_name}" />
    <meta property="og:description" content="{self.description}" />
    <meta property="og:url" content="{self.base_url}/" />
    <meta property="og:type" content="website" />
    <meta property="og:image" content="{self.og_image_url}" />
    <meta name="twitter:card" content="summary_large_image" />

    <!-- Answer Engine Optimization (AEO) Schema.org Linked Data Graph -->
    <script type="application/ld+json">
{json_ld_indented}
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
"""

        vite_plugin_ts = f"""import type {{ Plugin }} from "vite";

/**
 * Custom Vite Plugin to serve and build AEO discovery assets:
 * - /llms.txt
 * - /llms-full.txt
 * - /ai.txt
 * - /robots.txt
 * - /schema-graph.json
 */
export function aeoPlugin(): Plugin {{
  const assets: Record<string, string> = {{
    "llms.txt": {json.dumps(self.llms_txt)},
    "llms-full.txt": {json.dumps(self.llms_full_txt)},
    "ai.txt": {json.dumps(self.ai_txt)},
    "robots.txt": {json.dumps(self.robots_txt)},
    "schema-graph.json": {json.dumps(json.dumps(self.schema_graph, indent=2, ensure_ascii=False))},
  }};

  return {{
    name: "vite-plugin-aeo",
    configureServer(server) {{
      server.middlewares.use((req, res, next) => {{
        const url = (req.url || "").split("?")[0].replace(/^\\//, "");
        if (assets[url] !== undefined) {{
          const contentType = url.endsWith(".json")
            ? "application/json; charset=utf-8"
            : "text/plain; charset=utf-8";
          res.setHeader("Content-Type", contentType);
          res.setHeader("Cache-Control", "public, max-age=86400");
          res.end(assets[url]);
          return;
        }}
        next();
      }});
    }},
    generateBundle() {{
      for (const [fileName, source] of Object.entries(assets)) {{
        this.emitFile({{
          type: "asset",
          fileName,
          source,
        }});
      }}
    }},
  }};
}}

export default aeoPlugin;
"""

        aeo_meta_tsx = f"""import React, {{ useEffect }} from "react";

interface AeoMetaProps {{
  title?: string;
  description?: string;
  canonicalUrl?: string;
}}

const schemaGraph = {json.dumps(self.schema_graph, indent=2, ensure_ascii=False)};

export const AeoMeta: React.FC<AeoMetaProps> = ({{
  title = {json.dumps(self.site_name)},
  description = {json.dumps(self.description)},
  canonicalUrl = "{self.base_url}/",
}}) => {{
  useEffect(() => {{
    document.title = title;

    // Inject or update canonical tag
    let linkCanonical = document.querySelector<HTMLLinkElement>("link[rel='canonical']");
    if (!linkCanonical) {{
      linkCanonical = document.createElement("link");
      linkCanonical.rel = "canonical";
      document.head.appendChild(linkCanonical);
    }}
    linkCanonical.href = canonicalUrl;

    // Inject Schema.org script
    let scriptEl = document.getElementById("aeo-schema-graph") as HTMLScriptElement | null;
    if (!scriptEl) {{
      scriptEl = document.createElement("script");
      scriptEl.id = "aeo-schema-graph";
      scriptEl.type = "application/ld+json";
      document.head.appendChild(scriptEl);
    }}
    scriptEl.textContent = JSON.stringify(schemaGraph);
  }}, [title, description, canonicalUrl]);

  return null;
}};

export default AeoMeta;
"""

        return {
            "index.html": index_html,
            "vite-plugin-aeo.ts": vite_plugin_ts,
            "src/components/AeoMeta.tsx": aeo_meta_tsx,
            "public/llms.txt": self.llms_txt,
            "public/robots.txt": self.robots_txt,
        }

    # -------------------------------------------------------------------------
    # 5. SvelteKit
    # -------------------------------------------------------------------------
    def export_sveltekit(self) -> Dict[str, str]:
        """
        Generates SvelteKit integration files:
          - src/routes/+layout.svelte
          - src/routes/robots.txt/+server.ts
          - src/routes/llms.txt/+server.ts
          - src/routes/ai.txt/+server.ts
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        layout_svelte = f"""<script lang="ts">
  const schemaGraph = {json_ld_str};
  const jsonLdHtml = JSON.stringify(schemaGraph);
</script>

<svelte:head>
  <title>{self.site_name}</title>
  <meta name="description" content={json.dumps(self.description)} />
  <link rel="canonical" href="{self.base_url}/" />

  <!-- Open Graph / AI Indexing -->
  <meta property="og:title" content={json.dumps(self.site_name)} />
  <meta property="og:description" content={json.dumps(self.description)} />
  <meta property="og:url" content="{self.base_url}/" />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="{self.og_image_url}" />
  <meta name="twitter:card" content="summary_large_image" />

  <!-- AEO Schema.org Graph -->
  {{@html `<script type="application/ld+json">${{jsonLdHtml}}<` + `/script>`}}
</svelte:head>

<slot />
"""

        robots_server_ts = f"""import type {{ RequestHandler }} from "@sveltejs/kit";

const robotsContent = {json.dumps(self.robots_txt)};

export const GET: RequestHandler = () => {{
  return new Response(robotsContent, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    }},
  }});
}};
"""

        llms_server_ts = f"""import type {{ RequestHandler }} from "@sveltejs/kit";

const llmsContent = {json.dumps(self.llms_txt)};

export const GET: RequestHandler = () => {{
  return new Response(llmsContent, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    }},
  }});
}};
"""

        ai_server_ts = f"""import type {{ RequestHandler }} from "@sveltejs/kit";

const aiContent = {json.dumps(self.ai_txt)};

export const GET: RequestHandler = () => {{
  return new Response(aiContent, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    }},
  }});
}};
"""

        return {
            "src/routes/+layout.svelte": layout_svelte,
            "src/routes/robots.txt/+server.ts": robots_server_ts,
            "src/routes/llms.txt/+server.ts": llms_server_ts,
            "src/routes/ai.txt/+server.ts": ai_server_ts,
        }

    # -------------------------------------------------------------------------
    # 6. Remix
    # -------------------------------------------------------------------------
    def export_remix(self) -> Dict[str, str]:
        """
        Generates Remix integration files:
          - app/root.tsx (with meta function and schema script)
          - app/routes/robots[.]txt.ts (loader)
          - app/routes/llms[.]txt.ts (loader)
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        root_tsx = f"""import type {{ MetaFunction, LinksFunction }} from "@remix-run/node";
import {{
  Links,
  LiveReload,
  Meta,
  Outlet,
  Scripts,
  ScrollRestoration,
}} from "@remix-run/react";

export const meta: MetaFunction = () => [
  {{ title: {json.dumps(self.site_name)} }},
  {{ name: "description", content: {json.dumps(self.description)} }},
  {{ property: "og:title", content: {json.dumps(self.site_name)} }},
  {{ property: "og:description", content: {json.dumps(self.description)} }},
  {{ property: "og:url", content: "{self.base_url}/" }},
  {{ property: "og:image", content: "{self.og_image_url}" }},
  {{ property: "twitter:card", content: "summary_large_image" }},
  {{ tagName: "link", rel: "canonical", href: "{self.base_url}/" }},
];

const schemaGraph = {json_ld_str};

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
        <LiveReload />
      </body>
    </html>
  );
}}
"""

        robots_route_ts = f"""import type {{ LoaderFunctionArgs }} from "@remix-run/node";

const robotsContent = {json.dumps(self.robots_txt)};

export const loader = async ({{ request }}: LoaderFunctionArgs) => {{
  return new Response(robotsContent, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    }},
  }});
}};
"""

        llms_route_ts = f"""import type {{ LoaderFunctionArgs }} from "@remix-run/node";

const llmsContent = {json.dumps(self.llms_txt)};

export const loader = async ({{ request }}: LoaderFunctionArgs) => {{
  return new Response(llmsContent, {{
    headers: {{
      "Content-Type": "text/plain; charset=utf-8",
      "Cache-Control": "public, max-age=86400",
    }},
  }});
}};
"""

        return {
            "app/root.tsx": root_tsx,
            "app/routes/robots[.]txt.ts": robots_route_ts,
            "app/routes/llms[.]txt.ts": llms_route_ts,
        }

    # -------------------------------------------------------------------------
    # 7. Nuxt / Vue
    # -------------------------------------------------------------------------
    def export_nuxt(self) -> Dict[str, str]:
        """
        Generates Nuxt 3 / Vue integration files:
          - nuxt.config.ts (head config with JSON-LD)
          - app.vue (useHead composition API snippet)
          - server/routes/llms.txt.ts (server event handler)
          - server/routes/robots.txt.ts (server event handler)
        """
        json_ld_str = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        nuxt_config_ts = f"""const schemaGraph = {json_ld_str};

// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({{
  app: {{
    head: {{
      title: {json.dumps(self.site_name)},
      htmlAttrs: {{ lang: "en" }},
      meta: [
        {{ charset: "utf-8" }},
        {{ name: "viewport", content: "width=device-width, initial-scale=1" }},
        {{ name: "description", content: {json.dumps(self.description)} }},
        {{ property: "og:title", content: {json.dumps(self.site_name)} }},
        {{ property: "og:description", content: {json.dumps(self.description)} }},
        {{ property: "og:url", content: "{self.base_url}/" }},
        {{ property: "og:image", content: "{self.og_image_url}" }},
        {{ name: "twitter:card", content: "summary_large_image" }},
      ],
      link: [
        {{ rel: "canonical", href: "{self.base_url}/" }},
      ],
      script: [
        {{
          type: "application/ld+json",
          children: JSON.stringify(schemaGraph),
        }},
      ],
    }},
  }},
}});
"""

        app_vue = f"""<script setup lang="ts">
const schemaGraph = {json_ld_str};

useHead({{
  title: {json.dumps(self.site_name)},
  meta: [
    {{ name: "description", content: {json.dumps(self.description)} }},
    {{ property: "og:title", content: {json.dumps(self.site_name)} }},
    {{ property: "og:description", content: {json.dumps(self.description)} }},
    {{ property: "og:url", content: "{self.base_url}/" }},
    {{ property: "og:image", content: "{self.og_image_url}" }},
  ],
  link: [
    {{ rel: "canonical", href: "{self.base_url}/" }},
  ],
  script: [
    {{
      type: "application/ld+json",
      children: JSON.stringify(schemaGraph),
    }},
  ],
}});
</script>

<template>
  <div>
    <NuxtPage />
  </div>
</template>
"""

        server_llms_ts = f"""const llmsContent = {json.dumps(self.llms_txt)};

export default defineEventHandler((event) => {{
  setResponseHeader(event, "content-type", "text/plain; charset=utf-8");
  setResponseHeader(event, "cache-control", "public, max-age=86400");
  return llmsContent;
}});
"""

        server_robots_ts = f"""const robotsContent = {json.dumps(self.robots_txt)};

export default defineEventHandler((event) => {{
  setResponseHeader(event, "content-type", "text/plain; charset=utf-8");
  setResponseHeader(event, "cache-control", "public, max-age=86400");
  return robotsContent;
}});
"""

        return {
            "nuxt.config.ts": nuxt_config_ts,
            "app.vue": app_vue,
            "server/routes/llms.txt.ts": server_llms_ts,
            "server/routes/robots.txt.ts": server_robots_ts,
        }

    # -------------------------------------------------------------------------
    # 8. Static HTML / Hugo / Jekyll
    # -------------------------------------------------------------------------
    def export_static_html(self) -> Dict[str, str]:
        """Generates static HTML header partials and static root files."""
        json_ld_indented = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        partial_html = f"""<!-- Answer Engine Optimization (AEO) & Primary Meta -->
<title>{self.site_name}</title>
<meta name="description" content="{self.description}">
<link rel="canonical" href="{self.base_url}/">

<!-- OpenGraph & Twitter -->
<meta property="og:title" content="{self.site_name}">
<meta property="og:description" content="{self.description}">
<meta property="og:url" content="{self.base_url}/">
<meta property="og:type" content="website">
<meta property="og:image" content="{self.og_image_url}">
<meta name="twitter:card" content="summary_large_image">

<!-- Schema.org JSON-LD Linked Data Graph -->
<script type="application/ld+json">
{json_ld_indented}
</script>
"""

        return {
            "partials/aeo-head.html": partial_html,
            "llms.txt": self.llms_txt,
            "llms-full.txt": self.llms_full_txt,
            "ai.txt": self.ai_txt,
            "robots.txt": self.robots_txt,
            "schema-graph.json": json_ld_indented,
        }

    def export_hugo(self) -> Dict[str, str]:
        """Generates Hugo template partials and config snippet."""
        json_ld_indented = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        hugo_partial = f"""{{{{/* Hugo AEO Head Partial (layouts/partials/aeo-head.html) */}}}}
<title>{{{{ if .IsHome }}}}{{{{ .Site.Title }}}}{{{{ else }}}}{{{{ .Title }}}} | {{{{ .Site.Title }}}}{{{{ end }}}}</title>
<meta name="description" content="{{{{ with .Description }}}}{{{{ . }}}}{{{{ else }}}}{{{{ .Site.Params.description }}}}{{{{ end }}}}">
<link rel="canonical" href="{{{{ .Permalink }}}}">

<!-- Open Graph -->
<meta property="og:title" content="{{{{ if .IsHome }}}}{{{{ .Site.Title }}}}{{{{ else }}}}{{{{ .Title }}}}{{{{ end }}}}">
<meta property="og:description" content="{{{{ with .Description }}}}{{{{ . }}}}{{{{ else }}}}{{{{ .Site.Params.description }}}}{{{{ end }}}}">
<meta property="og:url" content="{{{{ .Permalink }}}}">
<meta property="og:type" content="{{{{ if .IsPage }}}}article{{{{ else }}}}website{{{{ end }}}}">

<!-- Schema.org JSON-LD Graph -->
<script type="application/ld+json">
{json_ld_indented}
</script>
"""

        hugo_config_toml = f"""# Add to hugo.toml / config.toml
baseURL = '{self.base_url}/'
title = '{self.site_name}'
languageCode = 'en-us'

[params]
  description = '{self.description}'
  tagline = '{self.tagline}'
"""

        return {
            "layouts/partials/aeo-head.html": hugo_partial,
            "hugo.toml.snippet": hugo_config_toml,
            "static/llms.txt": self.llms_txt,
            "static/robots.txt": self.robots_txt,
        }

    def export_jekyll(self) -> Dict[str, str]:
        """Generates Jekyll includes and config snippet."""
        json_ld_indented = json.dumps(self.schema_graph, indent=2, ensure_ascii=False)

        jekyll_include = f"""<!-- Jekyll AEO Head Include (_includes/aeo-head.html) -->
<title>{{% if page.title %}}{{{{ page.title }}}} | {{{{ site.title }}}}{{% else %}}{{{{ site.title }}}}{{% endif %}}</title>
<meta name="description" content="{{% if page.description %}}{{{{ page.description }}}}{{% else %}}{{{{ site.description }}}}{{% endif %}}">
<link rel="canonical" href="{{{{ page.url | absolute_url }}}}">

<!-- Open Graph -->
<meta property="og:title" content="{{% if page.title %}}{{{{ page.title }}}}{{% else %}}{{{{ site.title }}}}{{% endif %}}">
<meta property="og:description" content="{{% if page.description %}}{{{{ page.description }}}}{{% else %}}{{{{ site.description }}}}{{% endif %}}">
<meta property="og:url" content="{{{{ page.url | absolute_url }}}}">
<meta property="og:type" content="website">

<!-- Schema.org JSON-LD Graph -->
<script type="application/ld+json">
{json_ld_indented}
</script>
"""

        jekyll_config_yml = f"""# Add to _config.yml
url: "{self.base_url}"
title: "{self.site_name}"
description: "{self.description}"
"""

        return {
            "_includes/aeo-head.html": jekyll_include,
            "_config.yml.snippet": jekyll_config_yml,
            "llms.txt": self.llms_txt,
            "robots.txt": self.robots_txt,
        }

    # -------------------------------------------------------------------------
    # Unified Exporter
    # -------------------------------------------------------------------------
    def export_framework(self, framework: str) -> Dict[str, str]:
        """Exports integration files for the given framework name."""
        fn = normalize_framework_name(framework)
        if fn == "nextjs_app":
            return self.export_nextjs_app()
        elif fn == "nextjs_pages":
            return self.export_nextjs_pages()
        elif fn == "astro":
            return self.export_astro()
        elif fn == "vite_react":
            return self.export_vite_react()
        elif fn == "sveltekit":
            return self.export_sveltekit()
        elif fn == "remix":
            return self.export_remix()
        elif fn == "nuxt":
            return self.export_nuxt()
        elif fn == "static":
            return self.export_static_html()
        elif fn == "hugo":
            return self.export_hugo()
        elif fn == "jekyll":
            return self.export_jekyll()
        return self.export_nextjs_app()

    def export_all(self) -> Dict[str, Dict[str, str]]:
        """Exports integration files for all supported frameworks."""
        return {
            fw: self.export_framework(fw)
            for fw in SUPPORTED_FRAMEWORKS
        }

    def write_framework_bundle(
        self,
        framework: str,
        output_dir: Union[str, Path]
    ) -> Dict[str, str]:
        """
        Writes all generated integration files for a specific framework to disk.
        Returns a dict of relative file paths to absolute created file paths.
        """
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        files = self.export_framework(framework)
        written: Dict[str, str] = {}

        for rel_path, content in files.items():
            file_dest = out_path / rel_path
            file_dest.parent.mkdir(parents=True, exist_ok=True)
            with open(file_dest, "w", encoding="utf-8") as f:
                f.write(content)
            written[rel_path] = str(file_dest)

        return written

    # Method Aliases
    export = export_framework
    write_bundle = write_framework_bundle



# =============================================================================
# Auto-Remediation Generator
# =============================================================================

class AEORemediationGenerator:
    """
    Analyzes live AEO/GEO audit scan results and generates exact, concrete code fixes
    for all detected deficiencies tailored to the user's chosen web framework.
    """

    def __init__(
        self,
        scan_results: Union[Dict[str, Any], Any],
        config: Optional[Dict[str, Any]] = None,
        framework: str = "nextjs_app",
        niche: str = "developer_tools"
    ):
        # Extract dictionary if passed a LiveAEOScanner instance
        if hasattr(scan_results, "compute_audit_scores"):
            self.scan_data = scan_results.compute_audit_scores()
        elif isinstance(scan_results, dict):
            self.scan_data = scan_results
        else:
            self.scan_data = {}

        self.framework = normalize_framework_name(framework)
        self.niche = niche

        # Synthesize base config from scan results if not explicitly provided
        inferred_config = self._infer_config_from_scan(self.scan_data)
        if config:
            inferred_config.update(config)

        self.config = resolve_config(inferred_config, niche=niche)
        self.exporter = FrameworkExporter(self.config, niche=niche)

    def _infer_config_from_scan(self, scan_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts metadata from scan results to bootstrap configuration."""
        cfg: Dict[str, Any] = {}
        target_url = scan_data.get("target_url") or scan_data.get("origin")
        if target_url:
            cfg["base_url"] = target_url.rstrip("/")
            # extract domain
            from urllib.parse import urlparse
            parsed = urlparse(target_url)
            if parsed.netloc:
                cfg["domain"] = parsed.netloc

        pages = scan_data.get("pages", [])
        if pages and isinstance(pages, list):
            first_page = pages[0]
            if isinstance(first_page, dict):
                if first_page.get("title"):
                    cfg["site_name"] = first_page["title"]
                if first_page.get("description"):
                    cfg["description"] = first_page["description"]
                if first_page.get("tagline"):
                    cfg["tagline"] = first_page["tagline"]

        return cfg

    def generate_plan(self) -> Dict[str, Any]:
        """
        Generates the comprehensive remediation plan with concrete code fixes.
        """
        root_assets = self.scan_data.get("root_assets", {})
        pages = self.scan_data.get("pages", [])
        score = self.scan_data.get("overall_aeo_score", 0.0)
        bot_compat = self.scan_data.get("ai_engine_compatibility", {})

        remediations: List[Dict[str, Any]] = []
        files_to_create: Dict[str, str] = {}
        framework_files = self.exporter.export_framework(self.framework)

        # 1. Check llms.txt (Critical / High)
        llms_exists = root_assets.get("llms_txt", {}).get("exists", False)
        if not llms_exists:
            target_file, code = self._get_framework_target_for_llms_txt(framework_files)
            files_to_create[target_file] = code
            remediations.append({
                "id": "missing_llms_txt",
                "priority": "HIGH",
                "category": "Machine Discovery",
                "title": "Missing llms.txt Standard Manifest",
                "issue": "Your site does not serve an /llms.txt file matching the llmstxt.org standard.",
                "impact": "AI search engines (Perplexity, ChatGPT Search, Claude) fail to parse concise site docs within token limits (<50 tokens).",
                "framework": self.framework,
                "target_file": target_file,
                "action": "CREATE_FILE",
                "code": code,
                "instructions": f"Create `{target_file}` with the provided code to serve your canonical llms.txt manifest.",
            })

        # 2. Check llms-full.txt (Medium)
        llms_full_exists = root_assets.get("llms_full_txt", {}).get("exists", False)
        if not llms_full_exists:
            target_file, code = self._get_framework_target_for_llms_full_txt(framework_files)
            if target_file and code:
                files_to_create[target_file] = code
                remediations.append({
                    "id": "missing_llms_full_txt",
                    "priority": "MEDIUM",
                    "category": "Machine Discovery",
                    "title": "Missing Comprehensive Knowledge Base (/llms-full.txt)",
                    "issue": "No deep documentation index found at /llms-full.txt.",
                    "impact": "Deep-research AI agents (Perplexity Pro, OpenAI Operator) cannot ingest complete architectural reference in one request.",
                    "framework": self.framework,
                    "target_file": target_file,
                    "action": "CREATE_FILE",
                    "code": code,
                    "instructions": f"Add `{target_file}` to serve your comprehensive full-text knowledge base.",
                })

        # 3. Check Schema.org Linked Data (Critical)
        pages_with_schema = [p for p in pages if isinstance(p, dict) and p.get("schema_count", 0) > 0]
        has_graph = any(
            isinstance(p, dict) and any("@graph" in str(s) for s in p.get("schemas", []))
            for p in pages
        )
        has_faq = any(
            isinstance(p, dict) and any("FAQPage" in str(s) for s in p.get("schemas", []))
            for p in pages
        )

        if not pages_with_schema or not has_graph:
            target_file, code = self._get_framework_target_for_schema(framework_files)
            files_to_create[target_file] = code
            remediations.append({
                "id": "missing_schema_graph",
                "priority": "CRITICAL",
                "category": "Knowledge Graph",
                "title": "Missing Schema.org Linked Data @graph",
                "issue": "No connected Schema.org @graph (Organization, WebSite, App/Service, FAQPage) detected in <head>.",
                "impact": "Google AI Overviews and ChatGPT cannot disambiguate your brand entity or verify answer authenticity.",
                "framework": self.framework,
                "target_file": target_file,
                "action": "UPDATE_FILE" if target_file.endswith((".tsx", ".astro", ".svelte", ".vue", ".html")) else "CREATE_FILE",
                "code": code,
                "instructions": f"Embed the linked @graph in `{target_file}`.",
            })

        # 4. Check AI Crawler Governance in robots.txt (High)
        robots_exists = root_assets.get("robots_txt", {}).get("exists", False)
        robots_content = root_assets.get("robots_txt", {}).get("content", "").lower()
        has_ai_bots = (
            "gptbot" in robots_content or
            "perplexitybot" in robots_content or
            "claudebot" in robots_content
        )

        if not robots_exists or not has_ai_bots:
            target_file, code = self._get_framework_target_for_robots(framework_files)
            files_to_create[target_file] = code
            remediations.append({
                "id": "missing_ai_crawlers_robots",
                "priority": "HIGH",
                "category": "Crawler Policies",
                "title": "Missing Explicit AI Search Crawler Permissions in robots.txt",
                "issue": "robots.txt does not explicitly grant access to GPTBot, PerplexityBot, ClaudeBot, and Applebot-Extended.",
                "impact": "Modern AI search crawlers may throttle or skip indexing your site content.",
                "framework": self.framework,
                "target_file": target_file,
                "action": "CREATE_FILE" if not robots_exists else "UPDATE_FILE",
                "code": code,
                "instructions": f"Update `{target_file}` with modern AI crawler directives and canonical sitemap link.",
            })

        # 5. Check ai.txt Policy Manifest (Medium)
        ai_exists = root_assets.get("ai_txt", {}).get("exists", False)
        if not ai_exists:
            target_file, code = self._get_framework_target_for_ai_txt(framework_files)
            if target_file and code:
                files_to_create[target_file] = code
                remediations.append({
                    "id": "missing_ai_txt",
                    "priority": "MEDIUM",
                    "category": "AI Policy",
                    "title": "Missing /ai.txt Attribution Manifest",
                    "issue": "No machine-readable ai.txt declaration for citation rules and permissions.",
                    "impact": "AI models cite your content without canonical author attribution or licensing clarity.",
                    "framework": self.framework,
                    "target_file": target_file,
                    "action": "CREATE_FILE",
                    "code": code,
                    "instructions": f"Place `{target_file}` declaring canonical citation format and model access terms.",
                })

        # 6. Check Sitemap & Technical SEO (Medium / High)
        sitemap_exists = root_assets.get("sitemap_xml", {}).get("exists", False)
        if not sitemap_exists:
            target_file, code = self._get_framework_target_for_sitemap(framework_files)
            if target_file and code:
                files_to_create[target_file] = code
                remediations.append({
                    "id": "missing_sitemap_xml",
                    "priority": "HIGH",
                    "category": "Technical SEO",
                    "title": "Missing Automated Sitemap",
                    "issue": "No sitemap.xml endpoint discovered.",
                    "impact": "Search engines and AI crawler bots cannot systematically map all subpages.",
                    "framework": self.framework,
                    "target_file": target_file,
                    "action": "CREATE_FILE",
                    "code": code,
                    "instructions": f"Generate `{target_file}` to publish automatic sitemap.",
                })

        # Calculate counts
        critical_count = sum(1 for r in remediations if r["priority"] == "CRITICAL")
        high_count = sum(1 for r in remediations if r["priority"] == "HIGH")
        medium_count = sum(1 for r in remediations if r["priority"] == "MEDIUM")
        low_count = sum(1 for r in remediations if r["priority"] == "LOW")

        summary_md = self._generate_markdown_summary(
            remediations,
            score=score,
            critical=critical_count,
            high=high_count,
            medium=medium_count
        )

        return {
            "target_url": self.config.get("base_url", "https://example.com"),
            "framework": self.framework,
            "overall_score": score,
            "total_issues_count": len(remediations),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "low_count": low_count,
            "remediations": remediations,
            "all_files_to_create": files_to_create,
            "summary_markdown": summary_md,
        }

    # -------------------------------------------------------------------------
    # Target Resolution Helpers
    # -------------------------------------------------------------------------
    def _get_framework_target_for_llms_txt(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/llms.txt/route.ts"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework == "nextjs_pages":
            key = "pages/api/llms.txt.ts"
            return key, files.get(key, self.exporter.export_nextjs_pages()[key])
        elif self.framework == "astro":
            key = "public/llms.txt"
            return key, files.get(key, self.exporter.llms_txt)
        elif self.framework == "vite_react":
            key = "public/llms.txt"
            return key, files.get(key, self.exporter.llms_txt)
        elif self.framework == "sveltekit":
            key = "src/routes/llms.txt/+server.ts"
            return key, files.get(key, self.exporter.export_sveltekit()[key])
        elif self.framework == "remix":
            key = "app/routes/llms[.]txt.ts"
            return key, files.get(key, self.exporter.export_remix()[key])
        elif self.framework == "nuxt":
            key = "server/routes/llms.txt.ts"
            return key, files.get(key, self.exporter.export_nuxt()[key])
        elif self.framework == "hugo":
            key = "static/llms.txt"
            return key, files.get(key, self.exporter.llms_txt)
        elif self.framework == "jekyll":
            key = "llms.txt"
            return key, files.get(key, self.exporter.llms_txt)
        else:
            return "llms.txt", self.exporter.llms_txt

    def _get_framework_target_for_llms_full_txt(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/llms-full.txt/route.ts"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework in ("astro", "vite_react"):
            key = "public/llms-full.txt"
            return key, files.get(key, self.exporter.llms_full_txt)
        else:
            return "llms-full.txt", self.exporter.llms_full_txt

    def _get_framework_target_for_schema(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/layout.tsx"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework == "nextjs_pages":
            key = "pages/_document.tsx"
            return key, files.get(key, self.exporter.export_nextjs_pages()[key])
        elif self.framework == "astro":
            key = "src/components/AeoHead.astro"
            return key, files.get(key, self.exporter.export_astro()[key])
        elif self.framework == "vite_react":
            key = "index.html"
            return key, files.get(key, self.exporter.export_vite_react()[key])
        elif self.framework == "sveltekit":
            key = "src/routes/+layout.svelte"
            return key, files.get(key, self.exporter.export_sveltekit()[key])
        elif self.framework == "remix":
            key = "app/root.tsx"
            return key, files.get(key, self.exporter.export_remix()[key])
        elif self.framework == "nuxt":
            key = "nuxt.config.ts"
            return key, files.get(key, self.exporter.export_nuxt()[key])
        elif self.framework == "hugo":
            key = "layouts/partials/aeo-head.html"
            return key, files.get(key, self.exporter.export_hugo()[key])
        elif self.framework == "jekyll":
            key = "_includes/aeo-head.html"
            return key, files.get(key, self.exporter.export_jekyll()[key])
        else:
            key = "partials/aeo-head.html"
            return key, files.get(key, self.exporter.export_static_html()[key])

    def _get_framework_target_for_robots(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/robots.ts"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework == "sveltekit":
            key = "src/routes/robots.txt/+server.ts"
            return key, files.get(key, self.exporter.export_sveltekit()[key])
        elif self.framework == "remix":
            key = "app/routes/robots[.]txt.ts"
            return key, files.get(key, self.exporter.export_remix()[key])
        elif self.framework == "nuxt":
            key = "server/routes/robots.txt.ts"
            return key, files.get(key, self.exporter.export_nuxt()[key])
        elif self.framework == "astro":
            key = "public/robots.txt"
            return key, files.get(key, self.exporter.robots_txt)
        elif self.framework == "vite_react":
            key = "public/robots.txt"
            return key, files.get(key, self.exporter.robots_txt)
        elif self.framework == "hugo":
            key = "static/robots.txt"
            return key, files.get(key, self.exporter.robots_txt)
        elif self.framework == "jekyll":
            key = "robots.txt"
            return key, files.get(key, self.exporter.robots_txt)
        else:
            return "robots.txt", self.exporter.robots_txt

    def _get_framework_target_for_ai_txt(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/ai.txt/route.ts"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework == "sveltekit":
            key = "src/routes/ai.txt/+server.ts"
            return key, files.get(key, self.exporter.export_sveltekit()[key])
        elif self.framework in ("astro", "vite_react"):
            key = "public/ai.txt"
            return key, files.get(key, self.exporter.ai_txt)
        else:
            return "ai.txt", self.exporter.ai_txt

    def _get_framework_target_for_sitemap(self, files: Dict[str, str]) -> (str, str):
        if self.framework == "nextjs_app":
            key = "app/sitemap.ts"
            return key, files.get(key, self.exporter.export_nextjs_app()[key])
        elif self.framework == "astro":
            key = "astro.config.mjs"
            return key, files.get(key, self.exporter.export_astro()[key])
        else:
            return "sitemap.xml", f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>{self.config.get('base_url', 'https://example.com')}/</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>"""

    def _generate_markdown_summary(
        self,
        remediations: List[Dict[str, Any]],
        score: float,
        critical: int,
        high: int,
        medium: int
    ) -> str:
        """Generates a concise markdown summary for developers."""
        lines = [
            f"# AEO Auto-Remediation Plan — {self.config.get('site_name', 'Website')}",
            f"**Target URL:** {self.config.get('base_url')}  ",
            f"**Framework:** `{self.framework}`  ",
            f"**Current Audit Score:** {score}/100  ",
            f"**Issues Detected:** {len(remediations)} ({critical} Critical, {high} High, {medium} Medium)",
            "",
            "## Summary of Actions",
            "| Priority | Category | Target File | Action |",
            "|---|---|---|---|",
        ]

        for r in remediations:
            badge = f"**{r['priority']}**" if r["priority"] == "CRITICAL" else r["priority"]
            lines.append(f"| {badge} | {r['category']} | `{r['target_file']}` | {r['action']} |")

        lines.append("")
        lines.append("## Step-by-Step Remediation Files")
        lines.append("")

        for idx, r in enumerate(remediations, start=1):
            lines.append(f"### {idx}. [{r['priority']}] {r['title']}")
            lines.append(f"**Issue:** {r['issue']}")
            lines.append(f"**Impact:** {r['impact']}")
            lines.append(f"**File:** `{r['target_file']}` ({r['action']})")
            lines.append("")
            # Determine code block syntax
            syntax = "typescript"
            if r["target_file"].endswith(".astro"):
                syntax = "astro"
            elif r["target_file"].endswith(".svelte"):
                syntax = "svelte"
            elif r["target_file"].endswith(".vue"):
                syntax = "vue"
            elif r["target_file"].endswith(".html"):
                syntax = "html"
            elif r["target_file"].endswith(".txt"):
                syntax = "text"
            elif r["target_file"].endswith(".json"):
                syntax = "json"

            lines.append(f"```{syntax}")
            lines.append(r["code"].strip())
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

    def write_remediations(self, output_dir: Union[str, Path]) -> Dict[str, str]:
        """
        Writes all concrete remediation files directly to disk in output_dir.
        """
        out_path = Path(output_dir).resolve()
        out_path.mkdir(parents=True, exist_ok=True)

        plan = self.generate_plan()
        created: Dict[str, str] = {}

        for rel_file, content in plan["all_files_to_create"].items():
            dest = out_path / rel_file
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            created[rel_file] = str(dest)

        # Also write the plan summary markdown
        plan_md_path = out_path / "AEO_REMEDIATION_PLAN.md"
        with open(plan_md_path, "w", encoding="utf-8") as f:
            f.write(plan["summary_markdown"])
        created["AEO_REMEDIATION_PLAN.md"] = str(plan_md_path)

        return created


# =============================================================================
# Functional Convenience APIs
# =============================================================================

def export_framework_code(
    framework: str,
    config: Optional[Dict[str, Any]] = None,
    niche: str = "developer_tools"
) -> Dict[str, str]:
    """Generates integration files for the given framework."""
    exporter = FrameworkExporter(config=config, niche=niche)
    return exporter.export_framework(framework)


def generate_remediation_plan(
    scan_results: Union[Dict[str, Any], Any],
    framework: str = "nextjs_app",
    config: Optional[Dict[str, Any]] = None,
    niche: str = "developer_tools"
) -> Dict[str, Any]:
    """Generates an actionable AEO remediation plan based on scan results."""
    generator = AEORemediationGenerator(
        scan_results=scan_results,
        config=config,
        framework=framework,
        niche=niche
    )
    return generator.generate_plan()

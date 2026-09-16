# AEO Graph Engine - Real-World Examples & Showcase

This directory contains complete, realistic, copy-pasteable production implementations demonstrating Answer Engine Optimization (AEO), Generative Engine Optimization (GEO), Schema.org Linked Data Graphs, and machine discovery standards (`llms.txt`, `ai.txt`, `robots.txt`).

---

## 📂 Example Projects Overview

| Directory | Target Platform / Framework | Key Highlights |
| :--- | :--- | :--- |
| [`nextjs-app-router/`](./nextjs-app-router/) | **Next.js 14 / 15 (App Router)** | TypeScript `layout.tsx`, dynamic `robots.ts`, `sitemap.ts`, route handler for `llms.txt/route.ts`, and `public/ai.txt`. |
| [`astro-site/`](./astro-site/) | **Astro 4 / 5** | Zero-JS `<AeoHead.astro>` component, sitemap integration, `public/llms.txt`, and crawler `public/robots.txt`. |
| [`vite-react-spa/`](./vite-react-spa/) | **Vite + React SPA** | Raw HTML pre-injected Schema graph in `index.html`, automated `vite-plugin-aeo` asset bundler in `vite.config.ts`, and `public/llms.txt`. |
| [`saas-landing/`](./saas-landing/) | **Production B2B SaaS Showcase** | Full standalone AEO bundle (`aeo_config.json`, `schema-graph.json`, `llms.txt`, `ai.txt`, `robots.txt`) with enterprise features & FAQs. |
| [`mcp-clients/`](./mcp-clients/) | **Model Context Protocol (MCP)** | Plug-and-play JSON configs for **Claude Desktop**, **Cursor**, **Cline / Roo Code**, and **Zed Editor**. |

---

## 🏗️ Architecture Matrix

Every example is crafted to ensure full compatibility with modern AI search engines and crawler bots:

```text
                                  ┌────────────────────────┐
                                  │   Target Web Page /    │
                                  │      Application       │
                                  └───────────┬────────────┘
                                              │
               ┌──────────────────────────────┼──────────────────────────────┐
               │                              │                              │
               ▼                              ▼                              ▼
    ┌──────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
    │ Schema.org @graph    │      │  Machine Discovery   │      │  AI Crawler Rules    │
    │  (application/ld+json)│     │  (llms.txt, ai.txt)  │      │    (robots.txt)      │
    ├──────────────────────┤      ├──────────────────────┤      ├──────────────────────┤
    │ • Organization       │      │ • H1 Title           │      │ • GPTBot (OpenAI)    │
    │ • WebSite            │      │ • Blockquote Summary │      │ • PerplexityBot      │
    │ • SoftwareApplication│      │ • Markdown Links     │      │ • ClaudeBot          │
    │ • FAQPage            │      │ • API & Docs Index   │      │ • Google-Extended    │
    │ • BreadcrumbList     │      │ • Policy & Directives│      │ • Applebot-Extended  │
    └──────────────────────┘      └──────────────────────┘      └──────────────────────┘
```

---

## 🚀 Quickstart: Generating & Validating

### 1. Generating Framework Code with CLI
You can generate starter code for any supported framework using the `export` command:

```bash
# Next.js App Router
aeo-graph-engine export --framework nextjs_app --output ./my-next-app

# Astro
aeo-graph-engine export --framework astro --output ./my-astro-site

# Vite + React
aeo-graph-engine export --framework vite_react --output ./my-vite-app
```

### 2. Validating Examples
You can run the built-in diagnostic validator on any of these example folders to verify their **AEO Readiness Score (0-100)**:

```bash
# Validate SaaS Landing bundle
aeo-graph-engine validate ./examples/saas-landing

# Validate Next.js public assets
aeo-graph-engine validate ./examples/nextjs-app-router/public
```

---

## 🧪 Automated Testing

All examples in this directory are continuously tested and validated via `pytest`:

```bash
PYTHONPATH=src pytest tests/test_examples.py -v
```

The test harness verifies:
1. **JSON Validity**: Every `.json` configuration and schema file parses strictly.
2. **Schema.org Graph Compliance**: All graphs contain required entity types (`Organization`, `WebSite`, `SoftwareApplication` / `LocalBusiness`, `FAQPage`) and valid `@context`.
3. **llms.txt Compliance**: Adheres to the [llmstxt.org](https://llmstxt.org) standard (H1 header, summary blockquote, structured markdown links).
4. **ai.txt Directives**: Declares canonical discovery endpoints.
5. **robots.txt AI Bot Matrix**: Validates crawler authorizations and sitemap declaration.
6. **Documentation Completeness**: Every example provides clear, non-empty `README.md` documentation.

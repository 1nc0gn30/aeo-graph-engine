# SaaS Landing Page AEO Showcase

This directory contains a complete, production-ready Answer Engine Optimization (AEO) and machine discovery bundle designed for high-growth **B2B SaaS and developer tooling companies**.

---

## 🎯 Why AEO Matters for Modern SaaS

When potential enterprise buyers ask AI search tools (like **ChatGPT Search**, **Perplexity AI**, or **Claude**):
- *"What are the top enterprise multi-agent workflow engines with zero data retention?"*
- *"How does NexusFlow compare to LangChain and Temporal for private VPC deployment?"*

Answer engines rely on structured linked data (`Schema.org`), machine-readable summaries (`llms.txt`), and explicit bot authorizations (`robots.txt`) to extract authoritative answers and provide direct citations.

---

## 📁 Directory Structure & File Overview

```text
examples/saas-landing/
├── aeo_config.json           # Canonical source-of-truth configuration file
├── schema-graph.json         # Standalone Schema.org @graph JSON-LD linked data file
├── llms.txt                  # Standardized LLM context file per llmstxt.org
├── ai.txt                    # Machine discovery manifest & AI agent directives
├── robots.txt                # Production crawler permission matrix & sitemap reference
└── README.md                 # This guide
```

---

## 📄 File Details

### 1. `aeo_config.json`
The declarative blueprint defining all brand metadata, products, pricing models, feature sets, technical knowledge domains, and high-intent FAQs. You can use this file as input to the `aeo-graph-engine` CLI to generate or regenerate all other artifacts automatically:

```bash
aeo-graph-engine generate --config aeo_config.json --output ./public
```

### 2. `schema-graph.json`
A rich Schema.org `@graph` validated with `aeo-graph-engine validate`:
- **`Organization`**: Declares legal entity, logos, social profiles, and knowledge topics (`knowsAbout`).
- **`WebSite`**: Canonical domain and search actions.
- **`SoftwareApplication`**: Application category, pricing, licensing, and feature lists.
- **`FAQPage`**: High-intent structured Q&A pairs directly targetable by Answer Engines.
- **`BreadcrumbList`**: Structured navigation tree for indexing bots.

### 3. `llms.txt`
Structured markdown file conforming to [llmstxt.org](https://llmstxt.org) that allows LLMs to quickly grasp product capabilities, architecture, and documentation links without consuming massive context tokens.

### 4. `ai.txt`
Machine discovery manifest that establishes search-indexing permissions, citation requirements, and direct pointers to `/schema-graph.json` and `/llms.txt`.

### 5. `robots.txt`
Authorizes verified AI search bots (`GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot`, `Google-Extended`) while protecting sensitive internal application routes (`/admin/`, `/api/private/`).

---

## 🚀 How to Use in Production

1. **Static Site Hosting**: Copy all files (`schema-graph.json`, `llms.txt`, `ai.txt`, `robots.txt`) into your web server’s public root directory (e.g. `public/`, `dist/`, or `static/`).
2. **HTML Injection**: Embed the contents of `schema-graph.json` into the `<head>` of your landing page:
   ```html
   <script type="application/ld+json">
     /* Paste contents of schema-graph.json here */
   </script>
   ```
3. **CI/CD Automation**: Add validation to your deployment pipeline to ensure your score remains above 90:
   ```bash
   aeo-graph-engine validate ./public
   ```

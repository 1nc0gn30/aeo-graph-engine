<div align="center">

# <img src="https://raw.githubusercontent.com/1nc0gn30/aeo-graph-engine/main/public/assets/google-aeo-icon.svg" width="36" height="36" onerror="this.style.display='none'" style="vertical-align: middle;" /> AEO Graph Engine (`aeo-graph-engine`)

### *Autonomous Answer Engine Optimization (AEO/GEO), Live Site Crawler, Schema.org Linked Data `@graph`, `llms.txt` & Google-Grade UI Workbench*

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-00f0ff?style=for-the-badge&logo=pypi&logoColor=white)](https://github.com/1nc0gn30/aeo-graph-engine)
[![Tests](https://img.shields.io/badge/tests-29%2F29%20Passing%20(100%25)-34d399?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-fbbf24?style=for-the-badge&logo=python&logoColor=black)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-a855f7?style=for-the-badge&logo=open-source-initiative&logoColor=white)](LICENSE)
[![Zero-Dependencies](https://img.shields.io/badge/dependencies-Zero%20Runtime%20Deps-4ade80?style=for-the-badge&logo=checkmarx&logoColor=white)](src/aeo_graph_engine/)

<br>

<p align="center">
  <a href="#-google-designed-aeo-studio-workbench">Google AEO Studio UI</a> •
  <a href="#-live-site-scanner--ai-readiness-crawler">Live Site Crawler</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-why-aeo--geo-matters-in-2026">Why AEO Matters</a> •
  <a href="#%EF%B8%8F-cli-reference">CLI Reference</a> •
  <a href="#-python-library-api">Python API</a> •
  <a href="#-ai-crawler-compatibility--backlink-intelligence">AI Bot Matrix & Backlinks</a> •
  <a href="#-ci--post-build-automation">CI/CD Automation</a>
</p>

</div>

---

## 🌐 Overview

Traditional SEO was engineered for classic 10-blue-link search result pages. **Answer Engine Optimization (AEO)** and **Generative Engine Optimization (GEO)** optimize your website for direct conversational retrieval and factual synthesis by **ChatGPT Search, Perplexity AI, Claude, Google AI Overviews, Apple Intelligence, and Grok**.

**`aeo-graph-engine`** is a zero-runtime-dependency Python engine, live multi-page crawler, CLI, and **Google-styled Light Mode Web Workbench** extracted and modularized from the **Zoth Studio** architecture. It audits live URLs, generates interconnected Schema.org `@graph` JSON-LD, compiles standard `llms.txt` manifests, and optimizes AI bot directives.

```
                  ┌──────────────────────────────────────────────────────────┐
                  │                 YOUR APPLICATION / SITE                 │
                  └────────────────────────────┬─────────────────────────────┘
                                               │
                                 aeo scan https://mysite.com
                                               │
                ┌──────────────────────────────┼───────────────────────────────┐
                ▼                              ▼                               ▼
   ┌─────────────────────────┐    ┌───────────────────────────┐   ┌──────────────────────────┐
   │   schema-graph.json     │    │   llms.txt & llms-full    │   │    ai.txt & robots.txt   │
   │ • Organization          │    │ • llmstxt.org compliant   │   │ • Bot Access Policies    │
   │ • WebSite SearchAction  │    │ • Summary blockquotes     │   │ • GPTBot / Perplexity    │
   │ • SoftwareApp / Service │    │ • Deep research ontology  │   │ • ClaudeBot / Applebot   │
   │ • FAQPage (Q&A citations)│   │ • Direct markdown links   │   │ • Google-Extended rules  │
   └─────────────────────────┘    └───────────────────────────┘   └──────────────────────────┘
```

---

## 🎨 Google-Designed AEO Studio Workbench

`aeo-graph-engine` includes a built-in interactive **Google Light Mode Web UI** (`AEO Studio`) designed with Google Material 3 aesthetics: clean `#f8f9fa` canvas, Google brand colors (`#4285f4`, `#ea4335`, `#fbbc04`, `#34a853`), elevation cards, live entity graph previews, and a real-time 0–100 AEO readiness meter.

### Launch the Local Studio:

```bash
# Launch interactive local studio (runs on http://127.0.0.1:8080 or specified port)
aeo serve --port 8080

# Or open public/index.html directly in any browser (100% offline static app)
open public/index.html
```

#### Studio Workbench Capabilities:
- 🌐 **Live Website Scanner & Multi-Page Crawler**: Enter any live URL (or localhost) to audit real sitemaps, robots.txt, subpages, and calculate live AEO scores.
- 🪄 **AI Prompt Synthesizer**: Type a 1-sentence prompt (e.g. *"DeFi lending on Solana called SolarYield"*) to auto-generate full Schema, `llms.txt`, and metadata.
- 📊 **Real-time 0–100 AEO Readiness Meter**: Real weighted scores across 5 core dimensions (Schema, llms.txt, AI bots, content, technical SEO).
- 🕸️ **Visual Entity Graph & Schema Preview**: Live syntax-highlighted `@graph` JSON-LD generator with canonical `@id` linking.
- 📄 **`llms.txt` & `llms-full.txt` Compiler**: llmstxt.org-compliant machine index with structured markdown links.
- 🤖 **AI Bot Access Matrix**: Live compatibility breakdown for GPTBot, PerplexityBot, ClaudeBot, Applebot, and Google-Extended.
- 💉 **Live HTML Schema Injector**: Paste raw HTML to test idempotent script embedding.
- 🏛️ **AEO Backlink & Citation Playbook**: Actionable high-authority citation targets and niche distribution strategy.
- 📥 **One-Click `.zip` Export**: Download all generated files in a single clean archive.

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine

# Editable pip install (zero external runtime dependencies!)
pip install -e .
```

### 2. Live Crawl & Audit Any Website

```bash
# Crawl live site up to 5 internal pages and compute real AEO scores
aeo scan https://example.com --max-pages 5
```

**Output:**
```
================================================================================
  AEO GRAPH ENGINE — LIVE WEBSITE AUDIT & AI READINESS REPORT
================================================================================
  Target URL:    https://example.com
  Base Origin:   https://example.com
  Overall Score: 78.5 / 100 [GOOD]
  Pages Audited: 5

CATEGORY SCORE BREAKDOWN:
  • Schema Linked Data:     18.0 / 25.0 pts (72%)
  • Llms Txt Machine Index:  0.0 / 25.0 pts (0%)
  • Ai Crawler Governance:  20.0 / 20.0 pts (100%)
  • Semantic Content:       14.0 / 15.0 pts (93%)
  • Technical Seo:          15.0 / 15.0 pts (100%)

ROOT ASSET DISCOVERY:
  [✔ FOUND] robots.txt (HTTP 200)
  [✖ MISSING] llms.txt (HTTP 404)
  [✖ MISSING] llms-full.txt (HTTP 404)
  [✔ FOUND] sitemap.xml (HTTP 200)

AI SEARCH ENGINE BOT ACCESS:
  • OpenAI / ChatGPT (GPTBot):              Allowed [✔ FAQ Schema]
  • Perplexity AI (PerplexityBot):          Allowed [✔ Connected @graph]
  • Anthropic Claude (ClaudeBot):           Allowed
  • Apple Intelligence (Applebot-Extended): Allowed [✔ Software Schema]
  • Google AI Overviews (Google-Extended):  Allowed [✔ Linked Data]

ACTIONABLE OPTIMIZATION PRIORITIES:
  [HIGH] Missing llms.txt standard manifest
  -> Fix: Generate and place a standardized llms.txt at root (llmstxt.org spec) to allow ChatGPT & Perplexity to ingest docs in <50 tokens.
```

### 3. Synthesize from Natural Language Prompt

```bash
# Auto-configure and write AEO bundle from a natural language prompt
aeo prompt "An AI resume builder called CVForge on cvforge.app" --output-dir dist/
```

### 4. Inject Schema into HTML

```bash
# Idempotently embed or update Schema.org JSON-LD in your index.html
aeo --inject dist/index.html --niche saas
```

### 5. Audit Local Directory

```bash
# Audit built directory or single file with full diagnostics
aeo --validate dist/ --format json
```

---

## 💡 Why AEO / GEO Matters in 2026

| Dimension | Classic SEO | Modern AEO / GEO |
| :--- | :--- | :--- |
| **Primary Audience** | Web search crawlers (Googlebot, Bingbot) | LLM Answer Engines (ChatGPT, Perplexity, Claude, Applebot) |
| **Output Form** | 10 blue links on SERP | Synthesized conversational answers with grounding citations |
| **Key Metadata** | Meta keywords, basic title tags | Connected Schema.org `@graph`, `llms.txt`, FAQ ontologies |
| **Crawler Policy** | Blanket allow / disallow | Explicit per-model crawler permissions in `robots.txt` & `ai.txt` |
| **Knowledge Depth** | Shallow keyword density | Deep structured research manifests (`llms-full.txt`) |

---

## 🛠️ CLI Reference

```bash
usage: aeo [-h] [--generate-all] [--output-dir OUTPUT_DIR]
           [--niche {developer_tools,ai_swarm,saas,cybersecurity,spatial_3d,creator,ecommerce,local_business}]
           [--config CONFIG] [--site-name SITE_NAME] [--domain DOMAIN] [--version VERSION]
           [--format {text,json}] [--jsonld] [--llms] [--llms-full] [--ai-txt] [--robots]
           [--inject INJECT] [--validate VALIDATE] [--test] [--dry-run]
           {serve,ui,extract,prompt,scan} ...
```

### Commands & Subcommands

| Command / Flag | Description |
| :--- | :--- |
| `aeo scan <url> [--max-pages 5]` | Live multi-page crawler, sitemap & robots discovery, AEO scorecard, bot compatibility breakdown, and backlink/distribution strategy |
| `aeo prompt "<description>"` | Synthesize configuration from natural language prompt and generate AEO bundle |
| `aeo serve [--port 8080]` | Start the Google-styled interactive local AEO Studio UI server |
| `aeo ui` | Alias for `aeo serve` |
| `aeo extract <file>` | Extract metadata from an existing HTML file into JSON |
| `--generate-all` | Generate complete AEO bundle (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) |
| `--output-dir <dir>` | Target output directory (default: `dist`) |
| `--niche <preset>` | Select domain preset (`developer_tools`, `saas`, `ai_swarm`, `cybersecurity`, etc.) |
| `--config <path>` | Path to a custom JSON configuration file |
| `--inject <file>` | Inject or update Schema.org JSON-LD in target HTML document |
| `--validate <path>` | Audit and compute 0–100 AEO Readiness Score |
| `--format {text,json}` | Format validation output as human text or machine JSON (ideal for CI) |
| `--test` | Run built-in unit tests and zero-drift verification |

---

## 🐍 Python Library API

Import `aeo_graph_engine` directly into your Python backend, static site generator, or CI script:

```python
from aeo_graph_engine import (
    LiveAEOScanner,
    synthesize_config_from_prompt,
    generate_schema_graph,
    generate_llms_txt,
    generate_robots_txt,
    write_aeo_bundle,
    validate_aeo_bundle
)

# 1. Live crawl and audit any URL
scanner = LiveAEOScanner("https://example.com", max_pages=5)
audit = scanner.compute_audit_scores()
print(f"AEO Score: {audit['overall_aeo_score']}/100")
print(f"Action Items: {len(audit['action_items'])}")

# 2. Synthesize config from natural language
config = synthesize_config_from_prompt("DeFi protocol on Solana called SolarYield")

# 3. Generate Schema.org JSON-LD Graph dictionary
graph = generate_schema_graph(config, niche="saas")

# 4. Write complete bundle and inject into built HTML files
artifacts = write_aeo_bundle(
    output_dir="./dist",
    config=config,
    niche="saas",
    inject_html_files=["./dist/index.html"]
)

# 5. Validate AEO Readiness Score (0-100)
report = validate_aeo_bundle("./dist")
print(f"Readiness Score: {report.score}/100 - Status: {report.to_dict()['status']}")
```

---

## 🤖 AI Crawler Compatibility & Backlink Intelligence

### How AI Search Engines Ingest Your Content:
- **OpenAI / ChatGPT Search**: Combines Bing index with direct queries to `llms.txt`, `robots.txt`, and `FAQPage` JSON-LD schemas.
- **Perplexity AI**: Discovers URLs via sitemaps, indexes full-text deep research pages (`llms-full.txt`), and cross-references Wikidata and GitHub entities.
- **Anthropic Claude**: Extracts knowledge from clean structured markdown representations without visual layout boilerplate, respecting `ai.txt` attribution policies.
- **Google Gemini & AI Overviews**: Leverages Knowledge Graph nodes, requiring connected Schema.org `@graph` linking `Organization` to `WebSite` to `SoftwareApplication`.

### High-Authority Knowledge Graph Anchors:
1. **llmstxt.org Directory & Awesome-LLMS-Txt**: Direct crawler registry for AI documentation indexing.
2. **Wikidata & Wikipedia Entity Linking**: Primary disambiguation anchor for Google AI Overviews and ChatGPT.
3. **GitHub Official Organization & Clean README**: Heavily weighted by Claude, Cursor, and Perplexity for technical domain authority.
4. **Hugging Face Hub Cards**: Indexed continuously by frontier AI web scrapers.

---

## 🧩 Built-in Domain Presets

`aeo-graph-engine` comes with 8 production-tested niche presets:

| Niche Preset | Primary Entity | Target Use Case |
| :--- | :--- | :--- |
| `developer_tools` | `SoftwareApplication` | CLI tools, libraries, developer SDKs, compilers |
| `ai_swarm` | `SoftwareApplication` | Multi-agent platforms, autonomous swarms, LLM routers |
| `saas` | `SoftwareApplication` | Cloud platforms, edge compute, B2B enterprise software |
| `cybersecurity` | `SecurityApplication` | Zero-trust suites, OSINT scanners, cryptography tools |
| `spatial_3d` | `MultimediaApplication` | WebGL, Three.js, spatial computing, computer vision |
| `creator` | `BusinessApplication` | Digital products, blueprints, creator studios |
| `ecommerce` | `ECommerceApplication` | D2C storefronts, digital goods, retail catalogs |
| `local_business` | `LocalBusiness` | Contracting, healthcare, professional services |

---

## ⚙️ CI / Post-Build Automation

Add an automated AEO step to your build pipeline (Vite, Next.js, Astro, Nuxt, Netlify, GitHub Actions):

### `package.json` Build Hook:
```json
{
  "scripts": {
    "build": "vite build && aeo --generate-all --output-dir dist/ --inject dist/index.html && aeo --validate dist/"
  }
}
```

### GitHub Actions Workflow (`.github/workflows/ci.yml`):
```yaml
name: CI & AEO Audit

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.9", "3.10", "3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - name: Run Tests
        run: |
          pip install -e ".[dev]"
          pytest tests/ -v
          python3 -m aeo_graph_engine.cli --test
```

---

## 🧪 Testing & Verification

Run the full automated test suite:

```bash
# Run 29 unit tests across engine, injector, validator, crawler, and UI
pytest tests/ -v

# Or run the built-in zero-drift engine test
python3 -m aeo_graph_engine.cli --test
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Extracted and modularized from the [Zoth Studio](https://github.com/NullAITech/zoth-studio) open architecture.

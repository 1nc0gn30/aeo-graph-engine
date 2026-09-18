<div align="center">

# AEO Graph Engine (`aeo-graph-engine`)

### *Autonomous Answer Engine Optimization (AEO/GEO), Live Site Crawler, Schema.org Linked Data `@graph`, `llms.txt` & AEO Studio UI Workbench*

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-00f0ff?style=for-the-badge&logo=pypi&logoColor=white)](https://github.com/1nc0gn30/aeo-graph-engine)
[![Tests](https://img.shields.io/badge/tests-229%2F229%20Passing%20(100%25)-34d399?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Platforms](https://img.shields.io/badge/platforms-Linux%20%7C%20Termux%20%7C%20macOS%20%7C%20Windows-38bdf8?style=for-the-badge&logo=linux&logoColor=white)](docs/PLATFORMS.md)
[![MCP Protocol](https://img.shields.io/badge/MCP-JSON--RPC%202.0-8b5cf6?style=for-the-badge&logo=anthropic&logoColor=white)](docs/MCP_GUIDE.md)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-fbbf24?style=for-the-badge&logo=python&logoColor=black)](pyproject.toml)
[![Zero-Dependencies](https://img.shields.io/badge/dependencies-Zero%20Runtime%20Deps-4ade80?style=for-the-badge&logo=checkmarx&logoColor=white)](src/aeo_graph_engine/)

<br>

<p align="center">
  <a href="#-aeo-studio-workbench">AEO Studio UI</a> •
  <a href="#-interactive-cli-wizard-aeo-init">CLI Wizard</a> •
  <a href="#-live-ai-search-bot-inspector--waf-probe">Bot WAF Probe</a> •
  <a href="#%EF%B8%8F-head-to-head-competitor-benchmark">Competitor Benchmark</a> •
  <a href="#-automated-audit-reports-markdown--html">Audit Reports</a> •
  <a href="#-cicd-quality-gate--github-actions">CI Quality Gate</a> •
  <a href="examples/">Examples</a> •
  <a href="#%EF%B8%8F-cli-reference">CLI Reference</a>
</p>

</div>

---

## 🌐 Overview

Traditional SEO was engineered for classic 10-blue-link search result pages. **Answer Engine Optimization (AEO)** and **Generative Engine Optimization (GEO)** optimize your website for direct conversational retrieval and factual synthesis by **ChatGPT Search, Perplexity AI, Claude, Google AI Overviews, Apple Intelligence, and Grok**.

**`aeo-graph-engine`** is a zero-runtime-dependency Python engine, live multi-page crawler, CLI, and **Interactive Web Workbench (design influenced by Material 3)** extracted and modularized from the **Zoth Studio** architecture. It audits live URLs, generates interconnected Schema.org `@graph` JSON-LD, compiles standard `llms.txt` manifests, and optimizes AI bot directives.

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

## 🎨 AEO Studio Workbench (Design Influenced by Material 3)

`aeo-graph-engine` includes a built-in interactive **Light Mode Web UI** (`AEO Studio`) with design influenced by Material 3: clean `#f8f9fa` canvas, elevation cards, live entity graph previews, and a real-time 0–100 AEO readiness meter.

### Launch the Local Studio:

```bash
# Launch interactive local studio (runs on http://127.0.0.1:8080 or specified port)
aeo serve --port 8080

# Or open public/index.html directly in any browser (100% offline static app)
open public/index.html
```

#### Studio Workbench Capabilities:
- 🌐 **Live Website Scanner & Multi-Page Crawler**: Enter any live URL (or localhost) to audit real sitemaps, robots.txt, subpages, and calculate live AEO scores.
- ⚡ **AI Keys & Local Ports Gateway**: Configure API keys for OpenAI, Claude, Groq, Perplexity or connect free local models (Ollama, LM Studio, vLLM) on custom ports.
- 🪄 **AI Prompt Synthesizer**: Type a 1-sentence prompt (e.g. *"DeFi lending on Solana called SolarYield"*) to auto-generate full Schema, `llms.txt`, and metadata.
- 🤖 **AI Agent & MCP Hub**: Direct copy-paste configs for Claude Desktop, Cursor, Cline, Zed, and agent system prompt templates.
- 📦 **Framework Exporter**: One-click production code for Next.js App Router, Astro, Vite + React, SvelteKit, Remix, Nuxt, and Hugo/Jekyll.
- 📊 **Real-time 0–100 AEO Readiness Meter**: Real weighted scores across 5 core dimensions (Schema, llms.txt, AI bots, content, technical SEO).
- 🕸️ **Visual Entity Graph & Schema Preview**: Live syntax-highlighted `@graph` JSON-LD generator with canonical `@id` linking.
- 📄 **`llms.txt` & `llms-full.txt` Compiler**: llmstxt.org-compliant machine index with structured markdown links.
- 🤖 **AI Bot Access Matrix**: Live compatibility breakdown for GPTBot, PerplexityBot, ClaudeBot, Applebot, and Google-Extended.
- 💉 **Live HTML Schema Injector**: Paste raw HTML to test idempotent script embedding.
- 🏛️ **AEO Backlink & Citation Playbook**: Actionable high-authority citation targets and niche distribution strategy.
- 📥 **One-Click `.zip` Export**: Download all generated files in a single clean archive.

---

## ⚡ AI Agent API Keys & Local Endpoints / Port Gateway

`AEO Studio` includes a built-in **AI Provider & Custom Port Management Gateway** accessible directly from the UI or via REST API:

- 🔑 **Cloud AI Provider API Keys**:
  - **OpenAI** (`OPENAI_API_KEY`): GPT-4o, GPT-4o-mini, o1, o3-mini
  - **Anthropic** (`ANTHROPIC_API_KEY`): Claude 3.7 Sonnet, Claude 3.5 Sonnet, Claude 3.5 Haiku
  - **Perplexity AI** (`PERPLEXITY_API_KEY`): Sonar Pro, Sonar Reasoning
  - **Groq** (`GROQ_API_KEY`): Llama-3.3 70B, DeepSeek R1 Distill (ultra low-latency)
  - **OpenRouter** (`OPENROUTER_API_KEY`): Access 200+ frontier models with one key
  - **DeepSeek** (`DEEPSEEK_API_KEY`): DeepSeek V3 & R1
- 🔌 **Local LLM Endpoints & Ports (100% Free & Private)**:
  - **Ollama**: Default `http://127.0.0.1:11434` (Port 11434)
  - **LM Studio**: Default `http://127.0.0.1:1234/v1` (Port 1234)
  - **vLLM / llama.cpp**: Default `http://127.0.0.1:8000/v1` (Port 8000)
  - **Hermes Agent / Zoth Memory Daemon**: Default `http://127.0.0.1:8788/v1` (Port 8788)
  - **AEO MCP Gateway Port**: Port 8091
- ⚡ **Live Endpoint Latency & Connection Tester**: Ping any endpoint with 1 click to verify available models and response times.
- 🔮 **Live Answer Engine Perception Simulator**: Query simulated ChatGPT Search & Perplexity engines to verify how AI answer engines perceive and cite your domain.

---

## 🤖 Model Context Protocol (MCP) Server & AI Agent Hub

`aeo-graph-engine` exposes a **zero-dependency JSON-RPC 2.0 Model Context Protocol (MCP)** server over stdio. Connect any AI coding agent (Claude Desktop, Cursor, Cline, Zed, Hermes, OpenCode, AutoGen, CrewAI) so they can autonomously crawl URLs, generate Schema `@graphs`, and optimize your codebase.

👉 **Full MCP Setup Guide & Documentation**: [`docs/MCP_GUIDE.md`](docs/MCP_GUIDE.md)  
👉 **Agent Workflow & Autonomous Optimization**: [`docs/AI_AGENT_INTEGRATION.md`](docs/AI_AGENT_INTEGRATION.md)

### Connect with Claude Desktop / Cursor in 30 Seconds:

Run the config generator to get your exact configuration block:
```bash
aeo mcp --config claude_desktop
# or
aeo mcp --config cursor
```

**Add to Claude Desktop (`claude_desktop_config.json`):**
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"]
    }
  }
}
```

### 6 Native MCP Tools Available to AI Agents:
1. `aeo_scan_site`: Live URL crawler, multi-page audit, 0-100 AEO score, bot permissions.
2. `aeo_synthesize_prompt`: Turn natural language descriptions into complete structured AEO configs.
3. `aeo_generate_bundle`: Generate `schema-graph.json`, `llms.txt`, `ai.txt`, and `robots.txt`.
4. `aeo_inject_html`: Embed Schema.org JSON-LD directly into HTML files.
5. `aeo_validate`: Diagnostic audit and 0-100 readiness verification.
6. `aeo_get_framework_snippets`: Retrieve tailored code for Next.js, Astro, Vite, SvelteKit, etc.

---

## 📦 Framework Code Exporters & Auto-Remediation

Generate framework-native TypeScript/JavaScript code for all major stacks:

```bash
# Export Next.js App Router integration code
aeo framework nextjs_app --output-dir ./my-next-app

# Or auto-generate concrete code fixes from a live website scan
aeo fix https://mysite.com --framework astro --output-dir ./src/
```

Supported frameworks:
- **Next.js (App Router)**: `app/layout.tsx` (with `<script type="application/ld+json">`), `app/robots.ts`, `app/sitemap.ts`, `app/llms.txt/route.ts`
- **Next.js (Pages Router)**: `pages/_document.tsx`
- **Astro**: `src/components/AeoHead.astro` and `astro.config.mjs`
- **Vite + React / SPA**: `index.html` injection and `vite-plugin-aeo.ts`
- **SvelteKit**: `src/routes/+layout.svelte` and `src/routes/robots.txt/+server.ts`
- **Remix**: `app/root.tsx` meta export
- **Nuxt 3**: `nuxt.config.ts` and `app.vue` `useHead()`
- **Static HTML / Hugo / Jekyll**: Clean HTML partials

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

## 🎯 Atomic Claim-Evidence Matrix & Scroll-to-Text Fragments

Modern generative search engines (Perplexity Sonar, OpenAI SearchGPT, Gemini) perform grounded citation by extracting atomic factual propositions and pinning them to direct quotation fragments.

```bash
# Analyze document or HTML file into an atomic claim-evidence matrix
aeo claims README.md

# Export as Schema.org Statement linked data JSON
aeo claims public/index.html --format json --output claims.json

# Export as standalone dark-mode SVG badge
aeo claims technical_spec.md --format svg --output claims_matrix.svg
```

#### Core Capabilities:
- 🔬 **Atomic Assertion Decomposition**: Parses complex paragraphs into discrete, independently verifiable propositions.
- 📐 **Linguistic Categorization**: Classifies claims into `Quantitative`, `Architectural`, `Comparative`, and `Capability` tiers.
- 📊 **Quotability Scoring ($Q_{\text{atomic}}$)**: Heuristic evaluation penalizing speculative hedging ("might", "could", "we believe") and rewarding metric density and optimal citation sentence length (12–25 words).
- 🔗 **W3C Scroll-to-Text Fragment Generation**: Automatically calculates `#:~:text=start,end` deep links and SHA-256 quote hashes (`quote_hash`) enabling pinpoint footnote citations.
- 🏛️ **Schema.org ClaimReview & Statement Graph**: Synthesizes structured JSON-LD allowing AI search crawlers to ingest atomic assertions directly.

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
           [--format {text,json,github}] [--jsonld] [--llms] [--llms-full] [--ai-txt] [--robots]
           [--inject INJECT] [--validate VALIDATE] [--platform] [--test] [--dry-run]
           {init,wizard,scan,bot-audit,compare,report,check,framework,fix,mcp,prompt,serve,ui,extract,platform} ...
```

### Commands & Subcommands

| Command / Subcommand | Description |
| :--- | :--- |
| `aeo init [dir]` / `aeo wizard` | **Interactive & Scriptable Setup Wizard**: auto-detects frontend framework, profiles repo, generates bundle & framework code |
| `aeo scan <url> [--max-pages 5]` | **Live Multi-Page Crawler**: audits sitemaps, robots.txt, schema, word counts, and scores site across 5 AEO dimensions |
| `aeo bot-audit <url> [--timeout 5]` | **AI Bot WAF Inspector**: probes target with authentic User-Agents for 10 AI crawlers to detect Cloudflare/AWS WAF blocks |
| `aeo compare <url_a> <url_b>` | **Head-to-Head Competitor Benchmark**: compares two sites side-by-side on AEO scores, entity depth, and citation advantages |
| `aeo report <url> [--format both]` | **Audit Report Exporter**: generates professional GitHub Markdown (`AEO_AUDIT_REPORT.md`) & standalone HTML audit reports |
| `aeo check [target] [--min-score 80]` | **CI/CD Quality Gate**: enforces minimum AEO score on PRs and builds with GitHub Action annotations |
| `aeo framework <name> [--output-dir]` | Export typed integration code for Next.js (App/Pages), Astro, Vite, SvelteKit, Remix, Nuxt, Hugo/Jekyll |
| `aeo fix <url> --framework <name>` | Automatically generate concrete code fixes and remediation plan for missing AEO assets |
| `aeo mcp [--tools] [--config <client>]` | Start stdio Model Context Protocol (MCP) server or generate JSON config for Claude/Cursor/Cline/Zed |
| `aeo prompt "<description>"` | Synthesize full AEO configuration and linked data from a natural language description |
| `aeo claims <target>` | **Atomic Claim-Evidence Matrix**: extracts verifiable claims, computes quotability score, and generates W3C citation text fragments |
| `aeo serve [--port 8080]` | Start interactive AEO Studio UI Workbench (design influenced by Material 3) |
| `aeo platform` | Inspect multi-platform environment details (Linux, Termux Android, macOS, Windows) |
| `aeo extract <file>` | Extract metadata from an existing HTML file into JSON |
| `--generate-all` | Generate complete AEO bundle (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) |
| `--validate <path>` | Audit bundle or schema and compute 0–100 AEO Readiness Score |
| `--inject <file>` | Inject or update Schema.org JSON-LD in target HTML document |
| `--test` | Run built-in unit test suite (229 tests) with zero-drift verification |

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

## 📂 Real-World Reference Examples

Explore production-ready starter implementations in the [`examples/`](examples/) directory:

- ⚛️ **[`examples/nextjs-app-router/`](examples/nextjs-app-router/)**: Complete Next.js 14/15 App Router project with `layout.tsx` Schema.org injection, dynamic `app/robots.ts`, `app/sitemap.ts`, and `app/llms.txt/route.ts`.
- 🚀 **[`examples/astro-site/`](examples/astro-site/)**: Astro 4/5 integration with reusable `<AeoHead />` component, robots.txt, and llms.txt.
- ⚡ **[`examples/vite-react-spa/`](examples/vite-react-spa/)**: Vite React single-page app with custom `vite-plugin-aeo` that automatically emits machine manifests during `vite build`.
- ☁️ **[`examples/saas-landing/`](examples/saas-landing/)**: Production B2B SaaS configuration preset for multi-agent cloud orchestration.
- 🤖 **[`examples/mcp-clients/`](examples/mcp-clients/)**: Pre-built MCP integration configs for Claude Desktop, Cursor IDE, Cline, and Zed editor.

See the complete guide in [`examples/README.md`](examples/README.md).

---

## 🚦 CI/CD Quality Gate & GitHub Actions

Enforce minimum AEO Readiness scores on pull requests and deployments to prevent SEO/AEO regressions:

```bash
# Check local bundle or live URL (fails with exit code 1 if score < 85 or llms.txt missing)
aeo check . --min-score 85 --fail-on-missing-llms

# Output GitHub Actions formatted annotations (::error::, ::warning::)
aeo check https://mysite.com --format github
```

### Add to `.github/workflows/aeo-audit.yml`:

```yaml
name: AEO Quality Gate

on: [push, pull_request]

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install & Audit AEO
        run: |
          pip install -e .
          python3 -m aeo_graph_engine.cli check . --min-score 80 --fail-on-missing-llms --format github
```

---

## 🧪 Testing & Multi-Platform Verification

Run the full automated test suite:

```bash
# Run 168 unit tests across engine, crawler, WAF probe, benchmark, reporter, wizard, MCP server, framework exporter, and compat
pytest tests/ -v

# Or run the built-in zero-drift engine test
aeo --test

# Verify your current platform compatibility & environment info
aeo platform
```

---

## 🚀 Automated Release Pipeline

Every push to the `main` branch or tag creation (`v*`) triggers the automated release pipeline in `.github/workflows/release.yml`:
1. Runs full test matrix verification across Linux, macOS, and Windows across Python 3.9–3.13.
2. Builds distribution wheel (`.whl`) and source archive (`.tar.gz`).
3. Computes cryptographic SHA-256 checksums (`dist/SHA256SUMS.txt`).
4. Generates changelog and creates a published GitHub Release with attached assets.

---

## 📄 License

Licensed under the [MIT License](LICENSE). Extracted and modularized from the [Zoth Studio](https://github.com/NullAITech/zoth-studio) open architecture.



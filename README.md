<div align="center">

# <img src="https://raw.githubusercontent.com/1nc0gn30/aeo-graph-engine/main/public/assets/google-aeo-icon.svg" width="36" height="36" onerror="this.style.display='none'" style="vertical-align: middle;" /> AEO Graph Engine (`aeo-graph-engine`)

### *Autonomous Answer Engine Optimization (AEO/GEO), Schema.org Linked Data `@graph`, `llms.txt` & Google-Grade UI Workbench*

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-00f0ff?style=for-the-badge&logo=pypi&logoColor=white)](https://github.com/1nc0gn30/aeo-graph-engine)
[![Tests](https://img.shields.io/badge/tests-25%2F25%20Passing%20(100%25)-34d399?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-fbbf24?style=for-the-badge&logo=python&logoColor=black)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-a855f7?style=for-the-badge&logo=open-source-initiative&logoColor=white)](LICENSE)
[![Zero-Dependencies](https://img.shields.io/badge/dependencies-Zero%20Runtime%20Deps-4ade80?style=for-the-badge&logo=checkmarx&logoColor=white)](src/aeo_graph_engine/)

<br>

<p align="center">
  <a href="#-google-designed-aeo-studio-workbench">Google AEO Studio UI</a> •
  <a href="#-quick-start">Quick Start</a> •
  <a href="#-why-aeo--geo-matters-in-2026">Why AEO Matters</a> •
  <a href="#%EF%B8%8F-cli-reference">CLI Reference</a> •
  <a href="#-python-library-api">Python API</a> •
  <a href="#-built-in-domain-presets">Domain Presets</a> •
  <a href="#-ci--post-build-automation">CI/CD Automation</a>
</p>

</div>

---

## 🌐 Overview

Traditional SEO was engineered for classic 10-blue-link search result pages. **Answer Engine Optimization (AEO)** and **Generative Engine Optimization (GEO)** optimize your website for direct conversational retrieval by **ChatGPT Search, Perplexity AI, Claude, Google AI Overviews, Apple Intelligence, and Grok**.

**`aeo-graph-engine`** is a standalone, zero-runtime-dependency Python engine, CLI, and **Google-styled Light Mode Web Workbench** extracted and modularized from the **Zoth Studio** architecture. It automatically builds, validates, scores, and injects complete semantic machine discovery layers into any website or application.

```
                  ┌──────────────────────────────────────────────────────────┐
                  │                 YOUR APPLICATION / SITE                 │
                  └────────────────────────────┬─────────────────────────────┘
                                               │
                                      aeo --generate-all
                                               │
               ┌───────────────────────────────┼───────────────────────────────┐
               ▼                               ▼                               ▼
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

`aeo-graph-engine` includes a built-in interactive **Google Light Mode Web UI** (`AEO Studio`) designed with Google Material 3 aesthetics: clean `#f8f9fa` canvas, Google brand colors (`#4285f4`, `#ea4335`, `#fbbc04`, `#34a853`), elevation cards, live entity graph cards, and a real-time 0–100 AEO readiness meter.

### Launch the Local Studio:

```bash
# Launch interactive local studio (runs on http://127.0.0.1:8080)
aeo serve --port 8080

# Or open public/index.html directly in any browser (100% offline static app)
open public/index.html
```

#### Studio Capabilities:
- 📊 **Real-time 0–100 AEO Readiness Meter**: Instant feedback as you adjust content and metadata.
- 🕸️ **Visual Entity Graph & Schema Preview**: Live syntax-highlighted `@graph` JSON-LD generator.
- 📄 **`llms.txt` & `llms-full.txt` Compiler**: Markdown rendering + copy/export.
- 🤖 **AI Bot Crawler Matrix**: Visual status indicators for leading AI crawlers.
- 💉 **Live HTML Schema Injector**: Paste or drop HTML to test automated script embedding.
- 📥 **One-Click `.zip` Export**: Download all generated files in a single archive.

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

### 2. Generate an AEO Bundle

```bash
# Generate all 5 machine discovery files into your build/dist directory
aeo --generate-all --output-dir dist/ --site-name "Apex Platform" --domain "apex.dev" --niche saas
```

**Output:**
```
✨ AEO Bundle successfully generated in: /path/to/dist
  📄 schema-graph.json    -> /path/to/dist/schema-graph.json
  📄 llms.txt             -> /path/to/dist/llms.txt
  📄 llms-full.txt        -> /path/to/dist/llms-full.txt
  📄 ai.txt               -> /path/to/dist/ai.txt
  📄 robots.txt           -> /path/to/dist/robots.txt

📊 AEO Readiness Score: 100.0/100 (EXCELLENT)
```

### 3. Inject Schema into HTML

```bash
# Idempotently embed or update Schema.org JSON-LD in your index.html
aeo --inject dist/index.html --niche developer_tools
```

### 4. Audit & Validate

```bash
# Audit any directory or single file with full diagnostics
aeo --validate dist/
```

### 5. Extract Metadata from Existing HTML

```bash
# Automatically extract titles, OpenGraph tags, and existing schemas
aeo extract dist/index.html
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
           {serve,ui,extract} ...
```

### Commands & Subcommands

| Command / Flag | Description |
| :--- | :--- |
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
    generate_schema_graph,
    generate_llms_txt,
    generate_robots_txt,
    write_aeo_bundle,
    validate_aeo_bundle,
    extract_metadata_from_html
)

# 1. Custom configuration dictionary
config = {
    "site_name": "HyperScale AI",
    "domain": "hyperscale.ai",
    "tagline": "Next-Gen Autonomous Workflow & Model Mesh",
    "description": "Enterprise multi-agent routing with AST verification.",
    "features": [
        "Sub-10ms Global Edge Routing Mesh",
        "Multi-Model Consensus Arbitration",
        "Zero-Trust Encrypted BYOK Vault"
    ],
    "faqs": [
        {
            "question": "What is HyperScale AI?",
            "answer": "HyperScale AI is a high-throughput AI agent routing mesh."
        }
    ]
}

# 2. Generate Schema.org JSON-LD Graph dictionary
graph = generate_schema_graph(config, niche="saas")

# 3. Write complete bundle and inject into built HTML files
artifacts = write_aeo_bundle(
    output_dir="./dist",
    config=config,
    niche="saas",
    inject_html_files=["./dist/index.html"]
)

# 4. Validate AEO Readiness Score (0-100)
report = validate_aeo_bundle("./dist")
print(f"Readiness Score: {report.score}/100 - Status: {report.to_dict()['status']}")
```

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
# Run 25 unit tests
pytest tests/ -v

# Or run the built-in zero-drift engine test
python3 -m aeo_graph_engine.cli --test
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Extracted and modularized from the [Zoth Studio](https://github.com/NullAITech/zoth-studio) open architecture.

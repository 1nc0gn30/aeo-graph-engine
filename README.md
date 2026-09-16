# ⚡ AEO Graph Engine (`aeo-graph-engine`)

> **Autonomous Answer Engine Optimization (AEO/GEO), Schema.org Linked Data `@graph`, `llms.txt` & AI Search Discovery Engine**

[![PyPI Version](https://img.shields.io/badge/pypi-v1.0.0-00f0ff?style=for-the-badge&logo=pypi&logoColor=white)](https://github.com/1nc0gn30/aeo-graph-engine)
[![Tests](https://img.shields.io/badge/tests-Passing%20100%25-34d399?style=for-the-badge&logo=pytest&logoColor=white)](tests/)
[![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-fbbf24?style=for-the-badge&logo=python&logoColor=black)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-a855f7?style=for-the-badge&logo=open-source-initiative&logoColor=white)](LICENSE)
[![Zero-Dependencies](https://img.shields.io/badge/dependencies-Zero%20Runtime%20Deps-4ade80?style=for-the-badge&logo=checkmarx&logoColor=white)](src/aeo_graph_engine/)

---

## 🌐 Overview

Traditional SEO targets keyword matching on classic search engine results pages. **Answer Engine Optimization (AEO)** and **Generative Engine Optimization (GEO)** optimize your digital presence for generative AI answer engines—including **ChatGPT Search, Perplexity AI, Claude, Google AI Overviews, Apple Intelligence, and Grok**.

**`aeo-graph-engine`** is a standalone, zero-runtime-dependency Python CLI and library extracted from the **Zoth Studio** architecture. It automatically builds, validates, and injects complete semantic machine discovery layers:

1. **Schema.org Connected Knowledge Graph (`schema-graph.json`)**: Deep `@graph` linking `Organization`, `WebSite`, `SoftwareApplication` / `LocalBusiness`, `FAQPage`, `BreadcrumbList`, and `ItemList`.
2. **`llms.txt`**: Standardized concise AI index per the [llmstxt.org](https://llmstxt.org) standard.
3. **`llms-full.txt`**: Complete deep-research knowledge base designed for RAG ingestion and LLM citations.
4. **`ai.txt`**: Machine discovery manifest specifying canonical endpoints, bot policies, and citation formats.
5. **AI Crawler `robots.txt`**: Explicit crawler access rules optimized for `GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot-Extended`, and `Google-Extended`.
6. **HTML Injection Harness**: Idempotent `<script type="application/ld+json">` injection into target HTML files.
7. **AEO Readiness Linter & Scorer**: Automated 0–100 audit score with actionable diagnostic reports.

---

## 🚀 Installation & Quick Start

### 1. Install via pip / pipx

```bash
# Clone and install in editable mode
git clone https://github.com/1nc0gn30/aeo-graph-engine.git
cd aeo-graph-engine
pip install -e .
```

*Zero external runtime dependencies required—runs directly on standard Python 3.9+.*

### 2. Generate a Complete AEO Bundle

```bash
# Generate all AEO artifacts into your build or public directory
aeo --generate-all --output-dir dist/ --site-name "My SaaS App" --domain "mysaas.com" --niche saas
```

Output:
```
✨ AEO Bundle successfully generated in: /path/to/dist
  📄 schema-graph.json    -> /path/to/dist/schema-graph.json
  📄 llms.txt             -> /path/to/dist/llms.txt
  📄 llms-full.txt        -> /path/to/dist/llms-full.txt
  📄 ai.txt               -> /path/to/dist/ai.txt
  📄 robots.txt           -> /path/to/dist/robots.txt

📊 AEO Readiness Score: 100.0/100 (EXCELLENT)
```

### 3. Inject Schema directly into HTML files

```bash
# Idempotently inject or update JSON-LD in your HTML file
aeo --inject dist/index.html --niche developer_tools
```

### 4. Audit & Validate Existing Sites

```bash
# Run AEO readiness diagnostics on any directory or file
aeo --validate dist/
```

---

## 🛠️ CLI Reference

```bash
usage: aeo [-h] [--generate-all] [--output-dir OUTPUT_DIR]
           [--niche {developer_tools,ai_swarm,saas,cybersecurity,spatial_3d,creator,ecommerce,local_business}]
           [--config CONFIG] [--site-name SITE_NAME] [--domain DOMAIN] [--version VERSION]
           [--jsonld] [--llms] [--llms-full] [--ai-txt] [--robots]
           [--inject INJECT] [--validate VALIDATE] [--test] [--dry-run]
```

| Option | Description |
| :--- | :--- |
| `--generate-all` | Generate all AEO artifacts (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) |
| `--output-dir <dir>` | Directory to write generated assets (default: `dist`) |
| `--niche <preset>` | Select domain preset (`saas`, `ai_swarm`, `developer_tools`, `cybersecurity`, `spatial_3d`, `creator`, `ecommerce`, `local_business`) |
| `--config <path>` | Path to a custom JSON configuration file |
| `--site-name <name>` | Override site / brand name |
| `--domain <domain>` | Override domain name (e.g. `example.com`) |
| `--inject <file>` | Inject or update Schema.org JSON-LD in target HTML document |
| `--validate <path>` | Audit and compute 0–100 AEO Readiness Score for a directory or file |
| `--test` | Run built-in unit tests and zero-drift verification suite |
| `--dry-run` | Preview actions without modifying disk |

---

## 🐍 Python Library API

You can import `aeo_graph_engine` directly into your Python scripts, CI/CD runners, FastAPI backends, or static site generators:

```python
from aeo_graph_engine import (
    generate_schema_graph,
    generate_llms_txt,
    generate_robots_txt,
    write_aeo_bundle,
    validate_aeo_bundle,
    inject_jsonld_into_html
)

# 1. Custom configuration dictionary
config = {
    "site_name": "HyperScale AI",
    "domain": "hyperscale.ai",
    "tagline": "Next-Gen Autonomous Multi-Agent Mesh",
    "description": "Enterprise multi-agent inference routing with AST verification.",
    "features": [
        "Sub-10ms Global Edge Routing Mesh",
        "Multi-Model Consensus Arbitration",
        "Zero-Trust BYOK Encryption"
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

# 3. Generate standardized llms.txt string
llms_content = generate_llms_txt(config, niche="saas")

# 4. Write complete AEO bundle and inject into built HTML files
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

## 🏗️ Generated Artifacts Anatomy

### 1. `schema-graph.json`
Connected Schema.org JSON-LD `@graph` defining the entity network:
- **`Organization`**: Founding team, publisher authority, logo, contact points, `sameAs` social links, and `knowsAbout` topics.
- **`WebSite`**: Canonical URL, alternate names, and `potentialAction` `SearchAction`.
- **`SoftwareApplication` / `LocalBusiness`**: Category, OS compatibility, license, pricing, feature list, and aggregate ratings.
- **`FAQPage`**: Q&A pairs specifically formatted for AI answer engines to surface during conversational search queries.
- **`BreadcrumbList` & `ItemList`**: Structured surface navigation and capability lists.

### 2. `llms.txt`
Standardized machine-readable markdown file per the `llmstxt.org` specification. Contains:
- `# Project Name`
- `> Concise blockquote summary`
- Architecture & key capabilities
- Structured links `[Section Name](URL): Description` for LLM citation

### 3. `llms-full.txt`
Complete, in-depth text documentation including comprehensive technical overviews, surface maps, FAQ repositories, and citation policy rules.

### 4. `ai.txt`
Explicit machine discovery manifest declaring canonical entity identifiers, machine policy terms, and derivative work permissions.

### 5. `robots.txt`
Crawler directives designed specifically to grant access to modern AI engines (`GPTBot`, `ChatGPT-User`, `PerplexityBot`, `ClaudeBot`, `anthropic-ai`, `Applebot-Extended`, `Google-Extended`, `cohere-ai`, `Meta-ExternalAgent`) while securing internal directories.

---

## 🧩 Built-in Domain Presets

`aeo-graph-engine` comes with 8 production-tested niche presets:

| Niche Preset | Primary Entity | Target Audience |
| :--- | :--- | :--- |
| `developer_tools` | `SoftwareApplication` | CLI tools, libraries, developer SDKs, engines |
| `ai_swarm` | `SoftwareApplication` | Multi-agent platforms, autonomous swarms, LLM orchestration |
| `saas` | `SoftwareApplication` | Cloud platforms, edge compute, enterprise apps |
| `cybersecurity` | `SecurityApplication` | Zero-trust tools, OSINT scanners, cryptography suites |
| `spatial_3d` | `MultimediaApplication` | WebGL, Three.js, spatial computing, computer vision |
| `creator` | `BusinessApplication` | Digital products, blueprints, creator studios |
| `ecommerce` | `ECommerceApplication` | D2C storefronts, digital goods, retail catalogs |
| `local_business` | `LocalBusiness` | Local service providers, contracting, professional firms |

---

## 🧪 Testing & Verification

Run the full automated test suite with pytest:

```bash
# Run unit tests
pytest tests/ -v

# Or run the built-in zero-drift engine test
python3 -m aeo_graph_engine.cli --test
```

---

## 📄 License

Licensed under the [MIT License](LICENSE). Extracted and modularized from the [Zoth Studio](https://github.com/NullAITech/zoth-studio) architecture.

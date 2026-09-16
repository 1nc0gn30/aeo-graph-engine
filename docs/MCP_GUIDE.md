# 🔌 Model Context Protocol (MCP) Guide for AEO Graph Engine

> **Connect Any AI Coding Agent (Claude Desktop, Cursor, Cline, Zed, ChatGPT, Hermes, OpenCode, AutoGen, CrewAI, LangChain) to Automatically Optimize AEO During Development**

---

## 🎯 Executive Overview

The **Model Context Protocol (MCP)** is an open standard created by Anthropic that enables Large Language Models (LLMs) and AI coding agents to securely access external tools, local filesystems, and specialized engines.

By connecting your AI agent to **`aeo-graph-engine`** via MCP, your agent gains the autonomous ability to:
1. **Audit live websites and local build artifacts** against modern Answer Engine Optimization (AEO/GEO) standards.
2. **Synthesize interconnected Schema.org `@graph` JSON-LD**, `llms.txt`, `llms-full.txt`, `ai.txt`, and `robots.txt` manifests directly from conversational prompts.
3. **Idempotently inject and update structured metadata** in HTML files without touching existing layouts.
4. **Generate framework-specific integration code** for Next.js (App & Pages Router), Astro, Vite, Remix, Nuxt 3, and SvelteKit.
5. **Enforce a 0–100 AEO Readiness Score** in your local development loop before deploying to production.

```
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │                               AI AGENT CLIENT                                  │
 │   (Claude Desktop, Cursor, Cline, Zed, Hermes, OpenCode, AutoGen, CrewAI)     │
 └───────────────────────────────────────┬────────────────────────────────────────┘
                                         │ JSON-RPC 2.0 (stdio or HTTP/SSE)
                                         ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │                      AEO GRAPH ENGINE — MCP SERVER                             │
 │                                                                                │
 │   ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐   │
 │   │     aeo_scan_site     │  │ aeo_synthesize_prompt │  │   aeo_generate   │   │
 │   │ (Live Crawler & Score)│  │ (NLP Config Generator)│  │ (Bundle Creator) │   │
 │   └───────────────────────┘  └───────────────────────┘  └──────────────────┘   │
 │   ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐   │
 │   │    aeo_inject_html    │  │     aeo_validate      │  │  aeo_framework   │   │
 │   │ (HTML @graph Embedder)│  │ (Diagnostic Scorer)   │  │(Snippet Generator│   │
 │   └───────────────────────┘  └───────────────────────┘  └──────────────────┘   │
 └───────────────────────────────────────┬────────────────────────────────────────┘
                                         │
                                         ▼
 ┌────────────────────────────────────────────────────────────────────────────────┐
 │                       LOCAL WORKSPACE & TARGET WEB APP                         │
 │  dist/schema-graph.json • dist/llms.txt • dist/ai.txt • dist/index.html        │
 └────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Available MCP Tools

When `aeo-graph-engine` is registered as an MCP server, it exposes **6 primary tools** to connected AI agents:

| Tool Name | Purpose | Key Inputs | Output |
| :--- | :--- | :--- | :--- |
| `aeo_scan_site` | Crawls a live URL or localhost, audits sitemaps, robots.txt, schema graph, and bot access | `url` (str), `max_pages` (int), `timeout` (int) | Overall score (0–100), category breakdown, bot compatibility matrix, prioritized action items, and backlink targets. |
| `aeo_synthesize_prompt` | Converts a natural language app description into a complete AEO configuration dictionary | `prompt` (str), `base_niche` (str) | Full configuration JSON with entity mappings, features, surfaces, and auto-generated FAQs. |
| `aeo_generate_bundle` | Generates all 5 canonical AEO files (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) | `output_dir` (str), `config` (object), `niche` (str), `inject_html_files` (array) | File map of generated artifacts and status. |
| `aeo_inject_html` | Embeds or updates connected Schema.org JSON-LD in target HTML file(s) or string | `html_file_path` (str) or `html_content` (str), `schema_payload` (object), `config` (object), `niche` (str) | Confirmation of idempotent injection and tag position. |
| `aeo_validate` | Runs a diagnostic audit on a target build folder, single artifact, or in-memory payload | `target_path` (str), `schema_data` (object), `content` (str) | Score (0–100), status (`EXCELLENT`, `GOOD`, `NEEDS_ATTENTION`), passed checks, warnings, and errors. |
| `aeo_get_framework_snippets` | Generates copy-paste integration snippets for Next.js, Astro, Vite, Remix, Nuxt, SvelteKit, or HTML | `framework` (str), `schema_graph` (object), `niche` (str) | Framework-specific layout and configuration code with embedded schema graph. |

---

## 💻 Client Setup & Copy-Paste Configurations

You can generate exact configuration snippets for any client directly from the CLI:

```bash
# Generate config for Claude Desktop
python3 -m aeo_graph_engine.mcp_server --config claude_desktop

# Generate config for Cursor
python3 -m aeo_graph_engine.mcp_server --config cursor

# Generate config for Cline
python3 -m aeo_graph_engine.mcp_server --config cline

# Generate config for Zed
python3 -m aeo_graph_engine.mcp_server --config zed
```

---

### 1. Claude Desktop

To use `aeo-graph-engine` inside Anthropic's **Claude Desktop** app:

#### Configuration File Location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

#### Configuration (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": [
        "-m",
        "aeo_graph_engine.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "/path/to/aeo-graph-engine/src"
      }
    }
  }
}
```

---

### 2. Cursor

Cursor supports MCP servers natively. You can add it per-project or globally.

#### Project-level Configuration (`.cursor/mcp.json`):
Create `.cursor/mcp.json` in your repository root:

```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": [
        "-m",
        "aeo_graph_engine.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "${workspaceFolder}/src"
      }
    }
  }
}
```

#### In Cursor Settings:
1. Open **Cursor Settings** -> **Features** -> **MCP Servers**.
2. Click **+ Add New MCP Server**.
3. Name: `aeo-graph-engine`
4. Type: `command`
5. Command: `python3 -m aeo_graph_engine.mcp_server`

---

### 3. Cline (VS Code Extension)

**Cline** allows autonomous coding agents in VS Code to call MCP tools.

#### Configuration (`cline_mcp_settings.json`):
Open Cline -> Click the **MCP Servers** (plug) icon -> Click **Configure MCP Servers**:

```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": [
        "-m",
        "aeo_graph_engine.mcp_server"
      ],
      "env": {
        "PYTHONPATH": "/absolute/path/to/aeo-graph-engine/src"
      },
      "disabled": false,
      "autoApprove": [
        "aeo_scan_site",
        "aeo_synthesize_prompt",
        "aeo_generate_bundle",
        "aeo_inject_html",
        "aeo_validate",
        "aeo_get_framework_snippets"
      ]
    }
  }
}
```

---

### 4. Zed Editor

**Zed** natively integrates with Model Context Protocol servers in `settings.json`.

#### Configuration (`~/.config/zed/settings.json` or `.zed/settings.json`):
```json
{
  "context_servers": {
    "aeo-graph-engine": {
      "command": {
        "path": "python3",
        "args": [
          "-m",
          "aeo_graph_engine.mcp_server"
        ],
        "env": {
          "PYTHONPATH": "/path/to/aeo-graph-engine/src"
        }
      }
    }
  }
}
```

---

### 5. Hermes Agent & OpenCode

For autonomous terminal agents like **Hermes Agent** or **OpenCode**:

#### Hermes Configuration (`~/.hermes/config.yaml`):
```yaml
mcp_servers:
  aeo-graph-engine:
    command: "python3"
    args:
      - "-m"
      - "aeo_graph_engine.mcp_server"
    env:
      PYTHONPATH: "/path/to/aeo-graph-engine/src"
```

#### OpenCode Configuration (`opencode.json`):
```json
{
  "mcp": {
    "servers": {
      "aeo": {
        "command": "python3 -m aeo_graph_engine.mcp_server"
      }
    }
  }
}
```

---

### 6. ChatGPT Custom GPTs / OpenAI Actions

If you want a **Custom GPT** or OpenAI assistant to interact with `aeo-graph-engine`, start the built-in HTTP server:

```bash
# Start local/remote server
aeo serve --host 0.0.0.0 --port 8080
```

#### OpenAPI Schema for Custom GPT Actions:
```yaml
openapi: 3.0.1
info:
  title: AEO Graph Engine API
  description: Autonomous Answer Engine Optimization, Live Site Scanner & Schema Graph Engine
  version: 1.0.0
servers:
  - url: https://your-server-domain.com
paths:
  /api/scan:
    post:
      summary: Scan and audit a live website for AEO readiness
      operationId: scanWebsite
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [url]
              properties:
                url:
                  type: string
                  example: "https://example.com"
                max_pages:
                  type: integer
                  default: 5
      responses:
        '200':
          description: Live audit report with 0-100 score and bot matrix
  /api/agent/synthesize:
    post:
      summary: Synthesize AEO configuration from prompt
      operationId: synthesizeConfig
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [prompt]
              properties:
                prompt:
                  type: string
                niche:
                  type: string
      responses:
        '200':
          description: Synthesized AEO configuration
  /api/generate:
    post:
      summary: Generate Schema Graph, llms.txt, ai.txt, and robots.txt
      operationId: generateBundle
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
      responses:
        '200':
          description: Complete AEO bundle payload
```

---

### 7. Python Multi-Agent Frameworks (AutoGen, CrewAI, LangChain)

You can import and register `aeo-graph-engine` tools directly in Python multi-agent orchestration frameworks.

#### LangChain Custom Tools Example:
```python
from langchain.tools import tool
from aeo_graph_engine import (
    LiveAEOScanner,
    synthesize_config_from_prompt,
    write_aeo_bundle,
    validate_aeo_bundle,
    discover_project_metadata
)

@tool
def audit_website_aeo(url: str, max_pages: int = 5) -> dict:
    """Crawl a live URL and compute real AEO scores, missing machine manifests, and bot access."""
    scanner = LiveAEOScanner(url, max_pages=max_pages)
    return scanner.compute_audit_scores()

@tool
def generate_aeo_assets(prompt: str, output_dir: str = "dist", html_file: str = "dist/index.html") -> dict:
    """Synthesize configuration and generate schema-graph.json, llms.txt, robots.txt, and inject into HTML."""
    cfg = synthesize_config_from_prompt(prompt)
    inject_list = [html_file] if html_file else []
    created = write_aeo_bundle(output_dir, config=cfg, inject_html_files=inject_list)
    report = validate_aeo_bundle(output_dir)
    return {
        "created_files": created,
        "aeo_score": report.score,
        "status": report.to_dict()["status"]
    }
```

#### CrewAI Custom Tool Example:
```python
from crewai.tools import BaseTool
from aeo_graph_engine import LiveAEOScanner

class LiveAEOScannerTool(BaseTool):
    name: str = "Live AEO & AI Readiness Scanner"
    description: str = "Crawls any website to audit Schema.org, llms.txt, AI bot access, and returns a 0-100 AEO score."

    def _run(self, url: str) -> str:
        scanner = LiveAEOScanner(url, max_pages=5)
        report = scanner.compute_audit_scores()
        return f"AEO Score: {report['overall_aeo_score']}/100. Action items: {len(report['action_items'])}"
```

---

## ⚡ The Live In-Session Coding Experience

Here is how an AI coding assistant interacts with `aeo-graph-engine` during a real development session:

### Scenario: Building a New Landing Page
1. **User Request**:
   > *"Cursor, I just finished the build of our Solana Yield aggregator in `dist/`. Can you make sure it gets 100/100 on AEO so Perplexity and ChatGPT quote us accurately?"*

2. **Agent Autonomous Tool Execution**:
   - Agent invokes `aeo_synthesize_prompt(prompt="High-performance Solana DeFi lending protocol called SolarYield on solaryield.fi", base_niche="saas")`.
   - Agent invokes `aeo_generate_bundle(output_dir="dist", config=synthesized_cfg)`.
   - Agent invokes `aeo_inject_html(html_file_path="dist/index.html", config=synthesized_cfg)`.
   - Agent invokes `aeo_validate(target_path="dist")`.

3. **Agent Response to User**:
   > *"I have generated and verified the full AEO layer for SolarYield in `dist/`.*
   > - *Created `dist/schema-graph.json` with connected `@graph` (Organization, WebSite, SoftwareApplication, FAQPage).*
   > - *Generated `dist/llms.txt` and `dist/llms-full.txt` compliant with llmstxt.org.*
   > - *Generated `dist/ai.txt` and updated `dist/robots.txt` granting explicit crawler access to GPTBot, PerplexityBot, ClaudeBot, and Applebot.*
   > - *Injected Schema.org JSON-LD into `dist/index.html`.*
   > - *AEO Audit Score: **100.0 / 100 [EXCELLENT]** (0 warnings, 0 errors). Ready to ship!"*

---

## 🔍 Verification & Troubleshooting

### Test the MCP Server via Stdio
You can verify that the MCP server responds correctly to JSON-RPC 2.0 messages via bash:

```bash
# Test initialization handshake
echo '{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test-client", "version": "1.0.0"}}}' | python3 -m aeo_graph_engine.mcp_server
```

Expected JSON response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {
        "listChanged": false
      },
      "logging": {}
    },
    "serverInfo": {
      "name": "aeo-graph-engine-mcp",
      "version": "1.0.0"
    }
  }
}
```

### Common Issues & Fixes:

1. **`ModuleNotFoundError: No module named 'aeo_graph_engine'`**:
   - Ensure you specify the `PYTHONPATH` environment variable in your client config, or run `pip install -e .` in your virtual environment.
2. **File Permissions / Path Issues in Claude Desktop**:
   - Always use absolute paths (e.g., `/Users/username/repos/aeo-graph-engine/src`) in `claude_desktop_config.json`.
3. **HTML Injection in Custom Template Frameworks**:
   - `aeo_inject_html` looks for `</head>` or `<script type="application/ld+json">`. If building with Astro or Next.js, use `aeo_get_framework_snippets` to get native framework layout templates.

---

## 📚 Related Documentation

- [AI Agent Integration & Autonomous Execution Guide](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/AI_AGENT_INTEGRATION.md)
- [AEO & GEO Mastery Playbook](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/AEO_GEO_PLAYBOOK.md)
- [System Architecture & Schema Graph Linking](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/ARCHITECTURE.md)

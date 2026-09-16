# 🤖 AI Agent Integration & Autonomous Execution Guide

> **Architectural Blueprint for AI Coding Agents, Multi-Agent Swarms, and Autonomous Runners to Discover, Configure, Operate, and Verify Answer Engine Optimization (AEO/GEO)**

---

## 🎯 Executive Overview & Agent-Native Architecture

`aeo-graph-engine` was engineered from the ground up to be **100% AI-agent native**. Modern AI coding assistants (such as Antigravity, Claude Code, Cursor, Cline, Zed, Hermes Agent, AutoGPT, and OpenCode) are no longer just passive code generators—they autonomously create routes, build static landing pages, compile frontend bundles, and deploy production software.

However, traditional web builds frequently suffer from:
- **Fragmented or Missing Schema.org Data**: Search engines and LLMs cannot verify publisher authority or entity relationships.
- **Zero Standard Machine Discovery**: Missing `llms.txt` and `llms-full.txt` force LLMs to waste search context tokens scraping messy DOM trees.
- **Accidental Crawler Blocking**: Default `robots.txt` configurations often block AI answer crawlers like `GPTBot`, `PerplexityBot`, and `ClaudeBot`.
- **Hallucinated Brand Information**: Without structured FAQPage schemas, LLM search engines synthesize unverified answers.

`aeo-graph-engine` solves these challenges by providing AI agents with **deterministic, zero-dependency tools** to audit, synthesize, inject, and self-verify complete AEO/GEO infrastructures in real time.

```
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                   AI CODING AGENT                                      │
 │            (Claude Code, Cursor, Cline, Zed, Antigravity, Hermes, AutoGen)             │
 └───────────┬───────────────────────────┬───────────────────────────────┬────────────────┘
             │                           │                               │
             ▼                           ▼                               ▼
  [1] Natural Language Prompt     [2] Tool Calling / MCP          [3] Programmatic Python
      Synthesis Engine               JSON-RPC 2.0 Protocol             Library API
  `aeo prompt "..."`              `tools/call: aeo_generate`      `write_aeo_bundle()`
             │                           │                               │
             └───────────────────────────┼───────────────────────────────┘
                                         │
                                         ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                                AEO GRAPH ENGINE CORE                                   │
 │  • Rule-Based Heuristic NLP Synthesizer      • Relational @graph Schema Builder        │
 │  • Zero-Drift Regex HTML Injector            • 0-100 Diagnostic Audit Scorer           │
 │  • llmstxt.org Manifest Compiler             • Multi-Page Live Website Crawler         │
 └───────────────────────────────────────┬────────────────────────────────────────────────┘
                                         │
                                         ▼
 ┌────────────────────────────────────────────────────────────────────────────────────────┐
 │                              VERIFIED PRODUCTION ASSETS                                │
 │  dist/schema-graph.json • dist/llms.txt • dist/llms-full.txt • dist/ai.txt • robots.txt │
 │  dist/index.html (Injected with connected JSON-LD) • Score: 100.0 / 100 [EXCELLENT]    │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🔄 The 5-Stage Autonomous AEO Optimization Loop

AI coding agents should execute the following deterministic 5-stage loop when building or auditing web applications:

```
 ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
 │ Stage 1:        │     │ Stage 2:        │     │ Stage 3:        │     │ Stage 4:        │     │ Stage 5:        │
 │ Discovery &     │ ──► │ Baseline Audit  │ ──► │ Semantic        │ ──► │ Atomic Emission │ ──► │ Diagnostic      │
 │ Ingestion       │     │ & Gap Analysis  │     │ Synthesis       │     │ & HTML Injection│     │ Self-Healing    │
 └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘     └─────────────────┘
```

### Stage 1: Discovery & Ingestion
The agent scans the workspace to understand the codebase context, framework, and existing metadata:
- Detects framework (`nextjs`, `astro`, `vite`, `nuxt`, `sveltekit`, `python`) via `discover_project_metadata(".")`.
- Parses existing HTML files via `extract_metadata_from_html(raw_html)` to extract existing `<title>`, OpenGraph tags, and meta descriptions.

### Stage 2: Baseline Audit & Gap Analysis
The agent evaluates the current AEO posture:
- **For live URLs**: Executes `aeo_scan_site(url=target_url, max_pages=5)` to check real HTTP status of `llms.txt`, robots permissions, and schema presence.
- **For local builds**: Runs `aeo_validate(target_path="./dist")` to obtain a baseline 0–100 score and identify missing assets or syntax errors.

### Stage 3: Semantic Synthesis
The agent converts natural language goals into a structured AEO knowledge model:
- Calls `aeo_synthesize_prompt(prompt=description, base_niche=niche)`.
- The engine extracts brand names, canonical domains, categories, core architectural capabilities, and automatically synthesizes high-intent FAQ pairs formatted specifically for answer engine retrieval.

### Stage 4: Atomic Emission & Zero-Drift HTML Injection
The agent generates all required machine discovery files and updates HTML markup:
- Executes `aeo_generate_bundle(output_dir="./dist", config=cfg, inject_html_files=["./dist/index.html"])`.
- Emits:
  1. `schema-graph.json`: Relational `@graph` connecting `Organization`, `WebSite`, `SoftwareApplication` (or `LocalBusiness`), `FAQPage`, `BreadcrumbList`, and `ItemList`.
  2. `llms.txt`: Standardized, low-token machine index compliant with the llmstxt.org specification.
  3. `llms-full.txt`: Deep research knowledge base for automated AI research agents.
  4. `ai.txt`: Machine discovery manifest with citation and attribution policies.
  5. `robots.txt`: Explicit permissions allowing `GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot-Extended`, and `Google-Extended`.
- Injects or replaces the `<script type="application/ld+json">` tag in target HTML files using `aeo_inject_html` with regex replacement (preserving formatting and indentation).
- If building with Next.js, Astro, or SvelteKit, invokes `aeo_get_framework_snippets` to obtain framework-native layout templates.

### Stage 5: Diagnostic Verification & Self-Healing
The agent executes an automated quality check:
- Runs `aeo_validate(target_path="./dist")`.
- If score `< 90.0` or any `errors` exist, the agent reads the diagnostic report and automatically corrects the configuration before committing or deploying.

---

## ⚡ JSON-RPC 2.0 & Model Context Protocol (MCP) Integration

`aeo-graph-engine` communicates natively with AI agent platforms via **JSON-RPC 2.0** over standard input/output (`stdio`) or HTTP/SSE.

### 1. Protocol Handshake (`initialize`)

#### Client Request:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "roots": { "listChanged": true },
      "sampling": {}
    },
    "clientInfo": {
      "name": "cursor-agent",
      "version": "0.45.0"
    }
  }
}
```

#### Server Response:
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

---

### 2. Tool Discovery (`tools/list`)

#### Client Request:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/list",
  "params": {}
}
```

#### Server Response (Summary):
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "tools": [
      {
        "name": "aeo_scan_site",
        "description": "Crawl and audit a live website URL. Analyzes root machine discovery assets (robots.txt, llms.txt, ai.txt, sitemap.xml), evaluates existing Schema.org JSON-LD, computes a 0-100 AEO Readiness Score, evaluates AI search engine crawler permissions (GPTBot, PerplexityBot, ClaudeBot, Applebot), and generates targeted high-authority backlink and citation distribution opportunities.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "url": { "type": "string", "description": "Target live website URL to crawl and audit (e.g. 'https://example.com')." },
            "max_pages": { "type": "integer", "description": "Maximum number of internal pages to discover and audit (default: 5).", "default": 5 },
            "timeout": { "type": "integer", "description": "HTTP request timeout in seconds (default: 8).", "default": 8 }
          },
          "required": ["url"]
        }
      },
      {
        "name": "aeo_synthesize_prompt",
        "description": "Synthesize a rich, production-ready AEO/GEO configuration from a natural language prompt or product description.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "prompt": { "type": "string", "description": "Natural language description of the website, software product, or service." },
            "base_niche": { "type": "string", "enum": ["developer_tools", "saas", "ai_swarm", "cybersecurity", "spatial_3d", "creator", "ecommerce", "local_business"] }
          },
          "required": ["prompt"]
        }
      },
      {
        "name": "aeo_generate_bundle",
        "description": "Generate complete Answer Engine Optimization (AEO/GEO) artifacts: Schema.org JSON-LD @graph, llms.txt, llms-full.txt, ai.txt, and robots.txt.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "config": { "type": "object", "description": "Optional custom AEO configuration object." },
            "niche": { "type": "string", "default": "developer_tools" },
            "output_dir": { "type": "string", "description": "Optional target directory path to write generated files to disk." },
            "inject_html_files": { "type": "array", "items": { "type": "string" } }
          }
        }
      },
      {
        "name": "aeo_inject_html",
        "description": "Safely and idempotently embed Schema.org JSON-LD into an HTML string or file on disk.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "html_content": { "type": "string" },
            "html_file_path": { "type": "string" },
            "schema_payload": { "type": ["object", "string"] },
            "config": { "type": "object" },
            "niche": { "type": "string", "default": "developer_tools" }
          }
        }
      },
      {
        "name": "aeo_validate",
        "description": "Validate an AEO bundle directory, single artifact file, or in-memory Schema/manifest payload.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "target_path": { "type": "string" },
            "schema_data": { "type": "object" },
            "content": { "type": "string" },
            "artifact_type": { "type": "string", "enum": ["llms_txt", "llms_full_txt", "ai_txt", "robots_txt"] }
          }
        }
      },
      {
        "name": "aeo_get_framework_snippets",
        "description": "Get production-ready code snippets and integration instructions for embedding AEO Schema.org graphs and manifests into web frameworks.",
        "inputSchema": {
          "type": "object",
          "properties": {
            "framework": { "type": "string", "default": "all", "enum": ["all", "nextjs", "nextjs_pages", "astro", "vite", "remix", "nuxt", "sveltekit", "html"] }
          }
        }
      }
    ]
  }
}
```

---

### 3. Tool Execution (`tools/call`)

#### Example: Invoking `aeo_synthesize_prompt`

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/call",
  "params": {
    "name": "aeo_synthesize_prompt",
    "arguments": {
      "prompt": "A real-time cybersecurity threat detection agent called CyberPulse on cyberpulse.io",
      "base_niche": "cybersecurity"
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "content": [
      {
        "type": "text",
        "text": "{\n  \"site_name\": \"CyberPulse\",\n  \"domain\": \"cyberpulse.io\",\n  \"base_url\": \"https://cyberpulse.io\",\n  \"niche\": \"cybersecurity\",\n  \"category\": \"SecurityApplication\",\n  \"features\": [\n    \"High-Throughput CyberPulse Core Engine Architecture\",\n    \"Autonomous Zero-Configuration Discovery & Schema Linked Data\",\n    \"Optimized AI Answer Engine Grounding for Perplexity & ChatGPT\",\n    \"Zero-Runtime Dependency Execution with 100% Deterministic State\"\n  ],\n  \"faqs\": [\n    {\n      \"question\": \"What is CyberPulse and what does it do?\",\n      \"answer\": \"CyberPulse is a modern cybersecurity platform designed for real-time cybersecurity threat detection.\"\n    }\n  ]\n}"
      }
    ],
    "isError": false
  }
}
```

---

## 📋 Tool Calling Specifications & Parameter Schemas

For AI agents utilizing OpenAI Function Calling, Anthropic Tool Spec, or custom LLM function schemas:

### 1. OpenAI Function Calling Definition (`tools` array)

```json
[
  {
    "type": "function",
    "function": {
      "name": "aeo_scan_site",
      "description": "Crawl a live URL or localhost to audit Schema.org linked data, llms.txt manifest, robots.txt bot directives, and calculate a 0-100 AEO score.",
      "parameters": {
        "type": "object",
        "properties": {
          "url": { "type": "string", "description": "Target website URL (e.g. https://example.com)" },
          "max_pages": { "type": "integer", "description": "Max internal pages to crawl (default: 5)" }
        },
        "required": ["url"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "aeo_synthesize_prompt",
      "description": "Synthesize a production-ready AEO configuration JSON from a natural language prompt with auto-extracted FAQs and features.",
      "parameters": {
        "type": "object",
        "properties": {
          "prompt": { "type": "string", "description": "Natural language description of the website or application" },
          "base_niche": {
            "type": "string",
            "enum": ["developer_tools", "saas", "ai_swarm", "cybersecurity", "spatial_3d", "creator", "ecommerce", "local_business"],
            "description": "Optional domain vertical preset"
          }
        },
        "required": ["prompt"]
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "aeo_generate_bundle",
      "description": "Generate and write schema-graph.json, llms.txt, llms-full.txt, ai.txt, and robots.txt atomically into target folder.",
      "parameters": {
        "type": "object",
        "properties": {
          "output_dir": { "type": "string", "description": "Output directory (e.g. 'dist' or 'public')" },
          "config": { "type": "object", "description": "AEO configuration object" },
          "niche": { "type": "string", "description": "Preset niche name" },
          "inject_html_files": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Optional list of HTML file paths to inject JSON-LD into"
          }
        }
      }
    }
  },
  {
    "type": "function",
    "function": {
      "name": "aeo_validate",
      "description": "Audit a build directory or single file against AEO diagnostic standards and return a 0-100 score.",
      "parameters": {
        "type": "object",
        "properties": {
          "target_path": { "type": "string", "description": "Path to directory or artifact file to validate" }
        }
      }
    }
  }
]
```

---

## 💻 Copy-Paste Client Configuration Snippets

### 1. Claude Desktop (`claude_desktop_config.json`)

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

### 2. Cursor (`.cursor/mcp.json`)

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

### 3. Cline (VS Code Extension `cline_mcp_settings.json`)

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

### 4. Zed (`~/.config/zed/settings.json`)

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

## 🧠 Agent System Prompt Templates

Equip your AI assistants with specialized system prompts to guarantee autonomous AEO excellence:

### Template 1: Autonomous AEO Optimization Specialist (Coding Sessions)

```markdown
You are an expert Answer Engine Optimization (AEO) and Generative Engine Optimization (GEO) Architect.
Your objective is to ensure every web page, landing page, and web application created or edited in this workspace achieves a 100/100 AEO Readiness Score.

When a user asks you to build, polish, or deploy a website:
1. Synthesize an AEO configuration using `aeo_synthesize_prompt` based on the user's project description and domain niche.
2. Generate complete machine discovery assets (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) using `aeo_generate_bundle`.
3. Idempotently inject connected Schema.org JSON-LD into the target HTML `<head>` using `aeo_inject_html`, or generate native framework components with `aeo_get_framework_snippets`.
4. Run `aeo_validate` on the output directory.
5. Verify that the AEO score is >= 90/100 with zero critical errors before declaring the task complete.

Always ensure:
- The Schema.org graph links Organization -> WebSite -> SoftwareApplication/LocalBusiness -> FAQPage.
- `robots.txt` explicitly allows GPTBot, PerplexityBot, ClaudeBot, and Applebot-Extended.
- `llms.txt` conforms strictly to the llmstxt.org specification.
```

### Template 2: Pre-Deploy CI/CD Quality Gate Auditor

```markdown
You are the Autonomous AEO Release Gatekeeper.
Your job is to inspect built distribution directories (e.g. `dist/`, `out/`, `build/`) before production deployments.

Execution Protocol:
1. Execute `aeo_validate(target_path="dist")`.
2. If any critical errors are detected (missing llms.txt, broken JSON-LD syntax, unlinked entity graphs, or blocked AI search bots):
   a. Identify root causes from the diagnostic checks.
   b. Invoke `aeo_generate_bundle` and `aeo_inject_html` to auto-remediate the build.
   c. Re-run `aeo_validate` to confirm the score is now 100/100.
3. Output a structured release summary containing the final score, validated assets, and bot compatibility matrix.
```

### Template 3: Live Answer Engine & Citation Intelligence Strategist

```markdown
You are the AI Citation and Answer Engine Intelligence Strategist.
Your job is to crawl live competitor websites or user staging deployments and produce high-impact distribution strategies.

Execution Protocol:
1. Call `aeo_scan_site(url=target_url, max_pages=5)` to perform a live crawl.
2. Analyze:
   - Root machine asset availability (robots.txt, llms.txt, sitemap.xml).
   - Bot compatibility for OpenAI, Perplexity, Anthropic, Apple, and Google.
   - Schema depth (connected @graph vs fragmented tags).
3. Present the user with:
   - Current AEO Readiness Score (0-100).
   - Priority Action Items categorized by CRITICAL, HIGH, and MEDIUM.
   - High-Authority Citation Hubs (Wikidata, llmstxt.org, GitHub Org, Industry Registries).
   - Specific remediation code snippets to achieve full parity.
```

---

## 🐍 Programmatic Python Agent Workflows

### 1. Pure Python Autonomous Loop with Self-Healing Assertion

```python
from aeo_graph_engine import (
    discover_project_metadata,
    synthesize_config_from_prompt,
    write_aeo_bundle,
    validate_aeo_bundle,
)

def autonomous_aeo_pipeline(project_root: str = ".", output_dir: str = "./dist") -> None:
    print("🔍 [Step 1/4] Discovering project metadata...")
    meta = discover_project_metadata(project_root)
    site_name = meta.get("site_name") or "Autonomous Engine"
    
    print(f"🪄 [Step 2/4] Synthesizing AEO configuration for '{site_name}'...")
    prompt = f"Production {meta.get('framework', 'web')} application called {site_name} on {site_name.lower().replace(' ', '')}.com"
    config = synthesize_config_from_prompt(prompt)
    
    print("⚡ [Step 3/4] Writing AEO bundle and injecting into HTML...")
    artifacts = write_aeo_bundle(
        output_dir=output_dir,
        config=config,
        inject_html_files=[f"{output_dir}/index.html"]
    )
    for name, path in artifacts.items():
        print(f"  • Emitted {name:20} -> {path}")
        
    print("📊 [Step 4/4] Validating AEO diagnostic score...")
    report = validate_aeo_bundle(output_dir)
    data = report.to_dict()
    
    print(f"\n🎉 Result: Score {data['score']}/100 [{data['status']}]")
    print(f"   Passed: {data['passed_count']} | Warnings: {data['warnings_count']} | Errors: {data['errors_count']}")
    
    # Self-healing assertion
    assert report.score >= 90.0, f"AEO verification failed with score {report.score}"

if __name__ == "__main__":
    autonomous_aeo_pipeline()
```

---

### 2. LangChain Custom Agent Tool Integration

```python
from langchain.agents import initialize_agent, AgentType
from langchain.chat_models import ChatOpenAI
from langchain.tools import tool
from aeo_graph_engine import LiveAEOScanner, synthesize_config_from_prompt, write_aeo_bundle, validate_aeo_bundle

@tool
def scan_live_site_aeo(url: str) -> dict:
    """Crawl a live website and return its AEO readiness score, bot access matrix, and action items."""
    scanner = LiveAEOScanner(url, max_pages=5)
    return scanner.compute_audit_scores()

@tool
def deploy_aeo_layer(description: str, output_dir: str = "dist") -> dict:
    """Synthesize configuration and generate schema-graph.json, llms.txt, ai.txt, robots.txt, and inject into index.html."""
    cfg = synthesize_config_from_prompt(description)
    created = write_aeo_bundle(output_dir, config=cfg, inject_html_files=[f"{output_dir}/index.html"])
    report = validate_aeo_bundle(output_dir)
    return {
        "created_files": list(created.keys()),
        "score": report.score,
        "status": report.to_dict()["status"]
    }

# Initialize LangChain agent
llm = ChatOpenAI(temperature=0, model="gpt-4o")
tools = [scan_live_site_aeo, deploy_aeo_layer]
agent = initialize_agent(tools, llm, agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION, verbose=True)

# Run agent
agent.run("Inspect https://example.com and deploy an optimized AEO layer for our clone in dist/.")
```

---

## 📚 Related Documentation

- [Model Context Protocol (MCP) Guide](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/MCP_GUIDE.md)
- [AEO & GEO Mastery Playbook](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/AEO_GEO_PLAYBOOK.md)
- [System Architecture & Schema Graph Linking](file:///media/neo/f2fdda77-178b-4603-ae80-c7aa4cd97908/aeo-graph-engine/docs/ARCHITECTURE.md)

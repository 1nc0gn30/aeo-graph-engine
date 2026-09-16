# Model Context Protocol (MCP) Client Configuration Presets

The **`aeo-graph-engine`** includes a native, zero-dependency [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server (`aeo_graph_engine.mcp_server`). 

This allows AI agents and coding assistants like **Claude Desktop**, **Cursor**, **Cline / Roo Code**, and **Zed Editor** to directly audit sites, synthesize Schema.org graphs, validate AEO readiness, and generate framework code from natural language.

---

## 🧰 Available MCP Tools

When registered with your AI client, `aeo-graph-engine` provides the following native tools:

| Tool Name | Description |
| :--- | :--- |
| `aeo_scan_site` | Crawl and audit a live website URL. Analyzes robots.txt, llms.txt, ai.txt, sitemap.xml, evaluates Schema.org JSON-LD, scores AEO readiness (0-100), and inspects AI bot permissions. |
| `aeo_synthesize_prompt` | Convert a natural language description into a complete, structured AEO configuration with brand details, niche category, and FAQ pairs. |
| `aeo_generate_bundle` | Generate full AEO artifact bundles (`schema-graph.json`, `llms.txt`, `llms-full.txt`, `ai.txt`, `robots.txt`) in-memory or directly to disk. |
| `aeo_inject_html` | Idempotently embed structured JSON-LD `<script type="application/ld+json">` graphs into HTML files or string templates. |
| `aeo_validate` | Run a diagnostic audit on a local directory or file, returning passed checks, warnings, errors, and an AEO Readiness Score. |
| `aeo_get_framework_snippets` | Generate copy-pasteable integration code for Next.js (App & Pages Router), Astro, Vite/React, SvelteKit, Remix, and Nuxt. |

---

## ⚙️ Configuration by Client

### 1. Anthropic Claude Desktop
Configuration file location:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

Preset: `examples/mcp-clients/claude_desktop_config.json`
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/aeo-graph-engine/src"
      }
    }
  }
}
```

---

### 2. Cursor IDE
Configuration file location:
- Workspace: `.cursor/mcp.json`
- User Global: Cursor Settings > MCP Servers

Preset: `examples/mcp-clients/cursor_mcp.json`
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"],
      "env": {
        "PYTHONPATH": "/path/to/aeo-graph-engine/src"
      }
    }
  }
}
```

---

### 3. Cline / Roo Code (VS Code Extension)
Configuration file location:
- `~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json` (macOS)
- `%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json` (Windows)

Preset: `examples/mcp-clients/cline_mcp.json`
```json
{
  "mcpServers": {
    "aeo-graph-engine": {
      "command": "python3",
      "args": ["-m", "aeo_graph_engine.mcp_server"],
      "disabled": false,
      "autoApprove": [
        "aeo_scan_site",
        "aeo_validate",
        "aeo_get_framework_snippets",
        "aeo_synthesize_prompt"
      ],
      "env": {
        "PYTHONPATH": "/path/to/aeo-graph-engine/src"
      }
    }
  }
}
```

---

### 4. Zed Editor
Configuration file location:
- `~/.config/zed/settings.json`

Preset: `examples/mcp-clients/zed_settings.json`
```json
{
  "context_servers": {
    "aeo-graph-engine": {
      "command": {
        "path": "python3",
        "args": ["-m", "aeo_graph_engine.mcp_server"],
        "env": {
          "PYTHONPATH": "/path/to/aeo-graph-engine/src"
        }
      }
    }
  }
}
```

---

## 🧪 Testing the MCP Server

You can test the server or print the tool schemas directly from your terminal:

```bash
# List all registered MCP tools & input schemas:
python3 -m aeo_graph_engine.mcp_server --tools

# Generate a specific client config snippet:
python3 -m aeo_graph_engine.mcp_server --config claude_desktop
python3 -m aeo_graph_engine.mcp_server --config cursor
python3 -m aeo_graph_engine.mcp_server --config cline
python3 -m aeo_graph_engine.mcp_server --config zed
```

---

## 💬 Example Prompt Workflows Inside AI Assistants

Once connected, you can ask your AI assistant questions like:
- *"Audit https://example.com for Answer Engine Optimization and give me the readiness score."*
- *"Synthesize an AEO bundle for a Kubernetes security SaaS called KubeGuard and export Next.js App Router code."*
- *"Validate the files in ./dist and tell me what warnings need to be fixed for ChatGPT search."*

# 🤖 AI Agent Integration & Autonomous Execution Guide

> **How Autonomous Agents (Antigravity, Hermes, Claude Code, Cursor, AutoGPT) Can Operate AEO Graph Engine**

---

## 🎯 Overview

`aeo-graph-engine` is designed to be **AI-agent native**. AI assistants and autonomous coding agents can discover, configure, and operate this tool through:

1. **Natural Language Synthesis (`aeo prompt "..."`)**: The agent passes a high-level project goal or description, and the engine heuristic synthesizer automatically produces the entire schema configuration.
2. **JSON Schema Tool Calling (`aeo schema`)**: Exposes formal JSON-Schema definitions for OpenAI Function Calling, Anthropic Tool use, and Model Context Protocol (MCP).
3. **Programmatic Python API**: Seamless direct invocation in Python agent workflows.

---

## 💻 CLI Commands for AI Agents

### 1. Synthesize from Natural Language Prompt:
```bash
# Agent describes the target app in plain English
aeo prompt "A high-performance Solana DeFi lending protocol with sub-second liquidations called SolarYield on solaryield.fi" --output-dir dist/
```

### 2. Auto-Extract from Existing Codebase:
```bash
# Agent extracts metadata from built HTML
aeo extract dist/index.html
```

### 3. Dump Formal JSON Schema for Function Calling:
```bash
aeo schema
```

### 4. Structured JSON Output for Agent Decision-Making:
```bash
# Agent audits readiness and receives machine JSON
aeo --validate dist/ --format json
```

---

## 🐍 Python Agent Example

```python
from aeo_graph_engine import (
    synthesize_config_from_prompt,
    write_aeo_bundle,
    validate_aeo_bundle
)

# 1. Agent receives natural language instruction
user_prompt = "Build an AEO layer for an AI-powered resume builder called CVForge on cvforge.app"

# 2. Agent synthesizes configuration
config = synthesize_config_from_prompt(user_prompt)

# 3. Agent writes files & injects into static build
artifacts = write_aeo_bundle(
    output_dir="./dist",
    config=config,
    inject_html_files=["./dist/index.html"]
)

# 4. Agent self-verifies outcome
report = validate_aeo_bundle("./dist")
assert report.score >= 90.0, f"AEO Audit Failed with score {report.score}"
print(f"Agent generated {len(artifacts)} AEO assets with Score: {report.score}/100")
```

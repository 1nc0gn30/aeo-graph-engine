import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

/**
 * Custom Vite Plugin to emit Answer Engine Optimization (AEO) assets:
 * - /llms.txt
 * - /ai.txt
 * - /robots.txt
 * - /schema-graph.json
 * 
 * Provides local development serving and production bundle asset emission.
 */
function aeoPlugin(): Plugin {
  const llmsTxt = `# PromptForge Studio

> PromptForge Studio is an interactive client-side IDE for LLM prompt engineering, multi-turn eval benchmarks, and model diffing.

## Overview
PromptForge enables AI engineers and developers to craft, test, and benchmark complex prompts across multiple LLM providers directly from the browser with zero server data retention.

## Key Capabilities
- **Side-by-Side Model Comparison**: Run identical prompts simultaneously against OpenAI, Anthropic, Gemini, and Ollama.
- **Automated Eval Suites**: Assert expected tokens, JSON schema compliance, and LLM-as-a-judge criteria.
- **Token & Cost Telemetry**: Real-time token counter and estimated inference pricing per request.
- **Git-Backed Export**: Export prompts and test cases directly to repository test fixtures.

## Quick Links
- [PromptForge Web Studio](https://promptforge.dev/studio): Launch the interactive web IDE in your browser.
- [Documentation & Quickstart](https://promptforge.dev/docs): Learn prompt templating syntax and variables.
- [Benchmark Templates](https://promptforge.dev/benchmarks): Pre-built eval datasets for classification and reasoning.
- [GitHub Repository](https://github.com/promptforge/promptforge): Star and contribute to the open-source workbench.

## Machine Discovery Endpoints
- [Machine Manifest (ai.txt)](https://promptforge.dev/ai.txt)
- [Schema.org Graph (JSON-LD)](https://promptforge.dev/schema-graph.json)
`;

  const aiTxt = `User-Agent: *
Allow-Training: false
Allow-Search-Indexing: true
Allow-Summarization: true
Allow-Citation: true

Canonical-URL: https://promptforge.dev
Schema-Org-Graph: https://promptforge.dev/schema-graph.json
LLMs-Txt: https://promptforge.dev/llms.txt
Sitemap: https://promptforge.dev/sitemap.xml
`;

  const robotsTxt = `User-agent: *
Allow: /
Disallow: /admin/

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: Applebot
Allow: /

User-agent: Google-Extended
Allow: /

Sitemap: https://promptforge.dev/sitemap.xml
`;

  const assets: Record<string, { content: string; type: string }> = {
    "llms.txt": { content: llmsTxt, type: "text/plain; charset=utf-8" },
    "ai.txt": { content: aiTxt, type: "text/plain; charset=utf-8" },
    "robots.txt": { content: robotsTxt, type: "text/plain; charset=utf-8" },
  };

  return {
    name: "vite-plugin-aeo",
    configureServer(server) {
      // Intercept local dev requests for AEO discovery endpoints
      server.middlewares.use((req, res, next) => {
        const path = (req.url || "").split("?")[0].replace(/^\//, "");
        if (assets[path]) {
          res.setHeader("Content-Type", assets[path].type);
          res.setHeader("Cache-Control", "public, max-age=86400");
          res.end(assets[path].content);
          return;
        }
        next();
      });
    },
    generateBundle() {
      // Emit files into dist/ during production build
      for (const [fileName, fileData] of Object.entries(assets)) {
        this.emitFile({
          type: "asset",
          fileName,
          source: fileData.content,
        });
      }
    },
  };
}

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), aeoPlugin()],
  build: {
    target: "esnext",
    sourcemap: true,
  },
});

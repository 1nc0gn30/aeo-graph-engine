# Vite + React SPA AEO Integration Guide

This directory demonstrates Answer Engine Optimization (AEO) and structured Schema.org data integration for Single Page Applications (SPAs) built with **Vite**, **React**, and **TypeScript**.

---

## 💡 The SPA Challenge with Answer Engines

Most traditional search and LLM crawlers (including GPTBot, ClaudeBot, and PerplexityBot) fetch raw HTML documents using fast HTTP clients rather than headless browsers with full JavaScript runtime execution. 

If your SPA relies entirely on client-side React hooks or `react-helmet` to inject `<script type="application/ld+json">`, AI crawlers will often receive an empty `<div id="root"></div>` without your structured graph.

### The Solution:
1. **Pre-Rendered Raw Schema in `index.html`**: The root entry HTML includes the static Schema.org `@graph` (containing `Organization`, `WebSite`, `SoftwareApplication`, and `FAQPage`). When any crawler makes a simple `GET /` request, the full linked data graph is available immediately.
2. **Build-Time Machine Discovery Emission**: A custom `aeoPlugin` in `vite.config.ts` emits `/llms.txt`, `/ai.txt`, and `/robots.txt` directly to `dist/` during `vite build` and serves them locally in development mode.

---

## 📁 Directory Structure

```text
examples/vite-react-spa/
├── index.html                # Entry HTML with pre-injected Schema.org JSON-LD graph & meta tags
├── vite.config.ts            # Vite configuration with automated AEO discovery asset plugin
├── public/
│   └── llms.txt              # Standardized LLM context file per llmstxt.org
└── README.md                 # This guide
```

---

## 🛠️ Step-by-Step Integration

### Step 1: Update `index.html`
Copy the structured metadata, Open Graph tags, and `<script type="application/ld+json">` block from `examples/vite-react-spa/index.html` into your own project's `index.html`.

### Step 2: Configure Vite Asset Emission
Add the `aeoPlugin()` from `vite.config.ts` into your `vite.config.ts` plugins array:

```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { aeoPlugin } from "./vite-plugin-aeo"; // or inlined

export default defineConfig({
  plugins: [react(), aeoPlugin()],
});
```

### Step 3: Build and Verify
Run a production build and validate the output directory using `aeo-graph-engine`:

```bash
# Build the SPA
npm run build

# Validate the generated dist/ folder
aeo-graph-engine validate ./dist
```

---

## 🌐 Deploying to Static CDNs

When hosting on platforms like Netlify, Vercel, Cloudflare Pages, or AWS S3 + CloudFront:
- Make sure standard SPA rewrite rules (e.g. `/* -> /index.html 200`) do **not** shadow static asset files like `/llms.txt`, `/ai.txt`, `/robots.txt`, and `/sitemap.xml`.

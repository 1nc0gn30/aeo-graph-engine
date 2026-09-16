# Astro 4/5 AEO Integration Guide

This directory demonstrates a production-grade Answer Engine Optimization (AEO) and structured data setup for [Astro](https://astro.build) (v4.x and v5.x) websites, content sites, and documentation portals.

Astro’s zero-JS-by-default architecture makes it exceptionally fast for search engine bots and AI crawlers to parse. Adding structured Schema.org graphs and machine-readable `llms.txt` assets guarantees maximum citation visibility across AI search engines.

---

## 📁 Directory Structure

```text
examples/astro-site/
├── src/
│   └── components/
│       └── AeoHead.astro     # Reusable Astro component with Schema.org graph & meta tags
├── public/
│   ├── llms.txt              # Standardized LLM context file per llmstxt.org
│   └── robots.txt            # AI crawler permission rules & sitemap reference
└── README.md                 # This guide
```

---

## 🌟 How It Works

### 1. Reusable `<AeoHead />` Component
The `src/components/AeoHead.astro` component bundles:
- Canonical `<link rel="canonical">` handling.
- Open Graph and Twitter Card tags.
- Links to `/llms.txt` and `/schema-graph.json`.
- Complete JSON-LD `<script type="application/ld+json">` containing `Organization`, `WebSite`, `SoftwareApplication`, and `FAQPage` nodes.

### 2. Standardized `public/llms.txt`
Placed directly in Astro's `public/` directory, this file is copied untouched to the root of your production build (`/llms.txt`). AI agents (such as Perplexity, ChatGPT, and Claude) read this to understand project capabilities and documentation hierarchy.

### 3. AI-Optimized `public/robots.txt`
Authorizes modern answer engine crawlers (`GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot`, `Google-Extended`) while protecting sensitive internal paths and pointing to the generated `sitemap-index.xml`.

---

## 🛠️ Integration Instructions

### Step 1: Add Component to your Astro Layout
Copy `AeoHead.astro` into your Astro project's `src/components/` directory:

```bash
cp examples/astro-site/src/components/AeoHead.astro my-astro-project/src/components/
cp examples/astro-site/public/* my-astro-project/public/
```

### Step 2: Include in `src/layouts/Layout.astro`

```astro
---
import AeoHead from '../components/AeoHead.astro';

interface Props {
  title?: string;
  description?: string;
  canonical?: string;
}

const { title, description, canonical } = Astro.props;
---

<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
    
    <!-- Injects Canonical, OG, Twitter, and Schema.org JSON-LD Graph -->
    <AeoHead 
      title={title} 
      description={description} 
      canonical={canonical} 
    />
  </head>
  <body>
    <slot />
  </body>
</html>
```

### Step 3: Configure Astro Sitemap (`astro.config.mjs`)
Ensure `@astrojs/sitemap` is enabled so your sitemap URL matches `robots.txt`:

```javascript
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://docusphere.dev',
  integrations: [sitemap()],
});
```

### Step 4: Validate with AEO Graph Engine

```bash
# Build your static site
npm run build

# Validate the generated dist/ folder
aeo-graph-engine validate ./dist
```

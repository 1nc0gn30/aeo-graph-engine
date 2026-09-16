# Next.js 14/15 App Router AEO Integration

This directory demonstrates a complete, production-ready Answer Engine Optimization (AEO) and Generative Engine Optimization (GEO) setup for Next.js 14 & 15 applications using the App Router.

It provides out-of-the-box compliance with modern search and AI citation engines including **ChatGPT Search (GPTBot)**, **Perplexity AI (PerplexityBot)**, **Claude (ClaudeBot)**, **Google AI Overviews (Google-Extended)**, and **Apple Intelligence (Applebot)**.

---

## 📁 Directory Structure

```text
examples/nextjs-app-router/
├── app/
│   ├── layout.tsx            # Global HTML layout with Next Metadata & Schema.org JSON-LD graph
│   ├── robots.ts             # Dynamic robots.txt with AI bot crawler authorization matrix
│   ├── sitemap.ts            # Dynamic sitemap.xml route generator
│   └── llms.txt/
│       └── route.ts          # Static route handler serving curated llms.txt for AI agents
├── public/
│   └── ai.txt                # Static machine discovery manifest & indexing policy
└── README.md                 # This guide
```

---

## 🚀 Key Architectural Features

### 1. Unified Schema.org Linked Data Graph (`app/layout.tsx`)
Rather than injecting disconnected fragments across pages, the root layout injects a cohesive `@graph` structure linking:
- **`Organization`**: Brand authority, logo, contact points, and verified social profiles (`sameAs`).
- **`WebSite`**: Canonical URL, publisher attribution, and structured `SearchAction`.
- **`SoftwareApplication`**: Primary product metadata, application category, licensing, pricing, and key features.
- **`FAQPage`**: High-intent structured Q&A pairs heavily indexed by Answer Engines for direct answer extraction.
- **`BreadcrumbList`**: Structural hierarchy for search engine crawlers.

### 2. Modern AI Crawler Rules (`app/robots.ts`)
Next.js dynamic metadata route configuring granular access rules:
- Unlocks AI search crawlers (`GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot-Extended`, `Google-Extended`).
- Protects internal endpoints (`/api/private/`, `/admin/`).
- Declares the canonical sitemap location.

### 3. Route-Level `llms.txt` Endpoint (`app/llms.txt/route.ts`)
Implements the [llmstxt.org](https://llmstxt.org) standard via a static Next.js Route Handler:
- Cached with `Cache-Control: public, max-age=86400, stale-while-revalidate=3600`.
- Structured with markdown H1 title, blockquote summary, and curated documentation links for LLM agents.

### 4. Machine Discovery Manifest (`public/ai.txt`)
Provides AI governance policies and fast discovery links to `/schema-graph.json`, `/llms.txt`, and `/sitemap.xml`.

---

## 🛠️ Step-by-Step Integration Guide

### Step 1: Copy Integration Files
Copy the files from this directory into your Next.js project:

```bash
cp -r examples/nextjs-app-router/app/* my-nextjs-app/app/
cp -r examples/nextjs-app-router/public/* my-nextjs-app/public/
```

### Step 2: Customize Your Brand Parameters
Update `BASE_URL`, company name, product details, and FAQ questions in `app/layout.tsx` or generate a customized configuration using `aeo-graph-engine`:

```bash
# Generate tailored Next.js App Router code directly:
aeo-graph-engine export --framework nextjs_app --output ./my-nextjs-app
```

### Step 3: Verify and Audit Locally
Run the `aeo-graph-engine` audit to check your site's AEO Readiness Score:

```bash
# Validate generated artifacts
aeo-graph-engine validate ./my-nextjs-app/public

# Or audit your local dev server while running:
# Terminal 1: npm run dev
# Terminal 2:
aeo-graph-engine scan http://localhost:3000
```

---

## 🔍 Validation Checklist

| Target File | Status / Requirement |
| :--- | :--- |
| `app/layout.tsx` | Contains `<script type="application/ld+json">` with valid `@graph` containing `Organization`, `WebSite`, `SoftwareApplication`, and `FAQPage`. |
| `app/robots.ts` | Allows `GPTBot`, `PerplexityBot`, `ClaudeBot`, `Applebot`, and links `sitemap.xml`. |
| `app/sitemap.ts` | Exports valid `MetadataRoute.Sitemap` array with absolute URLs. |
| `app/llms.txt/route.ts` | Starts with `# <Title>`, contains `> <Summary>`, and lists markdown links. |
| `public/ai.txt` | Defines `User-Agent`, `Canonical-URL`, `Schema-Org-Graph`, and `LLMs-Txt`. |

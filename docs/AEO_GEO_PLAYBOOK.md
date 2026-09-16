# 📖 The 2026 AEO & GEO Mastery Playbook

> **How Answer Engine Optimization (AEO) and Generative Engine Optimization (GEO) Work in Practice**

---

## 🔍 The Paradigm Shift: SEO vs. AEO / GEO

| Classic Search Engine Optimization (SEO) | Answer Engine Optimization (AEO / GEO) |
| :--- | :--- |
| **Goal:** Rank on Google/Bing's 10 blue links SERP. | **Goal:** Get synthesized and cited directly in conversational answers across ChatGPT Search, Perplexity AI, Claude, Google AI Overviews, and Apple Intelligence. |
| **Mechanic:** Keyword density, backlink quantity, anchor text. | **Mechanic:** Connected Schema.org `@graph` linked data, standardized `llms.txt` indexes, structured Q&A entity ontologies, and factual entity authority. |
| **Consumption:** Web crawlers parse raw HTML text for keywords. | **Consumption:** Retrieval-Augmented Generation (RAG) models fetch vector embeddings and parse machine manifests (`llms.txt`, `ai.txt`) with strict token budgets. |
| **Penalty:** Duplicate keywords, slow TTFB. | **Penalty:** Hallucinated ambiguity, unlinked entities, blocked AI bots, missing structured Q&A. |

---

## 🧠 How AI Answer Engines Select & Cite Sources

Modern AI search engines (like Perplexity, SearchGPT, Claude, and Google AI Overviews) utilize a **four-stage pipeline**:

```
 ┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
 │ 1. Intent &    │     │ 2. Retrieval & │     │ 3. Entity      │     │ 4. Grounding & │
 │ Query Expansion│ ──► │ Vector Search  │ ──► │ Verification   │ ──► │ Citation       │
 └────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
```

1. **Intent & Query Expansion**: The model decomposes user prompts into semantic sub-queries.
2. **Retrieval & Vector Search**: The engine queries fast vector caches and searches machine discovery files (`llms.txt`, `ai.txt`, `robots.txt`).
3. **Entity Verification & Graph Linking**: The LLM parses `<script type="application/ld+json">` `@graph` blocks to establish **publisher authority**, **brand relationships**, and **official facts**.
4. **Grounding & Citation**: The answer is generated with inline citations linking back to canonical URLs declared in the structured schema.

---

## 🛠️ The 5 Core Pillars of AEO

### 1. Connected Schema.org `@graph` (Entity Authority)
Isolated schema tags (e.g. just a generic `WebSite` tag) are treated as low-confidence signals. **`aeo-graph-engine`** connects entities into an interdependent graph:
* `Organization` acts as the author and legal publisher.
* `WebSite` points back to `Organization` via `publisher: {"@id": "..."}`.
* `SoftwareApplication` or `LocalBusiness` points to `Organization` via `creator: {"@id": "..."}`.
* `FAQPage` supplies pre-verified question-answer pairs that LLMs can quote verbatim.
* `BreadcrumbList` dictates hierarchical depth and taxonomy.

### 2. Standardized `llms.txt` (Low-Token Machine Index)
LLMs have finite context windows when retrieving search results. `llms.txt` provides:
* An H1 project title.
* A concise blockquote summary (`> ...`).
* Bulleted resource links formatted as `[Section Name](URL): Detailed one-line description`.

### 3. Deep Research Manifest (`llms-full.txt`)
When deep-research agents (e.g. OpenAI Deep Research, Perplexity Deep Research) investigate a domain, they request `llms-full.txt` to parse entire architecture diagrams, capabilities, and FAQ matrices without scraping messy DOM trees.

### 4. Machine Access Policies (`ai.txt`)
Explicitly informs autonomous agents about:
* Canonical entity URLs.
* Attribution and citation format rules.
* Derivative work permissions.

### 5. Crawler Access Directives (`robots.txt`)
Ensures that leading AI search bots are explicitly allowed:
* `GPTBot` (OpenAI ChatGPT Search)
* `PerplexityBot` (Perplexity AI)
* `ClaudeBot` & `anthropic-ai` (Anthropic Claude)
* `Applebot-Extended` (Apple Intelligence)
* `Google-Extended` (Google Gemini / AI Overviews)

---

## 🚀 How to Achieve a 100/100 AEO Readiness Score

1. **Always include a clear FAQ section**: FAQs directly power conversational responses.
2. **Specify canonical domain names**: Ensure all `@id` URIs use absolute `https://` URLs.
3. **Declare publisher and creator entities**: Establishes verified provenance.
4. **Run continuous CI validation**: Use `aeo --validate dist/` in your deployment pipeline.

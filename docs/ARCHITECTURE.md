# 🏗️ AEO Graph Engine Architecture

> **Internal Pipeline, Schema Graph Linking, HTML Injection & Validation Mechanics**

---

## 📐 System Architecture Diagram

```
                              ┌───────────────────────────────┐
                              │  NATURAL LANGUAGE PROMPT OR   │
                              │     PROJECT CONFIG / HTML     │
                              └───────────────┬───────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      ▼                                               ▼
         ┌─────────────────────────┐                     ┌─────────────────────────┐
         │   ai_config.py /        │                     │   discovery.py /        │
         │   Prompt Synthesizer    │                     │   Metadata Extractor    │
         └────────────┬────────────┘                     └────────────┬────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │
                                              ▼
                                 ┌─────────────────────────┐
                                 │   core.py (Generator)   │
                                 │ • resolve_config()      │
                                 └────────────┬────────────┘
                                              │
       ┌───────────────────────────────┬──────┴────────────────────────┬───────────────────────────────┐
       ▼                               ▼                               ▼                               ▼
┌──────────────┐              ┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│ Schema Graph │              │    llms.txt     │             │  llms-full.txt  │             │ ai.txt & robots │
│ (@graph JSON)│              │ (llmstxt.org)   │             │ (Deep Research) │             │ (Bot Policies)  │
└──────┬───────┘              └────────┬────────┘             └────────┬────────┘             └────────┬────────┘
       │                               │                               │                               │
       └───────────────────────────────┼───────────────────────────────┴───────────────────────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │   write_aeo_bundle()      │
                         │ • Atomic File Emission    │
                         │ • HTML Injector Engine    │
                         └─────────────┬─────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────┐
                         │  validator.py (Scorer)    │
                         │ • 0-100 Diagnostic Score  │
                         └───────────────────────────┘
```

---

## 🧬 Schema.org `@graph` Linking Model

Unlike fragmented JSON-LD snippets, `aeo-graph-engine` constructs a **single relational graph**:

```json
{
  "@context": "https://schema.org",
  "@graph": [
    {
      "@id": "https://example.com/#organization",
      "@type": "Organization",
      "name": "Apex Corp",
      "url": "https://example.com/"
    },
    {
      "@id": "https://example.com/#website",
      "@type": "WebSite",
      "name": "Apex Platform",
      "url": "https://example.com/",
      "publisher": { "@id": "https://example.com/#organization" },
      "potentialAction": {
        "@type": "SearchAction",
        "target": "https://example.com/search/?q={search_term_string}"
      }
    },
    {
      "@id": "https://example.com/#application",
      "@type": "SoftwareApplication",
      "name": "Apex Platform",
      "creator": { "@id": "https://example.com/#organization" },
      "offers": { "@type": "Offer", "price": "0.00", "priceCurrency": "USD" }
    },
    {
      "@id": "https://example.com/#faq",
      "@type": "FAQPage",
      "url": "https://example.com/#faq",
      "mainEntity": [ ... ]
    },
    {
      "@id": "https://example.com/#breadcrumbs",
      "@type": "BreadcrumbList",
      "itemListElement": [ ... ]
    }
  ]
}
```

---

## 💉 Zero-Drift HTML Injection Mechanics

The `injector.py` module uses robust regex matching to guarantee idempotency:
1. **Existing Tag Detection**: Checks for `<script type="application/ld+json">.*?</script>`. If found, replaces the inner payload with zero formatting corruption.
2. **Head Injection**: If no tag exists, finds `</head>` and embeds the formatted block with proper indentation.
3. **Fallback Position**: If no `</head>` tag is found, safely places the tag right before `<body>` or prepends it to the file.

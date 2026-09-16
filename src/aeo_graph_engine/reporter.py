"""
Comprehensive AEO Audit & Competitive Benchmark Report Generator.
Generates GitHub-flavored Markdown reports and standalone, zero-dependency,
dark/light print-friendly HTML reports with embedded SVG score dials,
bot accessibility matrices, entity graph diagrams, and framework remediations.

Zero external runtime dependencies (pure Python standard library).
"""

import html
import json
import re
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from .framework_exporter import FrameworkExporter


def _format_score_bar(score: float, max_score: float = 25.0, length: int = 12) -> str:
    """Generates a text-based progress bar for markdown tables (e.g. [████████░░░░])."""
    if max_score <= 0:
        return "[░░░░░░░░░░░░]"
    pct = max(0.0, min(1.0, score / max_score))
    filled = int(round(pct * length))
    empty = length - filled
    return f"[{'█' * filled}{'░' * empty}] {int(pct * 100)}%"


def _get_grade(score: float) -> Tuple[str, str, str]:
    """Returns letter grade, badge color, and status label for a given score (0-100)."""
    if score >= 90:
        return "A+", "brightgreen", "EXCELLENT"
    elif score >= 80:
        return "A", "green", "EXCELLENT"
    elif score >= 70:
        return "B", "blue", "GOOD"
    elif score >= 60:
        return "C", "yellow", "NEEDS_OPTIMIZATION"
    elif score >= 45:
        return "D", "orange", "NEEDS_OPTIMIZATION"
    else:
        return "F", "red", "CRITICAL_GAPS"


def _normalize_inputs(
    scan_result: Dict[str, Any],
    benchmark_result: Optional[Dict[str, Any]] = None
) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Smartly normalizes scan and benchmark payloads if benchmark was passed as primary scan."""
    if "summary" in scan_result and "category_winners" in scan_result:
        # benchmark_result was passed as scan_result
        bench = scan_result
        scan = scan_result.get("raw_scan_a", {})
        if not scan:
            scan = {
                "target_url": bench.get("site_a", {}).get("url", "https://example.com"),
                "origin": bench.get("site_a", {}).get("origin", ""),
                "overall_aeo_score": bench.get("site_a", {}).get("overall_score", 0.0),
                "status": bench.get("site_a", {}).get("status", "UNKNOWN"),
            }
        return scan, bench
    return scan_result, benchmark_result


def generate_markdown_report(
    scan_result: Dict[str, Any],
    benchmark_result: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a professional, GitHub-flavored markdown audit report (AEO_AUDIT_REPORT.md).

    Includes executive scorecard, bot matrix table, entity graph visualization,
    prioritized action items, framework remediation steps, and optional competitor benchmark.
    """
    scan, bench = _normalize_inputs(scan_result, benchmark_result)

    target_url = scan.get("target_url", "https://example.com")
    overall_score = float(scan.get("overall_aeo_score", 0.0))
    status = scan.get("status", "NEEDS_OPTIMIZATION")
    date_str = datetime.date.today().isoformat()
    grade, badge_color, _ = _get_grade(overall_score)

    pages = scan.get("pages", [])
    pages_count = len(pages) if pages else int(scan.get("pages_audited_count", 1))

    # Category scores
    cat_scores = scan.get("category_scores", {})
    s_schema = float(cat_scores.get("schema_linked_data", {}).get("score", 0.0))
    m_schema = float(cat_scores.get("schema_linked_data", {}).get("max", 25.0))
    s_llms = float(cat_scores.get("llms_txt_machine_index", {}).get("score", 0.0))
    m_llms = float(cat_scores.get("llms_txt_machine_index", {}).get("max", 25.0))
    s_bots = float(cat_scores.get("ai_crawler_governance", {}).get("score", 0.0))
    m_bots = float(cat_scores.get("ai_crawler_governance", {}).get("max", 20.0))
    s_content = float(cat_scores.get("semantic_content_grounding", {}).get("score", 0.0))
    m_content = float(cat_scores.get("semantic_content_grounding", {}).get("max", 15.0))
    s_tech = float(cat_scores.get("technical_seo_foundation", {}).get("score", 0.0))
    m_tech = float(cat_scores.get("technical_seo_foundation", {}).get("max", 15.0))

    # Framework exporter for code remediation snippets
    site_name = ""
    description = ""
    for p in pages:
        if p.get("title") and not site_name:
            site_name = p.get("title")
        if p.get("description") and not description:
            description = p.get("description")
    if not site_name:
        site_name = target_url.replace("https://", "").replace("http://", "").split("/")[0]

    exporter = FrameworkExporter({
        "site_name": site_name,
        "base_url": target_url,
        "description": description or f"Official platform documentation and services for {site_name}.",
    })

    md_lines: List[str] = []

    # 1. Header & Badges
    md_lines.append(f"# 🌐 AEO & Answer Engine Optimization Audit Report")
    md_lines.append("")
    md_lines.append(f"![AEO Score](https://img.shields.io/badge/AEO_Score-{overall_score:.1f}%2F100-{badge_color}?style=for-the-badge) "
                    f"![Grade](https://img.shields.io/badge/Grade-{grade}-{badge_color}?style=for-the-badge) "
                    f"![Status](https://img.shields.io/badge/Status-{status}-blue?style=for-the-badge) "
                    f"![Date](https://img.shields.io/badge/Audit_Date-{date_str}-informational?style=for-the-badge)")
    md_lines.append("")
    md_lines.append(f"> **Target URL:** `{target_url}`  ")
    md_lines.append(f"> **Pages Audited:** `{pages_count}`  ")
    md_lines.append(f"> **Engine Version:** `AEO Graph Engine v1.0.0 (2026 Standards)`  ")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 2. Executive Summary Scorecard
    md_lines.append("## 📊 1. Executive Summary & Category Scorecard")
    md_lines.append("")
    md_lines.append("| Category | Score | Max | Progress | Status | Weight / Impact |")
    md_lines.append("| :--- | :---: | :---: | :--- | :---: | :--- |")
    md_lines.append(f"| **Schema.org Linked Data Graph** | `{s_schema:.1f}` | `{m_schema:.1f}` | {_format_score_bar(s_schema, m_schema)} | {'✅ High' if s_schema >= 18 else '⚠️ Needs Fix' if s_schema >= 10 else '❌ Missing'} | Knowledge graph entity resolution in Gemini & Claude |")
    md_lines.append(f"| **Machine Index (`llms.txt` / Full)** | `{s_llms:.1f}` | `{m_llms:.1f}` | {_format_score_bar(s_llms, m_llms)} | {'✅ Indexed' if s_llms >= 20 else '⚠️ Partial' if s_llms > 0 else '❌ Missing'} | Sub-50ms token ingestion in ChatGPT & Perplexity |")
    md_lines.append(f"| **AI Search Crawler Governance** | `{s_bots:.1f}` | `{m_bots:.1f}` | {_format_score_bar(s_bots, m_bots)} | {'✅ Allowed' if s_bots >= 16 else '⚠️ Partial' if s_bots >= 8 else '❌ Restricted'} | Live web access via GPTBot, PerplexityBot, Applebot |")
    md_lines.append(f"| **Semantic Content & Grounding** | `{s_content:.1f}` | `{m_content:.1f}` | {_format_score_bar(s_content, m_content)} | {'✅ Grounded' if s_content >= 12 else '⚠️ Thin' if s_content >= 6 else '❌ Low Density'} | Vector similarity retrieval & chunk answerability |")
    md_lines.append(f"| **Technical SEO & Discovery Base** | `{s_tech:.1f}` | `{m_tech:.1f}` | {_format_score_bar(s_tech, m_tech)} | {'✅ Solid' if s_tech >= 12 else '⚠️ Needs Work'} | HTTPS, XML sitemaps, and canonical linking |")
    md_lines.append(f"| **TOTAL AEO READINESS SCORE** | **`{overall_score:.1f}`** | **`100.0`** | **{_format_score_bar(overall_score, 100.0, 16)}** | **`{grade} ({status})`** | **Overall Generative AI Search Dominance** |")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 3. AI Search Engine Bot Compatibility Matrix
    md_lines.append("## 🤖 2. AI Search Engine Bot Compatibility Matrix")
    md_lines.append("")
    md_lines.append("Real-time audit of AI search crawler access policies and structured schema feature compatibility:")
    md_lines.append("")
    md_lines.append("| AI Search Engine | Crawler User-Agent | Access Status | Enhanced Feature Compatibility | Optimization Recommendation |")
    md_lines.append("| :--- | :--- | :---: | :--- | :--- |")

    bots_compat = scan.get("ai_engine_compatibility", {})
    if not bots_compat:
        bots_compat = {
            "ChatGPT (GPTBot)": {"allowed": True, "has_qa_schema": s_schema >= 15, "indexed_via_llms": s_llms >= 15},
            "Perplexity AI (PerplexityBot)": {"allowed": True, "has_deep_index": s_llms >= 20, "has_graph": s_schema >= 20},
            "Claude / Anthropic (ClaudeBot)": {"allowed": True, "has_ai_policy": False},
            "Apple Intelligence (Applebot-Extended)": {"allowed": True, "has_app_schema": s_schema >= 10},
            "Google AI Overviews (Google-Extended)": {"allowed": True, "has_linked_data": s_schema > 0},
        }

    for bot_name, info in bots_compat.items():
        allowed = info.get("allowed", False)
        status_badge = "✅ **Allowed**" if allowed else "❌ **Blocked / Restricted**"
        ua = bot_name.split("(")[-1].replace(")", "") if "(" in bot_name else bot_name

        features = []
        for k, v in info.items():
            if k != "allowed" and v:
                features.append(f"`{k.replace('has_', '').replace('_', ' ').title()}`")
        feat_str = ", ".join(features) if features else "None detected"

        rec = "Maintain open access." if allowed else f"Add `User-agent: {ua}` Allow directive in robots.txt."
        md_lines.append(f"| **{bot_name}** | `{ua}` | {status_badge} | {feat_str} | {rec} |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 4. Root Machine Discovery Assets Status
    md_lines.append("## 📁 3. Root Machine Discovery Assets Status")
    md_lines.append("")
    md_lines.append("| Asset Endpoint | Purpose & Spec Standard | Status | HTTP Code |")
    md_lines.append("| :--- | :--- | :---: | :---: |")

    root_assets = scan.get("root_assets", {})
    asset_meta = [
        ("robots.txt", "Robots Exclusion & AI Bot Directives", root_assets.get("robots_txt", {})),
        ("llms.txt", "Curated LLM Documentation Index (llmstxt.org)", root_assets.get("llms_txt", {})),
        ("llms-full.txt", "Comprehensive Full-Text Knowledge Corpus", root_assets.get("llms_full_txt", {})),
        ("ai.txt", "Canonical AI Citation & Licensing Policy", root_assets.get("ai_txt", {})),
        ("sitemap.xml", "XML Search & Discovery Index", root_assets.get("sitemap_xml", {})),
        ("schema-graph.json", "Standalone JSON-LD Entity Graph", root_assets.get("schema_graph_json", {})),
    ]

    for filename, purpose, ast in asset_meta:
        ex = ast.get("exists", False)
        code = ast.get("status", 200 if ex else 404)
        st_icon = "✅ **Present**" if ex else f"❌ **Missing**"
        md_lines.append(f"| `/{filename}` | {purpose} | {st_icon} | `{code}` |")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 5. Schema.org Knowledge Graph & Entity Structure
    md_lines.append("## 🧠 4. Schema.org Knowledge Graph & Entity Structure")
    md_lines.append("")
    md_lines.append("Answer Engines (Google AI Overviews, Perplexity, ChatGPT) require connected `@graph` entity nodes to construct knowledge authority:")
    md_lines.append("")
    md_lines.append("```mermaid")
    md_lines.append("flowchart TD")
    md_lines.append('    Org["Organization (#org)"] -->|publisher| Site["WebSite (#site)"]')
    md_lines.append('    Site -->|hasPart| App["SoftwareApplication / Service (#app)"]')
    md_lines.append('    Site -->|mainEntity| FAQ["FAQPage (#faq)"]')
    md_lines.append('    Org -->|sameAs| Socials["Authoritative Social Profiles"]')
    md_lines.append("```")
    md_lines.append("")

    # List schemas found across pages
    all_schemas = []
    for p in pages:
        for s in p.get("schemas", []):
            all_schemas.append(s)

    if all_schemas:
        md_lines.append(f"**Discovered Structured Data Entities ({len(all_schemas)} schema blocks detected):**")
        for idx, s in enumerate(all_schemas[:5], 1):
            stype = s.get("@type", "Unknown") if isinstance(s, dict) else "JSON-LD Object"
            md_lines.append(f"- `[{idx}]` **Schema Type:** `{stype}`")
    else:
        md_lines.append("> ⚠️ **No Schema.org JSON-LD found in audited pages.** Injection of `@graph` metadata is strongly recommended.")

    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # 6. Prioritized Action Items
    md_lines.append("## 🚨 5. Prioritized Action Items & Remediation Roadmap")
    md_lines.append("")

    action_items = scan.get("action_items", [])
    if not action_items:
        action_items = [
            {
                "priority": "CRITICAL" if s_schema < 15 else "MEDIUM",
                "category": "Knowledge Graph",
                "issue": "Upgrade schema to full connected @graph JSON-LD",
                "fix": "Inject Organization, WebSite, SoftwareApplication, and FAQPage schemas into your HTML <head>.",
            },
            {
                "priority": "HIGH" if s_llms < 15 else "LOW",
                "category": "Machine Discovery",
                "issue": "Publish standardized /llms.txt and /llms-full.txt endpoints",
                "fix": "Place llms.txt at root directory following the llmstxt.org specification for rapid LLM indexing.",
            },
            {
                "priority": "HIGH" if s_bots < 15 else "LOW",
                "category": "Crawler Policies",
                "issue": "Explicitly permit AI Search crawlers in robots.txt",
                "fix": "Add Allow directives for GPTBot, PerplexityBot, ClaudeBot, and Applebot.",
            },
        ]

    for item in action_items:
        prio = item.get("priority", "MEDIUM")
        icon = "🔴" if prio == "CRITICAL" else ("🟠" if prio == "HIGH" else "🔵")
        md_lines.append(f"### {icon} [{prio}] {item.get('category', 'General')}: {item.get('issue', 'Issue')}")
        md_lines.append(f"- **Recommended Fix:** {item.get('fix', 'Apply recommended standard updates.')}")
        md_lines.append("")

    md_lines.append("---")
    md_lines.append("")

    # 7. Competitive Benchmark Section (if provided)
    if bench:
        md_lines.append("## ⚔️ 6. Competitive Benchmark & Head-to-Head Analysis")
        md_lines.append("")
        site_a_url = bench.get("site_a", {}).get("url", target_url)
        site_b_url = bench.get("site_b", {}).get("url", "Competitor Site")
        summary = bench.get("summary", {})
        score_a = summary.get("score_a", overall_score)
        score_b = summary.get("score_b", 0.0)
        delta = summary.get("score_delta", round(score_a - score_b, 1))
        winner = summary.get("overall_winner", "tie")

        winner_display = f"🏆 **Site A ({site_a_url})**" if winner == "site_a" else (
            f"🏆 **Competitor ({site_b_url})**" if winner == "site_b" else "🤝 **Tie**"
        )

        md_lines.append(f"> **Overall Winner:** {winner_display}  ")
        md_lines.append(f"> **Score Delta:** `{'+' if delta > 0 else ''}{delta:.1f} pts`  ")
        md_lines.append(f"> **Takeaway:** {summary.get('lead_description', '')}")
        md_lines.append("")

        # Side by side category comparison table
        md_lines.append("### 📊 Head-to-Head Category Scores")
        md_lines.append("")
        md_lines.append(f"| Category | Your Site (`{site_a_url}`) | Competitor (`{site_b_url}`) | Delta | Category Winner |")
        md_lines.append("| :--- | :---: | :---: | :---: | :---: |")

        b_cat = bench.get("category_scores", {})
        for cat_k, cat_v in b_cat.items():
            name = cat_k.replace("_", " ").title()
            sa = cat_v.get("score_a", 0.0)
            sb = cat_v.get("score_b", 0.0)
            d = cat_v.get("delta", 0.0)
            w = cat_v.get("winner", "tie")
            w_badge = "🏆 **You Lead**" if w == "site_a" else ("⚠️ **Competitor Leads**" if w == "site_b" else "🤝 Tie")
            md_lines.append(f"| **{name}** | `{sa:.1f}` | `{sb:.1f}` | `{'+' if d > 0 else ''}{d:.1f}` | {w_badge} |")

        md_lines.append(f"| **OVERALL AEO SCORE** | **`{score_a:.1f}`** | **`{score_b:.1f}`** | **`{'+' if delta > 0 else ''}{delta:.1f}`** | {winner_display} |")
        md_lines.append("")

        # Schema & Entity Comparison
        schema_comp = bench.get("schema_comparison", {})
        md_lines.append("### 🧩 Entity & Schema Types Gap Analysis")
        md_lines.append("")
        md_lines.append(f"- **Shared Schema Types:** {', '.join(f'`{t}`' for t in schema_comp.get('shared_types', [])) or 'None'}")
        md_lines.append(f"- **Unique to Your Site:** {', '.join(f'`{t}`' for t in schema_comp.get('unique_to_a', [])) or 'None'}")
        md_lines.append(f"- **Competitor Schema Types You Lack:** {', '.join(f'🔴 `{t}`' for t in schema_comp.get('missing_in_a', [])) or '✅ None (Full Parity)'}")
        md_lines.append("")

        # Bot Accessibility Delta
        bot_comp = bench.get("bot_matrix_comparison", {})
        md_lines.append("### 🤖 Bot Accessibility Delta")
        md_lines.append("")
        md_lines.append(f"| Bot / AI Engine | Your Site | Competitor | Competitive Advantage |")
        md_lines.append("| :--- | :---: | :---: | :--- |")
        for b_row in bot_comp.get("bots", []):
            b_name = b_row.get("bot_name", "")
            st_a = "✅ Allowed" if b_row.get("site_a_allowed") else "❌ Blocked"
            st_b = "✅ Allowed" if b_row.get("site_b_allowed") else "❌ Blocked"
            adv = b_row.get("advantage", "equal")
            adv_str = "🏆 **Your Advantage**" if adv == "site_a" else ("⚠️ **Competitor Advantage**" if adv == "site_b" else "🤝 Equal")
            md_lines.append(f"| **{b_name}** | {st_a} | {st_b} | {adv_str} |")

        md_lines.append("")

        # Strategic Takeaways
        takeaways = bench.get("takeaways", [])
        if takeaways:
            md_lines.append("### 🎯 Concrete Strategic Takeaways to Outperform Competitor")
            md_lines.append("")
            for t in takeaways:
                prio = t.get("priority", "HIGH")
                icon = "🔥" if prio == "CRITICAL" else ("⚡" if prio == "HIGH" else "📌")
                md_lines.append(f"#### {icon} [{prio}] {t.get('category', '')}: {t.get('competitor_advantage', '')}")
                md_lines.append(f"- **Action Required:** {t.get('action', '')}")
                md_lines.append(f"- **Strategic Impact:** `{t.get('impact', '')}`")
                md_lines.append("")

        md_lines.append("---")
        md_lines.append("")

    # 8. High-Authority AI Distribution & Citation Targets
    strategy = scan.get("backlink_and_distribution_intelligence", {})
    if strategy:
        md_lines.append("## 🔗 7. High-Authority AI Distribution & Citation Targets")
        md_lines.append("")
        md_lines.append("To ensure continuous citation retrieval in ChatGPT, Perplexity, and Claude, seed authoritative entity references across key hubs:")
        md_lines.append("")
        for hub in strategy.get("high_authority_citation_hubs", []):
            md_lines.append(f"- **{hub.get('platform', '')}** (`{hub.get('role', '')}`): {hub.get('action', '')}")

        if strategy.get("vertical_specific_distribution"):
            md_lines.append("")
            md_lines.append("**Vertical-Specific Channels:**")
            for ch in strategy.get("vertical_specific_distribution", []):
                md_lines.append(f"- **{ch.get('platform', '')}**: {ch.get('action', '')}")

        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # 9. Framework Remediation & Implementation Guide
    md_lines.append("## 🛠️ 8. Framework Remediation & Copy-Paste Code")
    md_lines.append("")
    md_lines.append("Apply these pre-generated, production-ready code fixes to achieve 100% AEO readiness:")
    md_lines.append("")

    # Next.js App Router
    next_bundle = exporter.export_nextjs_app()
    md_lines.append("### [A] Next.js App Router (`app/layout.tsx` & `app/robots.ts`)")
    md_lines.append("")
    md_lines.append("```tsx")
    md_lines.append(f"// FILE: app/layout.tsx\n{next_bundle.get('app/layout.tsx', '')[:1000]}...")
    md_lines.append("```")
    md_lines.append("")

    # HTML <head> snippet
    md_lines.append("### [B] Static HTML / Universal `<head>` Schema Injection")
    md_lines.append("")
    md_lines.append("```html")
    md_lines.append(f"""<!-- Insert into <head> of your pages -->
<script type="application/ld+json">
{json.dumps(exporter.schema_graph, indent=2, ensure_ascii=False)}
</script>""")
    md_lines.append("```")
    md_lines.append("")

    # llms.txt snippet
    md_lines.append("### [C] Standard `llms.txt` Manifest (Save to `public/llms.txt`)")
    md_lines.append("")
    md_lines.append("```markdown")
    md_lines.append(exporter.llms_txt.strip())
    md_lines.append("```")
    md_lines.append("")

    # robots.txt snippet
    md_lines.append("### [D] AI-Optimized `robots.txt` (Save to `public/robots.txt`)")
    md_lines.append("")
    md_lines.append("```txt")
    md_lines.append(exporter.robots_txt.strip())
    md_lines.append("```")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("*Generated automatically by [AEO Graph Engine](https://github.com/1nc0gn30/aeo-graph-engine) — The Autonomous Answer Engine Optimization Toolkit.*")

    return "\n".join(md_lines)


def _render_svg_dial(score: float, size: int = 160, stroke_width: int = 12, label: str = "AEO SCORE") -> str:
    """Renders a crisp, responsive SVG circular score gauge with dynamic color and dashoffset."""
    radius = (size - stroke_width) / 2
    circumference = 2 * 3.141592653589793 * radius
    pct = max(0.0, min(1.0, score / 100.0))
    offset = circumference * (1.0 - pct)

    if score >= 85:
        stroke_color = "#10b981" # emerald
        bg_glow = "rgba(16, 185, 129, 0.2)"
    elif score >= 70:
        stroke_color = "#3b82f6" # blue
        bg_glow = "rgba(59, 130, 246, 0.2)"
    elif score >= 50:
        stroke_color = "#f59e0b" # amber
        bg_glow = "rgba(245, 158, 11, 0.2)"
    else:
        stroke_color = "#ef4444" # red
        bg_glow = "rgba(239, 68, 68, 0.2)"

    return f"""
    <div class="svg-dial-container" style="width: {size}px; height: {size}px;">
      <svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" class="score-dial">
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="var(--border-color)" stroke-width="{stroke_width}" opacity="0.4" />
        <circle cx="{size/2}" cy="{size/2}" r="{radius}" fill="none" stroke="{stroke_color}" stroke-width="{stroke_width}"
                stroke-dasharray="{circumference:.2f}" stroke-dashoffset="{offset:.2f}"
                stroke-linecap="round" transform="rotate(-90 {size/2} {size/2})"
                style="filter: drop-shadow(0 0 8px {bg_glow}); transition: stroke-dashoffset 1s ease-in-out;" />
      </svg>
      <div class="score-dial-text">
        <div class="score-value" style="color: {stroke_color};">{score:.1f}</div>
        <div class="score-max">/ 100</div>
        <div class="score-label">{html.escape(label)}</div>
      </div>
    </div>
    """


def generate_standalone_html_report(
    scan_result: Dict[str, Any],
    benchmark_result: Optional[Dict[str, Any]] = None
) -> str:
    """
    Generates a single-file, zero-dependency, dark/light print-friendly HTML report.

    Includes SVG score dials, interactive bot matrix, entity graph visualizer,
    prioritized action cards, tabbed framework remediation code blocks, and competitor benchmark.
    """
    scan, bench = _normalize_inputs(scan_result, benchmark_result)

    target_url = scan.get("target_url", "https://example.com")
    overall_score = float(scan.get("overall_aeo_score", 0.0))
    status = scan.get("status", "NEEDS_OPTIMIZATION")
    date_str = datetime.date.today().isoformat()
    grade, _, _ = _get_grade(overall_score)

    pages = scan.get("pages", [])
    pages_count = len(pages) if pages else int(scan.get("pages_audited_count", 1))

    # Category scores
    cat_scores = scan.get("category_scores", {})
    categories_list = [
        ("schema_linked_data", "Schema.org Linked Data", cat_scores.get("schema_linked_data", {}), 25.0),
        ("llms_txt_machine_index", "Machine Index (llms.txt)", cat_scores.get("llms_txt_machine_index", {}), 25.0),
        ("ai_crawler_governance", "AI Search Crawler Governance", cat_scores.get("ai_crawler_governance", {}), 20.0),
        ("semantic_content_grounding", "Semantic Content & Grounding", cat_scores.get("semantic_content_grounding", {}), 15.0),
        ("technical_seo_foundation", "Technical SEO Foundation", cat_scores.get("technical_seo_foundation", {}), 15.0),
    ]

    # Exporter for code blocks
    site_name = ""
    description = ""
    for p in pages:
        if p.get("title") and not site_name:
            site_name = p.get("title")
        if p.get("description") and not description:
            description = p.get("description")
    if not site_name:
        site_name = target_url.replace("https://", "").replace("http://", "").split("/")[0]

    exporter = FrameworkExporter({
        "site_name": site_name,
        "base_url": target_url,
        "description": description or f"Official platform documentation and services for {site_name}.",
    })

    next_bundle = exporter.export_nextjs_app()
    astro_bundle = exporter.export_astro()
    vite_bundle = exporter.export_vite_react()

    # Build HTML sections
    html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AEO Audit Report — {html.escape(target_url)}</title>
  <style>
    :root {{
      --bg: #090d16;
      --card-bg: #111827;
      --card-border: #1f2937;
      --text-main: #f9fafb;
      --text-muted: #9ca3af;
      --accent: #3b82f6;
      --accent-hover: #2563eb;
      --success: #10b981;
      --warning: #f59e0b;
      --danger: #ef4444;
      --border-color: #374151;
      --code-bg: #030712;
      --badge-bg: rgba(59, 130, 246, 0.15);
      --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }}

    [data-theme="light"] {{
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --card-border: #e2e8f0;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --accent: #2563eb;
      --accent-hover: #1d4ed8;
      --border-color: #cbd5e1;
      --code-bg: #0f172a;
      --badge-bg: #e0e7ff;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background-color: var(--bg);
      color: var(--text-main);
      font-family: var(--font-family);
      line-height: 1.6;
      padding: 32px 16px;
      transition: background-color 0.2s ease, color 0.2s ease;
    }}

    .container {{
      max-width: 1180px;
      margin: 0 auto;
    }}

    header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 16px;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 1px solid var(--card-border);
    }}

    .header-title h1 {{
      font-size: 1.85rem;
      font-weight: 800;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 10px;
    }}

    .header-title .subtitle {{
      color: var(--text-muted);
      font-size: 0.95rem;
      margin-top: 4px;
    }}

    .header-actions {{
      display: flex;
      gap: 12px;
      align-items: center;
    }}

    .btn {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-main);
      padding: 8px 16px;
      border-radius: 8px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: all 0.15s ease;
    }}
    .btn:hover {{
      border-color: var(--accent);
      color: var(--accent);
    }}
    .btn-primary {{
      background: var(--accent);
      border-color: var(--accent);
      color: #ffffff !important;
    }}
    .btn-primary:hover {{
      background: var(--accent-hover);
    }}

    /* Grid & Cards */
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }}

    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 16px;
      margin-bottom: 24px;
    }}

    .card {{
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }}

    .card-title {{
      font-size: 1.15rem;
      font-weight: 700;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}

    /* Score Dial */
    .hero-score-card {{
      display: flex;
      align-items: center;
      justify-content: space-around;
      flex-wrap: wrap;
      gap: 24px;
      padding: 32px;
      background: linear-gradient(135deg, var(--card-bg) 0%, rgba(59, 130, 246, 0.05) 100%);
    }}

    .svg-dial-container {{
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
    }}

    .score-dial-text {{
      position: absolute;
      text-align: center;
    }}

    .score-value {{
      font-size: 2.2rem;
      font-weight: 800;
      line-height: 1;
    }}

    .score-max {{
      font-size: 0.8rem;
      color: var(--text-muted);
      font-weight: 600;
    }}

    .score-label {{
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-top: 4px;
      color: var(--text-muted);
    }}

    /* Progress bars */
    .cat-bar-row {{
      margin-bottom: 14px;
    }}
    .cat-bar-header {{
      display: flex;
      justify-content: space-between;
      font-size: 0.875rem;
      margin-bottom: 4px;
    }}
    .progress-track {{
      background: var(--border-color);
      height: 8px;
      border-radius: 4px;
      overflow: hidden;
    }}
    .progress-fill {{
      height: 100%;
      border-radius: 4px;
      transition: width 0.8s ease-in-out;
    }}

    /* Tables */
    .table-container {{
      overflow-x: auto;
      margin-top: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }}
    th, td {{
      padding: 12px 16px;
      border-bottom: 1px solid var(--card-border);
    }}
    th {{
      background: rgba(0, 0, 0, 0.15);
      color: var(--text-muted);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 0.75rem;
      letter-spacing: 0.05em;
    }}
    tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}

    /* Badges */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 4px 8px;
      border-radius: 6px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .badge-success {{ background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .badge-warning {{ background: rgba(245, 158, 11, 0.15); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); }}
    .badge-danger {{ background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .badge-info {{ background: rgba(59, 130, 246, 0.15); color: #3b82f6; border: 1px solid rgba(59, 130, 246, 0.3); }}

    /* Priority Action Cards */
    .action-card {{
      padding: 16px;
      border-radius: 8px;
      margin-bottom: 12px;
      border-left: 4px solid var(--accent);
      background: rgba(0, 0, 0, 0.1);
    }}
    .action-card.CRITICAL {{ border-left-color: var(--danger); }}
    .action-card.HIGH {{ border-left-color: var(--warning); }}
    .action-card.MEDIUM {{ border-left-color: var(--accent); }}
    .action-card.LOW {{ border-left-color: var(--success); }}

    /* Code Blocks */
    .code-block-wrapper {{
      position: relative;
      background: var(--code-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      margin-top: 12px;
      overflow: hidden;
    }}
    .code-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 16px;
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid var(--card-border);
      font-family: monospace;
      font-size: 0.8rem;
      color: var(--text-muted);
    }}
    pre {{
      padding: 16px;
      overflow-x: auto;
      font-family: "JetBrains Mono", Consolas, Monaco, "Courier New", monospace;
      font-size: 0.85rem;
      color: #e5e7eb;
      line-height: 1.5;
    }}

    /* Tabs */
    .tabs-nav {{
      display: flex;
      gap: 8px;
      border-bottom: 1px solid var(--card-border);
      margin-bottom: 16px;
      overflow-x: auto;
    }}
    .tab-btn {{
      background: none;
      border: none;
      color: var(--text-muted);
      padding: 10px 16px;
      font-size: 0.875rem;
      font-weight: 600;
      cursor: pointer;
      border-bottom: 2px solid transparent;
      white-space: nowrap;
    }}
    .tab-btn.active {{
      color: var(--accent);
      border-bottom-color: var(--accent);
    }}
    .tab-pane {{
      display: none;
    }}
    .tab-pane.active {{
      display: block;
    }}

    /* Print styles */
    @media print {{
      body {{ background: #ffffff !important; color: #000000 !important; padding: 0; }}
      .card {{ border: 1px solid #cccccc !important; box-shadow: none !important; break-inside: avoid; }}
      .header-actions, .tabs-nav, .btn {{ display: none !important; }}
      .tab-pane {{ display: block !important; margin-bottom: 20px; }}
      pre {{ background: #f3f4f6 !important; color: #111827 !important; border: 1px solid #e5e7eb; }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="header-title">
        <h1><span>🌐</span> AEO & AI Search Readiness Audit</h1>
        <div class="subtitle">Audited Target: <strong>{html.escape(target_url)}</strong> &bull; Date: {html.escape(date_str)} &bull; AEO Graph Engine v1.0.0</div>
      </div>
      <div class="header-actions">
        <button class="btn" onclick="toggleTheme()">🌓 Toggle Theme</button>
        <button class="btn btn-primary" onclick="window.print()">🖨️ Print / Save PDF</button>
      </div>
    </header>

    <!-- Hero Scorecard -->
    <div class="card hero-score-card" style="margin-bottom: 24px;">
      {_render_svg_dial(overall_score, size=180, stroke_width=14, label="Overall AEO Score")}
      <div style="flex: 1; min-width: 280px; max-width: 600px;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
          <span class="badge badge-{'success' if overall_score >= 80 else 'warning' if overall_score >= 60 else 'danger'}" style="font-size: 0.95rem; padding: 6px 12px;">
            Grade: {grade} &bull; {html.escape(status)}
          </span>
          <span style="color: var(--text-muted); font-size: 0.85rem;">({pages_count} page{'s' if pages_count != 1 else ''} audited)</span>
        </div>
        <p style="color: var(--text-muted); font-size: 0.9rem; margin-bottom: 16px;">
          Measures authority, machine discoverability via <code>llms.txt</code>, Schema.org <code>@graph</code> depth, and AI crawler permissions for ChatGPT, Perplexity, Claude, Apple Intelligence, and Google AI Overviews.
        </p>
"""

    # Category progress bars
    for cat_key, cat_label, cdata, max_p in categories_list:
        score_val = float(cdata.get("score", 0.0))
        max_val = float(cdata.get("max", max_p))
        fill_pct = min(100.0, max(0.0, (score_val / max(1.0, max_val)) * 100.0))
        bar_color = "var(--success)" if fill_pct >= 75 else ("var(--accent)" if fill_pct >= 50 else ("var(--warning)" if fill_pct >= 30 else "var(--danger)"))

        html_content += f"""
        <div class="cat-bar-row">
          <div class="cat-bar-header">
            <span>{html.escape(cat_label)}</span>
            <strong>{score_val:.1f} / {max_val:.1f}</strong>
          </div>
          <div class="progress-track">
            <div class="progress-fill" style="width: {fill_pct:.1f}%; background: {bar_color};"></div>
          </div>
        </div>
        """

    html_content += """
      </div>
    </div>
    """

    # Optional Benchmark Side-by-Side Section
    if bench:
        site_a_url = bench.get("site_a", {}).get("url", target_url)
        site_b_url = bench.get("site_b", {}).get("url", "Competitor")
        summary = bench.get("summary", {})
        b_score_a = summary.get("score_a", overall_score)
        b_score_b = summary.get("score_b", 0.0)
        b_delta = summary.get("score_delta", round(b_score_a - b_score_b, 1))
        b_winner = summary.get("overall_winner", "tie")

        winner_label = f"🏆 Site A Leads (+{b_delta} pts)" if b_delta > 0 else (
            f"⚠️ Competitor Leads ({b_delta} pts)" if b_delta < 0 else "🤝 Dead Heat (Tie)"
        )

        html_content += f"""
        <div class="card" style="margin-bottom: 24px; border: 2px solid {'var(--success)' if b_delta >= 0 else 'var(--warning)'};">
          <div class="card-title" style="justify-content: space-between;">
            <span>⚔️ Competitor Benchmark Comparison</span>
            <span class="badge badge-{'success' if b_delta > 0 else 'warning' if b_delta < 0 else 'info'}" style="font-size: 0.9rem; padding: 6px 12px;">{html.escape(winner_label)}</span>
          </div>
          <div class="grid-2" style="align-items: center; margin-top: 16px;">
            <div style="display: flex; align-items: center; justify-content: space-around; gap: 16px;">
              <div style="text-align: center;">
                <div style="font-weight: 700; margin-bottom: 8px; color: var(--accent);">Your Site</div>
                {_render_svg_dial(b_score_a, size=130, stroke_width=10, label="Your Score")}
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">{html.escape(site_a_url)}</div>
              </div>
              <div style="font-size: 1.5rem; font-weight: 800; color: var(--text-muted);">VS</div>
              <div style="text-align: center;">
                <div style="font-weight: 700; margin-bottom: 8px; color: var(--text-muted);">Competitor</div>
                {_render_svg_dial(b_score_b, size=130, stroke_width=10, label="Comp Score")}
                <div style="font-size: 0.8rem; color: var(--text-muted); margin-top: 6px;">{html.escape(site_b_url)}</div>
              </div>
            </div>
            <div>
              <div class="table-container">
                <table>
                  <thead>
                    <tr>
                      <th>Category</th>
                      <th>You</th>
                      <th>Comp</th>
                      <th>Delta</th>
                      <th>Winner</th>
                    </tr>
                  </thead>
                  <tbody>
        """

        for cat_k, cat_v in bench.get("category_scores", {}).items():
            name = cat_k.replace("_", " ").title()
            sa = cat_v.get("score_a", 0.0)
            sb = cat_v.get("score_b", 0.0)
            d = cat_v.get("delta", 0.0)
            w = cat_v.get("winner", "tie")
            w_chip = "<span class='badge badge-success'>You</span>" if w == "site_a" else ("<span class='badge badge-warning'>Comp</span>" if w == "site_b" else "<span class='badge badge-info'>Tie</span>")
            html_content += f"""
                    <tr>
                      <td><strong>{html.escape(name)}</strong></td>
                      <td>{sa:.1f}</td>
                      <td>{sb:.1f}</td>
                      <td style="color: {'var(--success)' if d > 0 else 'var(--danger)' if d < 0 else 'var(--text-muted)'}; font-weight: 700;">{'+' if d > 0 else ''}{d:.1f}</td>
                      <td>{w_chip}</td>
                    </tr>
            """

        html_content += """
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        """

        # Strategic takeaways list
        takeaways = bench.get("takeaways", [])
        if takeaways:
            html_content += """
            <div style="margin-top: 20px;">
              <h4 style="font-size: 1rem; margin-bottom: 12px;">🎯 Key Strategic Gaps to Beat Competitor</h4>
            """
            for t in takeaways:
                prio = t.get("priority", "HIGH")
                html_content += f"""
                <div class="action-card {html.escape(prio)}">
                  <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <strong>[{html.escape(prio)}] {html.escape(t.get('category', ''))}</strong>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">{html.escape(t.get('impact', ''))}</span>
                  </div>
                  <div style="font-size: 0.875rem; color: var(--text-muted); margin-bottom: 6px;">{html.escape(t.get('competitor_advantage', ''))}</div>
                  <div style="font-size: 0.9rem;"><strong>Action:</strong> {html.escape(t.get('action', ''))}</div>
                </div>
                """
            html_content += "</div>"

        html_content += "</div>"

    # AI Bot Matrix & Machine Manifests in Grid
    html_content += f"""
    <div class="grid-2">
      <!-- AI Search Bot Matrix -->
      <div class="card">
        <div class="card-title">🤖 AI Search Crawler Access Matrix</div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Engine / Bot</th>
                <th>Status</th>
                <th>Features Supported</th>
              </tr>
            </thead>
            <tbody>
    """

    bots_compat = scan.get("ai_engine_compatibility", {})
    if not bots_compat:
        bots_compat = {
            "ChatGPT (GPTBot)": {"allowed": True, "has_qa_schema": True},
            "Perplexity AI (PerplexityBot)": {"allowed": True, "has_graph": True},
            "Claude (ClaudeBot)": {"allowed": True, "has_ai_policy": False},
            "Apple Intelligence (Applebot)": {"allowed": True, "has_app_schema": True},
            "Google AI Overviews": {"allowed": True, "has_linked_data": True},
        }

    for bname, binfo in bots_compat.items():
        allowed = binfo.get("allowed", False)
        st_chip = "<span class='badge badge-success'>Allowed</span>" if allowed else "<span class='badge badge-danger'>Blocked</span>"
        feats = [k.replace("has_", "").replace("_", " ").title() for k, v in binfo.items() if k != "allowed" and v]
        feats_str = ", ".join(feats) if feats else "Standard index"
        html_content += f"""
              <tr>
                <td><strong>{html.escape(bname)}</strong></td>
                <td>{st_chip}</td>
                <td><span style="font-size: 0.85rem; color: var(--text-muted);">{html.escape(feats_str)}</span></td>
              </tr>
        """

    html_content += f"""
            </tbody>
          </table>
        </div>
      </div>

      <!-- Root Machine Discovery Assets -->
      <div class="card">
        <div class="card-title">📁 Root Machine Discovery Files</div>
        <div class="table-container">
          <table>
            <thead>
              <tr>
                <th>Endpoint</th>
                <th>Standard</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
    """

    root_assets = scan.get("root_assets", {})
    for ep, label in [
        ("robots.txt", "Robots & AI Directives"),
        ("llms.txt", "LLM Index (llmstxt.org)"),
        ("llms-full.txt", "Deep Knowledge Corpus"),
        ("ai.txt", "AI Citation Policy"),
        ("sitemap.xml", "XML Sitemap Index"),
        ("schema-graph.json", "Linked Data Graph"),
    ]:
        ast = root_assets.get(ep.replace(".", "_"), {})
        ex = ast.get("exists", False)
        chip = "<span class='badge badge-success'>Present</span>" if ex else "<span class='badge badge-danger'>Missing</span>"
        html_content += f"""
              <tr>
                <td><code>/{html.escape(ep)}</code></td>
                <td>{html.escape(label)}</td>
                <td>{chip}</td>
              </tr>
        """

    html_content += f"""
            </tbody>
          </table>
        </div>
      </div>
    </div>
    """

    # Action Items
    action_items = scan.get("action_items", [])
    if action_items:
        html_content += """
        <div class="card" style="margin-bottom: 24px;">
          <div class="card-title">🚨 Prioritized Remediation Action Items</div>
        """
        for item in action_items:
            prio = item.get("priority", "MEDIUM")
            html_content += f"""
            <div class="action-card {html.escape(prio)}">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                <strong>[{html.escape(prio)}] {html.escape(item.get('category', ''))}</strong>
                <span class="badge badge-{'danger' if prio == 'CRITICAL' else 'warning' if prio == 'HIGH' else 'info'}">{html.escape(prio)}</span>
              </div>
              <div style="font-size: 0.9rem; margin-bottom: 6px;"><strong>Issue:</strong> {html.escape(item.get('issue', ''))}</div>
              <div style="font-size: 0.875rem; color: var(--text-muted);"><strong>Fix:</strong> {html.escape(item.get('fix', ''))}</div>
            </div>
            """
        html_content += "</div>"

    # Tabbed Framework Code Blocks
    html_content += f"""
    <div class="card" style="margin-bottom: 24px;">
      <div class="card-title">🛠️ Copy-Paste Framework Remediation Code</div>
      <div class="tabs-nav">
        <button class="tab-btn active" onclick="switchTab(event, 'tab-nextjs')">Next.js App Router</button>
        <button class="tab-btn" onclick="switchTab(event, 'tab-html')">Universal HTML &lt;head&gt;</button>
        <button class="tab-btn" onclick="switchTab(event, 'tab-astro')">Astro</button>
        <button class="tab-btn" onclick="switchTab(event, 'tab-vite')">Vite / React</button>
        <button class="tab-btn" onclick="switchTab(event, 'tab-llms')">llms.txt</button>
        <button class="tab-btn" onclick="switchTab(event, 'tab-robots')">robots.txt</button>
      </div>

      <!-- Tab Next.js -->
      <div id="tab-nextjs" class="tab-pane active">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>app/layout.tsx</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>{html.escape(next_bundle.get("app/layout.tsx", ""))}</code></pre>
        </div>
      </div>

      <!-- Tab HTML -->
      <div id="tab-html" class="tab-pane">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>index.html &lt;head&gt;</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>&lt;!-- Insert into &lt;head&gt; of your HTML --&gt;
&lt;script type="application/ld+json"&gt;
{html.escape(json.dumps(exporter.schema_graph, indent=2, ensure_ascii=False))}
&lt;/script&gt;</code></pre>
        </div>
      </div>

      <!-- Tab Astro -->
      <div id="tab-astro" class="tab-pane">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>src/components/AeoHead.astro</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>{html.escape(astro_bundle.get("src/components/AeoHead.astro", ""))}</code></pre>
        </div>
      </div>

      <!-- Tab Vite -->
      <div id="tab-vite" class="tab-pane">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>index.html (Vite)</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>{html.escape(vite_bundle.get("index.html", ""))}</code></pre>
        </div>
      </div>

      <!-- Tab llms.txt -->
      <div id="tab-llms" class="tab-pane">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>public/llms.txt</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>{html.escape(exporter.llms_txt)}</code></pre>
        </div>
      </div>

      <!-- Tab robots.txt -->
      <div id="tab-robots" class="tab-pane">
        <div class="code-block-wrapper">
          <div class="code-header">
            <span>public/robots.txt</span>
            <button class="btn" style="padding: 2px 8px; font-size: 0.75rem;" onclick="copyCode(this)">Copy Code</button>
          </div>
          <pre><code>{html.escape(exporter.robots_txt)}</code></pre>
        </div>
      </div>
    </div>

    <footer style="text-align: center; color: var(--text-muted); font-size: 0.85rem; margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--card-border);">
      Generated automatically by <strong>AEO Graph Engine</strong> &bull; Zero external dependencies &bull; 2026 Generative Search Standard
    </footer>
  </div>

  <script>
    function toggleTheme() {{
      const html = document.documentElement;
      const current = html.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      html.setAttribute('data-theme', next);
    }}

    function switchTab(event, tabId) {{
      document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
      document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
      event.currentTarget.classList.add('active');
      const target = document.getElementById(tabId);
      if (target) target.classList.add('active');
    }}

    function copyCode(btn) {{
      const code = btn.closest('.code-block-wrapper').querySelector('pre code').innerText;
      navigator.clipboard.writeText(code).then(() => {{
        const originalText = btn.innerText;
        btn.innerText = 'Copied!';
        btn.style.color = '#10b981';
        setTimeout(() => {{
          btn.innerText = originalText;
          btn.style.color = '';
        }}, 2000);
      }});
    }}
  </script>
</body>
</html>
"""
    return html_content


def save_report_to_file(content: str, output_path: Union[str, Path]) -> Path:
    """Convenience utility to save generated markdown or HTML reports to disk."""
    out = Path(output_path).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(content, encoding="utf-8")
    return out

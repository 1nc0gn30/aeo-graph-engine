"""
Atomic Claim-Evidence Matrix and Scroll-to-Text Citation Fragment Synthesizer.
Optimizes web content for LLM citation extraction (Perplexity, SearchGPT, Gemini, Claude).
Zero external runtime dependencies (100% Python Standard Library).
"""

from __future__ import annotations

import hashlib
import html
import re
import urllib.parse
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union


class ClaimCategory(str, Enum):
    """Categorization of atomic claims for answer engine grounding."""
    QUANTITATIVE = "quantitative"
    ARCHITECTURAL = "architectural"
    CAPABILITY = "capability"
    COMPARATIVE = "comparative"


# Regex patterns for linguistic and entity classification
RE_METRICS = re.compile(
    r"\b(?:\d+(?:\.\d+)?(?:\s*(?:%|x|ms|s|ns|min|mb|gb|tb|kb|hz|khz|mhz|ghz|qps|tps|tokens?/s|req/s|bytes?|bits?|db))\b|\b\d+(?:,\d{3})*(?:\.\d+)?\b|\bzero\s+(?:dependencies|deps|downtime|config|latency)\b)",
    re.IGNORECASE,
)

RE_HEDGING = re.compile(
    r"\b(?:maybe|perhaps|possibly|probably|might|could|we\s+believe|we\s+think|seems|seemingly|allegedly|supposedly|in\s+theory)\b",
    re.IGNORECASE,
)

RE_ARCHITECTURAL = re.compile(
    r"\b(?:rfc[-\s]?\d+|http[s]?|json-ld|schema\.org|mcp|rest|api|grpc|sqlite|python|postgres|sql|linux|macos|windows|termux|iso[-\s]?\d+|ieee|ansi|jwt|cors|sha[-\s]?256|pbkdf2|aes|hmac)\b",
    re.IGNORECASE,
)

RE_COMPARATIVE = re.compile(
    r"\b(?:than|compared\s+to|versus|vs\.?|better\s+than|faster\s+than|superior|replaces|alternative\s+to|outperforms|exceeds)\b",
    re.IGNORECASE,
)


def _clean_text_from_html(raw_html: str) -> str:
    """Strip HTML tags and convert entities to plain text."""
    # Remove script and style blocks
    cleaned = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
    # Remove all HTML tags
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    # Unescape HTML entities
    cleaned = html.unescape(cleaned)
    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def _split_into_sentences(text: str) -> List[str]:
    """Break raw text or markdown into distinct sentence candidate propositions."""
    # Normalize line breaks and list bullets
    text = re.sub(r"[\r\n]+", "\n", text)
    lines = text.split("\n")
    candidates: List[str] = []

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Strip markdown headers, bullets, or list indices
        line_clean = re.sub(r"^(?:#{1,6}\s+|[-*+]\s+|\d+\.\s+)", "", line_clean)
        # Split on sentence terminals: . ! ? preceded by non-abbreviation
        raw_sents = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'‘“])", line_clean)
        for s in raw_sents:
            s_stripped = s.strip()
            # Must have at least 4 words to be considered an assertion
            if len(s_stripped.split()) >= 4:
                candidates.append(s_stripped)

    return candidates


@dataclass
class AtomicClaim:
    """An individual verifiable atomic claim extracted from content."""
    id: str
    text: str
    category: str
    quotability_score: float
    metrics: List[str]
    hedging_words: List[str]
    quote_hash: str
    text_fragment: str
    word_count: int
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClaimEvidenceMatrix:
    """Matrix of atomic assertions, quotability metrics, and W3C text fragment anchors."""
    url_or_title: str
    total_claims: int
    mean_quotability_score: float
    quotability_grade: str
    claims: List[AtomicClaim]
    category_counts: Dict[str, int]
    quantitative_density: float
    high_quotability_count: int
    schema_org_claim_review: Dict[str, Any]
    actionable_recommendations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "url_or_title": self.url_or_title,
            "total_claims": self.total_claims,
            "mean_quotability_score": round(self.mean_quotability_score, 2),
            "quotability_grade": self.quotability_grade,
            "category_counts": self.category_counts,
            "quantitative_density": round(self.quantitative_density, 4),
            "high_quotability_count": self.high_quotability_count,
            "claims": [c.to_dict() for c in self.claims],
            "schema_org_claim_review": self.schema_org_claim_review,
            "actionable_recommendations": self.actionable_recommendations,
        }

    def to_markdown(self) -> str:
        """Render matrix as rich GitHub-flavored markdown report."""
        lines: List[str] = [
            f"# 🎯 Atomic Claim-Evidence & Citation Matrix: {self.url_or_title}",
            "",
            f"**Overall Quotability Score**: `{self.mean_quotability_score:.1f}/100` (Grade: **{self.quotability_grade}**)",
            f"- **Total Atomic Claims**: `{self.total_claims}`",
            f"- **High-Confidence Quotable Claims (≥75)**: `{self.high_quotability_count}`",
            f"- **Quantitative Claim Density**: `{self.quantitative_density * 100:.1f}%`",
            "",
            "## 📊 Claim Breakdown by Category",
            "",
            "| Category | Count | Distribution |",
            "| :--- | :--- | :--- |",
        ]
        for cat, cnt in self.category_counts.items():
            pct = (cnt / max(1, self.total_claims)) * 100
            lines.append(f"| **{cat.capitalize()}** | `{cnt}` | {pct:.1f}% |")

        lines.extend([
            "",
            "## 🔍 Extracted Atomic Claims & Citation Anchors",
            "",
            "| ID | Score | Category | Claim Statement | Metrics | Fragment Anchor |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for c in self.claims:
            metrics_str = ", ".join(f"`{m}`" for m in c.metrics) if c.metrics else "—"
            frag_snippet = f"`{c.quote_hash}`"
            lines.append(f"| **{c.id}** | `{c.quotability_score:.0f}` | `{c.category}` | {c.text} | {metrics_str} | {frag_snippet} |")

        if self.actionable_recommendations:
            lines.extend([
                "",
                "## 💡 Actionable Recommendations for SearchGPT & Perplexity Grounding",
                "",
            ])
            for rec in self.actionable_recommendations:
                lines.append(f"- {rec}")

        return "\n".join(lines)

    def to_svg(self) -> str:
        """Generate a dark-themed SVG badge and visualization card."""
        width = 800
        height = 480
        score_color = "#34a853" if self.mean_quotability_score >= 80 else ("#fbbc04" if self.mean_quotability_score >= 60 else "#ea4335")

        top_claims = self.claims[:4]
        items_svg = []
        y_pos = 230

        for c in top_claims:
            esc_text = html.escape(c.text[:85] + ("..." if len(c.text) > 85 else ""))
            badge_color = "#4285f4" if c.category == "quantitative" else ("#a142f4" if c.category == "architectural" else "#34a853")
            items_svg.append(f"""
            <g transform="translate(40, {y_pos})">
                <rect width="720" height="48" rx="8" fill="#1e1f20" stroke="#3c4043" stroke-width="1"/>
                <rect x="12" y="14" width="70" height="20" rx="4" fill="{badge_color}" fill-opacity="0.2"/>
                <text x="47" y="28" fill="{badge_color}" font-family="sans-serif" font-size="10" font-weight="600" text-anchor="middle">{c.category.upper()}</text>
                <text x="95" y="28" fill="#e3e3e3" font-family="sans-serif" font-size="12">{esc_text}</text>
                <rect x="640" y="14" width="68" height="20" rx="4" fill="#131314"/>
                <text x="674" y="28" fill="#9aa0a6" font-family="monospace" font-size="10" text-anchor="middle">#{c.quote_hash}</text>
            </g>
            """)
            y_pos += 56

        return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}">
  <style>
    .title {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; font-weight: 700; fill: #ffffff; font-size: 20px; }}
    .subtitle {{ font-family: sans-serif; fill: #9aa0a6; font-size: 13px; }}
    .metric-val {{ font-family: monospace; font-weight: 700; fill: #ffffff; font-size: 28px; }}
    .metric-lbl {{ font-family: sans-serif; fill: #9aa0a6; font-size: 11px; }}
  </style>
  <rect width="{width}" height="{height}" rx="16" fill="#131314" stroke="#28292a" stroke-width="2"/>
  
  <!-- Header -->
  <text x="40" y="48" class="title">🎯 Atomic Claim-Evidence &amp; Citation Matrix</text>
  <text x="40" y="70" class="subtitle">AEO/GEO Answer Engine Grounding • Perplexity &amp; SearchGPT Anchor Readiness</text>

  <!-- Metric Cards -->
  <g transform="translate(40, 95)">
    <!-- Card 1: Quotability Score -->
    <rect width="165" height="95" rx="10" fill="#1e1f20" stroke="#3c4043" stroke-width="1"/>
    <text x="20" y="45" class="metric-val" fill="{score_color}">{self.mean_quotability_score:.0f}<tspan font-size="16" fill="#9aa0a6">/100</tspan></text>
    <text x="20" y="72" class="metric-lbl">QUOTABILITY SCORE ({self.quotability_grade})</text>

    <!-- Card 2: Total Claims -->
    <rect x="185" width="165" height="95" rx="10" fill="#1e1f20" stroke="#3c4043" stroke-width="1"/>
    <text x="205" y="45" class="metric-val">{self.total_claims}</text>
    <text x="205" y="72" class="metric-lbl">ATOMIC PROPOSITIONS</text>

    <!-- Card 3: Quantitative Density -->
    <rect x="370" width="165" height="95" rx="10" fill="#1e1f20" stroke="#3c4043" stroke-width="1"/>
    <text x="390" y="45" class="metric-val">{self.quantitative_density * 100:.0f}%</text>
    <text x="390" y="72" class="metric-lbl">METRIC-GROUNDED CLAIMS</text>

    <!-- Card 4: High Confidence -->
    <rect x="555" width="165" height="95" rx="10" fill="#1e1f20" stroke="#3c4043" stroke-width="1"/>
    <text x="575" y="45" class="metric-val">{self.high_quotability_count}</text>
    <text x="575" y="72" class="metric-lbl">HIGH-CONFIDENCE CITABLE</text>
  </g>

  <!-- Extracted Claims Header -->
  <text x="40" y="218" fill="#e3e3e3" font-family="sans-serif" font-size="13" font-weight="600">Sample Atomic Claims &amp; Canonical Scroll-to-Text Quote Hashes</text>

  <!-- Items -->
  {''.join(items_svg)}
</svg>"""


def analyze_claim_evidence_matrix(
    content: str,
    base_url: str = "https://example.com",
    title: Optional[str] = None
) -> ClaimEvidenceMatrix:
    """
    Extract, evaluate, and synthesize an Atomic Claim-Evidence Matrix from text, markdown, or HTML.
    
    Generates W3C Scroll-to-Text fragments, evaluates LLM quotability scores, and produces
    Schema.org ClaimReview / Statement linked data entities.
    """
    # Auto-detect HTML and clean
    if "<html" in content.lower() or ("<body" in content.lower() and "<div" in content.lower()):
        plain_text = _clean_text_from_html(content)
        # Attempt to extract title from <title> tag
        title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE)
        doc_title = title or (title_match.group(1).strip() if title_match else "Web Content Document")
    else:
        plain_text = content
        doc_title = title or "Technical Specification Document"

    sentence_candidates = _split_into_sentences(plain_text)
    atomic_claims: List[AtomicClaim] = []

    category_counts = {
        ClaimCategory.QUANTITATIVE.value: 0,
        ClaimCategory.ARCHITECTURAL.value: 0,
        ClaimCategory.CAPABILITY.value: 0,
        ClaimCategory.COMPARATIVE.value: 0,
    }

    claim_idx = 1
    for sent in sentence_candidates:
        words = sent.split()
        word_count = len(words)

        # Skip non-assertive questions or trivial fragments
        if sent.endswith("?") or word_count < 5 or word_count > 60:
            continue

        # Extract metrics
        metrics = RE_METRICS.findall(sent)
        hedging = RE_HEDGING.findall(sent)
        has_arch = bool(RE_ARCHITECTURAL.search(sent))
        has_comp = bool(RE_COMPARATIVE.search(sent))

        # Categorize
        if metrics:
            cat = ClaimCategory.QUANTITATIVE.value
        elif has_arch:
            cat = ClaimCategory.ARCHITECTURAL.value
        elif has_comp:
            cat = ClaimCategory.COMPARATIVE.value
        else:
            cat = ClaimCategory.CAPABILITY.value

        category_counts[cat] += 1

        # Calculate Quotability Score (0 - 100)
        # 1. Base score
        score = 50.0

        # 2. Length heuristic (optimal 12-25 words for snippet quotation)
        if 12 <= word_count <= 25:
            score += 20.0
            len_rec = "Optimal concise length for LLM citation ingestion."
        elif 8 <= word_count < 12 or 26 <= word_count <= 35:
            score += 10.0
            len_rec = "Good length; slight refinement could maximize extractability."
        elif word_count < 8:
            score -= 10.0
            len_rec = "Very brief; lacks sufficient context for standalone citation."
        else:
            score -= 15.0
            len_rec = "Excessive length; break into smaller atomic propositions."

        # 3. Metrics bonus (+15)
        if metrics:
            score += 15.0
            metric_rec = f"Strong empirical grounding with metrics: {', '.join(metrics[:2])}."
        else:
            metric_rec = "Consider adding verifiable empirical metrics or numbers."

        # 4. Hedging penalty (-20)
        if hedging:
            score -= 20.0
            hedge_rec = f"Weakened by hedging words ({', '.join(hedging)}). Replace with direct assertions."
        else:
            hedge_rec = "Crisp authoritative phrasing without ambiguous hedging."

        # Clamp score
        score = max(0.0, min(100.0, score))

        # Generate Quote Hash & W3C Text Fragment
        clean_claim_bytes = sent.encode("utf-8")
        quote_hash = hashlib.sha256(clean_claim_bytes).hexdigest()[:8]

        # W3C Scroll-to-Text Fragment
        # Form: #:~:text=first_word...last_word or exact text
        if word_count > 6:
            text_fragment = f"#:~:text={urllib.parse.quote(words[0])},{urllib.parse.quote(words[-1])}"
        else:
            text_fragment = f"#:~:text={urllib.parse.quote(sent)}"

        # Combined recommendation
        rec_parts = [r for r in [hedge_rec if hedging else None, len_rec, metric_rec if not metrics else None] if r]
        recommendation = " ".join(rec_parts) if rec_parts else "High-fidelity quotation anchor ready for AI citation."

        atomic_claims.append(AtomicClaim(
            id=f"CLM-{claim_idx:03d}",
            text=sent,
            category=cat,
            quotability_score=round(score, 1),
            metrics=metrics,
            hedging_words=hedging,
            quote_hash=quote_hash,
            text_fragment=text_fragment,
            word_count=word_count,
            recommendation=recommendation
        ))
        claim_idx += 1

    total_claims = len(atomic_claims)
    if total_claims == 0:
        mean_score = 0.0
        grade = "F"
        quant_density = 0.0
        high_quot_count = 0
    else:
        mean_score = sum(c.quotability_score for c in atomic_claims) / total_claims
        quant_density = category_counts[ClaimCategory.QUANTITATIVE.value] / total_claims
        high_quot_count = sum(1 for c in atomic_claims if c.quotability_score >= 75.0)

        if mean_score >= 85:
            grade = "A+"
        elif mean_score >= 75:
            grade = "A"
        elif mean_score >= 65:
            grade = "B"
        elif mean_score >= 50:
            grade = "C"
        elif mean_score >= 35:
            grade = "D"
        else:
            grade = "F"

    # Actionable recommendations
    actionable_recs: List[str] = []
    if quant_density < 0.25:
        actionable_recs.append("Increase quantitative metric density: LLM search engines (Perplexity/SearchGPT) prefer citing pages with numerical benchmarks, percentages, or speeds.")
    if any(c.hedging_words for c in atomic_claims):
        actionable_recs.append("Eliminate speculative hedging ('might', 'could', 'we believe') in technical capability descriptions to increase answer certainty.")
    if high_quot_count < total_claims // 2:
        actionable_recs.append("Structure core assertions into 15–25 word atomic sentences to optimize for passage extraction and snippet footnotes.")
    if not actionable_recs:
        actionable_recs.append("Content possesses exceptional atomic quotability and quantitative grounding for Perplexity Sonar and SearchGPT.")

    # Synthesize Schema.org ClaimReview / Statement linked data
    schema_claims: List[Dict[str, Any]] = []
    for c in atomic_claims[:10]:  # Top 10 claims in schema
        schema_claims.append({
            "@type": "Statement",
            "@id": f"{base_url.rstrip('/')}/#quote-{c.quote_hash}",
            "name": f"Atomic Assertion {c.id}",
            "text": c.text,
            "category": c.category,
            "url": f"{base_url.rstrip('/')}/{c.text_fragment}",
            "disambiguatingDescription": f"Quotability: {c.quotability_score}/100"
        })

    schema_claim_graph = {
        "@context": "https://schema.org",
        "@type": "WebPage",
        "@id": f"{base_url.rstrip('/')}/#webpage",
        "name": doc_title,
        "url": base_url,
        "hasPart": schema_claims
    }

    return ClaimEvidenceMatrix(
        url_or_title=doc_title,
        total_claims=total_claims,
        mean_quotability_score=mean_score,
        quotability_grade=grade,
        claims=atomic_claims,
        category_counts=category_counts,
        quantitative_density=quant_density,
        high_quotability_count=high_quot_count,
        schema_org_claim_review=schema_claim_graph,
        actionable_recommendations=actionable_recs
    )

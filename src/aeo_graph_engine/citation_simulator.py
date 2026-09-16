"""
AEO AI Citation Simulator & Extractability Engine for AEO Graph Engine.
Simulates how modern Answer Engines (Perplexity, ChatGPT Search, Gemini, Claude, Apple Intelligence)
parse, index, extract, and cite content from web pages.
Zero external runtime dependencies (Python standard library).
"""

import os
import re
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from html.parser import HTMLParser
from typing import Dict, Any, List, Optional, Tuple, Union


class HTMLStructureParser(HTMLParser):
    """
    Zero-dependency HTML structural analyzer.
    Extracts headings (H1-H6), paragraphs, bullet lists, FAQ Q&A blocks,
    tables, code blocks, quote blocks, emphasized terms, and embedded JSON-LD schemas.
    """

    def __init__(self):
        super().__init__()
        self.title: Optional[str] = None
        self.meta_tags: Dict[str, str] = {}
        self.canonical_url: Optional[str] = None

        self.headings: List[Dict[str, Any]] = []
        self.paragraphs: List[Dict[str, Any]] = []
        self.lists: List[Dict[str, Any]] = []
        self.tables: List[Dict[str, Any]] = []
        self.code_blocks: List[Dict[str, Any]] = []
        self.blockquotes: List[Dict[str, Any]] = []
        self.bold_terms: List[str] = []
        self.json_ld_blocks: List[str] = []
        self.faq_blocks: List[Dict[str, str]] = []

        # Internal parser state
        self._current_tag: Optional[str] = None
        self._current_text: List[str] = []
        self._current_attrs: Dict[str, str] = {}
        self._tag_stack: List[str] = []

        # JSON-LD tracking
        self._in_json_ld: bool = False
        self._json_ld_buffer: List[str] = []

        # List tracking
        self._in_list: bool = False
        self._current_list_type: Optional[str] = None
        self._current_list_items: List[str] = []
        self._current_li_text: List[str] = []

        # Table tracking
        self._in_table: bool = False
        self._table_headers: List[str] = []
        self._table_rows: List[List[str]] = []
        self._current_row: List[str] = []
        self._current_cell_text: List[str] = []
        self._in_th: bool = False
        self._in_td: bool = False

        # Code block tracking
        self._in_pre: bool = False
        self._in_code: bool = False
        self._pre_buffer: List[str] = []
        self._code_lang: str = "text"

        # Blockquote tracking
        self._in_blockquote: bool = False
        self._blockquote_buffer: List[str] = []

        # FAQ Q&A tracking (details/summary, dt/dd)
        self._in_summary: bool = False
        self._summary_text: List[str] = []
        self._in_details: bool = False
        self._details_body: List[str] = []
        self._in_dt: bool = False
        self._dt_text: List[str] = []
        self._in_dd: bool = False
        self._dd_text: List[str] = []

        # Text stream
        self._full_text_buffer: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        tag_lower = tag.lower()
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        self._tag_stack.append(tag_lower)

        if tag_lower == "title":
            self._current_tag = "title"
            self._current_text = []
        elif tag_lower == "link":
            rel = attr_dict.get("rel", "").lower()
            if rel == "canonical" and "href" in attr_dict:
                self.canonical_url = attr_dict["href"]
        elif tag_lower == "meta":
            name = attr_dict.get("name") or attr_dict.get("property")
            content = attr_dict.get("content")
            if name and content:
                self.meta_tags[name.lower()] = content
        elif tag_lower == "script":
            script_type = attr_dict.get("type", "").lower()
            if script_type == "application/ld+json":
                self._in_json_ld = True
                self._json_ld_buffer = []
        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._current_tag = tag_lower
            self._current_text = []
        elif tag_lower == "p":
            self._current_tag = "p"
            self._current_text = []
        elif tag_lower in ("ul", "ol"):
            self._in_list = True
            self._current_list_type = tag_lower
            self._current_list_items = []
        elif tag_lower == "li":
            self._current_li_text = []
        elif tag_lower == "table":
            self._in_table = True
            self._table_headers = []
            self._table_rows = []
        elif tag_lower == "tr":
            self._current_row = []
        elif tag_lower == "th":
            self._in_th = True
            self._current_cell_text = []
        elif tag_lower == "td":
            self._in_td = True
            self._current_cell_text = []
        elif tag_lower == "pre":
            self._in_pre = True
            self._pre_buffer = []
            cls = attr_dict.get("class", "")
            lang_match = re.search(r'(?:lang|language)-([a-zA-Z0-9_-]+)', cls)
            self._code_lang = lang_match.group(1) if lang_match else "text"
        elif tag_lower == "code":
            self._in_code = True
            if not self._in_pre:
                cls = attr_dict.get("class", "")
                lang_match = re.search(r'(?:lang|language)-([a-zA-Z0-9_-]+)', cls)
                self._code_lang = lang_match.group(1) if lang_match else "inline"
        elif tag_lower == "blockquote":
            self._in_blockquote = True
            self._blockquote_buffer = []
        elif tag_lower in ("strong", "b"):
            self._current_tag = tag_lower
            self._current_text = []
        elif tag_lower == "details":
            self._in_details = True
            self._summary_text = []
            self._details_body = []
        elif tag_lower == "summary":
            self._in_summary = True
            self._summary_text = []
        elif tag_lower == "dt":
            self._in_dt = True
            self._dt_text = []
        elif tag_lower == "dd":
            self._in_dd = True
            self._dd_text = []

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if self._tag_stack and self._tag_stack[-1] == tag_lower:
            self._tag_stack.pop()

        if tag_lower == "title":
            raw_title = "".join(self._current_text).strip()
            if raw_title:
                self.title = raw_title
            self._current_tag = None
        elif tag_lower == "script" and self._in_json_ld:
            self._in_json_ld = False
            raw_json = "".join(self._json_ld_buffer).strip()
            if raw_json:
                self.json_ld_blocks.append(raw_json)
        elif tag_lower in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = "".join(self._current_text).strip()
            if text:
                level = int(tag_lower[1])
                self.headings.append({
                    "level": level,
                    "tag": tag_lower,
                    "text": text,
                    "word_count": len(text.split())
                })
            self._current_tag = None
        elif tag_lower == "p":
            text = "".join(self._current_text).strip()
            if text and len(text.split()) >= 3:
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
                self.paragraphs.append({
                    "text": text,
                    "word_count": len(text.split()),
                    "sentence_count": len(sentences),
                    "sentences": sentences
                })
            self._current_tag = None
        elif tag_lower == "li":
            item_text = "".join(self._current_li_text).strip()
            if item_text:
                self._current_list_items.append(item_text)
            self._current_li_text = []
        elif tag_lower in ("ul", "ol"):
            self._in_list = False
            if self._current_list_items:
                self.lists.append({
                    "type": self._current_list_type or "ul",
                    "items": list(self._current_list_items),
                    "item_count": len(self._current_list_items)
                })
            self._current_list_items = []
        elif tag_lower == "th":
            self._in_th = False
            cell_text = "".join(self._current_cell_text).strip()
            self._table_headers.append(cell_text)
            self._current_cell_text = []
        elif tag_lower == "td":
            self._in_td = False
            cell_text = "".join(self._current_cell_text).strip()
            self._current_row.append(cell_text)
            self._current_cell_text = []
        elif tag_lower == "tr":
            if self._current_row:
                self._table_rows.append(list(self._current_row))
            self._current_row = []
        elif tag_lower == "table":
            self._in_table = False
            if self._table_headers or self._table_rows:
                col_count = len(self._table_headers) if self._table_headers else (len(self._table_rows[0]) if self._table_rows else 0)
                self.tables.append({
                    "headers": list(self._table_headers),
                    "rows": list(self._table_rows),
                    "row_count": len(self._table_rows),
                    "col_count": col_count
                })
            self._table_headers = []
            self._table_rows = []
        elif tag_lower == "pre":
            self._in_pre = False
            code_text = "".join(self._pre_buffer).strip()
            if code_text:
                self.code_blocks.append({
                    "language": self._code_lang,
                    "code": code_text,
                    "line_count": len(code_text.splitlines())
                })
            self._pre_buffer = []
            self._code_lang = "text"
        elif tag_lower == "code":
            self._in_code = False
        elif tag_lower == "blockquote":
            self._in_blockquote = False
            quote_text = "".join(self._blockquote_buffer).strip()
            if quote_text:
                self.blockquotes.append({
                    "text": quote_text,
                    "word_count": len(quote_text.split())
                })
            self._blockquote_buffer = []
        elif tag_lower in ("strong", "b"):
            bold_text = "".join(self._current_text).strip()
            if bold_text and len(bold_text.split()) <= 8:
                self.bold_terms.append(bold_text)
            self._current_tag = None
        elif tag_lower == "summary":
            self._in_summary = False
        elif tag_lower == "details":
            self._in_details = False
            q = "".join(self._summary_text).strip()
            a = "".join(self._details_body).strip()
            if q and a:
                self.faq_blocks.append({"question": q, "answer": a, "source": "details"})
            self._summary_text = []
            self._details_body = []
        elif tag_lower == "dt":
            self._in_dt = False
        elif tag_lower == "dd":
            self._in_dd = False
            q = "".join(self._dt_text).strip()
            a = "".join(self._dd_text).strip()
            if q and a:
                self.faq_blocks.append({"question": q, "answer": a, "source": "dl"})
            self._dt_text = []
            self._dd_text = []

    def handle_data(self, data: str):
        if not data:
            return

        self._full_text_buffer.append(data)

        if self._in_json_ld:
            self._json_ld_buffer.append(data)
            return

        if self._in_pre:
            self._pre_buffer.append(data)
            return

        if self._in_blockquote:
            self._blockquote_buffer.append(data)

        if self._in_th or self._in_td:
            self._current_cell_text.append(data)

        if self._in_list and "li" in self._tag_stack:
            self._current_li_text.append(data)

        if self._in_summary:
            self._summary_text.append(data)
        elif self._in_details:
            self._details_body.append(data)

        if self._in_dt:
            self._dt_text.append(data)
        elif self._in_dd:
            self._dd_text.append(data)

        if self._current_tag in ("title", "h1", "h2", "h3", "h4", "h5", "h6", "p", "strong", "b"):
            self._current_text.append(data)

    def get_full_text(self) -> str:
        return " ".join("".join(self._full_text_buffer).split())


def extract_html_structure(html_content: str) -> Dict[str, Any]:
    """
    Parses HTML into a comprehensive structural breakdown for AEO citation analysis.
    """
    parser = HTMLStructureParser()
    try:
        parser.feed(html_content)
    except Exception:
        pass

    # Parse JSON-LD schemas
    schemas: List[Dict[str, Any]] = []
    for raw in parser.json_ld_blocks:
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                schemas.append(parsed)
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        schemas.append(item)
        except Exception:
            pass

    # Extract FAQs from JSON-LD schemas if available
    faq_items: List[Dict[str, str]] = list(parser.faq_blocks)
    for sch in schemas:
        graph = sch.get("@graph", [sch]) if isinstance(sch, dict) else [sch]
        for entity in graph:
            if not isinstance(entity, dict):
                continue
            if entity.get("@type") == "FAQPage":
                main_entity = entity.get("mainEntity", [])
                if isinstance(main_entity, list):
                    for q_node in main_entity:
                        if isinstance(q_node, dict) and q_node.get("@type") == "Question":
                            q_text = q_node.get("name", "")
                            ans_node = q_node.get("acceptedAnswer", {})
                            a_text = ans_node.get("text", "") if isinstance(ans_node, dict) else str(ans_node)
                            if q_text and a_text:
                                faq_items.append({"question": q_text, "answer": a_text, "source": "schema_jsonld"})

    # Check for heading-based Q&A patterns (e.g. H2/H3 starting with Q:, What, How, Why followed by P)
    for i, h in enumerate(parser.headings):
        htext = h["text"].strip()
        is_question = htext.endswith("?") or htext.lower().startswith(("what ", "how ", "why ", "when ", "where ", "who ", "can ", "does ", "is ", "q:"))
        if is_question and i < len(parser.headings):
            # Check if there's a matching paragraph nearby
            for p in parser.paragraphs:
                if len(p["sentences"]) > 0:
                    p_text = p["text"].strip()
                    # If question is in FAQ items already, skip
                    if not any(f["question"] == htext for f in faq_items):
                        faq_items.append({"question": htext, "answer": p_text, "source": "heading_pattern"})
                        break

    meta = parser.meta_tags
    title = parser.title or meta.get("og:title") or meta.get("twitter:title") or ""
    description = meta.get("description") or meta.get("og:description") or meta.get("twitter:description") or ""

    full_text = parser.get_full_text()
    words = full_text.split()
    total_words = len(words)

    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', full_text) if len(s.strip().split()) >= 3]

    return {
        "title": title.strip(),
        "meta_description": description.strip(),
        "canonical_url": parser.canonical_url or meta.get("og:url") or "",
        "headings": parser.headings,
        "paragraphs": parser.paragraphs,
        "lists": parser.lists,
        "tables": parser.tables,
        "code_blocks": parser.code_blocks,
        "blockquotes": parser.blockquotes,
        "bold_terms": list(set(parser.bold_terms)),
        "faq_blocks": faq_items,
        "schemas": schemas,
        "total_words": total_words,
        "total_sentences": len(sentences),
        "sentences": sentences,
        "full_text": full_text
    }


def calculate_citation_extractability_score(structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Computes the 5-pillar Citation Extractability Score (0-100):
    1. Heading Hierarchy (0-20)
    2. Claim Clarity (0-20)
    3. Entity Precision (0-20)
    4. Structured Data Anchoring (0-20)
    5. Quotability (0-20)
    """
    headings = structure.get("headings", [])
    paragraphs = structure.get("paragraphs", [])
    lists = structure.get("lists", [])
    tables = structure.get("tables", [])
    blockquotes = structure.get("blockquotes", [])
    faq_blocks = structure.get("faq_blocks", [])
    schemas = structure.get("schemas", [])
    sentences = structure.get("sentences", [])
    total_words = structure.get("total_words", 0)
    bold_terms = structure.get("bold_terms", [])
    title = structure.get("title", "")
    description = structure.get("meta_description", "")

    # =========================================================================
    # 1. Heading Hierarchy (0-20)
    # =========================================================================
    h_score = 0.0
    h_breakdown = []

    h1_count = sum(1 for h in headings if h["level"] == 1)
    h2_count = sum(1 for h in headings if h["level"] == 2)
    h3_count = sum(1 for h in headings if h["level"] == 3)
    h4_count = sum(1 for h in headings if h["level"] == 4)

    if h1_count == 1:
        h_score += 5.0
        h_breakdown.append("Single clean H1 tag (+5.0)")
    elif h1_count > 1:
        h_score += 3.0
        h_breakdown.append("Multiple H1 tags detected (+3.0)")
    else:
        h_breakdown.append("Missing H1 heading (0.0)")

    if h2_count >= 2:
        h_score += 5.0
        h_breakdown.append(f"Strong section segmentation with {h2_count} H2 tags (+5.0)")
    elif h2_count == 1:
        h_score += 3.0
        h_breakdown.append("Only 1 H2 tag (+3.0)")
    else:
        h_breakdown.append("No H2 headings (0.0)")

    # Check for level skipping (e.g. H1 directly to H3 without H2)
    levels = [h["level"] for h in headings]
    skips = 0
    for i in range(len(levels) - 1):
        if levels[i+1] > levels[i] + 1:
            skips += 1

    if headings and skips == 0:
        h_score += 4.0
        h_breakdown.append("Strict sequential heading nesting without skipped levels (+4.0)")
    elif skips <= 1:
        h_score += 2.0
        h_breakdown.append("Minor heading level skip detected (+2.0)")
    else:
        h_breakdown.append(f"{skips} heading level skips detected (0.0)")

    # Heading length quality (3 to 12 words per heading)
    if headings:
        avg_h_words = sum(h["word_count"] for h in headings) / len(headings)
        if 3.0 <= avg_h_words <= 12.0:
            h_score += 3.0
            h_breakdown.append(f"Descriptive heading lengths avg {avg_h_words:.1f} words (+3.0)")
        elif avg_h_words < 3.0:
            h_score += 1.5
            h_breakdown.append("Headings are very brief (+1.5)")
        else:
            h_score += 1.5
            h_breakdown.append("Headings are overly long (+1.5)")

    # Ratio of content to headings (one heading per 80-350 words is optimal)
    if headings and total_words > 0:
        words_per_heading = total_words / len(headings)
        if 50 <= words_per_heading <= 350:
            h_score += 3.0
            h_breakdown.append(f"Balanced text-to-heading density ({words_per_heading:.0f} words/heading) (+3.0)")
        else:
            h_score += 1.5
            h_breakdown.append(f"Suboptimal text-to-heading ratio ({words_per_heading:.0f} words/heading) (+1.5)")

    h_score = min(20.0, round(h_score, 1))

    # =========================================================================
    # 2. Claim Clarity (0-20)
    # =========================================================================
    c_score = 0.0
    c_breakdown = []

    # Declarative sentence density / Opening topic sentence clarity
    declarative_patterns = [
        r'\b(?:is an?|are|refers to|provides|enables|delivers|consists of|features|designed for|allows)\b',
        r'\b(?:built with|implements|generates|includes|contains|acts as|serves as)\b'
    ]
    decl_count = 0
    for s in sentences:
        for pat in declarative_patterns:
            if re.search(pat, s, re.IGNORECASE):
                decl_count += 1
                break

    if decl_count >= 5:
        c_score += 6.0
        c_breakdown.append(f"High density of direct declarative statements ({decl_count} found) (+6.0)")
    elif decl_count >= 2:
        c_score += 4.0
        c_breakdown.append(f"Moderate declarative statements ({decl_count} found) (+4.0)")
    elif decl_count >= 1:
        c_score += 2.0
        c_breakdown.append(f"Few declarative statements ({decl_count} found) (+2.0)")
    else:
        c_breakdown.append("Lacks definitive declarative statements (0.0)")

    # Sentence length sweet spot (12-25 words average is ideal for AI extraction)
    if sentences:
        sentence_word_counts = [len(s.split()) for s in sentences]
        avg_sentence_len = sum(sentence_word_counts) / len(sentences)
        if 12.0 <= avg_sentence_len <= 25.0:
            c_score += 5.0
            c_breakdown.append(f"Optimal sentence length for LLM tokenization (avg {avg_sentence_len:.1f} words) (+5.0)")
        elif 8.0 <= avg_sentence_len <= 32.0:
            c_score += 3.0
            c_breakdown.append(f"Acceptable sentence length (avg {avg_sentence_len:.1f} words) (+3.0)")
        else:
            c_score += 1.0
            c_breakdown.append(f"Sentences may be too long/short for clean quote extraction (avg {avg_sentence_len:.1f} words) (+1.0)")
    else:
        c_breakdown.append("No clear sentences detected (0.0)")

    # Opening paragraph / Answer capsule clarity
    if paragraphs:
        first_p = paragraphs[0]
        if first_p["word_count"] <= 45 and first_p["sentence_count"] >= 1:
            c_score += 5.0
            c_breakdown.append("Concise, direct opening capsule paragraph (+5.0)")
        elif first_p["word_count"] <= 80:
            c_score += 3.0
            c_breakdown.append("Opening paragraph is moderately concise (+3.0)")
        else:
            c_score += 1.5
            c_breakdown.append("Opening paragraph is lengthy (>80 words) (+1.5)")

    # Key terms emphasis (bold/strong terms)
    if len(bold_terms) >= 3:
        c_score += 4.0
        c_breakdown.append(f"Clear visual and semantic entity emphasis ({len(bold_terms)} terms) (+4.0)")
    elif len(bold_terms) >= 1:
        c_score += 2.0
        c_breakdown.append(f"Some key terms emphasized ({len(bold_terms)} terms) (+2.0)")
    else:
        c_breakdown.append("No bold/strong emphasis on key terminology (0.0)")

    c_score = min(20.0, round(c_score, 1))

    # =========================================================================
    # 3. Entity Precision (0-20)
    # =========================================================================
    e_score = 0.0
    e_breakdown = []

    # Concrete numerical metrics, versions, percentages, benchmarks
    metric_pattern = r'\b(?:\d+(?:\.\d+)?%|\d+(?:\.\d+)?x|\$\d+(?:\.\d+)?|v\d+(?:\.\d+)*|\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\s*(?:ms|s|min|sec|MB|GB|TB|KB|px|pts?|GHz|MHz|tokens?|reqs?))\b'
    metric_matches = re.findall(metric_pattern, structure.get("full_text", ""), re.IGNORECASE)

    if len(metric_matches) >= 5:
        e_score += 6.0
        e_breakdown.append(f"High quantitative precision with {len(metric_matches)} concrete metrics/numbers (+6.0)")
    elif len(metric_matches) >= 2:
        e_score += 4.0
        e_breakdown.append(f"Good quantitative anchoring ({len(metric_matches)} metrics) (+4.0)")
    elif len(metric_matches) >= 1:
        e_score += 2.0
        e_breakdown.append(f"Minimal numerical metrics ({len(metric_matches)} found) (+2.0)")
    else:
        e_breakdown.append("No quantitative metrics, percentages, or versions found (0.0)")

    # Title and meta description entity precision
    if title and len(title) >= 10:
        e_score += 3.0
        e_breakdown.append(f"Strong entity title: '{title[:40]}...' (+3.0)")
    elif title:
        e_score += 1.5
        e_breakdown.append("Short or weak title (+1.5)")

    if description and len(description) >= 50:
        e_score += 3.0
        e_breakdown.append("Rich meta description provides standalone entity context (+3.0)")
    elif description:
        e_score += 1.5
        e_breakdown.append("Brief meta description (+1.5)")

    # Schema entity alignment
    detected_schema_types: List[str] = []
    for s in schemas:
        graph = s.get("@graph", [s]) if isinstance(s, dict) else [s]
        for ent in graph:
            if isinstance(ent, dict) and ent.get("@type"):
                t = ent["@type"]
                if isinstance(t, list):
                    detected_schema_types.extend(t)
                else:
                    detected_schema_types.append(str(t))

    unique_schema_types = set(detected_schema_types)
    authoritative_types = {"Organization", "SoftwareApplication", "Product", "TechArticle", "Article", "LocalBusiness", "FAQPage", "WebSite", "BreadcrumbList"}
    matched_auth = unique_schema_types.intersection(authoritative_types)

    if len(matched_auth) >= 3:
        e_score += 5.0
        e_breakdown.append(f"Rich entity typing in Schema ({', '.join(matched_auth)}) (+5.0)")
    elif len(matched_auth) >= 1:
        e_score += 3.0
        e_breakdown.append(f"Standard entity typing in Schema ({', '.join(matched_auth)}) (+3.0)")
    elif unique_schema_types:
        e_score += 2.0
        e_breakdown.append(f"Generic schema types detected ({', '.join(unique_schema_types)}) (+2.0)")
    else:
        e_breakdown.append("No Schema.org entity types declared (0.0)")

    # Canonical URL and domain anchoring
    if structure.get("canonical_url"):
        e_score += 3.0
        e_breakdown.append("Canonical URL explicitly declared (+3.0)")
    else:
        e_breakdown.append("Missing canonical URL tag (0.0)")

    e_score = min(20.0, round(e_score, 1))

    # =========================================================================
    # 4. Structured Data Anchoring (0-20)
    # =========================================================================
    s_score = 0.0
    s_breakdown = []

    # Schema JSON-LD presence & depth
    if schemas:
        s_score += 6.0
        s_breakdown.append(f"JSON-LD structured data present ({len(schemas)} block(s)) (+6.0)")

        # Connected @graph bonus
        has_graph = any(isinstance(s, dict) and "@graph" in s for s in schemas)
        if has_graph:
            s_score += 4.0
            s_breakdown.append("Connected Schema.org @graph entity structure (+4.0)")
    else:
        s_breakdown.append("No Schema.org JSON-LD found (0.0)")

    # FAQ Page / Q&A structured items
    if len(faq_blocks) >= 3:
        s_score += 4.0
        s_breakdown.append(f"Rich FAQ Q&A dataset ({len(faq_blocks)} Q&A pairs) (+4.0)")
    elif len(faq_blocks) >= 1:
        s_score += 2.5
        s_breakdown.append(f"FAQ Q&A structure detected ({len(faq_blocks)} pair(s)) (+2.5)")
    else:
        s_breakdown.append("No structured FAQ Q&A blocks (0.0)")

    # HTML Tables
    if tables:
        s_score += 3.0
        s_breakdown.append(f"Structured comparison/data tables ({len(tables)} table(s)) (+3.0)")
    else:
        s_breakdown.append("No HTML data tables (0.0)")

    # Bullet / Numbered Lists
    if len(lists) >= 2:
        s_score += 3.0
        s_breakdown.append(f"Multiple structured lists ({len(lists)} lists) (+3.0)")
    elif len(lists) == 1:
        s_score += 2.0
        s_breakdown.append("Structured list present (+2.0)")
    else:
        s_breakdown.append("No bullet or numbered lists (0.0)")

    s_score = min(20.0, round(s_score, 1))

    # =========================================================================
    # 5. Quotability (0-20)
    # =========================================================================
    q_score = 0.0
    q_breakdown = []

    # Standalone high-signal quote sentences (10-32 words with subject, verb, and clear assertion)
    quotable_sentences: List[str] = []
    for s in sentences:
        w_count = len(s.split())
        if 10 <= w_count <= 35:
            # Check for high signal assertions
            if any(k in s.lower() for k in ["is ", "are ", "provides", "features", "allows", "built for", "supports", "enables", "scores", "generates"]):
                quotable_sentences.append(s)

    if len(quotable_sentences) >= 5:
        q_score += 6.0
        q_breakdown.append(f"Rich repository of standalone extractable quotes ({len(quotable_sentences)} sentences) (+6.0)")
    elif len(quotable_sentences) >= 2:
        q_score += 4.0
        q_breakdown.append(f"Good quotability ({len(quotable_sentences)} extractable quotes) (+4.0)")
    elif len(quotable_sentences) >= 1:
        q_score += 2.0
        q_breakdown.append(f"Few extractable quote candidates ({len(quotable_sentences)}) (+2.0)")
    else:
        q_breakdown.append("Lacks standalone quote-ready sentences (0.0)")

    # FAQ / Direct Q&A answers available for exact lookup
    if faq_blocks:
        q_score += 5.0
        q_breakdown.append(f"Direct answer capsules in FAQ ({len(faq_blocks)} questions) (+5.0)")
    else:
        q_breakdown.append("No direct Q&A capsules for question matching (0.0)")

    # Blockquotes / Highlights
    if blockquotes:
        q_score += 4.0
        q_breakdown.append(f"Explicit blockquote callouts ({len(blockquotes)} quotes) (+4.0)")
    else:
        q_breakdown.append("No blockquotes or curated summary callouts (0.0)")

    # High signal-to-noise ratio in lists
    list_items = [item for lst in lists for item in lst.get("items", [])]
    bullet_quotes = [item for item in list_items if 5 <= len(item.split()) <= 30]
    if len(bullet_quotes) >= 4:
        q_score += 5.0
        q_breakdown.append(f"Crisp bullet point claims ({len(bullet_quotes)} items) (+5.0)")
    elif len(bullet_quotes) >= 1:
        q_score += 3.0
        q_breakdown.append(f"Some crisp bullet points ({len(bullet_quotes)} items) (+3.0)")
    else:
        q_breakdown.append("No concise bullet claims (0.0)")

    q_score = min(20.0, round(q_score, 1))

    total_score = round(h_score + c_score + e_score + s_score + q_score, 1)

    if total_score >= 90:
        grade = "A+"
        status = "EXCELLENT"
    elif total_score >= 80:
        grade = "A"
        status = "VERY_STRONG"
    elif total_score >= 70:
        grade = "B"
        status = "STRONG"
    elif total_score >= 55:
        grade = "C"
        status = "MODERATE"
    elif total_score >= 40:
        grade = "D"
        status = "NEEDS_OPTIMIZATION"
    else:
        grade = "F"
        status = "POOR"

    return {
        "total_score": total_score,
        "grade": grade,
        "status": status,
        "sub_scores": {
            "heading_hierarchy": {
                "score": h_score,
                "max": 20.0,
                "percentage": round((h_score / 20.0) * 100, 1),
                "breakdown": h_breakdown
            },
            "claim_clarity": {
                "score": c_score,
                "max": 20.0,
                "percentage": round((c_score / 20.0) * 100, 1),
                "breakdown": c_breakdown
            },
            "entity_precision": {
                "score": e_score,
                "max": 20.0,
                "percentage": round((e_score / 20.0) * 100, 1),
                "breakdown": e_breakdown
            },
            "structured_data_anchoring": {
                "score": s_score,
                "max": 20.0,
                "percentage": round((s_score / 20.0) * 100, 1),
                "breakdown": s_breakdown
            },
            "quotability": {
                "score": q_score,
                "max": 20.0,
                "percentage": round((q_score / 20.0) * 100, 1),
                "breakdown": q_breakdown
            }
        },
        "quotable_sentences": quotable_sentences[:8]
    }


def generate_engine_previews(structure: Dict[str, Any], query: Optional[str] = None) -> Dict[str, Any]:
    """
    Simulates real-world AI answer engine synthesis and citation card previews for:
    1. Perplexity AI (Pro Search synthesis with [1][2] citations)
    2. ChatGPT Search (Conversational direct answer + linked pill)
    3. Google Gemini (AI Overview snapshot + entity card)
    4. Anthropic Claude (Grounded deep response with cited quotations)
    5. Apple Intelligence (Ultra-concise smart summary capsule)
    """
    title = structure.get("title") or "Platform Overview"
    description = structure.get("meta_description") or ""
    canonical_url = structure.get("canonical_url") or "https://example.com"
    domain = urllib.parse.urlparse(canonical_url).netloc or "example.com"

    # Derive optimal query if none provided
    h1s = [h["text"] for h in structure.get("headings", []) if h["level"] == 1]
    if not query:
        if h1s:
            query = f"What is {h1s[0]} and how does it work?"
        elif title:
            clean_title = title.split("-")[0].split("|")[0].strip()
            query = f"What is {clean_title}?"
        else:
            query = "What are the core capabilities and architecture of this platform?"

    # Find primary summary text
    primary_answer = ""
    faq_matches = structure.get("faq_blocks", [])
    if faq_matches:
        primary_answer = faq_matches[0]["answer"]
    elif structure.get("paragraphs"):
        primary_answer = structure["paragraphs"][0]["text"]
    elif description:
        primary_answer = description
    else:
        primary_answer = f"{title} is a web architecture platform with structured entity data."

    # Extract key bullets
    key_points: List[str] = []
    for lst in structure.get("lists", []):
        for itm in lst.get("items", [])[:4]:
            if 4 <= len(itm.split()) <= 25:
                key_points.append(itm)
        if len(key_points) >= 3:
            break

    if not key_points and len(structure.get("paragraphs", [])) > 1:
        for p in structure["paragraphs"][1:4]:
            if p.get("sentences"):
                key_points.append(p["sentences"][0])

    if not key_points:
        key_points = [
            f"Provides structured knowledge graph integration for Answer Engine Optimization.",
            f"Optimized for automated retrieval across major LLM search crawlers.",
            f"Maintains canonical entity attribution and machine-readable manifests."
        ]

    # Clean short quote snippet
    quote_snippet = primary_answer
    if len(quote_snippet.split()) > 35:
        quote_snippet = " ".join(quote_snippet.split()[:35]) + "..."

    # 1. Perplexity AI Preview
    perplexity_preview = {
        "engine": "Perplexity AI",
        "model_version": "Perplexity Pro / Sonar Reasoning",
        "simulated_query": query,
        "synthesis": (
            f"{primary_answer} [1].\n\n"
            f"Key capabilities include:\n" +
            "\n".join([f"- **{pt.split(':')[0] if ':' in pt else pt[:25]}**: {pt} [1]" for pt in key_points[:3]]) +
            f"\n\nAccording to {domain}, this enables complete end-to-end entity verification [1]."
        ),
        "citations": [
            {
                "index": 1,
                "title": title,
                "url": canonical_url or f"https://{domain}/",
                "domain": domain,
                "snippet": quote_snippet,
                "confidence_score": 0.98
            }
        ],
        "extraction_method": "Hybrid Vector RAG + Direct JSON-LD Knowledge Graph Lookup"
    }

    # 2. ChatGPT Search Preview
    chatgpt_preview = {
        "engine": "ChatGPT Search",
        "model_version": "GPT-4o Search",
        "simulated_query": query,
        "synthesis": (
            f"**{title}** is designed to provide comprehensive, machine-readable structured knowledge for answer engines.\n\n"
            f"{primary_answer}\n\n"
            f"### Highlights\n" +
            "\n".join([f"• {pt}" for pt in key_points[:3]])
        ),
        "source_pill": {
            "title": title,
            "url": canonical_url or f"https://{domain}/",
            "domain": domain,
            "favicon_url": f"https://{domain}/favicon.ico"
        },
        "attribution_format": f"[{domain} — {title}]({canonical_url or f'https://{domain}/'})"
    }

    # 3. Google Gemini (AI Overview) Preview
    gemini_preview = {
        "engine": "Google Gemini / AI Overviews",
        "model_version": "Gemini 1.5 Pro Search Grounding",
        "simulated_query": query,
        "overview_box": {
            "lead_answer": primary_answer,
            "bullet_points": key_points[:3],
            "knowledge_graph_card": {
                "entity_name": title.split("-")[0].strip(),
                "entity_type": "Software / Web Platform",
                "canonical_url": canonical_url or f"https://{domain}/",
                "schema_types_detected": [s.get("@type", "Entity") for s in structure.get("schemas", [])][:3]
            }
        },
        "featured_snippets_eligible": len(structure.get("faq_blocks", [])) > 0 or len(structure.get("tables", [])) > 0
    }

    # 4. Anthropic Claude (Direct Grounded Response) Preview
    claude_preview = {
        "engine": "Anthropic Claude",
        "model_version": "Claude 3.5 Sonnet / Research Grounding",
        "simulated_query": query,
        "synthesis": (
            f"Based on the official documentation for **{title}** ({canonical_url}):\n\n"
            f"> \"{quote_snippet}\"\n\n"
            f"The architecture is structured around the following verified specifications:\n\n" +
            "\n".join([f"1. **{pt.split(':')[0] if ':' in pt else 'Feature'}**: {pt}" for pt in key_points[:3]]) +
            f"\n\nAll statements are directly grounded in the provided document without extraneous extrapolation."
        ),
        "grounding_confidence": "High (Direct DOM Grounding)"
    }

    # 5. Apple Intelligence (Smart Summary Capsule)
    apple_preview = {
        "engine": "Apple Intelligence",
        "model_version": "Private Cloud Compute / Siri Smart Summaries",
        "simulated_query": query,
        "summary_capsule": {
            "headline": title.split("-")[0].strip(),
            "short_summary": " ".join(primary_answer.split()[:25]) + ("." if not primary_answer.endswith(".") else ""),
            "key_facts": key_points[:3],
            "domain_badge": domain,
            "privacy_verification": "On-Device / Secure Enclave Indexed"
        }
    }

    return {
        "query": query,
        "perplexity": perplexity_preview,
        "chatgpt": chatgpt_preview,
        "gemini": gemini_preview,
        "claude": claude_preview,
        "apple_intelligence": apple_preview
    }


def generate_optimization_tips(sub_scores: Dict[str, Any], structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Produces highly specific, prioritized, and actionable optimization tips based on
    the structural weaknesses and sub-score gaps identified.
    """
    tips: List[Dict[str, Any]] = []

    h_data = sub_scores.get("heading_hierarchy", {})
    c_data = sub_scores.get("claim_clarity", {})
    e_data = sub_scores.get("entity_precision", {})
    s_data = sub_scores.get("structured_data_anchoring", {})
    q_data = sub_scores.get("quotability", {})

    # Heading tips
    headings = structure.get("headings", [])
    h1_count = sum(1 for h in headings if h["level"] == 1)
    if h1_count == 0:
        tips.append({
            "priority": "HIGH",
            "pillar": "Heading Hierarchy",
            "issue": "Missing H1 tag",
            "tip": "Add exactly one descriptive <h1> heading that names your primary product or subject (e.g., '<h1>Product Name — Purpose</h1>').",
            "impact": "+5.0 pts"
        })
    elif h1_count > 1:
        tips.append({
            "priority": "MEDIUM",
            "pillar": "Heading Hierarchy",
            "issue": "Multiple H1 tags",
            "tip": "Consolidate to a single <h1> heading and demote secondary titles to <h2> tags.",
            "impact": "+2.0 pts"
        })

    h2_count = sum(1 for h in headings if h["level"] == 2)
    if h2_count < 2:
        tips.append({
            "priority": "HIGH",
            "pillar": "Heading Hierarchy",
            "issue": "Sparse H2 section segmentation",
            "tip": "Add definitive 1-sentence answers directly below H2 tags so AI search bots can extract standalone sections without parsing the entire DOM.",
            "impact": "+3.0 to +5.0 pts"
        })

    # Structured data tips
    schemas = structure.get("schemas", [])
    if not schemas:
        tips.append({
            "priority": "CRITICAL",
            "pillar": "Structured Data Anchoring",
            "issue": "Zero Schema.org JSON-LD structured data",
            "tip": "Inject a connected Schema.org @graph containing Organization, WebSite, SoftwareApplication/Product, and FAQPage into the document <head>.",
            "impact": "+10.0 pts"
        })
    else:
        has_faq = any("FAQPage" in str(s) for s in schemas)
        if not has_faq and len(structure.get("faq_blocks", [])) == 0:
            tips.append({
                "priority": "HIGH",
                "pillar": "Structured Data Anchoring",
                "issue": "Missing FAQPage structured Q&A schema",
                "tip": "Add a Schema.org FAQPage schema with at least 3-5 high-intent Question and Answer pairs to capture AI Answer Engine rich cards.",
                "impact": "+4.0 pts"
            })

    # Tables
    if not structure.get("tables"):
        tips.append({
            "priority": "MEDIUM",
            "pillar": "Structured Data Anchoring",
            "issue": "No HTML comparison or data tables",
            "tip": "Use comparison tables (<table>) for data-dense claims, pricing tiers, and feature matrices to facilitate tabular answer ingestion by Gemini and ChatGPT.",
            "impact": "+3.0 pts"
        })

    # Claim clarity & Quotability
    paragraphs = structure.get("paragraphs", [])
    long_paragraphs = [p for p in paragraphs if p["word_count"] > 60]
    if len(long_paragraphs) >= 2:
        tips.append({
            "priority": "HIGH",
            "pillar": "Claim Clarity & Quotability",
            "issue": f"{len(long_paragraphs)} overly long paragraphs (>60 words)",
            "tip": "Break dense paragraphs into concise 20-30 word declarative answer capsules placed immediately after section headers.",
            "impact": "+3.0 to +5.0 pts"
        })

    # Quantitative metrics
    full_text = structure.get("full_text", "")
    metric_matches = re.findall(r'\b(?:\d+(?:\.\d+)?%|\d+(?:\.\d+)?x|\$\d+|v\d+|\d+\s*ms)\b', full_text)
    if len(metric_matches) < 2:
        tips.append({
            "priority": "MEDIUM",
            "pillar": "Entity Precision",
            "issue": "Sparse numerical metrics and benchmark stats",
            "tip": "Include concrete numerical metrics, benchmark stats, or version numbers (e.g., '10x faster', '<5ms latency', 'v1.0.0') to boost factual retrieval confidence.",
            "impact": "+4.0 pts"
        })

    # Lists
    if not structure.get("lists"):
        tips.append({
            "priority": "MEDIUM",
            "pillar": "Quotability",
            "issue": "No bulleted or numbered lists",
            "tip": "Convert feature summaries and procedural steps into bulleted <ul> or numbered <ol> lists for structured synthesis.",
            "impact": "+3.0 pts"
        })

    # Canonical URL
    if not structure.get("canonical_url"):
        tips.append({
            "priority": "MEDIUM",
            "pillar": "Entity Precision",
            "issue": "Missing canonical URL link tag",
            "tip": "Add a <link rel='canonical' href='https://yourdomain.com/page'> in the <head> to prevent duplicate entity ambiguity in AI indexes.",
            "impact": "+3.0 pts"
        })

    return tips


def simulate_ai_citation(html_or_url: str, query: Optional[str] = None) -> Dict[str, Any]:
    """
    Primary API entrypoint:
    Analyzes an HTML string, file path, or live URL for AI Citation Extractability,
    computes 5-pillar scores (0-100), generates simulated engine previews
    (Perplexity, ChatGPT, Gemini, Claude, Apple Intelligence), and outputs concrete optimization tips.

    Zero external runtime dependencies.
    """
    html_content = ""
    source_type = "raw_html"
    source_location = None

    input_str = html_or_url.strip()

    if input_str.startswith("http://") or input_str.startswith("https://"):
        source_type = "url"
        source_location = input_str
        req = urllib.request.Request(
            input_str,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AEOGraphEngine-CitationSimulator/1.0; +https://github.com/1nc0gn30/aeo-graph-engine)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        )
        try:
            with urllib.request.urlopen(req, timeout=10.0) as resp:
                raw_bytes = resp.read(2_000_000)
                html_content = raw_bytes.decode("utf-8", errors="replace")
        except Exception as e:
            # Fallback if URL fetch fails in offline/test environment
            html_content = f"<html><head><title>Error fetching {input_str}</title></head><body><h1>Fetch Error</h1><p>{str(e)}</p></body></html>"
    elif input_str and "\n" not in input_str and ("<" not in input_str) and Path(input_str).is_file():
        source_type = "file"
        source_location = str(Path(input_str).resolve())
        with open(source_location, "r", encoding="utf-8", errors="replace") as f:
            html_content = f.read()
    else:
        html_content = input_str

    # 1. Parse HTML structure
    structure = extract_html_structure(html_content)

    # 2. Compute Citation Extractability Score
    scoring_result = calculate_citation_extractability_score(structure)

    # 3. Generate Simulated AI Answer Engine Previews
    simulated_citations = generate_engine_previews(structure, query=query)

    # 4. Generate Prioritized Optimization Tips
    optimization_tips = generate_optimization_tips(scoring_result["sub_scores"], structure)

    return {
        "source_type": source_type,
        "source_location": source_location,
        "target_query": simulated_citations["query"],
        "page_metadata": {
            "title": structure["title"],
            "meta_description": structure["meta_description"],
            "canonical_url": structure["canonical_url"],
            "word_count": structure["total_words"],
            "sentence_count": structure["total_sentences"]
        },
        "structural_analysis": {
            "headings_count": len(structure["headings"]),
            "headings": structure["headings"][:15],
            "paragraphs_count": len(structure["paragraphs"]),
            "lists_count": len(structure["lists"]),
            "tables_count": len(structure["tables"]),
            "code_blocks_count": len(structure["code_blocks"]),
            "blockquotes_count": len(structure["blockquotes"]),
            "faq_blocks_count": len(structure["faq_blocks"]),
            "schemas_count": len(structure["schemas"]),
            "bold_terms_count": len(structure["bold_terms"]),
            "bold_terms": structure["bold_terms"][:10]
        },
        "citation_score": scoring_result["total_score"],
        "grade": scoring_result["grade"],
        "status": scoring_result["status"],
        "sub_scores": scoring_result["sub_scores"],
        "key_extractable_quotes": scoring_result["quotable_sentences"],
        "simulated_citations": {
            "perplexity": simulated_citations["perplexity"],
            "chatgpt": simulated_citations["chatgpt"],
            "gemini": simulated_citations["gemini"],
            "claude": simulated_citations["claude"],
            "apple_intelligence": simulated_citations["apple_intelligence"]
        },
        "optimization_tips": optimization_tips
    }

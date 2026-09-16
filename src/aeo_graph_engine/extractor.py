"""
HTML Metadata and Structured Data Extractor for AEO Graph Engine.
Parses HTML files to extract title, description, OpenGraph tags, canonical URLs,
Twitter cards, and existing JSON-LD schemas to bootstrap AEO configurations.
"""

import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple
from html.parser import HTMLParser


class SimpleHTMLMetadataParser(HTMLParser):
    """Zero-dependency HTML metadata and JSON-LD parser."""

    def __init__(self):
        super().__init__()
        self.title: Optional[str] = None
        self.in_title: bool = False
        self.meta_tags: Dict[str, str] = {}
        self.canonical_url: Optional[str] = None
        self.in_json_ld: bool = False
        self.current_json_ld: List[str] = []
        self.json_ld_blocks: List[str] = []
        self.headings: List[Dict[str, str]] = []
        self.current_heading_tag: Optional[str] = None
        self.current_heading_text: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        attr_dict = {k.lower(): (v or "") for k, v in attrs}
        tag_lower = tag.lower()

        if tag_lower == "title":
            self.in_title = True
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
                self.in_json_ld = True
                self.current_json_ld = []
        elif tag_lower in ("h1", "h2", "h3"):
            self.current_heading_tag = tag_lower
            self.current_heading_text = []

    def handle_endtag(self, tag: str):
        tag_lower = tag.lower()
        if tag_lower == "title":
            self.in_title = False
        elif tag_lower == "script" and self.in_json_ld:
            self.in_json_ld = False
            raw = "".join(self.current_json_ld).strip()
            if raw:
                self.json_ld_blocks.append(raw)
        elif tag_lower in ("h1", "h2", "h3") and self.current_heading_tag == tag_lower:
            text = "".join(self.current_heading_text).strip()
            if text:
                self.headings.append({"tag": tag_lower, "text": text})
            self.current_heading_tag = None

    def handle_data(self, data: str):
        if self.in_title:
            if self.title is None:
                self.title = data.strip()
            else:
                self.title += " " + data.strip()
        elif self.in_json_ld:
            self.current_json_ld.append(data)
        elif self.current_heading_tag:
            self.current_heading_text.append(data)


def extract_metadata_from_html(html_content: str) -> Dict[str, Any]:
    """
    Parses an HTML string and returns structured metadata suitable for seeding an AEO configuration.
    """
    parser = SimpleHTMLMetadataParser()
    try:
        parser.feed(html_content)
    except Exception:
        pass

    meta = parser.meta_tags

    site_name = (
        meta.get("og:site_name")
        or (parser.title.split("-")[0].strip() if parser.title and "-" in parser.title else parser.title)
        or "Extracted Website"
    )

    tagline = (
        meta.get("og:title")
        or parser.title
        or "Next-Generation Web Platform"
    )

    description = (
        meta.get("description")
        or meta.get("og:description")
        or meta.get("twitter:description")
        or ""
    )

    og_image = meta.get("og:image") or meta.get("twitter:image")
    canonical = parser.canonical_url or meta.get("og:url")

    # Domain extraction
    domain = None
    if canonical and "://" in canonical:
        from urllib.parse import urlparse
        domain = urlparse(canonical).netloc

    # Parsed existing JSON-LD schemas
    parsed_schemas = []
    for raw_block in parser.json_ld_blocks:
        try:
            parsed_schemas.append(json.loads(raw_block))
        except Exception:
            pass

    return {
        "site_name": site_name.strip() if site_name else "Extracted Platform",
        "tagline": tagline.strip() if tagline else "",
        "description": description.strip(),
        "canonical_url": canonical,
        "domain": domain or (urlparse(canonical).netloc if canonical and "://" in canonical else "example.com"),
        "og_image_url": og_image,
        "headings": parser.headings,
        "existing_jsonld": parsed_schemas
    }


def extract_from_file(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Reads HTML file from disk and extracts metadata."""
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    data = extract_metadata_from_html(content)
    data["source_file"] = str(path)
    return data

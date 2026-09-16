"""
Validation and scoring engine for AEO Graph Engine.
Audits Schema.org JSON-LD, llms.txt, ai.txt, robots.txt, and HTML files,
producing a 0-100 AEO Readiness Score and detailed diagnostics.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple


class AEODiagnosticReport:
    """Detailed audit report containing scores, passed checks, warnings, and errors."""

    def __init__(self, target_path: str):
        self.target_path = target_path
        self.passed: List[str] = []
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.score: float = 100.0
        self.artifacts_checked: Dict[str, bool] = {
            "schema_jsonld": False,
            "llms_txt": False,
            "llms_full_txt": False,
            "ai_txt": False,
            "robots_txt": False,
            "html_injection": False
        }

    def add_pass(self, message: str) -> None:
        self.passed.append(message)

    def add_warn(self, message: str, penalty: float = 5.0) -> None:
        self.warnings.append(message)
        self.score = max(0.0, self.score - penalty)

    def add_error(self, message: str, penalty: float = 15.0) -> None:
        self.errors.append(message)
        self.score = max(0.0, self.score - penalty)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target_path,
            "score": round(self.score, 1),
            "status": "EXCELLENT" if self.score >= 90 else "GOOD" if self.score >= 70 else "NEEDS_IMPROVEMENT",
            "passed_count": len(self.passed),
            "warnings_count": len(self.warnings),
            "errors_count": len(self.errors),
            "artifacts_detected": self.artifacts_checked,
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors
        }


def validate_schema_jsonld_dict(data: Dict[str, Any], report: AEODiagnosticReport) -> None:
    """Validates an in-memory Schema.org JSON-LD dict."""
    report.artifacts_checked["schema_jsonld"] = True

    # Check @context
    ctx = data.get("@context", "")
    if "schema.org" in str(ctx).lower():
        report.add_pass("Schema.org @context is valid (https://schema.org)")
    else:
        report.add_error("Missing or invalid @context; expected 'https://schema.org'", 20.0)

    # Check @graph
    graph = data.get("@graph")
    if isinstance(graph, list) and len(graph) > 0:
        report.add_pass(f"Schema graph contains {len(graph)} linked entity nodes")
        
        found_types = set()
        for entity in graph:
            if isinstance(entity, dict):
                etype = entity.get("@type")
                if etype:
                    found_types.add(etype)
                if not entity.get("@id"):
                    report.add_warn(f"Entity of type '{etype}' lacks a canonical @id URI", 3.0)
                if not entity.get("name") and etype not in ("BreadcrumbList", "SearchAction"):
                    report.add_warn(f"Entity of type '{etype}' lacks a 'name' property", 3.0)

        # Expected core entity types
        expected = ["Organization", "WebSite"]
        for exp in expected:
            if exp in found_types:
                report.add_pass(f"Discovered required Schema entity: {exp}")
            else:
                report.add_error(f"Missing recommended Schema entity: {exp}", 10.0)

        if "SoftwareApplication" in found_types or "LocalBusiness" in found_types:
            report.add_pass("Discovered primary domain application/service entity")
        else:
            report.add_warn("No SoftwareApplication or LocalBusiness entity found in @graph", 5.0)

        if "FAQPage" in found_types:
            report.add_pass("Discovered FAQPage entity with structured Q&A pairs for Answer Engines")
        else:
            report.add_warn("Missing FAQPage entity; FAQs strongly boost LLM citations", 5.0)

        if "BreadcrumbList" in found_types:
            report.add_pass("Discovered BreadcrumbList entity for hierarchy indexing")

    elif "@type" in data:
        report.add_pass(f"Single entity Schema detected: {data.get('@type')}")
        report.add_warn("Schema uses single entity instead of linked @graph structure", 5.0)
    else:
        report.add_error("Schema payload lacks @graph array or @type declaration", 25.0)


def validate_llms_txt_content(content: str, report: AEODiagnosticReport, is_full: bool = False) -> None:
    """Validates llms.txt or llms-full.txt content according to llmstxt.org rules."""
    key = "llms_full_txt" if is_full else "llms_txt"
    report.artifacts_checked[key] = True

    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        report.add_error(f"{'llms-full.txt' if is_full else 'llms.txt'} is empty", 25.0)
        return

    # Check for H1 title
    has_h1 = any(line.startswith("# ") or (is_full and "=" in line) for line in lines[:5])
    if has_h1:
        report.add_pass(f"{'llms-full.txt' if is_full else 'llms.txt'} contains valid title header")
    else:
        report.add_error("llms.txt must start with a markdown '# <Project Name>' title", 10.0)

    # Check for summary blockquote in standard llms.txt
    if not is_full:
        has_blockquote = any(line.startswith("> ") for line in lines[:8])
        if has_blockquote:
            report.add_pass("llms.txt contains mandatory blockquote summary ('> ...')")
        else:
            report.add_warn("llms.txt should contain a concise blockquote summary per llmstxt.org", 5.0)

    # Check for markdown links
    link_matches = re.findall(r'\[([^\]]+)\]\((https?://[^\)]+|\/[^\)]+)\)', content)
    if len(link_matches) >= 3:
        report.add_pass(f"{'llms-full.txt' if is_full else 'llms.txt'} contains {len(link_matches)} structured markdown links")
    elif len(link_matches) > 0:
        report.add_warn(f"Found only {len(link_matches)} markdown link(s); recommend at least 3", 3.0)
    else:
        report.add_error(f"{'llms-full.txt' if is_full else 'llms.txt'} lacks markdown resource links", 10.0)


def validate_ai_txt_content(content: str, report: AEODiagnosticReport) -> None:
    """Validates ai.txt machine discovery manifest."""
    report.artifacts_checked["ai_txt"] = True

    required_fields = ["User-Agent", "Canonical-URL", "Schema-Org-Graph", "LLMs-Txt"]
    for rf in required_fields:
        if rf.lower() in content.lower():
            report.add_pass(f"ai.txt defines directive: {rf}")
        else:
            report.add_warn(f"ai.txt missing recommended field: {rf}", 3.0)


def validate_robots_txt_content(content: str, report: AEODiagnosticReport) -> None:
    """Validates robots.txt for AI search crawler authorizations."""
    report.artifacts_checked["robots_txt"] = True

    crawlers = ["GPTBot", "PerplexityBot", "ClaudeBot", "Applebot", "Google-Extended"]
    found_crawlers = [c for c in crawlers if c.lower() in content.lower()]

    if len(found_crawlers) >= 3:
        report.add_pass(f"robots.txt contains directives for {len(found_crawlers)} AI search bots ({', '.join(found_crawlers)})")
    elif len(found_crawlers) > 0:
        report.add_warn(f"robots.txt only specifies {len(found_crawlers)} AI bot(s); consider adding GPTBot, PerplexityBot, ClaudeBot", 5.0)
    else:
        report.add_warn("robots.txt lacks explicit permissions for modern AI search bots (GPTBot, PerplexityBot, ClaudeBot)", 8.0)

    if "sitemap:" in content.lower():
        report.add_pass("robots.txt declares canonical Sitemap URI")
    else:
        report.add_warn("robots.txt missing Sitemap directive", 3.0)


def validate_html_file(file_path: Path, report: AEODiagnosticReport) -> None:
    """Validates JSON-LD script tag in an HTML file."""
    report.artifacts_checked["html_injection"] = True
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        match = re.search(r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>', content, re.DOTALL | re.IGNORECASE)
        if match:
            raw_json = match.group(1).strip()
            parsed = json.loads(raw_json)
            report.add_pass(f"HTML file '{file_path.name}' contains valid embedded JSON-LD script")
            validate_schema_jsonld_dict(parsed, report)
        else:
            report.add_warn(f"HTML file '{file_path.name}' does not have an embedded application/ld+json script tag", 8.0)
    except Exception as e:
        report.add_error(f"Failed to parse HTML or embedded JSON-LD in '{file_path.name}': {e}", 15.0)


def validate_aeo_bundle(target: Union[str, Path]) -> AEODiagnosticReport:
    """
    Validates an AEO bundle directory or single artifact file.
    Calculates 0-100 AEO Readiness Score and provides detailed diagnostics.
    """
    path = Path(target).resolve()
    report = AEODiagnosticReport(str(path))

    if not path.exists():
        report.add_error(f"Target path does not exist: {path}", 100.0)
        return report

    if path.is_file():
        filename = path.name.lower()
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()

            if filename.endswith(".json"):
                parsed = json.loads(content)
                validate_schema_jsonld_dict(parsed, report)
            elif filename == "llms.txt":
                validate_llms_txt_content(content, report, is_full=False)
            elif filename == "llms-full.txt":
                validate_llms_txt_content(content, report, is_full=True)
            elif filename == "ai.txt":
                validate_ai_txt_content(content, report)
            elif filename == "robots.txt":
                validate_robots_txt_content(content, report)
            elif filename.endswith(".html") or filename.endswith(".htm"):
                validate_html_file(path, report)
            else:
                report.add_warn(f"Unrecognized file type for AEO validation: {filename}", 10.0)
        except Exception as e:
            report.add_error(f"Failed to read or parse file '{filename}': {e}", 25.0)
        return report

    # Directory validation
    schema_file = path / "schema-graph.json"
    if schema_file.exists():
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                parsed = json.loads(f.read())
            validate_schema_jsonld_dict(parsed, report)
        except Exception as e:
            report.add_error(f"Failed to parse schema-graph.json: {e}", 20.0)
    else:
        report.add_warn("schema-graph.json not found in directory", 15.0)

    llms_file = path / "llms.txt"
    if llms_file.exists():
        try:
            with open(llms_file, "r", encoding="utf-8") as f:
                validate_llms_txt_content(f.read(), report, is_full=False)
        except Exception as e:
            report.add_error(f"Failed to read llms.txt: {e}", 15.0)
    else:
        report.add_warn("llms.txt not found in directory", 15.0)

    llms_full_file = path / "llms-full.txt"
    if llms_full_file.exists():
        try:
            with open(llms_full_file, "r", encoding="utf-8") as f:
                validate_llms_txt_content(f.read(), report, is_full=True)
        except Exception as e:
            report.add_error(f"Failed to read llms-full.txt: {e}", 10.0)
    else:
        report.add_warn("llms-full.txt not found in directory", 8.0)

    ai_file = path / "ai.txt"
    if ai_file.exists():
        try:
            with open(ai_file, "r", encoding="utf-8") as f:
                validate_ai_txt_content(f.read(), report)
        except Exception as e:
            report.add_error(f"Failed to read ai.txt: {e}", 10.0)
    else:
        report.add_warn("ai.txt not found in directory", 5.0)

    robots_file = path / "robots.txt"
    if robots_file.exists():
        try:
            with open(robots_file, "r", encoding="utf-8") as f:
                validate_robots_txt_content(f.read(), report)
        except Exception as e:
            report.add_error(f"Failed to read robots.txt: {e}", 10.0)
    else:
        report.add_warn("robots.txt not found in directory", 8.0)

    # Check for any index.html
    html_file = path / "index.html"
    if html_file.exists():
        validate_html_file(html_file, report)

    return report

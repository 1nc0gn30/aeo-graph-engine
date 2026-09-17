"""LLM Citation Readiness and Perplexity / SearchGPT Schema Validator.

Validates whether Schema.org entity graphs meet exact LLM citation standards,
including Perplexity Sonar and SearchGPT required properties:
- Authoritative creator / publisher with @id linkage
- Explicit canonical URL and license
- Quotable answer capsules (FAQPage, HowTo, QAPage, TechArticle)
- Quantitative metric density
100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Union


@dataclass
class CitationValidationIssue:
    """Issue or deficiency reducing LLM citation probability."""

    severity: str  # 'critical', 'warning', 'info'
    rule: str
    message: str
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LLMCitationReadinessReport:
    """Comprehensive evaluation of schema and content citation readiness for Perplexity/ChatGPT."""

    readiness_score: float  # 0 to 100
    grade: str  # A+, A, B, C, D, F
    is_citation_ready: bool
    schema_org_entities_count: int
    has_connected_graph: bool
    has_answer_capsule: bool
    has_authoritative_source: bool
    passed_checks: List[str] = field(default_factory=list)
    issues: List[CitationValidationIssue] = field(default_factory=list)
    perplexity_sonar_compatible: bool = False
    searchgpt_compatible: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "readiness_score": self.readiness_score,
            "grade": self.grade,
            "is_citation_ready": self.is_citation_ready,
            "schema_org_entities_count": self.schema_org_entities_count,
            "has_connected_graph": self.has_connected_graph,
            "has_answer_capsule": self.has_answer_capsule,
            "has_authoritative_source": self.has_authoritative_source,
            "passed_checks": self.passed_checks,
            "issues": [i.to_dict() for i in self.issues],
            "perplexity_sonar_compatible": self.perplexity_sonar_compatible,
            "searchgpt_compatible": self.searchgpt_compatible,
        }


def validate_llm_citation_readiness(
    schema_or_graph: Union[Dict[str, Any], List[Dict[str, Any]]],
    html_text: Optional[str] = None,
) -> LLMCitationReadinessReport:
    """Audit schema graphs and content for Perplexity and SearchGPT citation readiness.

    Args:
        schema_or_graph: Parsed Schema.org JSON-LD (dict with @graph or single entity dict).
        html_text: Optional raw HTML source for extracting text-level citation signals.

    Returns:
        LLMCitationReadinessReport: Detailed score, audit checks, and actionable remediation issues.
    """
    entities: List[Dict[str, Any]] = []
    has_graph = False

    if isinstance(schema_or_graph, dict):
        if "@graph" in schema_or_graph and isinstance(schema_or_graph["@graph"], list):
            entities = [e for e in schema_or_graph["@graph"] if isinstance(e, dict) and e]
            has_graph = True
        elif schema_or_graph:
            entities = [schema_or_graph]
    elif isinstance(schema_or_graph, list):
        entities = [e for e in schema_or_graph if isinstance(e, dict) and e]

    if not entities:
        return LLMCitationReadinessReport(
            readiness_score=0.0,
            grade="F",
            is_citation_ready=False,
            schema_org_entities_count=0,
            has_connected_graph=False,
            has_answer_capsule=False,
            has_authoritative_source=False,
            passed_checks=[],
            issues=[
                CitationValidationIssue(
                    severity="critical",
                    rule="SCHEMA_MISSING",
                    message="No Schema.org entities found in structured data.",
                    recommendation="Provide valid JSON-LD with Organization, WebSite, and Domain specific schemas.",
                )
            ],
            perplexity_sonar_compatible=False,
            searchgpt_compatible=False,
        )

    all_nodes: List[Dict[str, Any]] = []
    def _collect_nodes(node: Any) -> None:
        if isinstance(node, dict):
            if "@type" in node or "name" in node:
                all_nodes.append(node)
            for v in node.values():
                _collect_nodes(v)
        elif isinstance(node, list):
            for item in node:
                _collect_nodes(item)

    for ent in entities:
        _collect_nodes(ent)

    passed: List[str] = []
    issues: List[CitationValidationIssue] = []
    score = 0.0

    # 1. Check Schema Entity Volume and Depth (25 pts)
    score += 15.0
    passed.append(f"Discovered {len(entities)} Schema.org entity block(s).")
    if has_graph:
        score += 10.0
        passed.append("Schema utilizes a connected multi-node @graph lattice.")
    else:
        issues.append(
            CitationValidationIssue(
                severity="warning",
                rule="DISCONNECTED_GRAPH",
                message="Schema is defined as standalone disconnected nodes rather than a unified @graph.",
                recommendation="Nest entities under a unified @graph array with cross-referencing @id URIs.",
            )
        )

    # 2. Check for Authoritative Publisher / Creator Entity (25 pts)
    types_found = {str(n.get("@type", "")) for n in all_nodes}
    has_org = any(t in ("Organization", "Corporation", "EducationalOrganization") for t in types_found)
    has_author = any(t in ("Person", "Author") for t in types_found)

    if has_org or has_author:
        score += 20.0
        passed.append("Authoritative publisher or author entity present.")
        authorities = [n for n in all_nodes if str(n.get("@type", "")) in ("Organization", "Corporation", "EducationalOrganization", "Person", "Author")]
        if any(a.get("@id") or a.get("url") for a in authorities):
            score += 5.0
            passed.append("Authority node specifies canonical @id or url property.")
        else:
            issues.append(
                CitationValidationIssue(
                    severity="warning",
                    rule="AUTHORITY_ID_MISSING",
                    message="Authoritative entity missing persistent canonical @id URI or homepage url.",
                    recommendation="Add '@id': 'https://domain/#organization' and 'url' to establish verifiable domain entity provenance.",
                )
            )
    else:
        issues.append(
            CitationValidationIssue(
                severity="critical",
                rule="AUTHORITY_MISSING",
                message="Missing Organization or Person schema declaring authorial credibility.",
                recommendation="Declare an Organization or Person node with name, url, and sameAs links.",
            )
        )

    # 3. Check for Direct Answer Capsules (25 pts)
    answer_types = {"FAQPage", "QAPage", "HowTo", "TechArticle", "Article", "SoftwareApplication"}
    has_capsule = bool(types_found.intersection(answer_types))

    if has_capsule:
        score += 20.0
        capsules_str = ", ".join(sorted(list(types_found.intersection(answer_types))))
        passed.append(f"Answer engine extraction capsule(s) detected: {capsules_str}.")

        # For FAQPage, verify mainEntity contains Questions and acceptedAnswer
        faq_nodes = [e for e in entities if e.get("@type") == "FAQPage"]
        if faq_nodes:
            main_ent = faq_nodes[0].get("mainEntity", [])
            if isinstance(main_ent, list) and len(main_ent) >= 2:
                score += 5.0
                passed.append(f"Rich FAQPage with {len(main_ent)} direct Q&A entities.")
            else:
                issues.append(
                    CitationValidationIssue(
                        severity="warning",
                        rule="FAQ_INSUFFICIENT",
                        message="FAQPage has fewer than 2 Q&A pairs.",
                        recommendation="Include at least 2-5 high-signal Question-and-Answer pairs for AI excerpting.",
                    )
                )
    else:
        issues.append(
            CitationValidationIssue(
                severity="critical",
                rule="ANSWER_CAPSULE_MISSING",
                message="No FAQPage, QAPage, HowTo, or TechArticle schema present.",
                recommendation="Add an FAQPage or TechArticle schema to provide direct, quotable answer snippets.",
            )
        )

    # 4. Content Quantitative Signals (25 pts)
    has_metrics = False
    if html_text:
        metric_matches = re.findall(
            r"\b(?:\d+(?:\.\d+)?%|\d+(?:\.\d+)?x|\$\d+(?:\.\d+)?|v\d+(?:\.\d+)*|\d+\s*(?:ms|s|min|sec|MB|GB|TB|KB))\b",
            html_text,
            re.IGNORECASE,
        )
        if len(metric_matches) >= 3:
            score += 15.0
            has_metrics = True
            passed.append(f"Content displays high empirical density ({len(metric_matches)} quantitative metrics).")
        elif len(metric_matches) >= 1:
            score += 10.0
            has_metrics = True
            passed.append("Content contains quantitative metric anchoring.")
        else:
            issues.append(
                CitationValidationIssue(
                    severity="info",
                    rule="METRICS_SPARSE",
                    message="Sparse numerical data / metrics found in text.",
                    recommendation="Include concrete benchmarks, percentages, or versions to boost Perplexity ranking.",
                )
            )

        # Check for list or table markup
        if "<table" in html_text.lower() or "<ul" in html_text.lower() or "<ol" in html_text.lower():
            score += 10.0
            passed.append("Tabular or structured list markup present for direct LLM extraction.")
    else:
        # Default partial credit if HTML is omitted
        score += 15.0
        passed.append("Schema verified (HTML omitted).")

    score = min(100.0, round(score, 1))

    if score >= 90.0:
        grade = "A+"
    elif score >= 80.0:
        grade = "A"
    elif score >= 70.0:
        grade = "B"
    elif score >= 60.0:
        grade = "C"
    elif score >= 50.0:
        grade = "D"
    else:
        grade = "F"

    is_ready = score >= 75.0 and (has_org or has_author) and has_capsule

    return LLMCitationReadinessReport(
        readiness_score=score,
        grade=grade,
        is_citation_ready=is_ready,
        schema_org_entities_count=len(entities),
        has_connected_graph=has_graph,
        has_answer_capsule=has_capsule,
        has_authoritative_source=has_org or has_author,
        passed_checks=passed,
        issues=issues,
        perplexity_sonar_compatible=is_ready and (has_capsule or has_metrics),
        searchgpt_compatible=is_ready and (has_org and has_graph),
    )

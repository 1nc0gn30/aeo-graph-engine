"""Semantic Triplet & Knowledge Graph Entity Resolver Engine for AEO / GEO.

Extracts subject-predicate-object semantic triplets from raw HTML and Markdown content,
computes entity graph centrality via PageRank, audits Schema.org @graph alignment and
detects orphan concepts, and synthesizes structured knowledge graph enrichment patches.

100% Python Standard Library. Zero external dependencies.
"""

from __future__ import annotations

import html
import json
import math
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple, Union


# Predicate mappings to Schema.org properties and Wikidata concepts
PREDICATE_SCHEMA_MAP: Dict[str, str] = {
    "is_a": "@type",
    "type_of": "@type",
    "instance_of": "@type",
    "created_by": "creator",
    "developed_by": "author",
    "maintained_by": "maintainer",
    "founded_by": "founder",
    "offers": "offers",
    "provides": "itemOffered",
    "features": "featureList",
    "supports": "knowsAbout",
    "integrates_with": "isRelatedTo",
    "depends_on": "requires",
    "runs_on": "operatingSystem",
    "built_on": "isBasedOn",
    "enables": "purpose",
    "automates": "purpose",
    "located_in": "location",
    "part_of": "isPartOf",
    "mentions": "mentions",
    "about": "about",
}

# Known authority Wikidata mappings for common tech entities
COMMON_WIKIDATA_ENTITIES: Dict[str, str] = {
    "python": "https://www.wikidata.org/wiki/Q28865",
    "javascript": "https://www.wikidata.org/wiki/Q2005",
    "typescript": "https://www.wikidata.org/wiki/Q21201",
    "react": "https://www.wikidata.org/wiki/Q19399674",
    "next.js": "https://www.wikidata.org/wiki/Q110852994",
    "astro": "https://www.wikidata.org/wiki/Q118287848",
    "schema.org": "https://www.wikidata.org/wiki/Q3475330",
    "json-ld": "https://www.wikidata.org/wiki/Q3178101",
    "google": "https://www.wikidata.org/wiki/Q95",
    "openai": "https://www.wikidata.org/wiki/Q22670182",
    "anthropic": "https://www.wikidata.org/wiki/Q117286395",
    "perplexity": "https://www.wikidata.org/wiki/Q115865243",
    "github": "https://www.wikidata.org/wiki/Q364",
    "solana": "https://www.wikidata.org/wiki/Q108876426",
    "ethereum": "https://www.wikidata.org/wiki/Q20667575",
}


@dataclass
class SemanticTriplet:
    """Directed semantic relationship extracted from content."""

    subject: str
    predicate: str
    object: str
    confidence: float
    context_snippet: str = ""
    inferred_schema_property: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class EntityNode:
    """Knowledge graph entity with structural centrality and schema coverage metrics."""

    name: str
    entity_type: str
    salience: float  # 0.0 to 1.0 (Composite importance score)
    pagerank: float  # Stationary graph distribution
    degree: int
    in_degree: int
    out_degree: int
    frequency: int
    in_schema: bool = False
    wikidata_id: Optional[str] = None
    same_as: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KnowledgeGraphReport:
    """Complete analysis of content semantic triplets and Schema.org alignment."""

    triplets_count: int
    entities_count: int
    entity_coverage_score: float  # 0.0 to 100.0%
    graph_density: float
    triplets: List[SemanticTriplet]
    entities: List[EntityNode]
    orphan_entities: List[str]  # High-salience entities missing in Schema.org
    suggested_schema_patches: List[Dict[str, Any]]
    rdf_ntriples: str
    turtle: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "triplets_count": self.triplets_count,
            "entities_count": self.entities_count,
            "entity_coverage_score": round(self.entity_coverage_score, 2),
            "graph_density": round(self.graph_density, 4),
            "triplets": [t.to_dict() for t in self.triplets],
            "entities": [e.to_dict() for e in self.entities],
            "orphan_entities": self.orphan_entities,
            "suggested_schema_patches": self.suggested_schema_patches,
            "rdf_ntriples": self.rdf_ntriples,
            "turtle": self.turtle,
        }


def _clean_html_to_text(html_content: str) -> str:
    """Strip scripts, styles, and markup to clean raw text while retaining heading markers."""
    cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", r"\n### \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<li[^>]*>(.*?)</li>", r"\n- \1\n", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = html.unescape(cleaned)
    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    return "\n".join(lines)


def _sanitize_entity_name(raw: str) -> str:
    """Normalize extracted entity token."""
    text = re.sub(r"[^\w\s\-\.\/\@]", "", raw).strip()
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing punctuation
    text = text.strip(".-_ ")
    return text


def extract_semantic_triplets(
    text_or_html: str,
    min_confidence: float = 0.4,
) -> List[SemanticTriplet]:
    """Extract semantic (subject, predicate, object) triplets from text or HTML.

    Applies deterministic linguistic pattern heuristics:
    1. Copula / Identity: X is an? (open-source)? Y
    2. Authorship: X was (created|developed|founded|maintained) by Y
    3. Capabilities: X (offers|provides|features|supports|includes) Y
    4. Integrations: X (integrates with|connects to|depends on|built on) Y
    5. Purpose / Actions: X (enables|automates|accelerates|secures) Y
    6. Locations: X is (located|headquartered|based) in Y
    """
    raw_text = text_or_html
    if "<html" in text_or_html.lower() or "<body" in text_or_html.lower() or "<div" in text_or_html.lower():
        raw_text = _clean_html_to_text(text_or_html)

    triplets: List[SemanticTriplet] = []
    seen: Set[Tuple[str, str, str]] = set()

    # Rule definitions: (regex, predicate_key, default_confidence)
    patterns = [
        # 1. Copula / Identity
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:is|are)\s+(?:an?|the)?\s*(?:open-source|cutting-edge|modern|autonomous)?\s*([A-Za-z0-9_\-\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "is_a",
            0.85,
        ),
        # 2. Authorship & Maintenance
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:is|was)\s+(?:created|built|developed|architected)\s+by\s+([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)(?:\.|\,|;|\n|$)",
            "developed_by",
            0.90,
        ),
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:is|was)\s+founded\s+by\s+([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)(?:\.|\,|;|\n|$)",
            "founded_by",
            0.95,
        ),
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+is\s+maintained\s+by\s+([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)(?:\.|\,|;|\n|$)",
            "maintained_by",
            0.90,
        ),
        # 3. Features & Capabilities
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:provides|offers|features|delivers)\s+([A-Za-z0-9_\-\.\s]{3,50}?)(?:\.|\,|;|\n|$)",
            "provides",
            0.80,
        ),
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+supports\s+([A-Za-z0-9_\-\.\s]{2,45}?)(?:\.|\,|;|\n|$)",
            "supports",
            0.75,
        ),
        # 4. Integrations & Dependencies
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+integrates\s+with\s+([A-Za-z0-9_\-\.\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "integrates_with",
            0.85,
        ),
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:depends\s+on|requires)\s+([A-Za-z0-9_\-\.\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "depends_on",
            0.85,
        ),
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+is\s+(?:built\s+on|powered\s+by)\s+([A-Za-z0-9_\-\.\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "built_on",
            0.80,
        ),
        # 5. Purpose & Automation
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:enables|automates|optimizes|accelerates)\s+([A-Za-z0-9_\-\.\s]{3,50}?)(?:\.|\,|;|\n|$)",
            "enables",
            0.75,
        ),
        # 6. Location
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+(?:is\s+headquartered|is\s+located|is\s+based)\s+in\s+([A-Z][A-Za-z0-9_\-\.\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "located_in",
            0.90,
        ),
        # 7. Part-of relationship
        (
            r"\b([A-Z][A-Za-z0-9_\-\.\s]{1,40}?)\s+is\s+(?:part\s+of|a\s+subsystem\s+of|a\s+module\s+of)\s+([A-Z][A-Za-z0-9_\-\.\s]{2,40}?)(?:\.|\,|;|\n|$)",
            "part_of",
            0.85,
        ),
    ]

    sentences = re.split(r"(?<=[.!?\n])\s+", raw_text)

    for sent in sentences:
        sent_clean = sent.strip()
        if not sent_clean or len(sent_clean) < 10:
            continue

        for pat, pred, base_conf in patterns:
            for match in re.finditer(pat, sent_clean):
                subj_raw, obj_raw = match.group(1), match.group(2)
                subj = _sanitize_entity_name(subj_raw)
                obj = _sanitize_entity_name(obj_raw)

                # Discard stop-word false positives
                stop_words = {"it", "this", "that", "these", "those", "which", "there", "what", "who", "all", "each"}
                if subj.lower() in stop_words or obj.lower() in stop_words:
                    continue
                if len(subj) < 2 or len(obj) < 2 or subj.lower() == obj.lower():
                    continue

                key = (subj.lower(), pred, obj.lower())
                if key in seen:
                    continue
                seen.add(key)

                schema_prop = PREDICATE_SCHEMA_MAP.get(pred, "isRelatedTo")

                triplets.append(
                    SemanticTriplet(
                        subject=subj,
                        predicate=pred,
                        object=obj,
                        confidence=base_conf,
                        context_snippet=sent_clean[:120],
                        inferred_schema_property=schema_prop,
                    )
                )

    return [t for t in triplets if t.confidence >= min_confidence]


def compute_pagerank(
    entities: List[str],
    adjacency: Dict[str, List[str]],
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """Calculate PageRank centrality vector for entity graph nodes."""
    n = len(entities)
    if n == 0:
        return {}
    if n == 1:
        return {entities[0]: 1.0}

    # Initialize uniform probability distribution
    ranks: Dict[str, float] = {e: 1.0 / n for e in entities}
    out_degree: Dict[str, int] = {e: len(adjacency.get(e, [])) for e in entities}

    for _ in range(max_iter):
        new_ranks: Dict[str, float] = {e: (1.0 - damping) / n for e in entities}

        # Calculate dangling node mass (nodes with zero out-edges)
        dangling_sum = sum(ranks[e] for e in entities if out_degree[e] == 0)
        dangling_contrib = (damping * dangling_sum) / n

        for u in entities:
            for v in adjacency.get(u, []):
                if v in new_ranks and out_degree[u] > 0:
                    new_ranks[v] += damping * (ranks[u] / out_degree[u])

        for e in entities:
            new_ranks[e] += dangling_contrib

        # Check convergence L1-norm
        diff = sum(abs(new_ranks[e] - ranks[e]) for e in entities)
        ranks = new_ranks
        if diff < tol:
            break

    # Normalize sum to 1.0
    total = sum(ranks.values()) or 1.0
    return {k: v / total for k, v in ranks.items()}


def build_entity_graph(
    triplets: List[SemanticTriplet],
    raw_text: str = "",
) -> Tuple[List[EntityNode], Dict[str, List[str]], float]:
    """Construct entity graph and compute topological metrics and PageRank."""
    adjacency: Dict[str, List[str]] = defaultdict(list)
    in_degrees: Dict[str, int] = defaultdict(int)
    out_degrees: Dict[str, int] = defaultdict(int)
    frequencies: Dict[str, int] = defaultdict(int)
    entity_name_map: Dict[str, str] = {}  # lower -> original

    for t in triplets:
        s_norm = t.subject.lower()
        o_norm = t.object.lower()
        entity_name_map[s_norm] = t.subject
        entity_name_map[o_norm] = t.object

        adjacency[s_norm].append(o_norm)
        out_degrees[s_norm] += 1
        in_degrees[o_norm] += 1

        frequencies[s_norm] += 1
        frequencies[o_norm] += 1

    all_nodes = list(entity_name_map.keys())
    if not all_nodes:
        return [], {}, 0.0

    # Calculate PageRank
    pagerank_scores = compute_pagerank(all_nodes, adjacency)

    # Graph density: E / (V * (V - 1))
    v = len(all_nodes)
    total_edges = sum(len(neighbors) for neighbors in adjacency.values())
    density = total_edges / (v * (v - 1)) if v > 1 else 0.0

    # Classify entity types and infer authority IDs
    nodes: List[EntityNode] = []
    max_pr = max(pagerank_scores.values()) if pagerank_scores else 1.0
    max_freq = max(frequencies.values()) if frequencies else 1.0

    for norm_name, orig_name in entity_name_map.items():
        pr = pagerank_scores.get(norm_name, 0.0)
        freq = frequencies.get(norm_name, 1)

        # Composite salience score (0.0 - 1.0)
        norm_pr = pr / max_pr if max_pr > 0 else 0.0
        norm_f = freq / max_freq if max_freq > 0 else 0.0
        salience = round(0.6 * norm_pr + 0.4 * norm_f, 3)

        # Authority resolution lookup
        wikidata_url = COMMON_WIKIDATA_ENTITIES.get(norm_name)
        same_as = [wikidata_url] if wikidata_url else []

        # Simple entity type heuristic
        if norm_name in ("python", "javascript", "typescript", "solana", "ethereum", "react", "next.js", "astro"):
            e_type = "SoftwareApplication"
        elif any(w in norm_name for w in ("foundation", "lab", "team", "technologies", "inc", "corp", "org")):
            e_type = "Organization"
        elif norm_name in ("schema.org", "json-ld", "rest", "graphql", "mcp"):
            e_type = "Intangible"
        else:
            e_type = "Thing"

        nodes.append(
            EntityNode(
                name=orig_name,
                entity_type=e_type,
                salience=salience,
                pagerank=round(pr, 4),
                degree=in_degrees[norm_name] + out_degrees[norm_name],
                in_degree=in_degrees[norm_name],
                out_degree=out_degrees[norm_name],
                frequency=freq,
                in_schema=False,
                wikidata_id=wikidata_url,
                same_as=same_as,
            )
        )

    # Sort nodes by salience descending
    nodes.sort(key=lambda n: n.salience, reverse=True)
    return nodes, adjacency, density


def _extract_schema_entities(schema_or_graph: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Set[str]:
    """Collect all entity names, types, IDs, and property names mentioned in Schema.org JSON-LD."""
    names: Set[str] = set()

    def _traverse(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in ("name", "legalName", "alternateName", "headline", "title", "operatingSystem"):
                    if isinstance(v, str):
                        names.add(v.strip().lower())
                elif k in ("@type",):
                    if isinstance(v, str):
                        names.add(v.strip().lower())
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                names.add(item.strip().lower())
                elif k in ("@id", "url", "sameAs"):
                    if isinstance(v, str):
                        names.add(v.strip().lower())
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                names.add(item.strip().lower())
                _traverse(v)
        elif isinstance(obj, list):
            for item in obj:
                _traverse(item)

    _traverse(schema_or_graph)
    return names


def audit_knowledge_graph_schema_alignment(
    triplets: List[SemanticTriplet],
    entities: List[EntityNode],
    schema_or_graph: Union[Dict[str, Any], List[Dict[str, Any]]],
    base_url: str = "https://example.com",
) -> KnowledgeGraphReport:
    """Audit semantic knowledge graph coverage against Schema.org JSON-LD definitions."""
    schema_names = _extract_schema_entities(schema_or_graph)

    # Update in_schema state
    matched_count = 0
    orphan_entities: List[str] = []

    for e in entities:
        norm = e.name.lower()
        # Direct match or partial substring match in schema tokens
        is_matched = any(norm == s_token or norm in s_token for s_token in schema_names)
        e.in_schema = is_matched
        if is_matched:
            matched_count += 1
        elif e.salience >= 0.4:
            orphan_entities.append(e.name)

    coverage_score = (matched_count / len(entities) * 100.0) if entities else 100.0

    # Build suggested Schema.org patches for orphan concepts
    suggested_patches: List[Dict[str, Any]] = []
    for orphan in orphan_entities[:5]:
        norm = orphan.lower()
        wikidata = COMMON_WIKIDATA_ENTITIES.get(norm)
        patch_entry: Dict[str, Any] = {
            "@type": "DefinedTerm",
            "name": orphan,
            "description": f"Core entity identified by knowledge graph extractor with high salience.",
        }
        if wikidata:
            patch_entry["sameAs"] = wikidata
            patch_entry["@id"] = f"{base_url.rstrip('/')}/#entity-{re.sub(r'[^a-zA-Z0-9]', '-', orphan).lower()}"
        suggested_patches.append(patch_entry)

    # Generate RDF N-Triples & Turtle
    rdf_triples = export_rdf_ntriples(triplets, base_url=base_url)
    turtle = export_turtle(triplets, base_url=base_url)

    # Compute graph density
    v = len(entities)
    total_edges = len(triplets)
    density = (total_edges / (v * (v - 1))) if v > 1 else 0.0

    return KnowledgeGraphReport(
        triplets_count=len(triplets),
        entities_count=len(entities),
        entity_coverage_score=coverage_score,
        graph_density=density,
        triplets=triplets,
        entities=entities,
        orphan_entities=orphan_entities,
        suggested_schema_patches=suggested_patches,
        rdf_ntriples=rdf_triples,
        turtle=turtle,
    )


def export_rdf_ntriples(triplets: List[SemanticTriplet], base_url: str = "https://example.com") -> str:
    """Format extracted triplets as W3C standard RDF N-Triples (<subject> <predicate> <object> .)."""
    base = base_url.rstrip("/")
    lines = []
    for t in triplets:
        s_uri = f"<{base}/resource/{re.sub(r'[^a-zA-Z0-9]', '_', t.subject)}>"
        p_uri = f"<https://schema.org/{t.inferred_schema_property or 'isRelatedTo'}>"
        o_clean = t.object.replace('"', '\\"').replace("\n", " ")
        o_val = f'"{o_clean}"'
        lines.append(f"{s_uri} {p_uri} {o_val} .")
    return "\n".join(lines)


def export_turtle(triplets: List[SemanticTriplet], base_url: str = "https://example.com") -> str:
    """Format extracted triplets as W3C Turtle document with prefixes."""
    base = base_url.rstrip("/")
    header = [
        "@prefix schema: <https://schema.org/> .",
        f"@prefix res: <{base}/resource/> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
    ]
    lines = list(header)
    for t in triplets:
        s_id = f"res:{re.sub(r'[^a-zA-Z0-9]', '_', t.subject)}"
        p_id = f"schema:{t.inferred_schema_property or 'isRelatedTo'}"
        o_clean = t.object.replace('"', '\\"').replace("\n", " ")
        lines.append(f'{s_id} {p_id} "{o_clean}" .')
    return "\n".join(lines)


def analyze_knowledge_graph(
    text_or_html: str,
    schema_or_graph: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = None,
    base_url: str = "https://example.com",
    min_confidence: float = 0.4,
) -> KnowledgeGraphReport:
    """High-level facade to extract triplets, compute centrality, and audit Schema.org alignment."""
    triplets = extract_semantic_triplets(text_or_html, min_confidence=min_confidence)
    entities, _, _ = build_entity_graph(triplets, raw_text=text_or_html)

    target_schema = schema_or_graph or {}
    return audit_knowledge_graph_schema_alignment(
        triplets=triplets,
        entities=entities,
        schema_or_graph=target_schema,
        base_url=base_url,
    )

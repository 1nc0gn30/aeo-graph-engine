"""
Schema.org JSON-LD Knowledge Graph Visualizer for AEO Graph Engine.
Renders interactive Mermaid flowchart diagrams and hierarchical ASCII trees
representing interconnected Schema.org @graph entities, cross-references, and properties.
Zero external runtime dependencies (Python standard library).
"""

import json
import re
from typing import Dict, Any, List, Optional, Set, Tuple, Union


def _sanitize_mermaid_id(raw_id: str) -> str:
    """Sanitizes strings for safe use as Mermaid node identifiers."""
    if not raw_id:
        return "node_anon"
    # Strip URL fragments or domain prefixes to keep IDs readable
    clean = re.sub(r'^https?://[^/]+/?', '', raw_id)
    clean = clean.lstrip("#/").replace("/", "_").replace("#", "_").replace("-", "_").replace(".", "_")
    clean = re.sub(r'[^a-zA-Z0-9_]', '_', clean)
    clean = re.sub(r'_+', '_', clean).strip('_')
    if not clean or clean[0].isdigit():
        clean = "node_" + clean
    return clean or "node_anon"


def _sanitize_mermaid_label(text: str) -> str:
    """Sanitizes label text to prevent Mermaid parser errors."""
    if not text:
        return ""
    # Replace troublesome characters
    sanitized = text.replace('"', "'").replace("\n", " ").replace("\r", " ")
    sanitized = sanitized.replace("[", "(").replace("]", ")")
    sanitized = sanitized.replace("{", "(").replace("}", ")")
    sanitized = sanitized.replace("<", "&lt;").replace(">", "&gt;")
    # Truncate if excessively long
    if len(sanitized) > 60:
        sanitized = sanitized[:57] + "..."
    return sanitized.strip()


def extract_graph_nodes_and_edges(schema_graph: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Extracts unified nodes and directed edges from Schema.org JSON-LD (supports both @graph and single objects).
    Returns (nodes, edges) where:
      nodes: list of {"id": str, "raw_id": str, "type": str, "name": str, "data": dict}
      edges: list of {"source": str, "target": str, "relation": str}
    """
    entities: List[Dict[str, Any]] = []

    if isinstance(schema_graph, dict):
        if not schema_graph:
            entities = []
        elif "@graph" in schema_graph and isinstance(schema_graph["@graph"], list):
            entities = schema_graph["@graph"]
        elif set(schema_graph.keys()) <= {"@context"}:
            entities = []
        else:
            entities = [schema_graph]
    elif isinstance(schema_graph, list):
        entities = schema_graph

    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    id_to_node: Dict[str, Dict[str, Any]] = {}
    known_node_ids: Set[str] = set()

    # Pass 1: Extract explicitly declared entities
    for idx, ent in enumerate(entities):
        if not isinstance(ent, dict) or not ent or set(ent.keys()) <= {"@context"}:
            continue

        raw_id = ent.get("@id") or f"anon_entity_{idx+1}"
        node_id = _sanitize_mermaid_id(raw_id)
        if node_id in known_node_ids:
            node_id = f"{node_id}_{idx+1}"
        known_node_ids.add(node_id)

        ent_type = ent.get("@type", "Thing")
        if isinstance(ent_type, list):
            ent_type = "/".join(str(t) for t in ent_type)

        ent_name = ent.get("name") or ent.get("legalName") or ent.get("headline") or ent.get("title") or ent_type

        node_obj = {
            "id": node_id,
            "raw_id": str(raw_id),
            "type": str(ent_type),
            "name": str(ent_name),
            "data": ent
        }
        nodes.append(node_obj)
        id_to_node[str(raw_id)] = node_obj
        id_to_node[node_id] = node_obj

    # Pass 2: Extract relationships and nested anonymous nodes
    nested_counter = 0

    def process_sub_entity(parent_node_id: str, relation: str, val: Any):
        nonlocal nested_counter
        if isinstance(val, dict):
            # Check if it's a reference to an existing @id
            if "@id" in val and len(val) == 1 and str(val["@id"]) in id_to_node:
                target_node = id_to_node[str(val["@id"])]
                edges.append({
                    "source": parent_node_id,
                    "target": target_node["id"],
                    "relation": relation
                })
                return

            if "@id" in val and str(val["@id"]) in id_to_node:
                target_node = id_to_node[str(val["@id"])]
                edges.append({
                    "source": parent_node_id,
                    "target": target_node["id"],
                    "relation": relation
                })
                return

            # Otherwise, it's a nested sub-entity (like Person, ContactPoint, Offer, Question, SearchAction)
            sub_type = val.get("@type", relation.capitalize())
            sub_name = val.get("name") or val.get("jobTitle") or val.get("contactType") or val.get("price") or val.get("target") or sub_type
            if relation == "offers" and "price" in val:
                sub_name = f"Offer (${val.get('price')} {val.get('priceCurrency', 'USD')})"

            nested_counter += 1
            nested_id = f"{parent_node_id}_{_sanitize_mermaid_id(relation)}_{nested_counter}"
            sub_node = {
                "id": nested_id,
                "raw_id": val.get("@id", f"nested_{nested_counter}"),
                "type": str(sub_type),
                "name": str(sub_name),
                "data": val
            }
            nodes.append(sub_node)
            id_to_node[nested_id] = sub_node
            edges.append({
                "source": parent_node_id,
                "target": nested_id,
                "relation": relation
            })

            # Check nested properties inside this sub-entity (e.g., Question -> acceptedAnswer)
            for sub_k, sub_v in val.items():
                if sub_k not in ("@context", "@type", "@id", "name", "description", "url"):
                    if isinstance(sub_v, dict):
                        process_sub_entity(nested_id, sub_k, sub_v)
                    elif isinstance(sub_v, list):
                        for sub_item in sub_v:
                            if isinstance(sub_item, dict):
                                process_sub_entity(nested_id, sub_k, sub_item)

        elif isinstance(val, list):
            for item in val:
                if isinstance(item, dict):
                    process_sub_entity(parent_node_id, relation, item)

    relationship_keys = {
        "publisher", "creator", "author", "founder", "contactPoint",
        "potentialAction", "offers", "mainEntity", "isPartOf", "about",
        "itemListElement", "hasPart", "item", "acceptedAnswer", "parentOrganization",
        "subOrganization", "organizer", "funder", "provider"
    }

    for n in list(nodes):
        data = n["data"]
        parent_id = n["id"]
        for key, val in data.items():
            if key in relationship_keys:
                if isinstance(val, dict):
                    process_sub_entity(parent_id, key, val)
                elif isinstance(val, list):
                    for item in val:
                        process_sub_entity(parent_id, key, item)

    return nodes, edges


def render_schema_mermaid(
    schema_graph: Dict[str, Any],
    direction: str = "TD",
    include_styling: bool = True
) -> str:
    """
    Renders valid Mermaid flowchart code (`flowchart TD` / `flowchart LR`)
    representing interconnected Schema.org entities with typed nodes,
    labeled relational edges, and customized color themes.
    """
    nodes, edges = extract_graph_nodes_and_edges(schema_graph)

    lines: List[str] = [
        f"flowchart {direction}",
        "    %% Schema.org Linked Knowledge Graph — Generated by AEO Graph Engine"
    ]

    # Render Node Declarations
    for n in nodes:
        nid = n["id"]
        ntype = _sanitize_mermaid_label(n["type"])
        nname = _sanitize_mermaid_label(n["name"])
        raw_id_short = _sanitize_mermaid_label(n["raw_id"].split("/")[-1]) if "#" in n["raw_id"] or "/" in n["raw_id"] else ""

        if raw_id_short and raw_id_short != nname:
            label = f"<b>{ntype}</b><br/>{nname}<br/><i><small>{raw_id_short}</small></i>"
        else:
            label = f"<b>{ntype}</b><br/>{nname}"

        lines.append(f'    {nid}["{label}"]')

    lines.append("")

    # Render Directed Edges
    for e in edges:
        src = e["source"]
        tgt = e["target"]
        rel = _sanitize_mermaid_label(e["relation"])
        lines.append(f"    {src} -->|{rel}| {tgt}")

    if include_styling and nodes:
        lines.append("")
        lines.append("    %% Entity Type Styles & Hierarchy Palette")
        lines.append("    classDef org fill:#1e3a8a,stroke:#3b82f6,color:#ffffff,stroke-width:2px;")
        lines.append("    classDef website fill:#065f46,stroke:#10b981,color:#ffffff,stroke-width:2px;")
        lines.append("    classDef app fill:#581c87,stroke:#a855f7,color:#ffffff,stroke-width:2px;")
        lines.append("    classDef faq fill:#78350f,stroke:#f59e0b,color:#ffffff,stroke-width:2px;")
        lines.append("    classDef itemlist fill:#164e63,stroke:#06b6d4,color:#ffffff,stroke-width:2px;")
        lines.append("    classDef action fill:#374151,stroke:#9ca3af,color:#ffffff,stroke-width:1px;")
        lines.append("    classDef question fill:#831843,stroke:#ec4899,color:#ffffff,stroke-width:1px;")

        for n in nodes:
            t = n["type"].lower()
            if "organization" in t or "localbusiness" in t:
                lines.append(f"    class {n['id']} org;")
            elif "website" in t or "webpage" in t:
                lines.append(f"    class {n['id']} website;")
            elif "softwareapplication" in t or "product" in t or "techarticle" in t:
                lines.append(f"    class {n['id']} app;")
            elif "faqpage" in t:
                lines.append(f"    class {n['id']} faq;")
            elif "itemlist" in t or "breadcrumblist" in t:
                lines.append(f"    class {n['id']} itemlist;")
            elif "action" in t or "offer" in t:
                lines.append(f"    class {n['id']} action;")
            elif "question" in t or "answer" in t:
                lines.append(f"    class {n['id']} question;")

    return "\n".join(lines)


def render_schema_ascii_tree(schema_graph: Dict[str, Any]) -> str:
    """
    Renders a clean, hierarchical ASCII tree diagram of Schema.org @graph entities,
    displaying entity types, identifiers, attributes, and cross-entity linkages.
    """
    nodes, edges = extract_graph_nodes_and_edges(schema_graph)

    if not nodes:
        return "Schema.org Graph: (Empty)"

    # Build adjacency mapping
    outbound: Dict[str, List[Dict[str, str]]] = {n["id"]: [] for n in nodes}
    inbound_count: Dict[str, int] = {n["id"]: 0 for n in nodes}
    node_map: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes}

    for e in edges:
        src = e["source"]
        tgt = e["target"]
        rel = e["relation"]
        if src in outbound:
            outbound[src].append({"target": tgt, "relation": rel})
        if tgt in inbound_count:
            inbound_count[tgt] += 1

    # Identify root entities (inbound_count == 0 or top-level declared in @graph)
    raw_entities = schema_graph.get("@graph", [schema_graph]) if isinstance(schema_graph, dict) else schema_graph
    top_raw_ids = set()
    if isinstance(raw_entities, list):
        for item in raw_entities:
            if isinstance(item, dict) and "@id" in item:
                top_raw_ids.add(str(item["@id"]))

    root_nodes = [n for n in nodes if n["raw_id"] in top_raw_ids or inbound_count[n["id"]] == 0]
    if not root_nodes:
        root_nodes = nodes[:1]

    # Remove duplicates from root_nodes
    seen_roots: Set[str] = set()
    unique_roots: List[Dict[str, Any]] = []
    for r in root_nodes:
        if r["id"] not in seen_roots:
            seen_roots.add(r["id"])
            unique_roots.append(r)

    lines: List[str] = [
        "Schema.org Linked Knowledge Graph",
        "=================================="
    ]

    def format_node_title(n: Dict[str, Any]) -> str:
        ntype = n["type"]
        nname = n["name"]
        raw_id = n["raw_id"]
        short_id = f" ({raw_id})" if raw_id and not raw_id.startswith("nested_") and not raw_id.startswith("anon_") else ""
        if nname and nname != ntype:
            return f"{ntype}: \"{nname}\"{short_id}"
        return f"{ntype}{short_id}"

    def build_tree(current_id: str, prefix: str, is_last: bool, visited: Set[str]):
        node = node_map.get(current_id)
        if not node:
            return

        connector = "└── " if is_last else "├── "
        title_str = format_node_title(node)
        lines.append(f"{prefix}{connector}{title_str}")

        if current_id in visited:
            sub_prefix = prefix + ("    " if is_last else "│   ")
            lines.append(f"{sub_prefix}└── (circular reference)")
            return

        new_visited = visited | {current_id}
        sub_prefix = prefix + ("    " if is_last else "│   ")

        # Get child edges
        children = outbound.get(current_id, [])

        # Also display key scalar properties
        scalar_props: List[Tuple[str, str]] = []
        data = node.get("data", {})
        interesting_keys = ["url", "inLanguage", "softwareVersion", "operatingSystem", "price", "priceCurrency", "text"]
        for ik in interesting_keys:
            if ik in data and isinstance(data[ik], (str, int, float)) and str(data[ik]).strip():
                scalar_props.append((ik, str(data[ik])))

        total_items = len(scalar_props) + len(children)

        # Render scalar properties
        for idx, (pk, pv) in enumerate(scalar_props):
            prop_is_last = (idx == len(scalar_props) - 1) and (len(children) == 0)
            p_conn = "└── " if prop_is_last else "├── "
            pv_clean = pv if len(pv) <= 50 else pv[:47] + "..."
            lines.append(f"{sub_prefix}{p_conn}{pk}: {pv_clean}")

        # Render children
        for idx, ch in enumerate(children):
            ch_is_last = (idx == len(children) - 1)
            target_id = ch["target"]
            relation = ch["relation"]
            t_node = node_map.get(target_id)
            if t_node:
                # If target is a top-level entity already printed, show link
                if t_node["raw_id"] in top_raw_ids and target_id != current_id:
                    c_conn = "└── " if ch_is_last else "├── "
                    lines.append(f"{sub_prefix}{c_conn}{relation} ──> {format_node_title(t_node)}")
                else:
                    child_connector = "└── " if ch_is_last else "├── "
                    lines.append(f"{sub_prefix}{child_connector}[{relation}]")
                    child_sub_prefix = sub_prefix + ("    " if ch_is_last else "│   ")
                    build_tree(target_id, child_sub_prefix, True, new_visited)

    for i, root in enumerate(unique_roots):
        is_last_root = (i == len(unique_roots) - 1)
        build_tree(root["id"], "", is_last_root, set())

    return "\n".join(lines)


def render_schema_summary_table(schema_graph: Dict[str, Any]) -> str:
    """
    Renders a Markdown summary table of all Schema.org entities,
    their types, canonical identifiers, and outbound relations.
    """
    nodes, edges = extract_graph_nodes_and_edges(schema_graph)

    outbound_map: Dict[str, List[str]] = {n["id"]: [] for n in nodes}
    for e in edges:
        outbound_map[e["source"]].append(f"{e['relation']} ({e['target']})")

    lines = [
        "| Entity Type | Name / Title | Identifier (@id) | Outbound Relationships |",
        "| :--- | :--- | :--- | :--- |"
    ]

    for n in nodes:
        ntype = n["type"]
        nname = n["name"] if len(n["name"]) <= 35 else n["name"][:32] + "..."
        nid = n["raw_id"] if len(n["raw_id"]) <= 40 else "..." + n["raw_id"][-37:]
        rels = ", ".join(outbound_map.get(n["id"], [])) or "None"
        if len(rels) > 45:
            rels = rels[:42] + "..."
        lines.append(f"| `{ntype}` | {nname} | `{nid}` | {rels} |")

    return "\n".join(lines)

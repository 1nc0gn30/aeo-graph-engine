"""
HTML Injection module for AEO Graph Engine.
Safely and idempotently embeds Schema.org JSON-LD scripts into HTML documents.
"""

import json
import re
from pathlib import Path
from typing import Dict, Any, Union


def inject_jsonld_into_html(
    html_content: str,
    schema_payload: Union[Dict[str, Any], str],
    indent: int = 2
) -> str:
    """
    Injects or replaces a Schema.org JSON-LD script tag in the provided HTML string.
    - If a <script type="application/ld+json"> already exists, its content is updated.
    - If no JSON-LD tag exists, a formatted script tag is inserted right before </head>.
    - If no </head> tag exists, it falls back to insertion before <body> or at the end.
    """
    if isinstance(schema_payload, (dict, list)):
        schema_json = json.dumps(schema_payload, indent=indent, ensure_ascii=False)
    else:
        # Validate that string payload is valid JSON
        parsed = json.loads(schema_payload)
        schema_json = json.dumps(parsed, indent=indent, ensure_ascii=False)

    script_tag = f'<script type="application/ld+json">\n{schema_json}\n</script>'

    # Check for existing ld+json script tag (case-insensitive regex)
    pattern = re.compile(
        r'<script\s+type=["\']application/ld\+json["\']\s*>.*?</script>',
        re.DOTALL | re.IGNORECASE
    )

    if pattern.search(html_content):
        # Replace existing tag
        return pattern.sub(script_tag, html_content, count=1)

    # Insert before </head>
    head_close_pattern = re.compile(r'(</head>)', re.IGNORECASE)
    if head_close_pattern.search(html_content):
        return head_close_pattern.sub(f'  {script_tag}\n\\1', html_content, count=1)

    # Fallback: Insert before <body>
    body_open_pattern = re.compile(r'(<body[^>]*>)', re.IGNORECASE)
    if body_open_pattern.search(html_content):
        return body_open_pattern.sub(f'{script_tag}\n\\1', html_content, count=1)

    # Fallback: Prepend to content
    return f"{script_tag}\n{html_content}"


def inject_file(
    html_file_path: Union[str, Path],
    schema_payload: Union[Dict[str, Any], str],
    backup: bool = False
) -> bool:
    """
    Reads an HTML file from disk, injects the Schema.org JSON-LD graph, and writes back.
    Optionally creates a .bak backup file.
    Returns True if successfully written.
    """
    path = Path(html_file_path).resolve()
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"HTML target file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        original = f.read()

    if backup:
        bak_path = path.with_suffix(path.suffix + ".bak")
        with open(bak_path, "w", encoding="utf-8") as f:
            f.write(original)

    updated = inject_jsonld_into_html(original, schema_payload)

    with open(path, "w", encoding="utf-8") as f:
        f.write(updated)

    return True

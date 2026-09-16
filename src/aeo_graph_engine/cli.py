"""
Command Line Interface for AEO Graph Engine.
Provides commands for generating, validating, inspecting, and testing AEO artifacts.
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Optional, List

from .core import (
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle,
    resolve_config
)
from .injector import inject_file, inject_jsonld_into_html
from .validator import validate_aeo_bundle
from .presets import NICHE_PRESETS


def run_internal_tests() -> int:
    """Runs built-in engine verification test suite."""
    print("=" * 70)
    print("⚡ RUNNING AEO GRAPH ENGINE TEST SUITE")
    print("=" * 70)

    # 1. Test Schema Graph Generation
    print("\n--- [1/5] Testing Schema.org JSON-LD Graph Generation ---")
    cfg = resolve_config(None, niche="developer_tools")
    graph = generate_schema_graph(cfg)
    assert graph["@context"] == "https://schema.org"
    assert len(graph["@graph"]) >= 5
    print(f"  ✅ Schema.org Graph validated ({len(graph['@graph'])} connected entities)")

    # 2. Test llms.txt & llms-full.txt
    print("\n--- [2/5] Testing llms.txt & llms-full.txt Generation ---")
    llms = generate_llms_txt(cfg)
    assert "# AEO Graph Engine" in llms
    assert "> " in llms
    print(f"  ✅ llms.txt validated ({len(llms.splitlines())} lines)")

    llms_full = generate_llms_full_txt(cfg)
    assert "COMPREHENSIVE SYSTEM KNOWLEDGE BASE" in llms_full
    print(f"  ✅ llms-full.txt validated ({len(llms_full.splitlines())} lines)")

    # 3. Test ai.txt and robots.txt
    print("\n--- [3/5] Testing ai.txt & robots.txt Crawler Directives ---")
    ai = generate_ai_txt(cfg)
    assert "Schema-Org-Graph:" in ai
    print("  ✅ ai.txt machine manifest validated")

    robots = generate_robots_txt(cfg)
    assert "GPTBot" in robots
    assert "PerplexityBot" in robots
    assert "ClaudeBot" in robots
    print("  ✅ robots.txt AI search directives validated")

    # 4. Test HTML Injection
    print("\n--- [4/5] Testing HTML Injection & Replacement ---")
    sample_html = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    injected = inject_jsonld_into_html(sample_html, graph)
    assert '<script type="application/ld+json">' in injected
    assert '</head>' in injected

    # Test Idempotent update
    re_injected = inject_jsonld_into_html(injected, graph)
    assert re_injected.count('<script type="application/ld+json">') == 1
    print("  ✅ HTML injection and idempotent replacement verified")

    # 5. Test Bundle Generation & Validation
    print("\n--- [5/5] Testing Directory Bundle Generation & Readiness Scorer ---")
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        html_file = tmp_path / "index.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(sample_html)

        bundle = write_aeo_bundle(tmp_path, cfg, inject_html_files=[html_file])
        assert len(bundle) >= 5

        report = validate_aeo_bundle(tmp_path)
        assert report.score >= 90.0
        print(f"  ✅ Directory bundle generated & validated (AEO Score: {report.score}/100 - {report.to_dict()['status']})")

    print("\n" + "=" * 70)
    print("🎉 ALL AEO GRAPH ENGINE TEST SUITES PASSED (100% SPEC CONFORMANCE)")
    print("=" * 70)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Constructs the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="aeo",
        description="AEO Graph Engine — Answer Engine Optimization, Schema.org Graph & llms.txt Generator"
    )

    parser.add_argument("--generate-all", action="store_true", help="Generate complete AEO bundle into output directory")
    parser.add_argument("--output-dir", type=str, default="dist", help="Output directory to write generated files (default: dist)")
    parser.add_argument(
        "--niche",
        choices=list(NICHE_PRESETS.keys()),
        default="developer_tools",
        help="Domain niche preset template (default: developer_tools)"
    )
    parser.add_argument("--config", type=str, help="Path to custom JSON configuration file")
    parser.add_argument("--site-name", type=str, help="Override site name")
    parser.add_argument("--domain", type=str, help="Override domain name (e.g. example.com)")
    parser.add_argument("--version", type=str, help="Override version string")

    # Single artifact output flags
    parser.add_argument("--jsonld", action="store_true", help="Print Schema.org JSON-LD graph to stdout")
    parser.add_argument("--llms", action="store_true", help="Print llms.txt to stdout")
    parser.add_argument("--llms-full", action="store_true", help="Print llms-full.txt to stdout")
    parser.add_argument("--ai-txt", action="store_true", help="Print ai.txt to stdout")
    parser.add_argument("--robots", action="store_true", help="Print robots.txt to stdout")

    # Injection and validation
    parser.add_argument("--inject", type=str, help="Inject Schema.org JSON-LD into specified HTML file")
    parser.add_argument("--validate", type=str, help="Validate AEO bundle directory or single artifact file")
    parser.add_argument("--test", action="store_true", help="Run comprehensive unit tests and engine verification")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files to disk")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.test:
        return run_internal_tests()

    # Load custom JSON config if provided
    user_config = {}
    if parsed_args.config:
        cfg_file = Path(parsed_args.config).resolve()
        if not cfg_file.exists():
            print(f"❌ Error: Config file not found at {cfg_file}", file=sys.stderr)
            return 1
        with open(cfg_file, "r", encoding="utf-8") as f:
            user_config = json.load(f)

    # Apply CLI flag overrides
    if parsed_args.site_name:
        user_config["site_name"] = parsed_args.site_name
    if parsed_args.domain:
        user_config["domain"] = parsed_args.domain
    if parsed_args.version:
        user_config["version"] = parsed_args.version

    cfg = resolve_config(user_config, niche=parsed_args.niche)

    # Handle Validation
    if parsed_args.validate:
        report = validate_aeo_bundle(parsed_args.validate)
        data = report.to_dict()
        print(f"\n🔍 AEO Audit Report for: {data['target']}")
        print(f"📊 AEO Readiness Score: {data['score']}/100 ({data['status']})")
        print(f"  • Passed checks: {data['passed_count']}")
        print(f"  • Warnings:      {data['warnings_count']}")
        print(f"  • Errors:        {data['errors_count']}\n")

        if data["passed"]:
            print("Passed Checks:")
            for p in data["passed"]:
                print(f"  ✅ {p}")

        if data["warnings"]:
            print("\nWarnings:")
            for w in data["warnings"]:
                print(f"  ⚠️  {w}")

        if data["errors"]:
            print("\nErrors:")
            for e in data["errors"]:
                print(f"  ❌ {e}")

        return 1 if data["errors_count"] > 0 else 0

    # Handle Injection into HTML file
    if parsed_args.inject:
        target_html = Path(parsed_args.inject).resolve()
        if not target_html.exists():
            print(f"❌ Error: HTML target file not found: {target_html}", file=sys.stderr)
            return 1
        graph = generate_schema_graph(cfg, niche=parsed_args.niche)
        inject_file(target_html, graph)
        print(f"✅ Successfully injected Schema.org JSON-LD into: {target_html}")
        return 0

    # Handle single stdout outputs
    if parsed_args.jsonld:
        graph = generate_schema_graph(cfg, niche=parsed_args.niche)
        print(json.dumps(graph, indent=2, ensure_ascii=False))
        return 0

    if parsed_args.llms:
        print(generate_llms_txt(cfg, niche=parsed_args.niche))
        return 0

    if parsed_args.llms_full:
        print(generate_llms_full_txt(cfg, niche=parsed_args.niche))
        return 0

    if parsed_args.ai_txt:
        print(generate_ai_txt(cfg, niche=parsed_args.niche))
        return 0

    if parsed_args.robots:
        print(generate_robots_txt(cfg, niche=parsed_args.niche))
        return 0

    # Default action: Generate all or warn if no flag passed
    if parsed_args.generate_all or not any([
        parsed_args.jsonld, parsed_args.llms, parsed_args.llms_full,
        parsed_args.ai_txt, parsed_args.robots, parsed_args.inject,
        parsed_args.validate, parsed_args.test
    ]):
        out_dir = Path(parsed_args.output_dir).resolve()
        if parsed_args.dry_run:
            print(f"[DRY-RUN] Would generate AEO bundle in {out_dir} with preset '{parsed_args.niche}'")
            return 0

        created = write_aeo_bundle(out_dir, cfg, niche=parsed_args.niche)
        print(f"✨ AEO Bundle successfully generated in: {out_dir}")
        for name, path in created.items():
            print(f"  📄 {name:20} -> {path}")

        # Automatically run validation on generated bundle
        report = validate_aeo_bundle(out_dir)
        print(f"\n📊 AEO Readiness Score: {report.score}/100 ({report.to_dict()['status']})")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

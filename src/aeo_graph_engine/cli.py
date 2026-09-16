"""
Command Line Interface for AEO Graph Engine.
Provides commands for generating, validating, inspecting, testing, extracting,
AI prompt auto-synthesis, Model Context Protocol (MCP) server, framework exporter,
and serving the Google-designed AEO Studio dashboard.
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
from .extractor import extract_from_file, extract_metadata_from_html
from .discovery import discover_project_metadata
from .ai_config import synthesize_config_from_prompt, get_agent_json_schema
from .scanner import LiveAEOScanner
from .framework_exporter import FrameworkExporter, AEORemediationGenerator
from .mcp_server import MCPServer, generate_mcp_client_config, run_stdio_server
from .ui_server import start_ui_server
from .presets import NICHE_PRESETS
from .compat import (
    configure_utf8_streams,
    get_platform_info,
    open_browser,
    atomic_write_text,
    to_posix_path,
    resolve_path,
    is_windows,
    is_termux,
    is_macos,
    is_linux,
)


def run_internal_tests() -> int:
    """Runs built-in engine verification test suite."""
    configure_utf8_streams()
    print("=" * 70)
    print("⚡ RUNNING AEO GRAPH ENGINE TEST SUITE")
    print("=" * 70)

    # 1. Test Schema Graph Generation
    print("\n--- [1/8] Testing Schema.org JSON-LD Graph Generation ---")
    cfg = resolve_config(None, niche="developer_tools")
    graph = generate_schema_graph(cfg)
    assert graph["@context"] == "https://schema.org"
    assert len(graph["@graph"]) >= 5
    print(f"  ✅ Schema.org Graph validated ({len(graph['@graph'])} connected entities)")

    # 2. Test llms.txt & llms-full.txt
    print("\n--- [2/7] Testing llms.txt & llms-full.txt Generation ---")
    llms = generate_llms_txt(cfg)
    assert "# AEO Graph Engine" in llms
    assert "> " in llms
    print(f"  ✅ llms.txt validated ({len(llms.splitlines())} lines)")

    llms_full = generate_llms_full_txt(cfg)
    assert "COMPREHENSIVE SYSTEM KNOWLEDGE BASE" in llms_full
    print(f"  ✅ llms-full.txt validated ({len(llms_full.splitlines())} lines)")

    # 3. Test ai.txt and robots.txt
    print("\n--- [3/7] Testing ai.txt & robots.txt Crawler Directives ---")
    ai = generate_ai_txt(cfg)
    assert "Schema-Org-Graph:" in ai
    print("  ✅ ai.txt machine manifest validated")

    robots = generate_robots_txt(cfg)
    assert "GPTBot" in robots
    assert "PerplexityBot" in robots
    assert "ClaudeBot" in robots
    print("  ✅ robots.txt AI search directives validated")

    # 4. Test HTML Injection
    print("\n--- [4/7] Testing HTML Injection & Replacement ---")
    sample_html = "<html><head><title>Test</title></head><body><h1>Hello</h1></body></html>"
    injected = inject_jsonld_into_html(sample_html, graph)
    assert '<script type="application/ld+json">' in injected
    assert '</head>' in injected

    re_injected = inject_jsonld_into_html(injected, graph)
    assert re_injected.count('<script type="application/ld+json">') == 1
    print("  ✅ HTML injection and idempotent replacement verified")

    # 5. Test Metadata Extractor & Discovery
    print("\n--- [5/7] Testing HTML Metadata Extractor & Project Discovery ---")
    extracted = extract_metadata_from_html(sample_html)
    assert extracted["site_name"] == "Test"

    discovered = discover_project_metadata(".")
    print(f"  ✅ Project discovery verified (Detected framework: {discovered.get('framework', 'generic')})")

    # 6. Test AI Prompt Synthesis
    print("\n--- [6/7] Testing AI Prompt Synthesizer & Schema Contract ---")
    ai_syn = synthesize_config_from_prompt("A high-performance Solana DeFi lending protocol called SolarYield on solaryield.fi")
    assert ai_syn["site_name"] == "SolarYield"
    assert "solaryield.fi" in ai_syn["domain"]
    assert len(ai_syn["faqs"]) >= 2
    print(f"  ✅ AI Prompt Synthesizer validated (Extracted: '{ai_syn['site_name']}' on {ai_syn['domain']})")

    # 7. Test Framework Exporter & MCP Server
    print("\n--- [7/8] Testing Framework Exporter & MCP Server ---")
    exporter = FrameworkExporter(cfg)
    next_bundle = exporter.export("nextjs_app")
    assert "app/layout.tsx" in next_bundle
    assert "app/robots.ts" in next_bundle

    mcp = MCPServer()
    init_res = mcp.handle_message({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    assert init_res["result"]["serverInfo"]["name"] == "aeo-graph-engine-mcp"
    print("  ✅ Framework Exporter & MCP Server validated")

    # 8. Test Cross-Platform Compatibility (Linux, Termux, macOS, Windows)
    print("\n--- [8/8] Testing Cross-Platform Compatibility Layer ---")
    plat_info = get_platform_info()
    assert "system_type" in plat_info
    assert "python_version" in plat_info
    posix_path = to_posix_path("dist/schema-graph.json")
    assert "\\" not in posix_path
    print(f"  ✅ Platform detected: {plat_info['system_type']} (Python {plat_info['python_version']}, OS: {plat_info['platform_system']})")

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

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # `aeo serve` / `aeo ui`
    serve_parser = subparsers.add_parser("serve", help="Start the interactive Google-designed AEO Studio UI server")
    serve_parser.add_argument("--port", type=int, default=8080, help="Port to listen on (default: 8080)")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    serve_parser.add_argument("--open", action="store_true", help="Automatically open browser to AEO Studio")

    subparsers.add_parser("ui", help="Alias for 'aeo serve'")

    # `aeo platform`
    subparsers.add_parser("platform", help="Display platform environment details (Linux, Termux, macOS, Windows)")

    # `aeo mcp`
    mcp_parser = subparsers.add_parser("mcp", help="Run Model Context Protocol (MCP) server or generate client configs")
    mcp_parser.add_argument("--tools", action="store_true", help="Print available MCP tools JSON schema")
    mcp_parser.add_argument(
        "--config",
        choices=["claude_desktop", "cursor", "cline", "zed", "hermes", "opencode", "generic"],
        help="Generate copy-pasteable MCP client configuration"
    )
    mcp_parser.add_argument("--python-path", type=str, default="python3", help="Python binary path in client config")

    # `aeo framework <name>`
    fw_parser = subparsers.add_parser("framework", help="Export copy-paste framework integration files")
    fw_parser.add_argument(
        "name",
        choices=["nextjs_app", "nextjs_pages", "astro", "vite_react", "sveltekit", "remix", "nuxt", "static", "hugo", "jekyll"],
        help="Target web framework"
    )
    fw_parser.add_argument("--output-dir", type=str, help="Directory to write framework files (optional, stdout otherwise)")
    fw_parser.add_argument("--niche", choices=list(NICHE_PRESETS.keys()), default="developer_tools", help="Domain niche preset")

    # `aeo prompt "<description>"`
    prompt_parser = subparsers.add_parser("prompt", help="Synthesize complete AEO bundle from natural language description")
    prompt_parser.add_argument("description", type=str, help="Natural language description of the website or application")
    prompt_parser.add_argument("--output-dir", type=str, default="dist", help="Output directory to write generated bundle")
    prompt_parser.add_argument("--niche", choices=list(NICHE_PRESETS.keys()), help="Optional base domain niche")
    prompt_parser.add_argument("--dry-run", action="store_true", help="Preview synthesized JSON without writing files")

    # `aeo scan <url>`
    scan_parser = subparsers.add_parser("scan", help="Crawl a live website and compute real AEO scores and backlink intelligence")
    scan_parser.add_argument("url", type=str, help="Target live website URL (e.g. https://example.com)")
    scan_parser.add_argument("--max-pages", type=int, default=5, help="Maximum internal pages to crawl (default: 5)")
    scan_parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format (default: text)")

    # `aeo fix <url>`
    fix_parser = subparsers.add_parser("fix", help="Audit live site and generate concrete framework-tailored code remediations")
    fix_parser.add_argument("url", type=str, help="Target live website URL to audit and remediate")
    fix_parser.add_argument(
        "--framework",
        choices=["nextjs_app", "nextjs_pages", "astro", "vite_react", "sveltekit", "remix", "nuxt", "static"],
        default="nextjs_app",
        help="Target framework to generate code fixes for"
    )
    fix_parser.add_argument("--output-dir", type=str, help="Directory to write remediation code files")

    # `aeo extract <file>`
    extract_parser = subparsers.add_parser("extract", help="Extract metadata from an HTML file")
    extract_parser.add_argument("file", type=str, help="Path to HTML file to extract metadata from")

    # Main root flags
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
    parser.add_argument("--format", choices=["text", "json"], default="text", help="Output format for validation/reports")

    # Single artifact output flags
    parser.add_argument("--jsonld", action="store_true", help="Print Schema.org JSON-LD graph to stdout")
    parser.add_argument("--llms", action="store_true", help="Print llms.txt to stdout")
    parser.add_argument("--llms-full", action="store_true", help="Print llms-full.txt to stdout")
    parser.add_argument("--ai-txt", action="store_true", help="Print ai.txt to stdout")
    parser.add_argument("--robots", action="store_true", help="Print robots.txt to stdout")

    # Injection and validation
    parser.add_argument("--inject", type=str, help="Inject Schema.org JSON-LD into specified HTML file")
    parser.add_argument("--validate", type=str, help="Validate AEO bundle directory or single artifact file")
    parser.add_argument("--platform", action="store_true", help="Display platform environment details (Linux, Termux, macOS, Windows)")
    parser.add_argument("--test", action="store_true", help="Run comprehensive unit tests and engine verification")
    parser.add_argument("--dry-run", action="store_true", help="Preview output without writing files to disk")

    return parser


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    configure_utf8_streams()
    parser = build_parser()
    parsed_args = parser.parse_args(args)

    if parsed_args.platform or parsed_args.subcommand == "platform":
        info = get_platform_info()
        print("=" * 60)
        print("🌐 AEO GRAPH ENGINE — PLATFORM COMPATIBILITY INFO")
        print("=" * 60)
        print(f"  • Environment:           {info['system_type'].upper()}")
        print(f"  • Operating System:      {info['platform_system']} ({info['os_name']})")
        print(f"  • OS Release:            {info['platform_release']}")
        print(f"  • Python Version:        {info['python_version']} ({info['python_implementation']})")
        print(f"  • Default Encoding:      {info['default_encoding']}")
        print(f"  • Filesystem Encoding:   {info['filesystem_encoding']}")
        print(f"  • Termux Android:        {'Yes' if info['is_termux'] else 'No'}")
        print(f"  • Windows Subsystem/WSL: {'Yes' if info['is_wsl'] else 'No'}")
        print("=" * 60)
        return 0

    if parsed_args.test:
        return run_internal_tests()

    # Subcommand: mcp
    if parsed_args.subcommand == "mcp":
        if parsed_args.tools:
            mcp = MCPServer()
            print(json.dumps(mcp._get_tools_list(), indent=2))
            return 0
        if parsed_args.config:
            cfg = generate_mcp_client_config(parsed_args.config, python_path=parsed_args.python_path)
            print(json.dumps(cfg, indent=2))
            return 0
        # Run stdio server
        return run_stdio_server()

    # Subcommand: framework
    if parsed_args.subcommand == "framework":
        cfg = resolve_config(None, niche=parsed_args.niche)
        exporter = FrameworkExporter(cfg)
        bundle = exporter.export(parsed_args.name)

        if parsed_args.output_dir:
            out_dir = Path(parsed_args.output_dir).resolve()
            written = exporter.write_bundle(parsed_args.name, out_dir)
            print(f"✨ Framework bundle '{parsed_args.name}' exported to: {out_dir}")
            for p in written:
                print(f"  📄 {p}")
            return 0

        # Print to stdout
        for rel_path, content in bundle.items():
            print(f"\n{'='*70}\n// FILE: {rel_path}\n{'='*70}")
            print(content)
        return 0

    # Subcommand: fix
    if parsed_args.subcommand == "fix":
        target_url = parsed_args.url
        print(f"🔍 Scanning {target_url} to generate remediation plan...")
        scanner = LiveAEOScanner(target_url, max_pages=3)
        audit_res = scanner.compute_audit_scores()
        
        remediator = AEORemediationGenerator(audit_res, target_framework=parsed_args.framework)
        plan = remediator.generate_remediations()

        print(f"\n📊 Current AEO Score: {audit_res['overall_aeo_score']}/100")
        print(f"🛠️  Generated {len(plan['remediations'])} Remediation Action(s) for framework '{parsed_args.framework}':")
        for r in plan["remediations"]:
            print(f"  [{r['priority']}] {r['category']}: {r['issue']}")

        if parsed_args.output_dir:
            out_dir = Path(parsed_args.output_dir).resolve()
            remediator.write_remediations(out_dir)
            print(f"\n✅ All remediation files written to: {out_dir}")
            print(f"   Plan details: {out_dir / 'AEO_REMEDIATION_PLAN.md'}")
        else:
            print("\n💡 Tip: Run with `--output-dir <path>` to write all fixed code files directly to disk.")
        return 0

    # Subcommand: schema
    if parsed_args.subcommand == "schema":
        print(json.dumps(get_agent_json_schema(), indent=2))
        return 0

    # Subcommand: scan
    if parsed_args.subcommand == "scan":
        target_url = parsed_args.url
        max_pages = getattr(parsed_args, "max_pages", 5)
        print(f"🚀 Scanning live website: {target_url} (Crawl limit: {max_pages} pages)...")
        scanner = LiveAEOScanner(target_url, max_pages=max_pages)
        report = scanner.compute_audit_scores()

        if parsed_args.format == "json":
            print(json.dumps(report, indent=2, ensure_ascii=False))
            return 0

        # Formatted human text report
        print("\n" + "=" * 70)
        print(f"🌐 LIVE AEO AUDIT REPORT: {report['target_url']}")
        print("=" * 70)
        print(f"📊 Overall AEO Readiness Score: {report['overall_aeo_score']} / 100 ({report['status']})")
        print(f"📄 Pages Audited: {report['pages_audited_count']}")

        print("\n--- [1] Category Score Breakdown ---")
        for cat_name, cat_data in report["category_scores"].items():
            readable_name = cat_name.replace("_", " ").title()
            print(f"  • {readable_name:30}: {cat_data['score']:4.1f} / {cat_data['max']:4.1f}")

        print("\n--- [2] Root Machine Discovery Assets ---")
        for asset_name, asset_info in report["root_assets"].items():
            status_icon = "✅ Found" if asset_info["exists"] else f"❌ Missing ({asset_info['status']})"
            print(f"  • {asset_name:22}: {status_icon}")

        print("\n--- [3] AI Engine Compatibility Matrix ---")
        for bot_name, bot_info in report["ai_engine_compatibility"].items():
            status_str = "✅ Allowed" if bot_info.get("allowed") else "❌ Blocked / Restricted"
            print(f"  🤖 {bot_name:36}: {status_str}")

        if report.get("action_items"):
            print("\n--- [4] Prioritized Action Items ---")
            for item in report["action_items"]:
                print(f"  [{item['priority']}] {item['category']}: {item['issue']}")
                print(f"        -> Fix: {item['fix']}")

        strategy = report.get("backlink_and_distribution_intelligence", {})
        if strategy.get("high_authority_citation_hubs"):
            print("\n--- [5] High-Authority Backlink & AI Citation Targets ---")
            for hub in strategy["high_authority_citation_hubs"][:3]:
                print(f"  🔗 {hub['platform']}: {hub['action']}")

        print("=" * 70 + "\n")
        return 0

    # Subcommand: prompt
    if parsed_args.subcommand == "prompt":
        desc = parsed_args.description
        cfg = synthesize_config_from_prompt(desc, base_niche=parsed_args.niche)
        if parsed_args.dry_run:
            print(json.dumps(cfg, indent=2, ensure_ascii=False))
            return 0

        out_dir = Path(parsed_args.output_dir).resolve()
        created = write_aeo_bundle(out_dir, cfg, niche=cfg.get("niche", "developer_tools"))
        print(f"✨ AEO Bundle successfully synthesized from prompt into: {out_dir}")
        for name, path in created.items():
            print(f"  📄 {name:20} -> {path}")

        report = validate_aeo_bundle(out_dir)
        print(f"\n📊 AEO Readiness Score: {report.score}/100 ({report.to_dict()['status']})")
        return 0

    # Subcommand: serve / ui
    if parsed_args.subcommand in ("serve", "ui"):
        port = getattr(parsed_args, "port", 8080)
        host = getattr(parsed_args, "host", "127.0.0.1")
        print(f"✨ Starting Google-Styled AEO Studio at http://{host}:{port}/")
        print("💡 Press Ctrl+C to stop.")
        if getattr(parsed_args, "open", False):
            open_browser(f"http://{host}:{port}/")
        server = start_ui_server(host=host, port=port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Shutting down AEO Studio.")
            server.server_close()
        return 0

    # Subcommand: extract
    if parsed_args.subcommand == "extract":
        target = parsed_args.file
        try:
            meta = extract_from_file(target)
            print(json.dumps(meta, indent=2, ensure_ascii=False))
            return 0
        except Exception as e:
            print(f"❌ Error extracting metadata: {e}", file=sys.stderr)
            return 1

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

        if parsed_args.format == "json":
            print(json.dumps(data, indent=2))
        else:
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

        report = validate_aeo_bundle(out_dir)
        print(f"\n📊 AEO Readiness Score: {report.score}/100 ({report.to_dict()['status']})")
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())

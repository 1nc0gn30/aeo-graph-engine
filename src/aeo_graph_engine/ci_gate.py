"""
CI/CD Quality Gate & Automated Enforcement for AEO Graph Engine.
Evaluates local project builds, static bundles, or live websites against AEO readiness
thresholds, formats GitHub Actions workflow annotations (::error::, ::warning::, ::notice::),
and renders terminal ASCII diagnostic tables.

Zero external dependencies (pure Python standard library).
"""

import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from .validator import validate_aeo_bundle, AEODiagnosticReport
from .scanner import LiveAEOScanner
from .compat import configure_utf8_streams, safe_print


# =============================================================================
# ANSI Styling Helpers
# =============================================================================

def _use_color() -> bool:
    """Determine whether color output is supported and not disabled."""
    if os.environ.get("NO_COLOR") or os.environ.get("TERM") == "dumb":
        return False
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class Colors:
    """ANSI color codes with automatic fallback."""
    RESET = "\033[0m" if _use_color() else ""
    BOLD = "\033[1m" if _use_color() else ""
    DIM = "\033[2m" if _use_color() else ""
    CYAN = "\033[36m" if _use_color() else ""
    GREEN = "\033[32m" if _use_color() else ""
    YELLOW = "\033[33m" if _use_color() else ""
    BLUE = "\033[34m" if _use_color() else ""
    RED = "\033[31m" if _use_color() else ""


# =============================================================================
# GitHub Actions Formatting
# =============================================================================

def format_github_annotation(
    level: str,
    message: str,
    title: Optional[str] = None,
    file: Optional[str] = None,
    line: Optional[int] = None,
    col: Optional[int] = None,
) -> str:
    """
    Formats a single GitHub Actions workflow command line:
    ::(error|warning|notice) file={file},line={line},title={title}::{message}
    """
    params = []
    if file:
        params.append(f"file={file}")
    if line is not None:
        params.append(f"line={line}")
    if col is not None:
        params.append(f"col={col}")
    if title:
        # Escape any colons or special chars in title if needed
        safe_title = title.replace("\n", " ").replace("\r", "")
        params.append(f"title={safe_title}")

    param_str = f" {','.join(params)}" if params else ""
    # GitHub command syntax: escape newlines in message
    escaped_msg = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    return f"::{level}{param_str}::{escaped_msg}"


def write_github_step_summary(
    report_dict: Dict[str, Any],
    passed: bool,
    min_score: int,
    reasons: List[str],
) -> None:
    """Writes GitHub Actions Markdown Step Summary if GITHUB_STEP_SUMMARY is configured."""
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    try:
        score = report_dict.get("score", 0.0)
        target = report_dict.get("target", "Target")
        status_icon = "✅ PASSED" if passed else "❌ FAILED"

        lines = [
            f"# 🛡️ AEO Quality Gate Summary — {status_icon}",
            "",
            f"| Metric | Value |",
            f"|---|---|",
            f"| **Target** | `{target}` |",
            f"| **AEO Readiness Score** | **{score}/100** (Min Threshold: {min_score}) |",
            f"| **Status** | {status_icon} |",
            f"| **Passed Checks** | {len(report_dict.get('passed', []))} |",
            f"| **Warnings** | {len(report_dict.get('warnings', []))} |",
            f"| **Errors** | {len(report_dict.get('errors', []))} |",
            "",
            "## 📦 Machine Discovery Artifacts",
            "",
            "| Artifact | Status |",
            "|---|---|",
        ]

        artifacts = report_dict.get("artifacts_detected", {})
        for art_name, art_found in artifacts.items():
            readable_art = art_name.replace("_", ".").replace("txt", ".txt").replace("jsonld", " (JSON-LD)")
            icon = "✅ Present & Valid" if art_found else "❌ Missing / Unverified"
            lines.append(f"| `{art_name}` | {icon} |")

        if reasons:
            lines.extend([
                "",
                "## ⚠️ Gate Failure Reasons",
                "",
            ])
            for r in reasons:
                lines.append(f"- ❌ {r}")

        if report_dict.get("warnings"):
            lines.extend([
                "",
                "## 🔍 Diagnostic Warnings",
                "",
            ])
            for w in report_dict["warnings"]:
                lines.append(f"- ⚠️ {w}")

        lines.append("")
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    except Exception:
        pass


# =============================================================================
# CI Quality Gate Check
# =============================================================================

def run_ci_check(
    target_url_or_path: str = ".",
    min_score: int = 80,
    fail_on_missing_llms: bool = True,
    output_format: str = "text",
) -> Tuple[bool, Dict[str, Any], str]:
    """
    Executes an Answer Engine Optimization (AEO) CI/CD quality gate check.

    Args:
        target_url_or_path: Directory path, artifact file path, or live URL (http:// or https://)
        min_score: Minimum AEO score (0-100) required to pass the gate (default: 80)
        fail_on_missing_llms: If True, fails the gate if llms.txt is missing regardless of overall score
        output_format: Output format: 'text', 'json', or 'github'

    Returns:
        Tuple[bool, Dict[str, Any], str]:
          - passed: True if all thresholds and criteria passed, False otherwise
          - report_dict: Structured dictionary containing score, diagnostics, artifact matrix
          - formatted_output: Formatted string suitable for terminal or CI logging
    """
    configure_utf8_streams()
    c = Colors
    target_str = str(target_url_or_path).strip()
    is_live_url = target_str.startswith("http://") or target_str.startswith("https://")

    passed_checks: List[str] = []
    warnings: List[str] = []
    errors: List[str] = []
    failure_reasons: List[str] = []
    artifacts_detected: Dict[str, bool] = {
        "schema_jsonld": False,
        "llms_txt": False,
        "llms_full_txt": False,
        "ai_txt": False,
        "robots_txt": False,
        "html_injection": False,
    }

    # Case A: Live URL Crawl & Audit
    if is_live_url:
        scanner = LiveAEOScanner(target_str, max_pages=3)
        scan_res = scanner.compute_audit_scores()
        score = float(scan_res.get("overall_aeo_score", 0.0))
        
        # Map root assets
        root_assets = scan_res.get("root_assets", {})
        artifacts_detected["schema_jsonld"] = root_assets.get("schema_org", {}).get("exists", False)
        artifacts_detected["llms_txt"] = root_assets.get("llms_txt", {}).get("exists", False)
        artifacts_detected["llms_full_txt"] = root_assets.get("llms_full_txt", {}).get("exists", False)
        artifacts_detected["ai_txt"] = root_assets.get("ai_txt", {}).get("exists", False)
        artifacts_detected["robots_txt"] = root_assets.get("robots_txt", {}).get("exists", False)

        for act in scan_res.get("action_items", []):
            if act.get("priority") == "CRITICAL":
                errors.append(f"{act['category']}: {act['issue']} (Fix: {act.get('fix')})")
            else:
                warnings.append(f"{act['category']}: {act['issue']} (Fix: {act.get('fix')})")

        passed_checks.append(f"Successfully audited live URL: {target_str}")
        if artifacts_detected["llms_txt"]:
            passed_checks.append("Discovered live llms.txt manifest")
        if artifacts_detected["schema_jsonld"]:
            passed_checks.append("Discovered live Schema.org JSON-LD")
        if artifacts_detected["robots_txt"]:
            passed_checks.append("Discovered live robots.txt AI bot directives")

    # Case B: Local Path / Directory Audit
    else:
        target_path = Path(target_str).resolve()
        if not target_path.exists():
            score = 0.0
            errors.append(f"Target path does not exist: {target_path}")
            failure_reasons.append(f"Target path does not exist: {target_path}")
            report_dict = {
                "target": str(target_path),
                "score": 0.0,
                "min_score": min_score,
                "passed_gate": False,
                "status": "FAILED",
                "artifacts_detected": artifacts_detected,
                "passed": [],
                "warnings": [],
                "errors": errors,
                "failure_reasons": failure_reasons,
            }
            formatted = f"::error title=AEO CI Gate Error::Target path does not exist: {target_path}\n" if output_format == "github" else f"❌ Error: Target path does not exist: {target_path}"
            return False, report_dict, formatted

        # Validate target directory or file
        report = validate_aeo_bundle(target_path)
        
        # If target_path is a directory and artifacts might be in subfolders (e.g. public/, static/, dist/),
        # check those as well if root validation didn't find them all.
        if target_path.is_dir():
            for sub_dir_name in ("public", "static", "dist"):
                sub_path = target_path / sub_dir_name
                if sub_path.is_dir():
                    sub_report = validate_aeo_bundle(sub_path)
                    # Merge artifact detections
                    for k, v in sub_report.artifacts_checked.items():
                        if v:
                            report.artifacts_checked[k] = True
                    # If sub_report has better score, use it
                    if sub_report.score > report.score:
                        report.score = sub_report.score
                    # Merge passes
                    for p in sub_report.passed:
                        if p not in report.passed:
                            report.passed.append(p)
                    # Filter out 'not found' warnings if they exist in subfolder
                    filtered_warns = []
                    for w in report.warnings:
                        if "not found in directory" in w:
                            fname = w.split()[0]
                            if (sub_path / fname).exists():
                                continue
                        filtered_warns.append(w)
                    report.warnings = filtered_warns

        score = round(report.score, 1)
        passed_checks = list(report.passed)
        warnings = list(report.warnings)
        errors = list(report.errors)
        artifacts_detected = dict(report.artifacts_checked)

    # -------------------------------------------------------------------------
    # Pass / Fail Evaluation Rules
    # -------------------------------------------------------------------------
    passed = True

    # Rule 1: Minimum Score Threshold
    if score < min_score:
        passed = False
        failure_reasons.append(f"AEO Readiness Score ({score}/100) is below required minimum threshold of {min_score}")

    # Rule 2: Mandatory llms.txt Check
    if fail_on_missing_llms and not artifacts_detected.get("llms_txt", False):
        passed = False
        failure_reasons.append("Mandatory llms.txt machine knowledge manifest is missing or empty")

    # Rule 3: Critical Schema or Bundle Errors
    if len(errors) > 0 and not is_live_url:
        for err in errors:
            if "lacks @graph" in err or "Missing or invalid @context" in err or "Failed to parse" in err:
                passed = False
                failure_reasons.append(f"Critical schema error: {err}")

    # Deduplicate failure reasons
    failure_reasons = list(dict.fromkeys(failure_reasons))

    # Construct structured report dictionary
    status_str = "PASSED" if passed else "FAILED"
    report_dict = {
        "target": target_str,
        "score": score,
        "min_score": min_score,
        "passed_gate": passed,
        "status": status_str,
        "fail_on_missing_llms": fail_on_missing_llms,
        "artifacts_detected": artifacts_detected,
        "passed": passed_checks,
        "warnings": warnings,
        "errors": errors,
        "failure_reasons": failure_reasons,
    }

    # Step Summary integration
    write_github_step_summary(report_dict, passed, min_score, failure_reasons)

    # -------------------------------------------------------------------------
    # Output Formatting
    # -------------------------------------------------------------------------
    if output_format == "json":
        return passed, report_dict, json.dumps(report_dict, indent=2, ensure_ascii=False)

    # Generate ASCII Summary Table
    out_lines: List[str] = []
    
    # Include GitHub annotations if in github format or in GitHub Actions environment
    include_gh_annotations = (output_format == "github") or (os.environ.get("GITHUB_ACTIONS") == "true")

    if include_gh_annotations:
        for err in errors:
            out_lines.append(format_github_annotation("error", err, title="AEO CI Gate Error"))
        for fail_r in failure_reasons:
            if fail_r not in errors:
                out_lines.append(format_github_annotation("error", fail_r, title="AEO CI Gate Failure Reason"))
        for warn in warnings:
            out_lines.append(format_github_annotation("warning", warn, title="AEO CI Gate Warning"))
        
        if passed:
            out_lines.append(format_github_annotation("notice", f"AEO Readiness Score: {score}/100 (Threshold: {min_score})", title="AEO CI Gate PASSED"))
        else:
            out_lines.append(format_github_annotation("error", f"AEO Readiness Score: {score}/100 failed minimum threshold of {min_score}", title="AEO CI Gate FAILED"))

    # Render Terminal Box Table
    status_badge = f"{c.GREEN}PASSED ✅{c.RESET}" if passed else f"{c.RED}FAILED ❌{c.RESET}"
    score_color = c.GREEN if score >= 85 else c.YELLOW if score >= 70 else c.RED

    out_lines.append(f"\n{c.BOLD}{c.CYAN}┌──────────────────────────────────────────────────────────────────────────────────┐{c.RESET}")
    out_lines.append(f"{c.BOLD}{c.CYAN}│  {c.BOLD}🛡️  AEO CI/CD QUALITY GATE AUDIT REPORT{c.CYAN}                                          │{c.RESET}")
    out_lines.append(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    out_lines.append(f"│  {c.BOLD}Target:{c.RESET}           {target_str:<65}│")
    out_lines.append(f"│  {c.BOLD}Final Score:{c.RESET}      {score_color}{score:>5.1f} / 100{c.RESET} (Required Minimum: {min_score}){'':<28}│")
    out_lines.append(f"│  {c.BOLD}Gate Status:{c.RESET}      {status_badge}{'':<62}│")
    out_lines.append(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    out_lines.append(f"│  {c.BOLD}Machine Discovery Artifact Matrix:{c.RESET}                                             │")

    art_labels = [
        ("schema_jsonld", "Schema.org Graph (schema-graph.json)"),
        ("llms_txt", "Machine Knowledge Base (llms.txt)"),
        ("llms_full_txt", "Extended Knowledge Base (llms-full.txt)"),
        ("ai_txt", "AI Machine Manifest (ai.txt)"),
        ("robots_txt", "AI Crawler Directives (robots.txt)"),
    ]
    for key, label in art_labels:
        found = artifacts_detected.get(key, False)
        status_icon = f"{c.GREEN}✅ PRESENT{c.RESET}" if found else f"{c.RED}❌ MISSING{c.RESET}"
        out_lines.append(f"│    • {label:<48}: {status_icon}{'':<17}│")

    out_lines.append(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    out_lines.append(f"│  {c.BOLD}Audit Checks:{c.RESET}     {len(passed_checks)} Passed Checks | {len(warnings)} Warning(s) | {len(errors)} Error(s){'':<20}│")

    if failure_reasons:
        out_lines.append(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
        out_lines.append(f"│  {c.BOLD}{c.RED}Gate Failure Reasons:{c.RESET}{'':<60}│")
        for fr in failure_reasons:
            out_lines.append(f"│    {c.RED}❌{c.RESET} {fr:<74}│")

    if warnings:
        out_lines.append(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
        out_lines.append(f"│  {c.BOLD}{c.YELLOW}Warnings & Recommendations:{c.RESET}{'':<54}│")
        for w in warnings[:5]:
            # Truncate warning line if needed for box layout
            w_disp = (w[:72] + "..") if len(w) > 74 else w
            out_lines.append(f"│    {c.YELLOW}⚠️{c.RESET}  {w_disp:<73}│")
        if len(warnings) > 5:
            out_lines.append(f"│    ... and {len(warnings) - 5} more warning(s){'':<52}│")

    out_lines.append(f"{c.BOLD}{c.CYAN}└──────────────────────────────────────────────────────────────────────────────────┘{c.RESET}\n")

    formatted_text = "\n".join(out_lines)
    return passed, report_dict, formatted_text


# =============================================================================
# CLI Entrypoint for ci_gate
# =============================================================================

def build_parser() -> argparse.ArgumentParser:
    """Builds CLI argument parser for AEO CI Gate."""
    parser = argparse.ArgumentParser(
        prog="python3 -m aeo_graph_engine.ci_gate",
        description="AEO CI/CD Quality Gate — Enforces AEO readiness scores and AI search discovery artifacts"
    )
    parser.add_argument(
        "target",
        nargs="?",
        default=".",
        help="Target directory, bundle path, or live URL to check (default: .)"
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=80,
        help="Minimum AEO Readiness Score (0-100) required to pass (default: 80)"
    )
    parser.add_argument(
        "--fail-on-missing-llms",
        action="store_true",
        default=True,
        help="Fail check if llms.txt is missing (default: True)"
    )
    parser.add_argument(
        "--no-fail-on-missing-llms",
        dest="fail_on_missing_llms",
        action="store_false",
        help="Do not fail on missing llms.txt"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "github"],
        default="text",
        help="Output format (default: text)"
    )
    return parser


def main(args: Optional[List[str]] = None) -> int:
    """CLI runner for ci_gate module."""
    parser = build_parser()
    parsed = parser.parse_args(args)
    passed, _, formatted_output = run_ci_check(
        target_url_or_path=parsed.target,
        min_score=parsed.min_score,
        fail_on_missing_llms=parsed.fail_on_missing_llms,
        output_format=parsed.format,
    )
    print(formatted_output)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())

"""
Interactive & Scriptable Project Setup Wizard for AEO Graph Engine.
Auto-detects framework (Next.js, Astro, Vite/React, SvelteKit, Remix, Nuxt, Static, Hugo, Jekyll),
profiles repository metadata, configures Answer Engine Optimization (AEO/GEO),
generates complete AEO bundles and framework integration code, and produces
colorful terminal summaries.

Zero external dependencies (pure Python standard library).
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Tuple

from .presets import DEFAULT_CONFIG, NICHE_PRESETS
from .core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle,
)
from .framework_exporter import (
    FrameworkExporter,
    SUPPORTED_FRAMEWORKS,
    normalize_framework_name,
)
from .validator import validate_aeo_bundle
from .injector import inject_jsonld_into_html, inject_file
from .compat import configure_utf8_streams, safe_print, is_windows


# =============================================================================
# ANSI Terminal Styling Helpers
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
    MAGENTA = "\033[35m" if _use_color() else ""
    RED = "\033[31m" if _use_color() else ""
    BG_BLUE = "\033[44m" if _use_color() else ""
    BG_GREEN = "\033[42m" if _use_color() else ""


# =============================================================================
# Framework and Niche Helpers
# =============================================================================

def normalize_niche_name(niche: Optional[str]) -> str:
    """Normalizes various niche aliases to canonical preset keys."""
    if not niche:
        return "developer_tools"
    n = niche.lower().strip().replace("-", "_").replace(" ", "_")
    if n in NICHE_PRESETS:
        return n
    if n in ("saas_b2b", "saas_enterprise", "b2b", "enterprise"):
        return "saas"
    if n in ("ai_agent", "ai_agents", "agents", "llm", "swarm", "ai"):
        return "ai_swarm"
    if n in ("crypto", "crypto_web3", "web3", "defi", "solana"):
        return "developer_tools"
    if n in ("media", "publisher", "publisher_media", "blog", "content"):
        return "creator"
    if n in ("security", "infosec"):
        return "cybersecurity"
    if n in ("3d", "spatial", "graphics"):
        return "spatial_3d"
    if n in ("shop", "store"):
        return "ecommerce"
    if n in ("local", "business", "services"):
        return "local_business"
    return "developer_tools"


def detect_framework(project_dir: Union[str, Path] = ".") -> str:
    """
    Auto-detects the web framework used in the given project directory by inspecting
    configuration files and package.json dependencies.

    Returns canonical framework identifier:
      - 'nextjs_app' (Next.js App Router)
      - 'nextjs_pages' (Next.js Pages Router)
      - 'astro' (Astro)
      - 'vite_react' (Vite / React / Vue SPA)
      - 'sveltekit' (SvelteKit)
      - 'remix' (Remix)
      - 'nuxt' (Nuxt / Vue)
      - 'hugo' (Hugo Static Site)
      - 'jekyll' (Jekyll)
      - 'static' (Vanilla HTML / Static Site)
    """
    root = Path(project_dir).resolve()
    if not root.exists() or not root.is_dir():
        return "static"

    # 1. Check Next.js
    next_configs = ["next.config.js", "next.config.mjs", "next.config.ts"]
    has_next_config = any((root / f).exists() for f in next_configs)

    # 2. Check Astro
    astro_configs = ["astro.config.mjs", "astro.config.ts", "astro.config.js", "astro.config.cjs"]
    if any((root / f).exists() for f in astro_configs):
        return "astro"

    # 3. Check Nuxt
    nuxt_configs = ["nuxt.config.js", "nuxt.config.ts", "nuxt.config.mjs"]
    if any((root / f).exists() for f in nuxt_configs):
        return "nuxt"

    # 4. Check SvelteKit
    svelte_configs = ["svelte.config.js", "svelte.config.ts"]
    if any((root / f).exists() for f in svelte_configs):
        return "sveltekit"

    # 5. Check Remix
    remix_configs = ["remix.config.js", "remix.config.ts"]
    if any((root / f).exists() for f in remix_configs):
        return "remix"

    # 6. Check Hugo
    hugo_configs = ["hugo.toml", "hugo.yaml", "hugo.json", "config.toml", "config.yaml"]
    if any((root / f).exists() for f in hugo_configs) and (root / "archetypes").is_dir():
        return "hugo"

    # 7. Check Jekyll
    jekyll_configs = ["_config.yml", "_config.yaml"]
    if any((root / f).exists() for f in jekyll_configs):
        return "jekyll"

    # 8. Check Vite
    vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs", "vite.config.cjs"]
    has_vite_config = any((root / f).exists() for f in vite_configs)

    # 9. Deep package.json inspection
    pkg_file = root / "package.json"
    if pkg_file.exists():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "next" in deps or has_next_config:
                # Differentiate App Router vs Pages Router
                has_app_dir = (root / "app").is_dir() or (root / "src" / "app").is_dir()
                has_pages_dir = (root / "pages").is_dir() or (root / "src" / "pages").is_dir()
                if has_app_dir:
                    return "nextjs_app"
                elif has_pages_dir:
                    return "nextjs_pages"
                return "nextjs_app"

            if "astro" in deps:
                return "astro"
            if "@sveltejs/kit" in deps or "svelte" in deps:
                return "sveltekit"
            if "@remix-run/react" in deps or "@remix-run/node" in deps or "remix" in deps:
                return "remix"
            if "nuxt" in deps or "nuxt3" in deps:
                return "nuxt"
            if has_vite_config or "vite" in deps or "react" in deps:
                return "vite_react"
        except Exception:
            pass

    if has_next_config:
        has_app_dir = (root / "app").is_dir() or (root / "src" / "app").is_dir()
        return "nextjs_app" if has_app_dir else "nextjs_pages"

    if has_vite_config:
        return "vite_react"

    # Check for Hugo files
    if (root / "content").is_dir() and (root / "layouts").is_dir():
        return "hugo"

    # Default to static
    return "static"


def detect_project_profile(project_dir: Union[str, Path] = ".") -> Dict[str, Any]:
    """
    Scans the repository and returns full project metadata profile including:
    - site_name
    - description
    - domain / base_url
    - repository URL
    - detected framework
    - public directory
    - inferred domain niche
    - existing AEO artifacts
    """
    root = Path(project_dir).resolve()
    framework = detect_framework(root)

    profile: Dict[str, Any] = {
        "project_dir": str(root),
        "framework": framework,
        "site_name": None,
        "description": None,
        "version": "1.0.0",
        "domain": None,
        "base_url": None,
        "repository": None,
        "niche": "developer_tools",
        "public_dir": "public",
        "has_existing_aeo": False,
        "existing_artifacts": []
    }

    # Determine default public directory based on framework
    if framework == "sveltekit":
        profile["public_dir"] = "static" if (root / "static").is_dir() else "static"
    elif framework == "hugo":
        profile["public_dir"] = "static" if (root / "static").is_dir() else "static"
    elif framework in ("static", "jekyll"):
        profile["public_dir"] = "public" if (root / "public").is_dir() else "."
    else:
        profile["public_dir"] = "public"

    # 1. Read package.json
    pkg_file = root / "package.json"
    if pkg_file.exists():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            raw_name = pkg.get("name")
            if raw_name:
                # Clean up scoped npm names like @org/my-app -> My App
                cleaned = re.sub(r"^@[^/]+/", "", raw_name).replace("-", " ").replace("_", " ").title()
                profile["site_name"] = cleaned

            profile["description"] = pkg.get("description")
            if pkg.get("version"):
                profile["version"] = pkg.get("version")

            if pkg.get("homepage"):
                hp = pkg.get("homepage", "").rstrip("/")
                if hp.startswith("http"):
                    profile["base_url"] = hp
                    # Extract domain without protocol
                    domain_m = re.search(r"https?://([^/]+)", hp)
                    if domain_m:
                        profile["domain"] = domain_m.group(1)

            repo = pkg.get("repository")
            if isinstance(repo, dict):
                profile["repository"] = repo.get("url")
            elif isinstance(repo, str):
                profile["repository"] = repo
        except Exception:
            pass

    # 2. Read pyproject.toml if package.json didn't provide name
    pyproj_file = root / "pyproject.toml"
    if pyproj_file.exists() and not profile["site_name"]:
        try:
            content = pyproj_file.read_text(encoding="utf-8")
            name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_m:
                profile["site_name"] = name_m.group(1).replace("-", " ").replace("_", " ").title()
            desc_m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_m and not profile["description"]:
                profile["description"] = desc_m.group(1)
        except Exception:
            pass

    # 3. Read CNAME file if present
    cname_file = root / "CNAME"
    if not cname_file.exists() and (root / "public" / "CNAME").exists():
        cname_file = root / "public" / "CNAME"
    if cname_file.exists():
        try:
            cname = cname_file.read_text(encoding="utf-8").strip()
            if cname:
                profile["domain"] = cname
                profile["base_url"] = f"https://{cname}"
        except Exception:
            pass

    # 4. Fallback site name to folder name
    if not profile["site_name"]:
        folder_name = root.name
        profile["site_name"] = folder_name.replace("-", " ").replace("_", " ").title()

    # 5. Fallback domain
    if not profile["domain"]:
        slug = re.sub(r"[^a-z0-9]", "", profile["site_name"].lower())
        profile["domain"] = f"{slug or 'example'}.com"
        profile["base_url"] = f"https://{profile['domain']}"

    # 6. Heuristic niche inference from description and dependencies
    text_corpus = f"{profile['site_name']} {profile.get('description', '')}".lower()
    if any(k in text_corpus for k in ("defi", "solana", "ethereum", "web3", "crypto", "token", "wallet", "nft", "blockchain")):
        profile["niche"] = "developer_tools"
    elif any(k in text_corpus for k in ("agent", "llm", "ai ", "gpt", "model", "prompt", "inference", "rag", "embedding")):
        profile["niche"] = "ai_swarm"
    elif any(k in text_corpus for k in ("shop", "store", "commerce", "cart", "product", "checkout", "clothing", "retail")):
        profile["niche"] = "ecommerce"
    elif any(k in text_corpus for k in ("b2b", "saas", "enterprise", "crm", "workflow", "platform", "billing", "analytics")):
        profile["niche"] = "saas"
    elif any(k in text_corpus for k in ("doctor", "dental", "lawyer", "plumber", "clinic", "restaurant", "local", "gym")):
        profile["niche"] = "local_business"
    elif any(k in text_corpus for k in ("news", "blog", "magazine", "media", "journal", "newsletter", "article")):
        profile["niche"] = "creator"
    elif any(k in text_corpus for k in ("security", "auth", "soc2", "vulnerability", "audit", "pentest")):
        profile["niche"] = "cybersecurity"
    else:
        profile["niche"] = "developer_tools"

    # 7. Check for existing AEO artifacts
    check_paths = [
        root / "schema-graph.json",
        root / "public" / "schema-graph.json",
        root / "static" / "schema-graph.json",
        root / "llms.txt",
        root / "public" / "llms.txt",
        root / "static" / "llms.txt",
        root / "ai.txt",
        root / "public" / "ai.txt",
        root / "robots.txt",
        root / "public" / "robots.txt",
    ]
    for cp in check_paths:
        if cp.exists():
            profile["has_existing_aeo"] = True
            profile["existing_artifacts"].append(str(cp.relative_to(root)))

    return profile


# =============================================================================
# Terminal UI & Interactive Prompting
# =============================================================================

def _print_banner() -> None:
    """Prints the colorful ASCII banner."""
    c = Colors
    print(f"\n{c.BOLD}{c.CYAN}╔══════════════════════════════════════════════════════════════════════════════════╗{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║  {c.GREEN}⚡ AEO GRAPH ENGINE — INTERACTIVE PROJECT SETUP WIZARD{c.CYAN}                          ║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}║  {c.DIM}Answer Engine Optimization (AEO/GEO), Schema.org Graph & llms.txt Generator{c.CYAN}    ║{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}╚══════════════════════════════════════════════════════════════════════════════════╝{c.RESET}\n")


def _prompt_user(label: str, default: str, options: Optional[List[str]] = None) -> str:
    """Prompts the user interactively with fallback handling."""
    c = Colors
    opt_str = f" ({'/'.join(options)})" if options else ""
    prompt_str = f"  {c.BOLD}{c.CYAN}?{c.RESET} {c.BOLD}{label}{opt_str}{c.RESET} [{c.GREEN}{default}{c.RESET}]: "
    try:
        val = input(prompt_str).strip()
        return val if val else default
    except (EOFError, KeyboardInterrupt):
        print(f"\n{c.YELLOW}Defaulting to: {default}{c.RESET}")
        return default


def _prompt_yes_no(label: str, default: bool = True) -> bool:
    """Prompts for a yes/no boolean value."""
    default_str = "Y/n" if default else "y/N"
    c = Colors
    prompt_str = f"  {c.BOLD}{c.CYAN}?{c.RESET} {c.BOLD}{label}{c.RESET} [{c.GREEN}{default_str}{c.RESET}]: "
    try:
        val = input(prompt_str).strip().lower()
        if not val:
            return default
        return val in ("y", "yes", "true", "1")
    except (EOFError, KeyboardInterrupt):
        return default


# =============================================================================
# Wizard Execution
# =============================================================================

def run_wizard(
    project_dir: str = ".",
    non_interactive: bool = False,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Runs the project setup wizard.
    
    1. Scans and profiles the repository.
    2. Collects settings (interactively or via overrides/defaults).
    3. Generates complete AEO bundle (schema-graph.json, llms.txt, llms-full.txt, ai.txt, robots.txt).
    4. Writes framework integration code (layout, head tags, route handlers).
    5. Validates generated bundle and computes AEO Readiness Score.
    6. Prints colorful summary table.

    Returns:
        Dict with success status, profile, config, created files, score, and validation report.
    """
    configure_utf8_streams()
    c = Colors
    root_path = Path(project_dir).resolve()
    overrides = overrides or {}

    # Step 1: Detect repository profile
    profile = detect_project_profile(root_path)

    site_name = overrides.get("site_name") or profile["site_name"] or "My Application"
    domain = overrides.get("domain") or profile["domain"] or "example.com"
    base_url = overrides.get("base_url") or profile["base_url"] or f"https://{domain}"
    description = overrides.get("description") or profile.get("description") or f"{site_name} Official Platform"
    framework = overrides.get("framework") or profile["framework"]
    framework = normalize_framework_name(framework)
    niche = normalize_niche_name(overrides.get("niche") or profile["niche"])
    public_dir_name = overrides.get("public_dir") or profile["public_dir"]
    write_framework_code = overrides.get("write_framework_code", True)

    # Step 2: Interactive Prompts (if not non-interactive)
    if not non_interactive:
        _print_banner()
        print(f"  {c.BOLD}Detected Project Context:{c.RESET}")
        print(f"    • Root Directory: {c.CYAN}{root_path}{c.RESET}")
        print(f"    • Framework:      {c.GREEN}{framework}{c.RESET}")
        print(f"    • Suggested Name: {c.GREEN}{site_name}{c.RESET}")
        print(f"    • Domain / URL:   {c.GREEN}{domain}{c.RESET}")
        print(f"    • Domain Niche:   {c.GREEN}{niche}{c.RESET}")
        if profile["has_existing_aeo"]:
            print(f"    • Existing AEO:   {c.YELLOW}{', '.join(profile['existing_artifacts'])}{c.RESET}")
        print()

        site_name = _prompt_user("Application / Website Name", site_name)
        domain = _prompt_user("Primary Domain / Hostname", domain)
        if not domain.startswith("http"):
            base_url = f"https://{domain}"
        else:
            base_url = domain
            domain = re.sub(r"^https?://", "", domain).split("/")[0]

        description = _prompt_user("Short Description / Tagline", description)

        # Niche selection
        niche_list = list(NICHE_PRESETS.keys())
        niche_input = _prompt_user("Domain Niche Preset", niche, options=niche_list[:4])
        niche = normalize_niche_name(niche_input)

        # Framework selection
        framework = _prompt_user("Web Framework", framework, options=SUPPORTED_FRAMEWORKS[:5])
        framework = normalize_framework_name(framework)

        # Public directory
        public_dir_name = _prompt_user("Static Assets Directory", public_dir_name)
        write_framework_code = _prompt_yes_no("Generate Framework Integration Code & SEO Components?", default=True)
    else:
        # Non-interactive announcement
        print(f"{c.CYAN}🚀 AEO Wizard: Initializing project at '{root_path}' for framework '{framework}'...{c.RESET}")

    # Step 3: Resolve Configuration
    user_config = {
        "site_name": site_name,
        "domain": domain,
        "base_url": base_url,
        "description": description,
        "tagline": description,
        "framework": framework,
    }
    if profile.get("repository"):
        user_config["repository"] = profile["repository"]

    resolved_cfg = resolve_config(user_config, niche=niche)

    # Step 4: Write Core AEO Bundle & Framework Integration Code
    created_files: Dict[str, str] = {}
    
    # Target directory for public discovery assets (llms.txt, robots.txt, schema-graph.json, etc.)
    if public_dir_name in (".", "", None):
        bundle_dest = root_path
    else:
        bundle_dest = root_path / public_dir_name
    bundle_dest.mkdir(parents=True, exist_ok=True)

    # 4a. Core AEO Machine Discovery Bundle
    schema_graph = generate_schema_graph(resolved_cfg, niche=niche)
    llms_txt = generate_llms_txt(resolved_cfg, niche=niche)
    llms_full_txt = generate_llms_full_txt(resolved_cfg, niche=niche)
    ai_txt = generate_ai_txt(resolved_cfg, niche=niche)
    robots_txt = generate_robots_txt(resolved_cfg, niche=niche)

    schema_file = bundle_dest / "schema-graph.json"
    with open(schema_file, "w", encoding="utf-8") as f:
        json.dump(schema_graph, f, indent=2, ensure_ascii=False)
    created_files["schema-graph.json"] = str(schema_file)

    llms_file = bundle_dest / "llms.txt"
    with open(llms_file, "w", encoding="utf-8") as f:
        f.write(llms_txt)
    created_files["llms.txt"] = str(llms_file)

    llms_full_file = bundle_dest / "llms-full.txt"
    with open(llms_full_file, "w", encoding="utf-8") as f:
        f.write(llms_full_txt)
    created_files["llms-full.txt"] = str(llms_full_file)

    ai_file = bundle_dest / "ai.txt"
    with open(ai_file, "w", encoding="utf-8") as f:
        f.write(ai_txt)
    created_files["ai.txt"] = str(ai_file)

    # Write robots.txt if not in nextjs_app (which uses app/robots.ts)
    if framework != "nextjs_app":
        robots_file = bundle_dest / "robots.txt"
        with open(robots_file, "w", encoding="utf-8") as f:
            f.write(robots_txt)
        created_files["robots.txt"] = str(robots_file)

    # 4b. Framework Integration Code
    if write_framework_code:
        exporter = FrameworkExporter(config=resolved_cfg, niche=niche)
        fw_files = exporter.export_framework(framework)
        for rel_p, content in fw_files.items():
            dest = root_path / rel_p
            dest.parent.mkdir(parents=True, exist_ok=True)
            with open(dest, "w", encoding="utf-8") as f:
                f.write(content)
            created_files[rel_p] = str(dest)

    # 4c. Inject into root index.html if static and index.html exists
    index_html = root_path / "index.html"
    if index_html.exists() and framework in ("static", "vite_react"):
        try:
            inject_file(index_html, schema_graph)
            created_files["index.html (injected)"] = str(index_html)
        except Exception:
            pass

    # Step 5: Validate the Generated Bundle
    validation_report = validate_aeo_bundle(bundle_dest)
    report_data = validation_report.to_dict()
    score = report_data["score"]
    status = report_data["status"]

    # Step 6: Print Colorful Terminal Summary
    print(f"\n{c.BOLD}{c.CYAN}┌──────────────────────────────────────────────────────────────────────────────────┐{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}│  {c.GREEN}✨ AEO GRAPH ENGINE INITIALIZATION COMPLETE{c.CYAN}                                      │{c.RESET}")
    print(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    print(f"│  {c.BOLD}Project Name:{c.RESET}     {site_name:<59}│")
    print(f"│  {c.BOLD}Canonical URL:{c.RESET}    {base_url:<59}│")
    print(f"│  {c.BOLD}Framework:{c.RESET}        {framework:<59}│")
    print(f"│  {c.BOLD}Domain Niche:{c.RESET}     {niche:<59}│")
    print(f"│  {c.BOLD}Assets Dest:{c.RESET}      {str(bundle_dest):<59}│")
    print(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    print(f"│  {c.BOLD}Generated Artifacts & Integration Files:{c.RESET}                                      │")
    for fname in sorted(created_files.keys()):
        print(f"│    {c.GREEN}✔{c.RESET} {fname:<74}│")
    print(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    
    score_color = c.GREEN if score >= 85 else c.YELLOW if score >= 70 else c.RED
    print(f"│  {c.BOLD}AEO Readiness Score:{c.RESET} {score_color}{score:>5.1f} / 100 [{status}]{c.RESET}                                      │")
    print(f"│  {c.BOLD}Validation Summary:{c.RESET}  {report_data['passed_count']} Passed Checks | {report_data['warnings_count']} Warning(s) | {report_data['errors_count']} Error(s)         │")
    print(f"{c.BOLD}{c.CYAN}├──────────────────────────────────────────────────────────────────────────────────┤{c.RESET}")
    print(f"│  {c.BOLD}Next Steps:{c.RESET}                                                                        │")
    print(f"│    1. Inspect {c.CYAN}{bundle_dest / 'llms.txt'}{c.RESET} and customize project sections.                 │")
    print(f"│    2. Run CI audit gate: {c.GREEN}python3 -m aeo_graph_engine.ci_gate .{c.RESET}                     │")
    print(f"│    3. Launch Studio:     {c.GREEN}aeo serve --open{c.RESET}                                             │")
    print(f"{c.BOLD}{c.CYAN}└──────────────────────────────────────────────────────────────────────────────────┘{c.RESET}\n")

    return {
        "success": True,
        "score": score,
        "status": status,
        "framework": framework,
        "project_dir": str(root_path),
        "bundle_dir": str(bundle_dest),
        "config": resolved_cfg,
        "profile": profile,
        "files_created": created_files,
        "validation_report": report_data,
    }

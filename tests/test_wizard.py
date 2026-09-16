"""
Unit tests for AEO Project Setup Wizard and Framework Auto-Detection.
"""

import json
from pathlib import Path
from unittest.mock import patch

from aeo_graph_engine.wizard import (
    detect_framework,
    detect_project_profile,
    run_wizard,
)
from aeo_graph_engine.cli import main


def test_detect_framework_nextjs_app(tmp_path):
    # App router: next.config.js + app/ dir
    (tmp_path / "next.config.js").write_text("module.exports = {};", encoding="utf-8")
    (tmp_path / "app").mkdir()
    assert detect_framework(tmp_path) == "nextjs_app"


def test_detect_framework_nextjs_pages(tmp_path):
    # Pages router: next.config.mjs + pages/ dir
    (tmp_path / "next.config.mjs").write_text("export default {};", encoding="utf-8")
    (tmp_path / "pages").mkdir()
    assert detect_framework(tmp_path) == "nextjs_pages"


def test_detect_framework_astro(tmp_path):
    # Astro: astro.config.mjs
    (tmp_path / "astro.config.mjs").write_text("export default defineConfig({});", encoding="utf-8")
    assert detect_framework(tmp_path) == "astro"


def test_detect_framework_vite_react(tmp_path):
    # Vite React: vite.config.ts
    (tmp_path / "vite.config.ts").write_text("export default defineConfig({});", encoding="utf-8")
    assert detect_framework(tmp_path) == "vite_react"


def test_detect_framework_sveltekit(tmp_path):
    # SvelteKit: svelte.config.js
    (tmp_path / "svelte.config.js").write_text("export default {};", encoding="utf-8")
    assert detect_framework(tmp_path) == "sveltekit"


def test_detect_framework_remix(tmp_path):
    # Remix: remix.config.js
    (tmp_path / "remix.config.js").write_text("module.exports = {};", encoding="utf-8")
    assert detect_framework(tmp_path) == "remix"


def test_detect_framework_nuxt(tmp_path):
    # Nuxt: nuxt.config.ts
    (tmp_path / "nuxt.config.ts").write_text("export default defineNuxtConfig({});", encoding="utf-8")
    assert detect_framework(tmp_path) == "nuxt"


def test_detect_framework_hugo(tmp_path):
    # Hugo: config.toml + archetypes/
    (tmp_path / "config.toml").write_text("baseURL = 'https://example.org/'", encoding="utf-8")
    (tmp_path / "archetypes").mkdir()
    assert detect_framework(tmp_path) == "hugo"


def test_detect_framework_jekyll(tmp_path):
    # Jekyll: _config.yml
    (tmp_path / "_config.yml").write_text("title: My Jekyll Site", encoding="utf-8")
    assert detect_framework(tmp_path) == "jekyll"


def test_detect_framework_package_json_fallback(tmp_path):
    # Package json dependencies detection
    pkg_data = {
        "name": "my-remix-app",
        "dependencies": {
            "@remix-run/react": "^2.0.0",
            "@remix-run/node": "^2.0.0"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data), encoding="utf-8")
    assert detect_framework(tmp_path) == "remix"


def test_detect_project_profile_metadata_extraction(tmp_path):
    pkg_data = {
        "name": "@acme/defi-yield-protocol",
        "description": "High-performance decentralized lending protocol on Solana",
        "version": "2.1.0",
        "homepage": "https://defiyield.io",
        "repository": "https://github.com/acme/defi-yield",
        "dependencies": {
            "astro": "^4.0.0"
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg_data), encoding="utf-8")
    (tmp_path / "astro.config.mjs").write_text("export default {};", encoding="utf-8")

    profile = detect_project_profile(tmp_path)
    assert profile["site_name"] == "Defi Yield Protocol"
    assert profile["domain"] == "defiyield.io"
    assert profile["base_url"] == "https://defiyield.io"
    assert profile["version"] == "2.1.0"
    assert profile["framework"] == "astro"
    assert profile["niche"] == "developer_tools"
    assert profile["public_dir"] == "public"


def test_detect_project_profile_cname(tmp_path):
    (tmp_path / "CNAME").write_text("superdocs.dev\n", encoding="utf-8")
    profile = detect_project_profile(tmp_path)
    assert profile["domain"] == "superdocs.dev"
    assert profile["base_url"] == "https://superdocs.dev"


def test_run_wizard_non_interactive_nextjs(tmp_path):
    # Setup mock Next.js project
    (tmp_path / "next.config.js").write_text("module.exports = {};", encoding="utf-8")
    (tmp_path / "app").mkdir()
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "saas-flow",
        "description": "Enterprise workflow automation platform"
    }), encoding="utf-8")

    res = run_wizard(project_dir=str(tmp_path), non_interactive=True)
    assert res["success"] is True
    assert res["framework"] == "nextjs_app"
    assert res["score"] >= 80

    pub_dir = tmp_path / "public"
    assert (pub_dir / "schema-graph.json").exists()
    assert (pub_dir / "llms.txt").exists()
    assert (pub_dir / "llms-full.txt").exists()
    assert (pub_dir / "ai.txt").exists()

    # Framework integration files
    assert (tmp_path / "app" / "robots.ts").exists()
    assert (tmp_path / "app" / "sitemap.ts").exists()
    assert (tmp_path / "app" / "layout.tsx").exists()
    assert (tmp_path / "app" / "llms.txt" / "route.ts").exists()


def test_run_wizard_non_interactive_astro_with_overrides(tmp_path):
    overrides = {
        "site_name": "Agentic AI Tools",
        "domain": "agentictools.ai",
        "description": "Open source AI agents registry",
        "niche": "ai_agent",
        "framework": "astro",
    }
    res = run_wizard(project_dir=str(tmp_path), non_interactive=True, overrides=overrides)
    assert res["success"] is True
    assert res["framework"] == "astro"
    assert res["score"] >= 85

    pub_dir = tmp_path / "public"
    assert (pub_dir / "schema-graph.json").exists()
    assert (pub_dir / "llms.txt").exists()
    assert (pub_dir / "ai.txt").exists()
    assert (pub_dir / "robots.txt").exists()

    # Check Astro integration components
    assert (tmp_path / "src" / "components" / "AeoHead.astro").exists()

    schema_json = json.loads((pub_dir / "schema-graph.json").read_text(encoding="utf-8"))
    assert schema_json["@context"] == "https://schema.org"


def test_run_wizard_non_interactive_vite_react(tmp_path):
    (tmp_path / "vite.config.ts").write_text("export default {};", encoding="utf-8")
    (tmp_path / "index.html").write_text("<!DOCTYPE html><html><head><title>App</title></head><body><div id='root'></div></body></html>", encoding="utf-8")

    res = run_wizard(project_dir=str(tmp_path), non_interactive=True)
    assert res["success"] is True
    assert res["framework"] == "vite_react"

    pub_dir = tmp_path / "public"
    assert (pub_dir / "schema-graph.json").exists()
    assert (pub_dir / "llms.txt").exists()
    assert (tmp_path / "src" / "components" / "AeoMeta.tsx").exists()
    assert (tmp_path / "vite-plugin-aeo.ts").exists()


def test_run_wizard_interactive_mocked(tmp_path):
    # Mock user input responses (7 prompts)
    mock_inputs = [
        "Interactive App",       # site_name
        "https://interactive.dev", # domain
        "Interactive description", # description
        "developer_tools",        # niche
        "static",                 # framework
        ".",                      # public_dir
        "y",                      # write_framework_code
    ]
    with patch("builtins.input", side_effect=mock_inputs):
        res = run_wizard(project_dir=str(tmp_path), non_interactive=False)
        assert res["success"] is True
        assert res["framework"] == "static"
        assert (tmp_path / "schema-graph.json").exists()
        assert (tmp_path / "llms.txt").exists()


def test_cli_wizard_command(tmp_path):
    # Test CLI invocation: aeo init <dir> --non-interactive
    (tmp_path / "package.json").write_text(json.dumps({
        "name": "cli-test-project",
        "description": "CLI tested setup"
    }), encoding="utf-8")

    ret = main([
        "init",
        str(tmp_path),
        "--non-interactive",
        "--framework", "astro",
        "--site-name", "CLI Wizard App",
        "--domain", "cliwizard.dev",
        "--niche", "saas"
    ])
    assert ret == 0
    assert (tmp_path / "public" / "schema-graph.json").exists()
    assert (tmp_path / "public" / "llms.txt").exists()
    assert (tmp_path / "src" / "components" / "AeoHead.astro").exists()

"""
Framework and Project Auto-Discovery for AEO Graph Engine.
Detects site metadata, repositories, and documentation paths from
package.json, pyproject.toml, astro.config, next.config, etc.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union


def discover_project_metadata(root_dir: Union[str, Path] = ".") -> Dict[str, Any]:
    """
    Scans a project directory for common configuration files (package.json, pyproject.toml, etc.)
    and returns detected metadata to seed AEO configuration.
    """
    root = Path(root_dir).resolve()
    discovered: Dict[str, Any] = {
        "site_name": None,
        "description": None,
        "version": None,
        "domain": None,
        "framework": "static",
        "repository": None
    }

    # 1. Inspect package.json
    pkg_file = root / "package.json"
    if pkg_file.exists():
        try:
            with open(pkg_file, "r", encoding="utf-8") as f:
                pkg = json.load(f)
            discovered["site_name"] = pkg.get("name")
            discovered["description"] = pkg.get("description")
            discovered["version"] = pkg.get("version")

            # Check framework dependencies
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            if "next" in deps:
                discovered["framework"] = "nextjs"
            elif "astro" in deps:
                discovered["framework"] = "astro"
            elif "nuxt" in deps:
                discovered["framework"] = "nuxt"
            elif "svelte" in deps or "@sveltejs/kit" in deps:
                discovered["framework"] = "sveltekit"
            elif "vite" in deps:
                discovered["framework"] = "vite"

            repo = pkg.get("repository")
            if isinstance(repo, dict):
                discovered["repository"] = repo.get("url")
            elif isinstance(repo, str):
                discovered["repository"] = repo
        except Exception:
            pass

    # 2. Inspect pyproject.toml
    pyproject_file = root / "pyproject.toml"
    if pyproject_file.exists():
        try:
            with open(pyproject_file, "r", encoding="utf-8") as f:
                content = f.read()
            import re
            name_m = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
            if name_m and not discovered["site_name"]:
                discovered["site_name"] = name_m.group(1)

            desc_m = re.search(r'description\s*=\s*["\']([^"\']+)["\']', content)
            if desc_m and not discovered["description"]:
                discovered["description"] = desc_m.group(1)

            ver_m = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
            if ver_m and not discovered["version"]:
                discovered["version"] = ver_m.group(1)

            discovered["framework"] = "python"
        except Exception:
            pass

    # Clean site name
    if discovered["site_name"]:
        # Turn kebab-case or snake_case to Title Case if suitable
        name = discovered["site_name"].replace("-", " ").replace("_", " ").title()
        discovered["site_name"] = name

    return discovered

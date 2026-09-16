#!/usr/bin/env python3
"""
Example CI/CD Post-Build Hook for automated AEO artifact generation and HTML injection.
Can be integrated into Vite, Next.js, Astro, Nuxt, or Hugo build steps.
"""

import sys
import os
from pathlib import Path

# Add src to path if running directly
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from aeo_graph_engine import write_aeo_bundle, validate_aeo_bundle, resolve_config


def run_postbuild_aeo(dist_dir: str = "dist", config_path: str = "examples/sample_config.json") -> int:
    dist_path = Path(dist_dir).resolve()
    print(f"🚀 Running AEO post-build automation for build directory: {dist_path}")

    # 1. Load config if available
    import json
    cfg = None
    if Path(config_path).exists():
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = json.load(f)

    # 2. Find any HTML files to inject
    html_files = list(dist_path.glob("**/*.html")) if dist_path.exists() else []

    # 3. Generate all AEO artifacts into dist/ and inject HTML
    artifacts = write_aeo_bundle(
        output_dir=dist_path,
        config=cfg,
        inject_html_files=html_files
    )

    print(f"✅ Generated {len(artifacts)} AEO assets:")
    for name, filepath in artifacts.items():
        print(f"  • {name} -> {filepath}")

    # 4. Validate output
    report = validate_aeo_bundle(dist_path)
    res = report.to_dict()
    print(f"\n📊 AEO Readiness Audit Score: {res['score']}/100 ({res['status']})")

    if res["errors_count"] > 0:
        print("❌ AEO validation encountered errors!", file=sys.stderr)
        return 1

    print("🎉 AEO post-build process completed successfully!")
    return 0


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "dist"
    sys.exit(run_postbuild_aeo(dist_dir=target))

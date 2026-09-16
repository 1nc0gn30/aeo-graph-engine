"""
AEO Graph Engine
Answer Engine Optimization (AEO/GEO), Schema.org Graph & llms.txt Generator Engine.
"""

__version__ = "1.0.0"
__author__ = "NullAI / 757tech Team"
__license__ = "MIT"

from .core import (
    resolve_config,
    generate_schema_graph,
    generate_llms_txt,
    generate_llms_full_txt,
    generate_ai_txt,
    generate_robots_txt,
    write_aeo_bundle,
)
from .injector import inject_jsonld_into_html, inject_file
from .validator import validate_aeo_bundle, AEODiagnosticReport
from .presets import DEFAULT_CONFIG, NICHE_PRESETS

__all__ = [
    "__version__",
    "resolve_config",
    "generate_schema_graph",
    "generate_llms_txt",
    "generate_llms_full_txt",
    "generate_ai_txt",
    "generate_robots_txt",
    "write_aeo_bundle",
    "inject_jsonld_into_html",
    "inject_file",
    "validate_aeo_bundle",
    "AEODiagnosticReport",
    "DEFAULT_CONFIG",
    "NICHE_PRESETS",
]

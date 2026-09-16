"""
AEO Graph Engine
Answer Engine Optimization (AEO/GEO), Schema.org Graph & llms.txt Generator Engine.
Includes Google-designed AEO Studio interactive dashboard, Model Context Protocol (MCP) server,
framework exporter, HTML extractor, and live multi-page audit crawler.
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
from .extractor import extract_metadata_from_html, extract_from_file
from .discovery import discover_project_metadata
from .ai_config import synthesize_config_from_prompt, get_agent_json_schema
from .scanner import LiveAEOScanner
from .framework_exporter import (
    FrameworkExporter,
    AEORemediationGenerator,
    get_supported_frameworks,
    normalize_framework_name,
)
from .mcp_server import MCPServer, generate_mcp_client_config, run_stdio_server
from .compat import (
    is_windows,
    is_macos,
    is_linux,
    is_termux,
    is_wsl,
    get_platform_info,
    configure_utf8_streams,
    safe_print,
    open_browser,
    atomic_write_text,
    to_posix_path,
    resolve_path,
)
from .ai_gateway import AIGateway, DEFAULT_AI_GATEWAY_CONFIG
from .bot_inspector import BotInspector, AI_BOT_REGISTRY
from .benchmark import compare_sites, CompetitorBenchmark
from .reporter import generate_markdown_report, generate_standalone_html_report, save_report_to_file
from .wizard import run_wizard, detect_framework, detect_project_profile
from .ci_gate import run_ci_check
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
    "extract_metadata_from_html",
    "extract_from_file",
    "discover_project_metadata",
    "synthesize_config_from_prompt",
    "get_agent_json_schema",
    "LiveAEOScanner",
    "FrameworkExporter",
    "AEORemediationGenerator",
    "get_supported_frameworks",
    "normalize_framework_name",
    "MCPServer",
    "generate_mcp_client_config",
    "run_stdio_server",
    "AIGateway",
    "DEFAULT_AI_GATEWAY_CONFIG",
    "BotInspector",
    "AI_BOT_REGISTRY",
    "compare_sites",
    "CompetitorBenchmark",
    "generate_markdown_report",
    "generate_standalone_html_report",
    "save_report_to_file",
    "is_windows",
    "is_macos",
    "is_linux",
    "is_termux",
    "is_wsl",
    "get_platform_info",
    "configure_utf8_streams",
    "safe_print",
    "open_browser",
    "atomic_write_text",
    "to_posix_path",
    "resolve_path",
    "start_ui_server",
    "run_wizard",
    "detect_framework",
    "detect_project_profile",
    "run_ci_check",
    "DEFAULT_CONFIG",
    "NICHE_PRESETS",
]

#!/usr/bin/env python3
"""AEO Graph Engine Standalone Production Server on Port 8127.

Provides real REST API endpoints:
  - /health & /api/health
  - /api/status
  - /api/schema
  - /api/mcp/config
  - /api/export-zip
  - /api/scan
  - /api/generate
  - /api/validate
  - /api/knowledge-graph
and serves the standalone AEO Studio from public/.
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SRC_DIR = ROOT_DIR / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aeo_graph_engine.ui_server import start_ui_server

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AEO Graph Engine Standalone Workstation")
    parser.add_argument("--port", type=int, default=8127, help="Port to listen on (default: 8127)")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    args = parser.parse_args()

    print(f"Starting AEO Graph Engine Server on {args.host}:{args.port}...")
    server = start_ui_server(host=args.host, port=args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AEO Graph Engine server...")
    finally:
        server.server_close()

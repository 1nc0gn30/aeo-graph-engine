"""
Executable module entrypoint for `python3 -m aeo_graph_engine`.
"""

import sys
from .cli import main

if __name__ == "__main__":
    sys.exit(main())

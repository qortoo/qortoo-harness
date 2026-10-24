#!/usr/bin/env python3
"""Backward-compatibility wrapper for scripts/sync_agents.py."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import sync_agents

if __name__ == "__main__":
    # Forward to sync_agents targeting bench-agent
    sys.argv[0] = str(Path(__file__).resolve())
    if "--agent" not in sys.argv:
        sys.argv.extend(["--agent", "bench-agent"])
    sync_agents.main()

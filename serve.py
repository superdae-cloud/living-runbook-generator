#!/usr/bin/env python3
"""
serve.py — runs the FastAPI backend (and, once built, the React dashboard
it serves as static files) on http://127.0.0.1:8000.

USAGE:
    python3 serve.py
    python3 serve.py --port 8080 --no-reload
"""

from __future__ import annotations

import argparse
from pathlib import Path

import uvicorn

SRC_DIR = Path(__file__).parent / "src"


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the Living Runbook Generator API + dashboard.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload on code changes")
    args = parser.parse_args()

    uvicorn.run(
        "lrg.api:app",
        host=args.host,
        port=args.port,
        reload=not args.no_reload,
        app_dir=str(SRC_DIR),
    )


if __name__ == "__main__":
    main()

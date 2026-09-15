#!/usr/bin/env python3
"""
generate_runbooks.py — the "press this button when new tickets show up"
entry point.

USAGE:
    python3 generate_runbooks.py
    python3 generate_runbooks.py --tickets-dir tickets --runbooks-dir runbooks
    python3 generate_runbooks.py --threshold 0.3 --verbose

This ties the whole pipeline together:
    1. ingest.py     — parse every ticket file into a structured Ticket
    2. nlp.py        — vectorize tickets (TF-IDF) so similarity is computable
    3. cluster.py    — group tickets into symptom-signature clusters
    4. generate.py   — render/refresh one runbook Markdown file per cluster,
                        preserving any hand-written manual notes

This is the whole "living" mechanic: nothing here is a one-time script.
Every time it runs, it re-reads ALL tickets (old and new) from scratch and
regenerates every runbook, so a new incident can join an existing pattern
(bumping its frequency count and updating "last seen"), reveal a brand new
pattern (a new runbook file appears), or shift a device list without
anyone manually touching a wiki page.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from lrg import llm
from lrg.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Regenerate troubleshooting runbooks from NOC tickets.")
    parser.add_argument("--tickets-dir", default="tickets", help="Folder of ticket .md files (default: tickets)")
    parser.add_argument("--runbooks-dir", default="runbooks", help="Folder to write runbooks into (default: runbooks)")
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.35,
        help="Cosine-similarity threshold for grouping tickets into one signature (default: 0.35)",
    )
    parser.add_argument(
        "--llm-root-cause",
        action="store_true",
        help="Ask Claude to synthesize one root-cause paragraph per cluster (needs Anthropic credentials; "
        "falls back silently to the verbatim list if unavailable). Cached per cluster in "
        "runbooks/.llm_cache.json so unchanged clusters aren't re-billed on every run.",
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-cluster details while running")
    args = parser.parse_args()

    if args.llm_root_cause and not llm.has_credentials():
        print("Warning: --llm-root-cause was passed but no Anthropic credentials were found — "
              "root causes will fall back to the verbatim per-incident list.")

    result = run_pipeline(
        Path(args.tickets_dir),
        Path(args.runbooks_dir),
        threshold=args.threshold,
        synthesize_root_cause=args.llm_root_cause,
    )
    print(f"Loaded {len(result.tickets)} ticket(s) from {args.tickets_dir}/")
    print(f"Found {len(result.runbooks)} distinct symptom signature(s) at threshold={args.threshold}")

    for runbook, row_indices in zip(result.runbooks, result.clusters):
        if args.verbose:
            ids = ", ".join(result.tickets[i].id for i in row_indices)
            ai_note = " [AI root cause synthesized]" if runbook.ai_root_cause else ""
            print(f"  - {runbook.filename}: {len(row_indices)} incident(s) [{ids}]{ai_note}")
        else:
            print(f"  - wrote {Path(args.runbooks_dir) / runbook.filename}")

    print(f"Wrote index: {result.index_path}")


if __name__ == "__main__":
    main()

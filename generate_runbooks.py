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

from lrg.ingest import load_tickets
from lrg.nlp import build_documents, vectorize
from lrg.cluster import cluster_tickets
from lrg.generate import build_runbook, write_runbook, write_index


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
    parser.add_argument("--verbose", action="store_true", help="Print per-cluster details while running")
    args = parser.parse_args()

    tickets_dir = Path(args.tickets_dir)
    runbooks_dir = Path(args.runbooks_dir)
    runbooks_dir.mkdir(parents=True, exist_ok=True)

    tickets = load_tickets(tickets_dir)
    print(f"Loaded {len(tickets)} ticket(s) from {tickets_dir}/")

    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)

    clusters = cluster_tickets(matrix, threshold=args.threshold)
    print(f"Found {len(clusters)} distinct symptom signature(s) at threshold={args.threshold}")

    runbooks = []
    for row_indices in clusters:
        cluster_tickets_list = [tickets[i] for i in row_indices]
        runbook = build_runbook(cluster_tickets_list, vectorizer, matrix, row_indices)
        out_path = write_runbook(runbook, runbooks_dir)
        runbooks.append(runbook)

        if args.verbose:
            ids = ", ".join(t.id for t in cluster_tickets_list)
            print(f"  - {out_path.name}: {len(cluster_tickets_list)} incident(s) [{ids}]")
        else:
            print(f"  - wrote {out_path}")

    index_path = write_index(runbooks, runbooks_dir)
    print(f"Wrote index: {index_path}")


if __name__ == "__main__":
    main()

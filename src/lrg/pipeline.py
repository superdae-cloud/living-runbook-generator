"""
pipeline.py — the single "run the whole thing" function shared by the CLI
(generate_runbooks.py) and the API server (api.py), so the two can never
drift apart into two slightly-different implementations of the same
ingest -> vectorize -> cluster -> generate pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .cluster import cluster_tickets, compute_similarity
from .generate import Runbook, build_runbook, write_index, write_runbook
from .ingest import Ticket, load_tickets
from .nlp import build_documents, vectorize


@dataclass
class PipelineResult:
    tickets: list[Ticket]
    clusters: list[list[int]]  # row indices into `tickets`, one list per runbook
    similarity: "numpy.ndarray"  # noqa: F821 — avoids importing numpy just for the type
    runbooks: list[Runbook]
    index_path: Path


def run_pipeline(tickets_dir: Path, runbooks_dir: Path, threshold: float = 0.35) -> PipelineResult:
    tickets_dir = Path(tickets_dir)
    runbooks_dir = Path(runbooks_dir)
    runbooks_dir.mkdir(parents=True, exist_ok=True)

    tickets = load_tickets(tickets_dir)
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)
    similarity = compute_similarity(matrix)
    clusters = cluster_tickets(similarity, threshold=threshold)

    runbooks = []
    for row_indices in clusters:
        cluster_ticket_list = [tickets[i] for i in row_indices]
        runbook = build_runbook(cluster_ticket_list, vectorizer, matrix, row_indices)
        write_runbook(runbook, runbooks_dir)
        runbooks.append(runbook)

    index_path = write_index(runbooks, runbooks_dir)

    return PipelineResult(
        tickets=tickets,
        clusters=clusters,
        similarity=similarity,
        runbooks=runbooks,
        index_path=index_path,
    )

"""
pipeline.py — the single "run the whole thing" function shared by the CLI
(generate_runbooks.py) and the API server (api.py), so the two can never
drift apart into two slightly-different implementations of the same
ingest -> vectorize -> cluster -> generate pipeline.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from . import llm
from .cluster import cluster_tickets, compute_similarity
from .generate import Runbook, build_runbook, write_index, write_runbook
from .ingest import Ticket, load_tickets
from .nlp import build_documents, vectorize

CACHE_FILENAME = ".llm_cache.json"


@dataclass
class PipelineResult:
    tickets: list[Ticket]
    clusters: list[list[int]]  # row indices into `tickets`, one list per runbook
    similarity: "numpy.ndarray"  # noqa: F821 — avoids importing numpy just for the type
    runbooks: list[Runbook]
    index_path: Path


def _cluster_cache_key(tickets: list[Ticket]) -> str:
    """
    Identifies a cluster by its actual evidence (ticket IDs + their
    diagnostics/root-cause text), not just row indices — so the cache
    naturally invalidates when a new incident joins the cluster or an
    existing ticket's text changes, and naturally hits again if the same
    set of tickets reappears after an unrelated regenerate.
    """
    joined = "\n".join(sorted(f"{t.id}:{t.diagnostics}:{t.root_cause}" for t in tickets))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def _load_llm_cache(runbooks_dir: Path) -> dict:
    path = runbooks_dir / CACHE_FILENAME
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_llm_cache(runbooks_dir: Path, cache: dict) -> None:
    path = runbooks_dir / CACHE_FILENAME
    path.write_text(json.dumps(cache, indent=2, sort_keys=True), encoding="utf-8")


def run_pipeline(
    tickets_dir: Path,
    runbooks_dir: Path,
    threshold: float = 0.35,
    synthesize_root_cause: bool = False,
) -> PipelineResult:
    tickets_dir = Path(tickets_dir)
    runbooks_dir = Path(runbooks_dir)
    runbooks_dir.mkdir(parents=True, exist_ok=True)

    tickets = load_tickets(tickets_dir)
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)
    similarity = compute_similarity(matrix)
    clusters = cluster_tickets(similarity, threshold=threshold)

    cache = _load_llm_cache(runbooks_dir) if synthesize_root_cause else {}
    cache_dirty = False

    runbooks = []
    for row_indices in clusters:
        cluster_ticket_list = [tickets[i] for i in row_indices]
        runbook = build_runbook(cluster_ticket_list, vectorizer, matrix, row_indices)

        if synthesize_root_cause:
            cache_key = _cluster_cache_key(cluster_ticket_list)
            cached = cache.get(cache_key)
            if cached:
                runbook.ai_root_cause = cached
                runbook.ai_root_cause_model = llm.DEFAULT_MODEL
            else:
                synthesized = llm.synthesize_root_cause(cluster_ticket_list)
                if synthesized:
                    runbook.ai_root_cause = synthesized
                    runbook.ai_root_cause_model = llm.DEFAULT_MODEL
                    cache[cache_key] = synthesized
                    cache_dirty = True
                # else: leave ai_root_cause=None — caller falls back to the
                # verbatim list. Deliberately NOT cached, so a transient
                # failure (or missing credentials at the time) gets retried
                # on the next run instead of being stuck forever.

        write_runbook(runbook, runbooks_dir)
        runbooks.append(runbook)

    if cache_dirty:
        _save_llm_cache(runbooks_dir, cache)

    index_path = write_index(runbooks, runbooks_dir)

    return PipelineResult(
        tickets=tickets,
        clusters=clusters,
        similarity=similarity,
        runbooks=runbooks,
        index_path=index_path,
    )

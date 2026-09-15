"""
api.py — a thin FastAPI wrapper around the existing pipeline, for the
web dashboard.

DESIGN: this module doesn't reimplement any pipeline logic. It calls
pipeline.run_pipeline() (the same function generate_runbooks.py calls) and
serves its result as JSON, plus two write endpoints — creating a new
ticket file and triggering regeneration — that mutate the same tickets/
and runbooks/ folders the CLI already works with. That means the CLI and
the web UI are always looking at the same on-disk state; there's no
separate database to keep in sync.

State is held in a module-level dict (`_state`) rather than a database
because the "database" here *is* the tickets/ and runbooks/ folders —
_state is just a cache of the last pipeline run so every request doesn't
re-run TF-IDF + clustering from scratch.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import llm
from .generate import runbook_to_dict
from .ingest import Ticket
from .pipeline import PipelineResult, run_pipeline

REPO_ROOT = Path(__file__).resolve().parents[2]
TICKETS_DIR = REPO_ROOT / "tickets"
RUNBOOKS_DIR = REPO_ROOT / "runbooks"
DEFAULT_THRESHOLD = 0.35

app = FastAPI(title="Living Runbook Generator API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_state: dict = {"result": None, "threshold": DEFAULT_THRESHOLD, "synthesize": False}


def _regenerate(threshold: float | None = None, synthesize: bool | None = None) -> PipelineResult:
    active_threshold = threshold if threshold is not None else _state["threshold"]
    active_synthesize = synthesize if synthesize is not None else _state["synthesize"]
    result = run_pipeline(
        TICKETS_DIR,
        RUNBOOKS_DIR,
        threshold=active_threshold,
        synthesize_root_cause=active_synthesize,
    )
    _state["result"] = result
    _state["threshold"] = active_threshold
    _state["synthesize"] = active_synthesize
    return result


def _current() -> PipelineResult:
    if _state["result"] is None:
        _regenerate()
    return _state["result"]


@app.on_event("startup")
def _on_startup() -> None:
    _regenerate()


class TicketIn(BaseModel):
    date: str
    device: str
    tags: list[str] = Field(default_factory=list)
    symptoms: str
    diagnostics: str = ""
    root_cause: str = ""
    resolution: str = ""


def _next_ticket_id(tickets: list[Ticket]) -> str:
    nums = []
    for t in tickets:
        digits = "".join(ch for ch in t.id if ch.isdigit())
        if digits:
            nums.append(int(digits))
    return f"INC-{(max(nums) + 1) if nums else 1000}"


def _ticket_markdown(ticket_id: str, payload: TicketIn) -> str:
    tags_yaml = "[" + ", ".join(payload.tags) + "]"
    return (
        "---\n"
        f"id: {ticket_id}\n"
        f"date: {payload.date}\n"
        f"device: {payload.device}\n"
        f"tags: {tags_yaml}\n"
        "---\n\n"
        "## Symptoms\n"
        f"{payload.symptoms.strip()}\n\n"
        "## Diagnostics\n"
        f"{payload.diagnostics.strip() or '- (none recorded)'}\n\n"
        "## Root Cause\n"
        f"{payload.root_cause.strip() or '(unknown)'}\n\n"
        "## Resolution\n"
        f"{payload.resolution.strip() or '- (none recorded)'}\n"
    )


@app.get("/api/runbooks")
def list_runbooks():
    result = _current()
    items = [runbook_to_dict(rb, RUNBOOKS_DIR) for rb in result.runbooks]
    items.sort(key=lambda r: r["incident_count"], reverse=True)
    return items


@app.get("/api/runbooks/{slug}")
def get_runbook(slug: str):
    result = _current()
    for rb in result.runbooks:
        if rb.slug == slug:
            return runbook_to_dict(rb, RUNBOOKS_DIR)
    raise HTTPException(404, f"No runbook with slug '{slug}'")


@app.get("/api/tickets")
def list_tickets():
    result = _current()
    return [
        {
            "id": t.id,
            "date": t.date,
            "device": t.device,
            "tags": t.tags,
            "symptoms": t.symptoms,
            "file": t.source_path.name,
        }
        for t in sorted(result.tickets, key=lambda t: t.date, reverse=True)
    ]


@app.get("/api/tickets/{ticket_id}")
def get_ticket(ticket_id: str):
    result = _current()
    for t in result.tickets:
        if t.id == ticket_id:
            return {
                "id": t.id,
                "date": t.date,
                "device": t.device,
                "tags": t.tags,
                "symptoms": t.symptoms,
                "diagnostics": t.diagnostics,
                "root_cause": t.root_cause,
                "resolution": t.resolution,
                "file": t.source_path.name,
            }
    raise HTTPException(404, f"No ticket with id '{ticket_id}'")


@app.post("/api/tickets", status_code=201)
def create_ticket(payload: TicketIn):
    result = _current()
    ticket_id = _next_ticket_id(result.tickets)
    filename = f"{payload.date}-{ticket_id.lower()}.md"
    path = TICKETS_DIR / filename
    if path.exists():
        raise HTTPException(409, f"{filename} already exists — try a different date")

    path.write_text(_ticket_markdown(ticket_id, payload), encoding="utf-8")
    new_result = _regenerate()
    return {
        "created": ticket_id,
        "file": filename,
        "ticket_count": len(new_result.tickets),
        "runbook_count": len(new_result.runbooks),
    }


@app.post("/api/regenerate")
def regenerate(threshold: float | None = None, synthesize: bool | None = None):
    result = _regenerate(threshold, synthesize)
    return {
        "ticket_count": len(result.tickets),
        "cluster_count": len(result.runbooks),
        "threshold": _state["threshold"],
        "synthesize_enabled": _state["synthesize"],
        "synthesized_count": sum(1 for rb in result.runbooks if rb.ai_root_cause),
        "runbook_slugs": [rb.slug for rb in result.runbooks],
    }


@app.get("/api/status")
def status():
    """Lets the frontend know whether the AI-synthesis toggle would actually
    do anything before the user flips it — and after, whether it's on."""
    return {
        "llm_configured": llm.has_credentials(),
        "llm_model": llm.DEFAULT_MODEL,
        "synthesize_enabled": _state["synthesize"],
        "threshold": _state["threshold"],
    }


@app.get("/api/graph")
def graph(threshold: float | None = None):
    """
    Node/edge data for a similarity-graph visualization: one node per
    ticket, one edge per pair whose cosine similarity clears `threshold`
    (defaults to whatever threshold the current runbooks were generated
    at, so the graph always matches what's on screen elsewhere).
    """
    result = _current()
    active_threshold = threshold if threshold is not None else _state["threshold"]

    cluster_of_index: dict[int, str] = {}
    for rb, row_indices in zip(result.runbooks, result.clusters):
        for i in row_indices:
            cluster_of_index[i] = rb.slug

    tickets = result.tickets
    sim = result.similarity

    nodes = [
        {
            "id": t.id,
            "device": t.device,
            "tags": t.tags,
            "date": t.date,
            "cluster": cluster_of_index.get(i, "unclustered"),
        }
        for i, t in enumerate(tickets)
    ]

    edges = []
    n = len(tickets)
    for i in range(n):
        for j in range(i + 1, n):
            weight = float(sim[i, j])
            if weight >= active_threshold:
                edges.append({"source": tickets[i].id, "target": tickets[j].id, "weight": weight})

    return {"nodes": nodes, "edges": edges, "threshold": active_threshold}


@app.get("/api/search")
def search(q: str = ""):
    q_lower = q.lower().strip()
    if not q_lower:
        return {"tickets": [], "runbooks": []}

    result = _current()

    ticket_hits = [
        {"id": t.id, "date": t.date, "device": t.device, "tags": t.tags}
        for t in result.tickets
        if q_lower in t.symptoms.lower()
        or q_lower in t.root_cause.lower()
        or q_lower in t.device.lower()
        or any(q_lower in tag for tag in t.tags)
    ]
    runbook_hits = [
        {"slug": rb.slug, "title": rb.title}
        for rb in result.runbooks
        if q_lower in rb.title.lower() or any(q_lower in term for term in rb.signature_terms)
    ]
    return {"tickets": ticket_hits, "runbooks": runbook_hits}


# Serve the built React app (if present) so `python3 serve.py` alone is
# enough to demo the whole thing — no separate frontend dev server needed.
_web_dist = REPO_ROOT / "web" / "dist"
if _web_dist.exists():
    from fastapi.staticfiles import StaticFiles

    app.mount("/", StaticFiles(directory=str(_web_dist), html=True), name="web")

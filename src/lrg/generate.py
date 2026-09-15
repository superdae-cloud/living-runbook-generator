"""
generate.py — turns a cluster of tickets into an actual runbook Markdown
file, and re-generates that file every time this pipeline runs without
destroying notes a human engineer has hand-written into it.

THE "LIVING" PART OF "LIVING RUNBOOK GENERATOR" LIVES HERE. A static wiki
page, once written, only changes when someone remembers to edit it. This
generator instead treats the runbook body as a *derived artifact* —
something rebuilt fresh from ticket history every time — while keeping
one clearly-marked section that's the human's to own:

    <!-- MANUAL NOTES START -->
    (anything an engineer types here survives regeneration)
    <!-- MANUAL NOTES END -->

Before overwriting a runbook file, we check whether it already exists,
and if so, slice out whatever's between those two markers and splice it
back into the freshly-generated version. This is the same idea as a
"generated code" header in scaffolded source files — machine-owned above
the line, human-owned below it.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .ingest import Ticket
from .nlp import top_terms_for_rows

MANUAL_NOTES_START = "<!-- MANUAL NOTES START -->"
MANUAL_NOTES_END = "<!-- MANUAL NOTES END -->"

MANUAL_NOTES_BLOCK_RE = re.compile(
    re.escape(MANUAL_NOTES_START) + r"(.*?)" + re.escape(MANUAL_NOTES_END),
    re.DOTALL,
)


@dataclass
class Runbook:
    slug: str
    title: str
    signature_terms: list[str]
    tickets: list[Ticket]
    ai_root_cause: str | None = None
    ai_root_cause_model: str | None = None

    @property
    def filename(self) -> str:
        return f"{self.slug}.md"


def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _format_tag(tag: str) -> str:
    """'pe-router' -> 'PE-Router', 'bgp' -> 'BGP', 'mtu' -> 'MTU'."""
    parts = tag.split("-")
    return "-".join(p.upper() if len(p) <= 4 else p.capitalize() for p in parts)


def _cluster_slug_and_title(tickets: list[Ticket], signature_terms: list[str]) -> tuple[str, str]:
    tag_counts = Counter(tag for t in tickets for tag in t.tags)
    top_tags = [tag for tag, _ in tag_counts.most_common(3)]

    if top_tags:
        slug = _slugify("-".join(top_tags))
        title = " + ".join(_format_tag(tag) for tag in top_tags)
    elif signature_terms:
        slug = _slugify("-".join(signature_terms[:3]))
        title = " / ".join(signature_terms[:3]).title()
    else:
        slug = _slugify(tickets[0].id)
        title = f"Incident pattern ({tickets[0].id})"

    return slug, title


def _dedupe_lines(blocks: list[str]) -> list[str]:
    """
    Flattens a list of multi-line bullet blocks into a deduplicated,
    order-preserving list of unique lines. Real ticket text won't be
    byte-identical across incidents, so this is deliberately simple
    (exact-match after normalization) rather than trying to do fuzzy
    semantic dedup — it's easy to reason about, and leaving some
    near-duplicate lines in a runbook is far safer than a dedup step
    that accidentally throws away a distinct diagnostic step.
    """
    seen: set[str] = set()
    ordered: list[str] = []
    for block in blocks:
        for raw_line in block.splitlines():
            line = raw_line.strip().lstrip("-*").strip()
            if not line:
                continue
            key = line.lower()
            if key not in seen:
                seen.add(key)
                ordered.append(line)
    return ordered


def build_runbook(tickets: list[Ticket], vectorizer, matrix, row_indices: list[int]) -> Runbook:
    signature_terms = top_terms_for_rows(vectorizer, matrix, row_indices)
    slug, title = _cluster_slug_and_title(tickets, signature_terms)
    return Runbook(slug=slug, title=title, signature_terms=signature_terms, tickets=tickets)


def extract_manual_notes(path: Path) -> str:
    if not path.exists():
        return ""
    match = MANUAL_NOTES_BLOCK_RE.search(path.read_text(encoding="utf-8"))
    return match.group(1).strip("\n") if match else ""


def runbook_view(runbook: Runbook, existing_manual_notes: str) -> dict:
    """
    Computes every derived field a rendered runbook needs (sorted tickets,
    deduped diagnostics/resolutions, ranked root causes, etc.) as a plain
    dict. This is the single source of truth for "what a runbook contains" —
    both the Markdown renderer below and the API's JSON responses build on
    top of this instead of recomputing it separately, so the web UI can
    never drift from the generated .md files.
    """
    tickets = sorted(runbook.tickets, key=lambda t: t.date)
    dates = [t.date for t in tickets if t.date]
    devices = sorted({t.device for t in tickets if t.device})

    diagnostics = _dedupe_lines([t.diagnostics for t in tickets])
    resolutions = _dedupe_lines([t.resolution for t in tickets])
    root_causes = Counter(t.root_cause.strip() for t in tickets if t.root_cause.strip())

    return {
        "slug": runbook.slug,
        "title": runbook.title,
        "signature_terms": runbook.signature_terms,
        "devices": devices,
        "incident_count": len(tickets),
        "first_seen": dates[0] if dates else None,
        "last_seen": dates[-1] if dates else None,
        "diagnostics": diagnostics,
        "root_causes": [{"cause": cause, "count": count} for cause, count in root_causes.most_common()],
        "resolutions": resolutions,
        "source_incidents": [
            {"id": t.id, "date": t.date, "device": t.device, "file": t.source_path.name} for t in tickets
        ],
        "manual_notes": existing_manual_notes,
        "ai_root_cause": runbook.ai_root_cause,
        "ai_root_cause_model": runbook.ai_root_cause_model,
    }


def render_runbook_markdown(runbook: Runbook, existing_manual_notes: str) -> str:
    view = runbook_view(runbook, existing_manual_notes)
    tickets = sorted(runbook.tickets, key=lambda t: t.date)
    dates = [t.date for t in tickets if t.date]
    devices = view["devices"]
    diagnostics = view["diagnostics"]
    resolutions = view["resolutions"]

    lines: list[str] = []
    lines.append(f"# {runbook.title}")
    lines.append("")
    lines.append(
        f"*Auto-generated from {len(tickets)} incident(s)"
        + (f", {dates[0]} → {dates[-1]}" if dates else "")
        + ". Do not hand-edit above the manual notes section — it will be"
        " overwritten next time this pipeline runs.*"
    )
    lines.append("")

    lines.append("## Symptom signature")
    if runbook.signature_terms:
        for term in runbook.signature_terms:
            lines.append(f"- {term}")
    else:
        lines.append("- (no distinguishing terms extracted yet)")
    if devices:
        lines.append(f"- Seen on: {', '.join(devices)}")
    lines.append("")

    lines.append("## Frequency")
    lines.append(f"- {len(tickets)} incident(s) matched this signature")
    if dates:
        lines.append(f"- First seen: {dates[0]}")
        lines.append(f"- Last seen: {dates[-1]}")
    lines.append("")

    lines.append("## Diagnostic steps seen across these incidents")
    if diagnostics:
        for line in diagnostics:
            lines.append(f"- {line}")
    else:
        lines.append("- (none recorded)")
    lines.append("")

    lines.append("## Root cause")
    if view["ai_root_cause"]:
        model_note = f" using {view['ai_root_cause_model']}" if view["ai_root_cause_model"] else ""
        lines.append(
            f"*AI-synthesized from {len(tickets)} incident(s){model_note} — verify against"
            " source tickets before treating this as ground truth during a live incident.*"
        )
        lines.append("")
        lines.append(view["ai_root_cause"])
        lines.append("")
        lines.append("<details>")
        lines.append("<summary>Raw root-cause reports per incident</summary>")
        lines.append("")
        for rc in view["root_causes"]:
            prefix = f"**({rc['count']}x)** " if rc["count"] > 1 else ""
            lines.append(f"- {prefix}{rc['cause']}")
        lines.append("")
        lines.append("</details>")
    elif view["root_causes"]:
        for rc in view["root_causes"]:
            prefix = f"**({rc['count']}x)** " if rc["count"] > 1 else ""
            lines.append(f"- {prefix}{rc['cause']}")
    else:
        lines.append("- (none recorded)")
    lines.append("")

    lines.append("## Resolution steps that worked")
    if resolutions:
        for line in resolutions:
            lines.append(f"- {line}")
    else:
        lines.append("- (none recorded)")
    lines.append("")

    lines.append("## Source incidents")
    for t in tickets:
        lines.append(f"- `{t.id}` ({t.date}, {t.device or 'device n/a'}) — `{t.source_path.name}`")
    lines.append("")

    lines.append("## Manual notes")
    lines.append(
        "*Anything you write between the two markers below survives the"
        " next auto-regeneration.*"
    )
    lines.append("")
    lines.append(MANUAL_NOTES_START)
    lines.append(existing_manual_notes if existing_manual_notes else "\n(add engineer notes here)\n")
    lines.append(MANUAL_NOTES_END)
    lines.append("")

    return "\n".join(lines)


def write_runbook(runbook: Runbook, runbooks_dir: Path) -> Path:
    out_path = Path(runbooks_dir) / runbook.filename
    existing_notes = extract_manual_notes(out_path)
    content = render_runbook_markdown(runbook, existing_notes)
    out_path.write_text(content, encoding="utf-8")
    return out_path


def runbook_to_dict(runbook: Runbook, runbooks_dir: Path) -> dict:
    """Same manual-notes-preserving lookup as write_runbook(), but for
    callers (the API) that want JSON instead of a rendered .md file."""
    out_path = Path(runbooks_dir) / runbook.filename
    existing_notes = extract_manual_notes(out_path)
    return runbook_view(runbook, existing_notes)


def write_index(runbooks: list[Runbook], runbooks_dir: Path) -> Path:
    lines = ["# Runbook index", "", "*Auto-generated. Ranked by incident frequency.*", ""]
    for rb in sorted(runbooks, key=lambda r: len(r.tickets), reverse=True):
        lines.append(f"- [{rb.title}](./{rb.filename}) — {len(rb.tickets)} incident(s)")
    out_path = Path(runbooks_dir) / "index.md"
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out_path

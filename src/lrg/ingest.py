"""
ingest.py — turns raw ticket files into structured Ticket objects.

WHY THIS SHAPE: an NLP pipeline is only as good as the structure you can
pull out of your raw text. Rather than throwing whole ticket files at a
model, we parse them into named sections up front (Symptoms, Diagnostics,
Root Cause, Resolution). Everything downstream — signature extraction,
clustering, runbook rendering — works on these fields instead of raw
blobs of prose, which makes it far more predictable and debuggable.

Ticket file format (see tickets/*.md for real examples):

    ---
    id: INC-1001
    date: 2024-01-15
    device: PE1-DEN
    tags: [bgp, cpu, pe-router]
    ---

    ## Symptoms
    ...free text...

    ## Diagnostics
    - bullet point
    - bullet point

    ## Root Cause
    ...free text...

    ## Resolution
    - bullet point
    - bullet point

This is just YAML frontmatter (metadata) + Markdown headers (sections) —
a format you've likely already seen if you've poked at static site
generators or Obsidian notes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)
SECTION_HEADER_RE = re.compile(r"^##\s+(.+)")


@dataclass
class Ticket:
    id: str
    date: str
    device: str
    tags: list[str]
    symptoms: str
    diagnostics: str
    root_cause: str
    resolution: str
    source_path: Path = field(repr=False)

    @property
    def nlp_text(self) -> str:
        """The text we actually feed to the NLP layer for this ticket."""
        return f"{self.symptoms}\n{self.diagnostics}".strip()


def _split_sections(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    buf: list[str] = []

    for line in body.splitlines():
        header_match = SECTION_HEADER_RE.match(line)
        if header_match:
            if current is not None:
                sections[current] = "\n".join(buf).strip()
            current = header_match.group(1).strip().lower()
            buf = []
        else:
            buf.append(line)

    if current is not None:
        sections[current] = "\n".join(buf).strip()

    return sections


def parse_ticket(path: Path) -> Ticket:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ValueError(
            f"{path} doesn't look like a ticket file — missing '---' YAML "
            "frontmatter at the top."
        )

    frontmatter = yaml.safe_load(match.group(1)) or {}
    sections = _split_sections(match.group(2))

    return Ticket(
        id=str(frontmatter.get("id", path.stem)),
        date=str(frontmatter.get("date", "")),
        device=str(frontmatter.get("device", "")),
        tags=[str(t).strip().lower() for t in frontmatter.get("tags", [])],
        symptoms=sections.get("symptoms", ""),
        diagnostics=sections.get("diagnostics", ""),
        root_cause=sections.get("root cause", ""),
        resolution=sections.get("resolution", ""),
        source_path=path,
    )


def load_tickets(tickets_dir: Path) -> list[Ticket]:
    files = sorted(Path(tickets_dir).glob("*.md"))
    if not files:
        raise FileNotFoundError(
            f"No .md ticket files found in {tickets_dir}. Drop some in there "
            "first — see tickets/ for the expected format."
        )
    return [parse_ticket(f) for f in files]

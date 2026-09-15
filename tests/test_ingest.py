import pytest

from lrg.ingest import load_tickets, parse_ticket

TICKET_TEXT = """---
id: INC-9001
date: 2025-06-01
device: PE9-TEST
tags: [bgp, cpu, pe-router]
---

## Symptoms
BGP session flapping under load.

## Diagnostics
- checked show bgp neighbors
- checked show processes cpu

## Root Cause
A malformed route-map.

## Resolution
- fixed the route-map
"""


def test_parse_ticket_extracts_frontmatter_and_sections(tmp_path):
    path = tmp_path / "2025-06-01-inc-9001.md"
    path.write_text(TICKET_TEXT, encoding="utf-8")

    ticket = parse_ticket(path)

    assert ticket.id == "INC-9001"
    assert ticket.date == "2025-06-01"
    assert ticket.device == "PE9-TEST"
    assert ticket.tags == ["bgp", "cpu", "pe-router"]
    assert "BGP session flapping" in ticket.symptoms
    assert "checked show bgp neighbors" in ticket.diagnostics
    assert ticket.root_cause == "A malformed route-map."
    assert "fixed the route-map" in ticket.resolution
    assert ticket.source_path == path


def test_parse_ticket_lowercases_tags(tmp_path):
    text = TICKET_TEXT.replace("tags: [bgp, cpu, pe-router]", "tags: [BGP, CPU]")
    path = tmp_path / "t.md"
    path.write_text(text, encoding="utf-8")

    ticket = parse_ticket(path)

    assert ticket.tags == ["bgp", "cpu"]


def test_parse_ticket_missing_frontmatter_raises(tmp_path):
    path = tmp_path / "not-a-ticket.md"
    path.write_text("# Just a heading\n\nSome text.\n", encoding="utf-8")

    with pytest.raises(ValueError, match="frontmatter"):
        parse_ticket(path)


def test_parse_ticket_missing_sections_default_to_empty(tmp_path):
    path = tmp_path / "sparse.md"
    path.write_text("---\nid: INC-1\ndate: 2025-01-01\ndevice: X\ntags: []\n---\n", encoding="utf-8")

    ticket = parse_ticket(path)

    assert ticket.symptoms == ""
    assert ticket.diagnostics == ""
    assert ticket.root_cause == ""
    assert ticket.resolution == ""


def test_nlp_text_combines_symptoms_and_diagnostics(tmp_path):
    path = tmp_path / "t.md"
    path.write_text(TICKET_TEXT, encoding="utf-8")
    ticket = parse_ticket(path)

    assert "BGP session flapping" in ticket.nlp_text
    assert "checked show bgp neighbors" in ticket.nlp_text
    # nlp_text must not include root cause / resolution — those aren't
    # symptom-signature signal, they're what we're trying to predict.
    assert "malformed route-map" not in ticket.nlp_text.lower()


def test_load_tickets_raises_on_empty_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_tickets(tmp_path)


def test_load_tickets_reads_all_md_files_sorted(tmp_path):
    (tmp_path / "2024-03-01-b.md").write_text(TICKET_TEXT, encoding="utf-8")
    (tmp_path / "2024-01-01-a.md").write_text(TICKET_TEXT, encoding="utf-8")

    tickets = load_tickets(tmp_path)

    assert len(tickets) == 2
    assert [t.source_path.name for t in tickets] == ["2024-01-01-a.md", "2024-03-01-b.md"]


def test_load_tickets_against_sample_data(sample_tickets_dir):
    tickets = load_tickets(sample_tickets_dir)
    assert len(tickets) == 7
    assert all(t.id.startswith("INC-") for t in tickets)

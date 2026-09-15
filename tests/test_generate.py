from lrg.generate import (
    MANUAL_NOTES_END,
    MANUAL_NOTES_START,
    Runbook,
    _cluster_slug_and_title,
    _dedupe_lines,
    build_runbook,
    extract_manual_notes,
    render_runbook_markdown,
    runbook_view,
    write_runbook,
)
from lrg.nlp import build_documents, vectorize


def test_dedupe_lines_removes_exact_duplicates_case_insensitive():
    blocks = ["- checked BGP neighbors\n- fixed it", "- Checked bgp neighbors\n- new step"]
    result = _dedupe_lines(blocks)
    assert result == ["checked BGP neighbors", "fixed it", "new step"]


def test_dedupe_lines_skips_blank_lines():
    result = _dedupe_lines(["- one\n\n- two\n   \n"])
    assert result == ["one", "two"]


def test_build_runbook_titles_from_top_tags(make_ticket):
    tickets = [
        make_ticket(id="INC-1", tags=["bgp", "cpu", "pe-router"]),
        make_ticket(id="INC-2", tags=["bgp", "cpu", "pe-router"]),
    ]
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)

    runbook = build_runbook(tickets, vectorizer, matrix, [0, 1])

    assert runbook.slug == "bgp-cpu-pe-router"
    assert runbook.title == "BGP + CPU + PE-Router"
    assert runbook.filename == "bgp-cpu-pe-router.md"


def test_cluster_slug_falls_back_to_incident_id_without_tags_or_terms(make_ticket):
    ticket = make_ticket(id="INC-42", tags=[])
    slug, title = _cluster_slug_and_title([ticket], signature_terms=[])
    assert "inc-42" in slug
    assert "INC-42" in title


def test_cluster_slug_prefers_signature_terms_over_ticket_id(make_ticket):
    ticket = make_ticket(id="INC-42", tags=[])
    slug, title = _cluster_slug_and_title([ticket], signature_terms=["route-map", "hold timer"])
    assert slug == "route-map-hold-timer"


def test_render_includes_placeholder_manual_notes_when_none_exist():
    runbook = Runbook(slug="x", title="X", signature_terms=[], tickets=[])
    md = render_runbook_markdown(runbook, existing_manual_notes="")
    assert MANUAL_NOTES_START in md
    assert MANUAL_NOTES_END in md
    assert "add engineer notes here" in md


def test_write_runbook_preserves_manual_notes_across_regeneration(tmp_path, make_ticket):
    ticket = make_ticket(id="INC-1", tags=["bgp"])
    docs = build_documents([ticket])
    vectorizer, matrix = vectorize(docs)
    runbook = build_runbook([ticket], vectorizer, matrix, [0])

    out_path = write_runbook(runbook, tmp_path)
    content = out_path.read_text(encoding="utf-8")
    content = content.replace(
        "\n(add engineer notes here)\n",
        "\nEscalate immediately if this recurs.\n",
    )
    out_path.write_text(content, encoding="utf-8")

    # Regenerate — same ticket, same runbook — the hand-written note must survive.
    runbook2 = build_runbook([ticket], vectorizer, matrix, [0])
    write_runbook(runbook2, tmp_path)

    final = out_path.read_text(encoding="utf-8")
    assert "Escalate immediately if this recurs." in final


def test_extract_manual_notes_returns_empty_for_missing_file(tmp_path):
    assert extract_manual_notes(tmp_path / "does-not-exist.md") == ""


def test_runbook_view_includes_ai_fields_default_none(make_ticket):
    ticket = make_ticket(id="INC-1")
    runbook = Runbook(slug="x", title="X", signature_terms=[], tickets=[ticket])

    view = runbook_view(runbook, existing_manual_notes="")

    assert view["ai_root_cause"] is None
    assert view["ai_root_cause_model"] is None
    assert view["incident_count"] == 1


def test_render_shows_ai_synthesis_and_keeps_raw_list(make_ticket):
    tickets = [
        make_ticket(id="INC-1", root_cause="cause A"),
        make_ticket(id="INC-2", root_cause="cause B"),
    ]
    runbook = Runbook(
        slug="x",
        title="X",
        signature_terms=[],
        tickets=tickets,
        ai_root_cause="Synthesized paragraph.",
        ai_root_cause_model="claude-opus-5",
    )

    md = render_runbook_markdown(runbook, existing_manual_notes="")

    assert "Synthesized paragraph." in md
    assert "claude-opus-5" in md
    assert "cause A" in md
    assert "cause B" in md
    assert "Raw root-cause reports per incident" in md

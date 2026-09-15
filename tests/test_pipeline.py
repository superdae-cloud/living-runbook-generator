from lrg.pipeline import run_pipeline


def test_run_pipeline_against_sample_data(tmp_path, sample_tickets_dir):
    result = run_pipeline(sample_tickets_dir, tmp_path, threshold=0.35)

    assert len(result.tickets) == 7
    assert len(result.runbooks) == 4

    cluster_sizes = sorted((len(c) for c in result.clusters), reverse=True)
    assert cluster_sizes == [3, 2, 1, 1]

    assert (tmp_path / "index.md").exists()
    for runbook in result.runbooks:
        assert (tmp_path / runbook.filename).exists()


def test_run_pipeline_no_llm_cache_file_when_synthesis_disabled(tmp_path, sample_tickets_dir):
    run_pipeline(sample_tickets_dir, tmp_path, threshold=0.35, synthesize_root_cause=False)
    assert not (tmp_path / ".llm_cache.json").exists()


def test_run_pipeline_preserves_manual_notes_across_reruns(tmp_path, sample_tickets_dir):
    result = run_pipeline(sample_tickets_dir, tmp_path, threshold=0.35)
    biggest = max(result.runbooks, key=lambda rb: len(rb.tickets))
    path = tmp_path / biggest.filename

    content = path.read_text(encoding="utf-8").replace(
        "\n(add engineer notes here)\n",
        "\nCall the on-call lead if this recurs.\n",
    )
    path.write_text(content, encoding="utf-8")

    run_pipeline(sample_tickets_dir, tmp_path, threshold=0.35)

    assert "Call the on-call lead if this recurs." in path.read_text(encoding="utf-8")


def test_run_pipeline_raises_on_empty_tickets_dir(tmp_path):
    empty_tickets = tmp_path / "tickets"
    empty_tickets.mkdir()
    runbooks_dir = tmp_path / "runbooks"

    import pytest

    with pytest.raises(FileNotFoundError):
        run_pipeline(empty_tickets, runbooks_dir)

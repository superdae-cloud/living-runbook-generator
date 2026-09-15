import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

import pytest

from lrg.ingest import Ticket


@pytest.fixture
def make_ticket(tmp_path):
    """Builds a Ticket with sensible defaults, overridable per test, and a
    real (if empty) source_path so code that reads t.source_path.name works."""

    def _make(
        id="INC-0001",
        date="2024-01-01",
        device="PE1-TEST",
        tags=None,
        symptoms="Something broke.",
        diagnostics="- checked the thing",
        root_cause="A thing was misconfigured.",
        resolution="- fixed the thing",
    ):
        path = tmp_path / f"{id.lower()}.md"
        path.touch()
        return Ticket(
            id=id,
            date=date,
            device=device,
            tags=tags if tags is not None else [],
            symptoms=symptoms,
            diagnostics=diagnostics,
            root_cause=root_cause,
            resolution=resolution,
            source_path=path,
        )

    return _make


@pytest.fixture
def sample_tickets_dir():
    return REPO_ROOT / "tickets"

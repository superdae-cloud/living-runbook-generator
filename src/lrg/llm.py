"""
llm.py — optional LLM-assisted root-cause synthesis.

WHY: cluster.py groups tickets by symptom signature, but each ticket's Root
Cause field is still whatever that ticket's author wrote — near-duplicate
phrasings of the same underlying defect. generate.py already lists these
verbatim, ranked by frequency. This module adds an optional extra step:
ask Claude to read every incident's diagnostics + root cause in a cluster
and write ONE concise statement, the way a senior engineer would summarize
"we've seen this five times, here's what's actually going on" instead of
making the reader parse five slightly different descriptions of the same
route-map bug.

THIS IS OPT-IN AND FAILS SOFT. No credentials configured, the `anthropic`
package missing, a network error, a rate limit — any of it — and
synthesize_root_cause() returns None. Callers fall back to the verbatim
per-incident list that already existed before this module. A "nice to
have" AI feature must never be able to break the core pipeline.
"""

from __future__ import annotations

import os
from pathlib import Path

from .ingest import Ticket

DEFAULT_MODEL = os.environ.get("LRG_LLM_MODEL", "claude-opus-5")

_SYSTEM_PROMPT = (
    "You are helping a NOC (network operations center) turn incident history "
    "into a troubleshooting runbook. You will be shown the diagnostics and "
    "root-cause notes from several past incidents that already share the "
    "same symptom signature (they were clustered by a separate similarity "
    "step, not by you). Write ONE concise paragraph (2-4 sentences) stating "
    "the underlying root cause these incidents share, in the voice of a "
    "senior engineer briefing the team. Call out operationally relevant "
    "variation between incidents (e.g. different devices, different config "
    "file) if present. Do not invent details that aren't in the source "
    "material. Output only the paragraph — no preamble, no headers, no "
    "markdown formatting."
)


def has_credentials() -> bool:
    """
    Best-effort check for whether an Anthropic API call would even have
    credentials to try — lets callers (the API's /status endpoint, the
    CLI's --verbose output) report "AI synthesis unavailable" up front
    instead of only discovering it after a failed call.
    """
    if os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return True
    profile_dir = Path.home() / ".config" / "anthropic"
    return profile_dir.exists() and any(profile_dir.iterdir())


def _build_prompt(tickets: list[Ticket]) -> str:
    blocks = []
    for t in tickets:
        blocks.append(
            f"Incident {t.id} ({t.date}, {t.device or 'device n/a'}):\n"
            f"Diagnostics: {t.diagnostics or '(none recorded)'}\n"
            f"Root cause: {t.root_cause or '(none recorded)'}"
        )
    return "\n\n".join(blocks)


def synthesize_root_cause(tickets: list[Ticket], model: str = DEFAULT_MODEL) -> str | None:
    """
    Returns a single synthesized root-cause paragraph, or None if synthesis
    isn't available or didn't succeed for any reason — callers should treat
    None as "fall back to the verbatim per-incident list", not as an error
    to surface.
    """
    if len(tickets) < 2:
        return None  # nothing to synthesize from a single incident's own words

    if not has_credentials():
        return None

    try:
        import anthropic
    except ImportError:
        return None

    try:
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(tickets)}],
        )
    except Exception:
        # Deliberately broad: auth errors, rate limits, network errors, or
        # any other SDK exception should all just mean "no synthesis this
        # run", never a pipeline crash.
        return None

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    return text or None

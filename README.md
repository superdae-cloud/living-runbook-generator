# Living Runbook Generator

An NLP layer that reads through a NOC's past incident tickets and
postmortems and auto-builds troubleshooting runbooks keyed to symptom
signatures (e.g. "BGP flap + high CPU on PE routers") — and keeps
updating those runbooks as new incidents come in, instead of going
stale like a wiki page nobody remembers to edit.

This is a working, runnable prototype built with synthetic sample
tickets. It's designed to teach you the whole pipeline end to end so
you can explain (and extend) every piece of it, then swap in real
ticket data later.

## Quick start

```bash
cd living-runbook-generator
pip install -r requirements.txt   # scikit-learn, PyYAML, numpy — that's it
python3 generate_runbooks.py --verbose
```

Open `runbooks/index.md` — you'll see four auto-generated runbooks built
from six sample incidents, ranked by how often each pattern has occurred.

## How it works — the pipeline

```
tickets/*.md  →  ingest.py  →  nlp.py  →  cluster.py  →  generate.py  →  runbooks/*.md
 (raw text)      (structured)  (vectors)   (groups)      (rendered)
```

**1. `ingest.py` — parse raw tickets into structured data.**
Each ticket file is YAML frontmatter (`id`, `date`, `device`, `tags`)
plus Markdown sections (`## Symptoms`, `## Diagnostics`, `## Root Cause`,
`## Resolution`). Parsing this up front means every later stage works
with named fields instead of guessing at raw prose.

**2. `nlp.py` — turn each ticket into a vector.**
This uses **TF-IDF** (Term Frequency–Inverse Document Frequency), not
embeddings. That's a deliberate choice, not a shortcut — see
"Why TF-IDF instead of embeddings?" below. Tags get repeated 3x in the
text fed to the vectorizer, because a human-assigned tag is a stronger
signal than a word the pipeline extracted automatically.

**3. `cluster.py` — group tickets that represent the same recurring problem.**
Any two tickets whose cosine similarity clears a threshold (default
`0.35`) get linked into the same cluster, and links chain transitively
(Union-Find / single-linkage clustering). This means you never have to
tell it how many distinct symptom signatures exist — that number grows
on its own as new *kinds* of incidents show up.

**4. `generate.py` — render (and re-render) a runbook per cluster.**
For each cluster it extracts the top shared TF-IDF terms (the "symptom
signature"), merges diagnostic/resolution steps, ranks root causes by
frequency, and writes a Markdown file. Every run **regenerates every
runbook from scratch** — that's what makes it "living" instead of static.

## The "living" part — how updates work without losing human edits

Every runbook file has a marked section:

```markdown
<!-- MANUAL NOTES START -->
(engineer notes go here)
<!-- MANUAL NOTES END -->
```

Before overwriting a runbook, the generator reads whatever's currently
between those markers and splices it back in after regenerating. So an
engineer can write "escalate immediately if this hits a 3rd device" once,
and it survives forever — while the frequency count, device list, and
incident list above it keep updating automatically.

**Try it yourself:** open `runbooks/bgp-cpu-pe-router.md`, notice the
manual note already there (added while building this), then look at
`tickets/2024-11-06-inc-1067.md` — a third incident on a third PE router.
Run `python3 generate_runbooks.py --verbose` again and diff the runbook:
the frequency count, device list, and date range update, and the note
is untouched. Drop in a new ticket file at any time and re-run to see
it happen live.

## Ticket file format

```markdown
---
id: INC-1099
date: 2024-12-01
device: PE5-SEA
tags: [bgp, cpu, pe-router]
---

## Symptoms
Free text describing what was observed.

## Diagnostics
- Bullet points of commands run and what they showed

## Root Cause
Free text — one sentence is fine.

## Resolution
- Bullet points of what fixed it
```

`tags` matter most for clustering quality — they're the single biggest
lever if two incidents that *should* cluster together aren't.

## Tuning the clustering threshold

```bash
python3 generate_runbooks.py --threshold 0.25 --verbose   # looser — bigger, noisier clusters
python3 generate_runbooks.py --threshold 0.5  --verbose   # stricter — smaller, cleaner clusters
```

There's no universally correct value — this is a normal, expected part
of building an NLP pipeline, not a sign of a bug. Start around
`0.3`–`0.4` and adjust after reading the actual output against tickets
you know the answer for.

## Why TF-IDF instead of embeddings?

Most similarity-search tutorials reach straight for sentence embeddings
(sentence-transformers, OpenAI/Claude embeddings, etc.). Those shine
when the same idea gets phrased many different ways in natural language.
NOC tickets are the opposite case: engineers repeat precise technical
vocabulary — "BGP", "hold timer", "CRC", "route-map" — because that's
how the domain communicates. TF-IDF rewards two tickets sharing rare,
specific terms and downweights generic filler words, which is exactly
the signal symptom-signature matching needs, with zero extra
dependencies and no model to download.

## Leveling this up

Once this pipeline feels familiar, here's the natural progression:

1. **Semantic embeddings.** Swap `nlp.vectorize()` for a
   `sentence-transformers` call (e.g. `all-MiniLM-L6-v2`). Nothing else
   changes — `cluster.py` and `generate.py` only care that similar rows
   in the matrix mean similar incidents. Worth it once free-text
   descriptions get less consistent (different engineers, less
   disciplined ticket templates).
2. **Real ticket sources.** Write a new module next to `ingest.py`
   (e.g. `ingest_csv.py` or `ingest_servicenow.py`) that produces the
   same `Ticket` objects from a CSV export or a ticketing-system API.
   Everything downstream is unchanged — this is the payoff of having a
   structured `Ticket` type in the middle of the pipeline.
3. **Scheduling.** Once tickets flow in automatically, replace "run the
   script by hand" with a cron job (`crontab -e`, run nightly) or a
   webhook that fires `generate_runbooks.py` when a ticket closes.
4. **LLM-assisted root-cause synthesis.** Right now root causes are
   listed verbatim, ranked by frequency. A next step is asking an LLM
   to synthesize a single best-guess root-cause statement from the
   cluster's raw text instead of listing each ticket's version
   separately — useful once clusters get large enough that a raw list
   becomes unwieldy.
5. **Vector database.** If the ticket corpus grows into the tens of
   thousands, an in-memory cosine-similarity matrix stops scaling.
   That's when a vector DB (Chroma, FAISS) earns its complexity.

## Project layout

```
living-runbook-generator/
├── generate_runbooks.py     # entry point — run this
├── requirements.txt
├── tickets/                 # sample synthetic NOC tickets (input)
├── runbooks/                # auto-generated output (index.md + one file per signature)
└── src/lrg/
    ├── ingest.py            # parse ticket files
    ├── nlp.py                # TF-IDF vectorization
    ├── cluster.py            # similarity-based grouping
    └── generate.py           # runbook rendering + manual-notes preservation
```

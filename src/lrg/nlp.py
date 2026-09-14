"""
nlp.py — turns tickets into vectors so a computer can judge "how similar
is this incident to that one?"

WHY TF-IDF INSTEAD OF SOMETHING FANCIER: you'll see plenty of NLP tutorials
reach straight for embeddings (sentence-transformers, OpenAI embeddings,
etc.) for similarity tasks. Those are great for natural language that
uses varied phrasing to mean the same thing ("the car wouldn't start" vs.
"vehicle failed to turn over"). NOC tickets are the opposite: engineers
use precise, repeated technical vocabulary — "BGP", "hold timer",
"CRC errors", "route-map" — because that's how the domain works. TF-IDF
(Term Frequency–Inverse Document Frequency) rewards exact shared
terminology and downweights generic words, which is exactly the signal
you want when clustering by symptom signature.

TF-IDF, in one sentence: every ticket becomes a vector where each number
says "how much does this specific technical term matter for THIS ticket,
relative to how common it is across ALL tickets." Two tickets that share
rare, specific terms (like "route-map" or "hold timer expired") end up
with vectors that point in a similar direction — that's what cosine
similarity (in cluster.py) measures.

This module also deliberately weights the `tags` field more heavily than
free text — tags are the engineer's own hand-labeled signal, so we trust
them more than words we extracted automatically.

LEVEL-UP LATER: once you outgrow this, swap `vectorize()` for a
sentence-transformers embedding call. The rest of the pipeline
(cluster.py, generate.py) doesn't care how the vectors were made — it
just needs a matrix where similar rows mean similar incidents. See the
README for notes on making that swap.
"""

from __future__ import annotations

from sklearn.feature_extraction.text import TfidfVectorizer

from .ingest import Ticket

TAG_WEIGHT = 3  # how many times to repeat tag words relative to free text


def build_documents(tickets: list[Ticket]) -> list[str]:
    """Build one text 'document' per ticket for the vectorizer to consume."""
    docs = []
    for t in tickets:
        tag_text = (" ".join(t.tags) + " ") * TAG_WEIGHT
        docs.append(f"{tag_text}{t.nlp_text}")
    return docs


def vectorize(docs: list[str]):
    """
    Returns (vectorizer, matrix). `matrix` is a sparse (n_tickets x
    n_terms) TF-IDF matrix — row i is ticket i's vector.
    """
    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2),  # captures two-word technical phrases like "hold timer"
        min_df=1,
    )
    matrix = vectorizer.fit_transform(docs)
    return vectorizer, matrix


def top_terms_for_rows(vectorizer: TfidfVectorizer, matrix, row_indices: list[int], n: int = 6) -> list[str]:
    """
    Given a cluster's row indices, return the top-N TF-IDF terms averaged
    across those rows. This becomes the human-readable "symptom
    signature" for a runbook.
    """
    import numpy as np

    sub = matrix[row_indices]
    mean_scores = np.asarray(sub.mean(axis=0)).ravel()
    terms = vectorizer.get_feature_names_out()
    top_idx = mean_scores.argsort()[::-1]

    results = []
    for idx in top_idx:
        term = terms[idx]
        if mean_scores[idx] <= 0:
            break
        # skip single generic-looking numeric/short tokens
        if len(term) < 3:
            continue
        results.append(term)
        if len(results) >= n:
            break
    return results

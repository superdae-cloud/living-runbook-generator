"""
cluster.py — groups tickets into "this is the same recurring problem"
buckets, without needing to know in advance how many distinct problems
exist in your ticket history.

WHY NOT K-MEANS: the classic clustering algorithms most tutorials teach
first (k-means, for example) require you to say up front how many
clusters you want. That's backwards for this problem — you don't know
how many distinct symptom signatures are hiding in a NOC's ticket
history, and that number grows every time a new *kind* of incident
happens. Instead we use a threshold-based approach: any two tickets
whose similarity clears a threshold get linked into the same group, and
groups merge transitively (if A links to B, and B links to C, then A,
B, and C are all one cluster even if A and C never appear "similar"
directly). This is effectively single-linkage clustering, implemented
with a Union-Find (disjoint-set) structure — a classic CS building
block worth knowing on its own.

TUNING THE THRESHOLD: `threshold` is the one knob you'll want to
experiment with.
  - Too low → unrelated incidents get lumped into one noisy runbook.
  - Too high → near-duplicate incidents (same root cause, different
    hostname) get split into separate runbooks instead of reinforcing
    one strong pattern.
Start around 0.3–0.4 for TF-IDF cosine similarity and adjust after
looking at real output — this is normal, expected NLP-pipeline tuning,
not a sign something is broken.
"""

from __future__ import annotations

from sklearn.metrics.pairwise import cosine_similarity


class _UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, x: int) -> int:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, a: int, b: int) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[ra] = rb


def cluster_tickets(matrix, threshold: float = 0.35) -> list[list[int]]:
    """
    Returns a list of clusters, each a list of row indices into `matrix`
    (and therefore into the original `tickets` list, which must be in
    the same order used to build the matrix).
    """
    similarity = cosine_similarity(matrix)
    n = similarity.shape[0]
    uf = _UnionFind(n)

    for i in range(n):
        for j in range(i + 1, n):
            if similarity[i, j] >= threshold:
                uf.union(i, j)

    groups: dict[int, list[int]] = {}
    for i in range(n):
        root = uf.find(i)
        groups.setdefault(root, []).append(i)

    # Largest / most-established patterns first — these are the ones a
    # NOC engineer most wants to see at the top of a runbook index.
    return sorted(groups.values(), key=len, reverse=True)

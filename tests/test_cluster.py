import numpy as np

from lrg.cluster import cluster_tickets, compute_similarity


def test_compute_similarity_identical_docs_score_one():
    matrix = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0]])
    similarity = compute_similarity(matrix)
    assert similarity[0, 1] == 1.0
    assert similarity[0, 2] == 0.0


def test_cluster_tickets_groups_above_threshold():
    # 0-1 similar (0.9), 1-2 similar (0.9), 0-2 dissimilar (0.1) directly —
    # but transitive union-find should still merge all three into one group.
    similarity = np.array(
        [
            [1.0, 0.9, 0.1],
            [0.9, 1.0, 0.9],
            [0.1, 0.9, 1.0],
        ]
    )
    clusters = cluster_tickets(similarity, threshold=0.5)
    assert len(clusters) == 1
    assert sorted(clusters[0]) == [0, 1, 2]


def test_cluster_tickets_splits_below_threshold():
    similarity = np.array(
        [
            [1.0, 0.1],
            [0.1, 1.0],
        ]
    )
    clusters = cluster_tickets(similarity, threshold=0.5)
    assert len(clusters) == 2
    assert sorted(len(c) for c in clusters) == [1, 1]


def test_cluster_tickets_sorted_largest_first():
    similarity = np.array(
        [
            [1.0, 0.9, 0.9, 0.0],
            [0.9, 1.0, 0.9, 0.0],
            [0.9, 0.9, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    clusters = cluster_tickets(similarity, threshold=0.5)
    assert len(clusters) == 2
    assert len(clusters[0]) == 3
    assert len(clusters[1]) == 1


def test_cluster_tickets_threshold_is_inclusive():
    similarity = np.array([[1.0, 0.35], [0.35, 1.0]])
    clusters = cluster_tickets(similarity, threshold=0.35)
    assert len(clusters) == 1

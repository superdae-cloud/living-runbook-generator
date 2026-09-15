from lrg.nlp import build_documents, top_terms_for_rows, vectorize


def test_build_documents_repeats_tags_three_times(make_ticket):
    ticket = make_ticket(tags=["bgp", "cpu"], symptoms="something", diagnostics="")
    docs = build_documents([ticket])

    assert docs[0].count("bgp") == 3
    assert docs[0].count("cpu") == 3
    assert "something" in docs[0]


def test_build_documents_one_doc_per_ticket(make_ticket):
    tickets = [make_ticket(id=f"INC-{i}") for i in range(3)]
    docs = build_documents(tickets)
    assert len(docs) == 3


def test_vectorize_matrix_shape_matches_ticket_count(make_ticket):
    tickets = [make_ticket(id=f"INC-{i}", symptoms=f"symptom text {i}") for i in range(4)]
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)

    assert matrix.shape[0] == 4


def test_top_terms_for_rows_prefers_shared_vocabulary(make_ticket):
    tickets = [
        make_ticket(id="INC-1", tags=["bgp"], symptoms="bgp session flapping hold timer expired"),
        make_ticket(id="INC-2", tags=["bgp"], symptoms="bgp session flapping hold timer expired"),
        make_ticket(id="INC-3", tags=["ospf"], symptoms="ospf adjacency stuck in exstart"),
    ]
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)

    terms = top_terms_for_rows(vectorizer, matrix, [0, 1])

    assert "bgp" in terms
    assert "ospf" not in terms


def test_top_terms_for_rows_skips_short_tokens(make_ticket):
    tickets = [make_ticket(id="INC-1", symptoms="a bb ccc dddd")]
    docs = build_documents(tickets)
    vectorizer, matrix = vectorize(docs)

    terms = top_terms_for_rows(vectorizer, matrix, [0])

    assert all(len(t) >= 3 for t in terms)

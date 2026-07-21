"""Tests for the RAG retrieval layer."""
from __future__ import annotations

import pytest

pytest.importorskip("sklearn")

from chakravyuh.rag import get_retriever, reset_cache  # noqa: E402


@pytest.fixture(autouse=True)
def _reset():
    reset_cache()
    yield
    reset_cache()


def test_retrieval_ranks_relevant_documents_first():
    retriever = get_retriever()
    assert retriever is not None
    docs = retriever.retrieve("credential dumping domain controller", k=3)
    assert docs, "expected at least one retrieved document"
    assert docs[0].source.startswith("ATT&CK T1003") or "Credential" in docs[0].text
    assert all(docs[i].score >= docs[i + 1].score for i in range(len(docs) - 1))


def test_empty_query_returns_nothing():
    retriever = get_retriever()
    assert retriever.retrieve("") == []


def test_irrelevant_query_returns_low_or_no_results():
    retriever = get_retriever()
    docs = retriever.retrieve("unrelated topic xyzxyzxyz", k=3)
    assert all(d.score < 0.3 for d in docs)

"""TF-IDF retrieval over the ATT&CK/CVE/CERT-In-advisory knowledge corpus.

Sources the knowledge graph's flattened documents when Neo4j is
configured/reachable; falls back to the small offline ATT&CK lookup
otherwise (fewer documents, but retrieval still works with zero
infrastructure).
"""
from __future__ import annotations

from dataclasses import dataclass

from ..knowledge import attack as offline_attack
from ..knowledge.graph import get_graph


@dataclass
class RetrievedDoc:
    source: str
    text: str
    score: float


def _offline_documents() -> list[dict[str, str]]:
    return [
        {
            "source": f"ATT&CK {t.technique_id}",
            "text": f"{t.technique_id} {t.name} ({t.tactic}).",
        }
        for t in offline_attack.TECHNIQUES.values()
    ]


def _documents() -> list[dict[str, str]]:
    graph = get_graph()
    if graph is not None:
        docs = graph.all_documents()
        if docs:
            return docs
    return _offline_documents()


class Retriever:
    def __init__(self) -> None:
        self._vectorizer = None
        self._matrix = None
        self._docs: list[dict[str, str]] = []
        self._build()

    def _build(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        self._docs = _documents()
        texts = [d["text"] for d in self._docs]
        if not texts:
            return
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(texts)

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedDoc]:
        if self._vectorizer is None or not query.strip():
            return []
        from sklearn.metrics.pairwise import cosine_similarity

        q = self._vectorizer.transform([query])
        sims = cosine_similarity(q, self._matrix)[0]
        top = sims.argsort()[::-1][:k]
        return [
            RetrievedDoc(
                source=self._docs[i]["source"],
                text=self._docs[i]["text"],
                score=float(sims[i]),
            )
            for i in top
            if sims[i] > 0
        ]


_cached: Retriever | None = None


def get_retriever(refresh: bool = False) -> Retriever | None:
    """Return a cached Retriever, or None if scikit-learn is unavailable."""
    global _cached
    if _cached is not None and not refresh:
        return _cached
    try:
        import sklearn  # noqa: F401
    except ImportError:
        return None
    _cached = Retriever()
    return _cached


def reset_cache() -> None:
    global _cached
    _cached = None

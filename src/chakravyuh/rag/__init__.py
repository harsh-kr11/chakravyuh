"""Retrieval-augmented context for the analyst copilot.

Retrieval is local (TF-IDF, scikit-learn) and dependency-light by design.
The LLM in ``chakravyuh.agents.copilot`` only ever *generates* over documents
already retrieved here — it never performs retrieval itself, and it never
touches detection/interdiction/response decisions.
"""
from .retriever import RetrievedDoc, Retriever, get_retriever, reset_cache

__all__ = ["RetrievedDoc", "Retriever", "get_retriever", "reset_cache"]

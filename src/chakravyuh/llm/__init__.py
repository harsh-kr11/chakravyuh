"""Optional LLM interface (rationale only, never in the safety path)."""
from .base import LLMClient, NullLLM
from .providers import make_llm

__all__ = ["LLMClient", "NullLLM", "make_llm"]

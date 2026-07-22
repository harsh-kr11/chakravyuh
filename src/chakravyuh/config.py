"""Runtime configuration, loaded from environment variables.

All settings are optional and have safe defaults, so the system runs fully
offline with zero configuration. API keys are only needed if you opt into
the Analyst Copilot agent (see docs/PREREQUISITES.md). If a ``.env`` file is
present (git-ignored), it's loaded once here so you can drop keys there
instead of exporting them in your shell — Claude Code / any assistant never
needs to see the raw value that way.

``Settings`` itself just holds plain values (handy for direct construction in
tests, e.g. ``Settings(llm_provider="none")``). Always go through
``load_settings()`` to get the *current* environment — it re-reads
``os.environ`` on every call. (A dataclass field default like
``x: str = _get(...)`` would instead be evaluated once, at class-definition
time, and silently go stale — see the regression this caused in
``docs/PREREQUISITES.md``'s test notes.)
"""
from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - python-dotenv is a core dep, but
    pass              # degrade gracefully if it's ever missing.


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


@dataclass
class Settings:
    # --- LLM (all optional; default is deterministic, no-LLM mode) --------- #
    # none|anthropic|openai|gemini. The LLM is only ever used for read-only
    # analyst rationale (chakravyuh.agents.copilot) — never in the
    # detection/interdiction/response decision path.
    llm_provider: str = "none"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    gemini_api_key: str = ""
    # Empty = each provider picks its own sensible default model.
    llm_model: str = ""

    # --- detection / interdiction policy ---------------------------------- #
    anomaly_threshold: float = 0.5
    blast_radius_threshold: float = 5.0

    # --- api --------------------------------------------------------------- #
    api_host: str = "127.0.0.1"
    api_port: int = 8080

    # --- persistence --------------------------------------------------------#
    db_path: str = "data/chakravyuh.db"

    # --- knowledge graph (Neo4j; optional — falls back to an offline lookup) #
    neo4j_uri: str = ""
    neo4j_user: str = "neo4j"
    neo4j_password: str = ""

    # --- action connector (optional; default is a safe in-memory simulation) #
    connector: str = "none"    # none | webhook | slack
    webhook_url: str = ""
    slack_webhook_url: str = ""

    @property
    def llm_enabled(self) -> bool:
        return self.llm_provider.lower() != "none"

    @property
    def neo4j_enabled(self) -> bool:
        return bool(self.neo4j_uri)


def load_settings() -> Settings:
    """Read the current environment (including any loaded ``.env``) fresh."""
    return Settings(
        llm_provider=_get("CHAKRAVYUH_LLM_PROVIDER", "none"),
        anthropic_api_key=_get("ANTHROPIC_API_KEY"),
        openai_api_key=_get("OPENAI_API_KEY"),
        gemini_api_key=_get("GEMINI_API_KEY", _get("GOOGLE_API_KEY")),
        llm_model=_get("CHAKRAVYUH_LLM_MODEL", ""),
        anomaly_threshold=_get_float("CHAKRAVYUH_ANOMALY_THRESHOLD", 0.5),
        blast_radius_threshold=_get_float("CHAKRAVYUH_BLAST_RADIUS", 5.0),
        api_host=_get("CHAKRAVYUH_API_HOST", "127.0.0.1"),
        api_port=int(_get("CHAKRAVYUH_API_PORT", "8080")),
        db_path=_get("CHAKRAVYUH_DB_PATH", "data/chakravyuh.db"),
        neo4j_uri=_get("CHAKRAVYUH_NEO4J_URI", ""),
        neo4j_user=_get("CHAKRAVYUH_NEO4J_USER", "neo4j"),
        neo4j_password=_get("CHAKRAVYUH_NEO4J_PASSWORD", ""),
        connector=_get("CHAKRAVYUH_CONNECTOR", "none"),
        webhook_url=_get("CHAKRAVYUH_WEBHOOK_URL", ""),
        slack_webhook_url=_get("CHAKRAVYUH_SLACK_WEBHOOK_URL", ""),
    )

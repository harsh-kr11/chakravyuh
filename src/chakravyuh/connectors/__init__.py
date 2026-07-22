"""Connectors carry out already-decided containment actions on real systems.

Zero-config default: no connector configured, actions are simulated
in-memory (safe, and how the demo/tests run). Set ``CHAKRAVYUH_CONNECTOR``
to opt into a real one.
"""
from __future__ import annotations

from ..config import Settings
from .base import Connector, ConnectorResult
from .slack import SlackConnector
from .webhook import WebhookConnector

__all__ = [
    "Connector", "ConnectorResult", "WebhookConnector", "SlackConnector",
    "make_connector",
]


def make_connector(settings: Settings) -> Connector | None:
    kind = settings.connector.lower()
    if kind == "webhook" and settings.webhook_url:
        return WebhookConnector(settings.webhook_url)
    if kind == "slack" and settings.slack_webhook_url:
        return SlackConnector(settings.slack_webhook_url)
    return None

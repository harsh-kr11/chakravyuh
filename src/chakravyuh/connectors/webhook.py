"""Generic webhook connector — POSTs the action as JSON to a configured URL.

This is the safest possible first real connector to wire behind a real
human approval: it produces a genuine, verifiable external side effect
(an HTTP request actually happens) without requiring access to a real
firewall, identity provider, or industrial system. Point it at anything
that accepts a JSON POST — a logging endpoint, an internal ticketing
system, or (see ``slack.py``) Slack's incoming-webhook format.
"""
from __future__ import annotations

from ..schemas import ContainmentAction
from .base import Connector, ConnectorResult


class WebhookConnector(Connector):
    def __init__(self, url: str, timeout: float = 5.0) -> None:
        self.url = url
        self.timeout = timeout

    def _payload(self, action: ContainmentAction, incident_id: str) -> dict:
        return {
            "incident_id": incident_id,
            "action_type": action.action_type.value,
            "target": action.target,
            "rationale": action.rationale,
            "est_disruption": action.est_disruption,
        }

    def execute(
        self, action: ContainmentAction, *, incident_id: str
    ) -> ConnectorResult:
        import httpx

        try:
            resp = httpx.post(
                self.url, json=self._payload(action, incident_id),
                timeout=self.timeout,
            )
            if resp.status_code < 400:
                return ConnectorResult(ok=True, detail=f"HTTP {resp.status_code}")
            return ConnectorResult(
                ok=False, detail=f"HTTP {resp.status_code}: {resp.text[:200]}"
            )
        except Exception as exc:  # network error, timeout, bad URL, etc.
            return ConnectorResult(ok=False, detail=str(exc))

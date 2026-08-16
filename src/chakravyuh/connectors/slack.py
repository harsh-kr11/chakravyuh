"""Slack connector — posts a human-readable notification to a Slack
incoming webhook when an action is carried out.

This does not require the Slack SDK: a Slack "incoming webhook" is just a
URL that accepts ``{"text": "..."}`` as a JSON POST, which is exactly what
``WebhookConnector`` already does — this subclass only formats the message.
"""
from __future__ import annotations

from ..schemas import ContainmentAction, format_target
from .webhook import WebhookConnector


class SlackConnector(WebhookConnector):
    def _payload(self, action: ContainmentAction, incident_id: str) -> dict:
        target = format_target(action.target)
        text = (
            f":shield: *CHAKRAVYUH* executed `{action.action_type.value}` "
            f"on `{target}` for incident `{incident_id}`.\n"
            f"> {action.rationale}"
        )
        return {"text": text}

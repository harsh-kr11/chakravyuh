"""Tests for the connector interface and pending-approval / observe-only modes.

No network calls — WebhookConnector/SlackConnector are tested with a mocked
HTTP call, so CI doesn't need a real endpoint.
"""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from chakravyuh.agents import auto_approve, deny_all, pending_approval
from chakravyuh.agents.response import ResponseAgent
from chakravyuh.config import Settings
from chakravyuh.connectors import make_connector
from chakravyuh.connectors.slack import SlackConnector
from chakravyuh.connectors.webhook import WebhookConnector
from chakravyuh.schemas import ActionType, ContainmentAction


def _action(gated: bool) -> ContainmentAction:
    return ContainmentAction(
        action_type=ActionType.REVOKE_CREDENTIAL,
        target="engineer_cred",
        requires_human_gate=gated,
        rationale="test",
    )


def test_pending_gate_marks_result_pending_not_executed():
    agent = ResponseAgent(gate=pending_approval)
    result = agent.process([_action(gated=True)])[0]
    assert result.pending is True
    assert result.executed is False
    assert result.approved_by is None


def test_auto_approve_executes_immediately():
    agent = ResponseAgent(gate=auto_approve)
    result = agent.process([_action(gated=True)])[0]
    assert result.pending is False
    assert result.executed is True
    assert result.approved_by == "analyst:demo"


def test_deny_all_never_executes():
    agent = ResponseAgent(gate=deny_all)
    result = agent.process([_action(gated=True)])[0]
    assert result.pending is False
    assert result.executed is False


def test_ungated_action_ignores_gate_entirely():
    agent = ResponseAgent(gate=deny_all)  # would deny if gated -- but it's not
    result = agent.process([_action(gated=False)])[0]
    assert result.executed is True
    assert result.pending is False


def test_webhook_connector_success():
    fake_response = MagicMock(status_code=200, text="")
    with patch("httpx.post", return_value=fake_response) as mock_post:
        connector = WebhookConnector("https://example.invalid/hook")
        result = connector.execute(_action(gated=False), incident_id="INC-1")
    assert result.ok is True
    mock_post.assert_called_once()
    _, kwargs = mock_post.call_args
    assert kwargs["json"]["incident_id"] == "INC-1"
    assert kwargs["json"]["action_type"] == "revoke_credential"


def test_webhook_connector_http_failure():
    fake_response = MagicMock(status_code=500, text="boom")
    with patch("httpx.post", return_value=fake_response):
        connector = WebhookConnector("https://example.invalid/hook")
        result = connector.execute(_action(gated=False), incident_id="INC-1")
    assert result.ok is False
    assert "500" in result.detail


def test_webhook_connector_network_error_does_not_raise():
    with patch("httpx.post", side_effect=ConnectionError("refused")):
        connector = WebhookConnector("https://example.invalid/hook")
        result = connector.execute(_action(gated=False), incident_id="INC-1")
    assert result.ok is False
    assert "refused" in result.detail


def test_slack_connector_formats_message():
    fake_response = MagicMock(status_code=200, text="")
    with patch("httpx.post", return_value=fake_response) as mock_post:
        connector = SlackConnector("https://hooks.slack.com/services/xyz")
        connector.execute(_action(gated=False), incident_id="INC-1")
    _, kwargs = mock_post.call_args
    assert "revoke_credential" in kwargs["json"]["text"]
    assert "INC-1" in kwargs["json"]["text"]


def test_response_agent_uses_connector_when_configured():
    fake_response = MagicMock(status_code=200, text="")
    with patch("httpx.post", return_value=fake_response) as mock_post:
        connector = WebhookConnector("https://example.invalid/hook")
        agent = ResponseAgent(gate=auto_approve, connector=connector)
        result = agent.process([_action(gated=True)], incident_id="INC-9")[0]
    assert result.executed is True
    assert result.error is None
    mock_post.assert_called_once()


def test_make_connector_returns_none_by_default():
    assert make_connector(Settings()) is None


def test_make_connector_builds_webhook_when_configured():
    settings = Settings(connector="webhook", webhook_url="https://example.invalid")
    connector = make_connector(settings)
    assert isinstance(connector, WebhookConnector)


def test_make_connector_builds_slack_when_configured():
    settings = Settings(connector="slack", slack_webhook_url="https://example.invalid")
    connector = make_connector(settings)
    assert isinstance(connector, SlackConnector)

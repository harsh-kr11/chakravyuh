"""Connector interface — the write-side mirror of an ingestion translator.

A translator turns a company's real logs INTO chakravyuh (see
``docs/INTEGRATION.md``). A connector turns an already-decided
``ContainmentAction`` OUT to a real system — a firewall, an identity
provider, a chat tool for notification. CHAKRAVYUH never decides *which*
action to take via a connector; the interdiction engine already decided
that deterministically. A connector only ever carries out a decision it's
handed, and reports whether that succeeded.

Ship your own by implementing ``Connector`` and wiring it up the same way
``WebhookConnector``/``SlackConnector`` are wired in ``chakravyuh.config`` /
``make_connector``.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..schemas import ContainmentAction


@dataclass
class ConnectorResult:
    ok: bool
    detail: str = ""


class Connector(ABC):
    @abstractmethod
    def execute(
        self, action: ContainmentAction, *, incident_id: str
    ) -> ConnectorResult:
        """Carry out an already-approved action. Never called for actions
        that haven't been through the human-gate/approval flow."""

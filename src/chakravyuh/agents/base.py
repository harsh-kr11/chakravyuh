"""Base agent abstraction.

Agents are deliberately small, single-responsibility units. The orchestrator
wires them into a pipeline. Detection / interdiction / blast-radius logic is
deterministic (ML or graph algorithms) rather than LLM-driven, which is a
safety and reproducibility decision; the LLM (in production) is used only for
attribution reasoning and natural-language rationale generation.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class AgentConfig:
    anomaly_threshold: float = 0.5   # min score to raise an AnomalySignal
    ot_always_gate: bool = True      # OT actions always require a human
    blast_radius_threshold: float = 5.0  # gate actions above this disruption


class Agent:
    name: str = "agent"

    def __init__(self, config: AgentConfig | None = None) -> None:
        self.config = config or AgentConfig()

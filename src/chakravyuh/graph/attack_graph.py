"""Live attack-graph model.

A directed graph over assets. Edges represent a feasible attacker move
(lateral movement, exploit, credential use). Each edge carries two costs:

* ``exploit_cost``  -- attacker's cost/effort to traverse the edge. Lower =
  easier for the attacker. Used to compute the attacker's cheapest path to a
  crown jewel (``-log(prob)`` semantics if you prefer probabilities).
* ``cut_cost``      -- the *defender's* availability/operational disruption if
  this edge is blocked by a containment action. This is the capacity used by
  the interdiction min-cut.

Edges may be flagged ``protected=True`` (e.g. a hospital's power-dependency)
meaning they must never be cut; the interdiction solver gives them infinite
capacity so a minimum cut can never sever them.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from ..schemas import ActionType, Asset, ContainmentAction


@dataclass
class AttackGraph:
    g: nx.DiGraph = field(default_factory=nx.DiGraph)

    # -- construction ------------------------------------------------------- #
    def add_asset(self, asset: Asset) -> None:
        self.g.add_node(
            asset.asset_id,
            asset=asset,
            crown_jewel=asset.is_crown_jewel,
        )

    def add_edge(
        self,
        src: str,
        dst: str,
        *,
        exploit_cost: float = 1.0,
        cut_cost: float = 1.0,
        protected: bool = False,
        action_type: ActionType = ActionType.BLOCK_LINK,
    ) -> None:
        self.g.add_edge(
            src,
            dst,
            exploit_cost=float(exploit_cost),
            cut_cost=float(cut_cost),
            protected=protected,
            action_type=action_type,
        )

    # -- queries ------------------------------------------------------------ #
    def crown_jewels(self) -> list[str]:
        return [n for n, d in self.g.nodes(data=True) if d.get("crown_jewel")]

    def asset(self, node: str) -> Asset:
        try:
            return self.g.nodes[node]["asset"]
        except KeyError as exc:
            raise KeyError(f"unknown asset {node!r}") from exc

    def attacker_min_cost(self, sources: list[str], target: str) -> float:
        """Cheapest attacker path-cost from any source to target (inf if none)."""
        best = float("inf")
        for s in sources:
            if s not in self.g or target not in self.g:
                continue
            try:
                c = nx.shortest_path_length(
                    self.g, s, target, weight="exploit_cost"
                )
                best = min(best, c)
            except nx.NetworkXNoPath:
                continue
        return best

    def edge_to_action(self, src: str, dst: str) -> ContainmentAction:
        """Map a graph edge onto the containment action that blocks it.

        Target semantics:
          * ISOLATE_HOST      -> the destination host being isolated
          * REVOKE_CREDENTIAL -> the source identity/credential being revoked
          * BLOCK_LINK        -> the (src, dst) edge

        Human-gating policy: an action is gated iff it acts on (or severs
        connectivity to) an OT asset. Revoking a purely-IT credential runs
        autonomously; cutting a link into an OT device is gated.
        """
        if not self.g.has_edge(src, dst):
            raise KeyError(f"unknown edge {src!r} -> {dst!r}")
        data = self.g.edges[src, dst]
        atype: ActionType = data.get("action_type", ActionType.BLOCK_LINK)

        if atype == ActionType.ISOLATE_HOST:
            target: str | tuple[str, str] = dst
            gate = self.asset(dst).is_ot
        elif atype == ActionType.REVOKE_CREDENTIAL:
            target = src
            gate = self.asset(src).is_ot
        else:  # BLOCK_LINK
            target = (src, dst)
            gate = self.asset(src).is_ot or self.asset(dst).is_ot

        return ContainmentAction(
            action_type=atype,
            target=target,
            reversible=True,
            est_disruption=float(data.get("cut_cost", 1.0)),
            requires_human_gate=gate,
            rationale=f"block attacker move {src} -> {dst}",
        )

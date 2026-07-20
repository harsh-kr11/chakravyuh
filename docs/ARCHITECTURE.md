# Architecture

CHAKRAVYUH is a deterministic multi-agent pipeline. Each agent is a small,
single-responsibility unit; the orchestrator wires them together and enforces
the audit fail-safe.

```
 TelemetryEvent[]                (from OpTC / HAI / CybORG / scenario)
      │
      ▼
 ┌─────────────┐   AnomalySignal[]
 │ Detection   │───────────────────────────┐
 │ (UEBA)      │  behavioural, no signatures│
 └─────────────┘                            ▼
 ┌─────────────┐   IncidentContext (techniques + attacker_frontier)
 │ Attribution │  MITRE ATT&CK (+ ICS), RAG-ready
 └─────────────┘
      │
      ▼
 ┌─────────────┐   CascadeAssessment (threatened crown jewels, dependent
 │ Cascade     │   loads at risk, cross-sector flag)
 └─────────────┘
      │
      ▼
 ┌─────────────┐   InterdictionPlan   ◀── THE NOVEL CORE
 │ Interdiction│   min-cost cross-sector cut, availability-aware,
 │             │   protected dependencies never severed
 └─────────────┘
      │
      ▼  (audit-before-execute)
 ┌─────────────┐   ExecutionResult[]  (OT & high-blast-radius = human-gated)
 │ Response    │   SOAR connectors / simulated adapter
 └─────────────┘
      │
      ├───────────────► Compliance: CERT-In 6-hour report (draft)
      └───────────────► Audit: hash-chained, tamper-evident, verify()
```

## Design decisions

**Deterministic core, LLM at the edges.** Detection, interdiction, blast-radius
scoring and audit are deterministic (ML models + graph algorithms + hashing).
The LLM (in production) is confined to attribution reasoning and natural-language
rationale, behind an interface. This keeps the safety-critical path reproducible
and testable, and avoids putting a stochastic model in charge of actuation.

**The tool/response layer is the only thing that touches the environment.** No
agent acts except by emitting a `ContainmentAction` the orchestrator has logged
and (if required) a human has approved. This single choke-point is what makes
the system auditable.

**Adapters isolate the environment.** Detection consumes `TelemetryEvent`s and
response emits actions through an adapter interface. Swap the scenario adapter
for `CybORGAdapter` (closed-loop), `ReplayAdapter` (OpTC/HAI replay), or a
stubbed `RealAdapter` (never wired live for research).

## The interdiction formulation (summary)

Build a flow network: a super-source → every attacker-frontier node (∞
capacity); sink = crown jewel; each real edge's capacity = its operational
`cut_cost`; protected cross-sector dependencies get ∞ capacity. The **minimum
s-t cut** is, by construction, the least-disruptive set of containment actions
that separates the attacker from the crown jewel while never severing a
protected dependency. Each cut edge maps to one `ContainmentAction`. See
`chakravyuh/graph/interdiction.py` and [`NOVELTY.md`](NOVELTY.md).

## Safety model

- OT and high-blast-radius actions are **human-gated** (`requires_human_gate`).
- The response agent's default gate on timeout is **deny** (fail safe).
- The audit fail-safe logs intent **before** execution and aborts unlogged
  actions.
- Irreversible/destructive tools are intentionally **absent** from the action
  set (no wipe/power-off) — containment is reversible by design.

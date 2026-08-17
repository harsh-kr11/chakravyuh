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
The LLM is a **read-only analyst copilot**: it explains an already-computed
incident using retrieved ATT&CK/CVE/CERT-In context. It never selects, approves,
or executes containment actions, and its output is never fed back into the
orchestrator. Attribution itself is a deterministic ATT&CK lookup (graph-first,
offline fallback) — not an LLM. This keeps the safety-critical path
reproducible and testable.

**The tool/response layer is the only thing that touches the environment.** No
agent acts except by emitting a `ContainmentAction` the orchestrator has logged
and (if required) a human has approved. This single choke-point is what makes
the system auditable.

**Adapters isolate the environment.** Detection consumes `TelemetryEvent`s and
response emits actions through an adapter interface. The shipped adapters are
`ScenarioAdapter` (bundled case library) and `ReplayAdapter` (bring-your-own
events on a bundled topology). `CybORGAdapter` (closed-loop) and a live
`RealAdapter` are **roadmap**, not shipped — see [`ROADMAP.md`](ROADMAP.md).

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

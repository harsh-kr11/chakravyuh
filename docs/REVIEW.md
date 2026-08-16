# Review notes for co-authors

Branch: `product-readiness` → PR against `main`. Do not push `main`.

This is what landed, why, and how to check it. Design record:
[`final-plan.md`](../final-plan.md). Case honesty: [`CASES.md`](CASES.md).

---

## What this is

The demo is now a **product surface**: five public-source cases run through
the same orchestrator, compared to the historical / naive decision, with
honest pending vs executed reporting.

We did **not** add live victim telemetry, a fake SOC feed, or autonomous OT.

---

## What changed (by area)

### Case library (new)

| File | Role |
|---|---|
| `src/chakravyuh/scenarios/catalog.py` | registry, `GET /scenarios` payload |
| `colonial.py` / `synnovis.py` | must-ship thesis cases |
| `ukraine2015.py` / `aiims.py` | same catalog shape; AIIMS admits encryption already happened |
| `redecho.py` | `META` + `historical()`; graph unchanged (keep 3.0 vs 108.0) |
| `dashboard/index.html` | case picker, idle one-liner + disclaimer, generic `service_load` map |

API: `GET /scenarios`, `GET /scenario?id=colonial`, analyze `{scenario}`.
CLI: `chakravyuh demo --scenario colonial` and `--hitl`
(`Orchestrator(gate=pending_approval)` — ungated still runs).

### Honesty / crash fixes (engine)

- Empty frontier and attacker-on-jewel → failed plan, not a 500, not “protected”.
- `_apply_actual_outcome`: `all([])` is not containment. Used on analyze,
  approve, **and** GET.
- CERT-In: proposed vs executed vs pending. Observe mode is **PROPOSED**,
  not HELD / DENIED. Sectors come from the graph.
- Store History uses `crown_jewel_protected_now` / `has_pending`. Deny is
  not green.
- Copilot: sanitize/truncate `history`; no key → `llm_used=false`.
- IsolationForest save/score, bad `CHAKRAVYUH_API_PORT`, Slack tuple
  targets, `isolated.add` only on success.

Greedy isolate-frontier is a **third** comparison column only when it costs
more than min-cut. The table works with min-cut vs naive alone.

### Packaging

- Docker: `pip install ".[api,detect]"`.
- CI: `pip install -e ".[dev,api]"` so FastAPI/HITL tests actually run.
- Compose default = API + dashboard. Neo4j is `docker compose --profile full`.
- `GET /readyz` reports detector, LLM, Neo4j, store.

### Docs

| Doc | For |
|---|---|
| `docs/CASES.md` | claim / do-not-claim per case |
| `docs/JUDGE_QA.md` | 10-minute Q&A, never-say |
| `docs/WALKTHROUGH.md` | projector script |
| `docs/ARCHITECTURE.md` | LLM is copilot only; CybORG is roadmap |
| `docs/HITL_AND_MODES.md` | CLI `--hitl` vs API pending |

`plan-grok.md` is a scratch audit and is **not** in this PR.

---

## What it is *not*

- Production auth (anyone who can reach `/approve` can approve).
- A customer-uploaded asset graph (picker of five bundled topologies).
- Decrypting AIIMS / keeping eHospital “fully up”.
- A replay of Mumbai 2020.
- LLM in the cut.

---

## How to review locally

```bash
pip install -e ".[dev,api]"
ruff check src tests
pytest
python -m chakravyuh.demo --scenario colonial
python -m chakravyuh.demo --scenario synnovis
python -m chakravyuh.demo --hitl
```

Dashboard: `chakravyuh serve` + `python -m http.server --directory dashboard 8081`.
Idle should show the picker and a disclaimer. Run Colonial in Observe + Act;
Approve should be locked while `has_pending`. Copilot without a key should
still return retrieved context.

LLM API key: **not required**. Do not commit `.env`.

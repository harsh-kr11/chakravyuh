# CHAKRAVYUH — final plan

Status: **the plan to implement**. Supersedes `plan-grok.md` and the Cursor plan `chakravyuh_product_readiness_c1028d71`.
Git: branch `product-readiness` → PR against `main`. Do not push `main`.

Decisions after the second review (this is what we are coding):

- **Triage:** `redecho` (already ships) + `colonial` + `synnovis` are must-ship. `ukraine2015` + `aiims` still ship in this PR (same catalog shape, slightly less polish) so the picker is complete — they are not blocked on extra graph art.
- **`all([])`:** one helper `_apply_actual_outcome`; call it from analyze, approve, **and** `GET /incidents/{id}`.
- **Greedy baseline:** implement if RedEcho greedy cost > 3.0; the comparison table is min-cut vs historical/naive either way. Greedy is a third column only when it is strictly worse.
- **`--hitl`:** CLI constructs `Orchestrator(gate=pending_approval)` and runs the same pipeline. It is **not** observe-only (observe executes nothing; HITL executes ungated actions and leaves OT pending).
- **Idle UI:** case picker visible on load, one-liner per case + disclaimer in the feed, “Run interdiction” as the call to action. Not a blank map.
- **Copilot:** sanitize/truncate `history` entries; copilot must return `llm_used=false` + retrieved context when no API key (venue default).
- **JUDGE_QA.md** is a real stand-up script, not a stub (SIEM vs containment, firewall vs availability-aware cut, real data, autonomous OT).

This is a **product** plan. The venue walkthrough is how we show the product.

Merged from two audits:

- **Grok:** runnable five-case library, false-containment / HITL honesty, command-centre as product UI
- **Other:** crash bugs (`get_model` save, port parse, Slack tuple, `isolated.add`, MTTD, `inf` print), Synnovis 2024, CLI comparison table

Dropped on purpose:

- “Our demo *replays* RedEcho” / Mumbai “timeline matches” — MITRE C0043 did not reach OT; Recorded Future called Mumbai unsubstantiated
- WannaCry as a runnable case — worm + kill-switch, not a min-cut
- Case studies as markdown-only — incidents go **into the engine**, not only into a PDF
- Oldsmar as a fifth graph — keep as Q&A (why OT is gated); Synnovis is the better protected-edge case

---

## 1. Product

CHAKRAVYUH answers the question operators currently answer with panic:

> Which smallest set of containment actions cuts the attacker off from the crown jewel **without** taking down the hospital, the pipeline, or the blood-result path that depends on that system?

Mechanism: minimum-cost s-t cut on a live attack graph. Capacity = operational disruption. Protected cross-sector dependencies = infinite capacity (never chosen). Detection, cut, HITL, connectors, CERT-In draft, hash-chained audit = the product. LLM copilot explains an already-computed incident; it never chooses the cut.

We do not invent min-cut. We ship incident-time, availability-aware, cross-sector, human-gated, auditable interdiction.

Live victim SIEM is not available and will not be faked. Proof is a **case library**: public-source reconstructions run through the real engine, compared to the historical decision.

Keeper quote: *“Colonial paid $4.4M in ransom. The real cost was shutting a pipeline that did not need to be shut. They could not model what to isolate. We can.”*

---

## 2. Five runnable cases (in the product)

Catalog + command-centre picker + `chakravyuh demo --scenario <id>`. Default walkthrough: `redecho`. Each module: `META`, `CROWN_JEWEL`, `build_graph()`, `telemetry_stream()`, `historical()`. `kind` is `reconstruction` except RedEcho (`synthetic_illustration`). Disclaimer and sources on the card. Never “live incident.”

### 2.1 `redecho` — Indian power pre-positioning (exists)

- MITRE campaign **C0043**, group **G1042**. Recorded Future: RLDCs / SLDCs, seaports, ShadowPad / AXIOMATICASYMPTOTE.
- Job: grid IT → OT SCADA; hospital power is protected.
- Keep **3.0 vs naive 108.0**, two actions, hospital uncut. Do not retune the graph.
- Honesty: C0043 did **not** reach OT. Mumbai Oct 2020 ↔ malware is **unsubstantiated**. Power Minister: human error. Say “inspired by C0043 pre-positioning,” never “we replayed the campaign” or “we would have stopped the blackout.”

### 2.2 `colonial` — May 2021 (the product thesis)

- DarkSide on **IT**. Legacy VPN, no MFA, one password. CISA AA21-131A: OT not known hit. CEO halted **5,500 miles** in ~15 minutes. Fuel shortages. Outage **was** the containment decision.
- Crown jewel: pipeline SCADA. Protected: East-Coast fuel delivery.
- Historical: halt OT. CHAKRAVYUH: revoke VPN + isolate alerting IT / block IT→OT. Fuel delivery uncut.
- Sources: CISA AA21-131A; Blount testimony; Mandiant/Bloomberg.

### 2.3 `ukraine2015` — December 2015

- MITRE **C0028**. BlackEnergy → creds → ICS VPN → HMI → breakers. ~225k customers, ~6h. KillDisk, TDoS, bricked converters. Operators drove to substations.
- Crown jewel: distribution HMI/SCADA. Protected: civilian / hospital load.
- Historical: attackers reached HMI; later, coarse SCADA isolation. CHAKRAVYUH: cut **upstream of HMI**, not the breaker circuit.
- Sources: MITRE C0028; SANS/E-ISAC; CISA IR-ALERT-H-16-056-01.

### 2.4 `aiims` — November 2022 (India hospital)

- CERT-In / Parliament: **five** eHospital servers, ~**1.3 TB**, improper segmentation, ~two weeks of paper. Registration back ~6 Dec.
- Crown jewel: eHospital. Protected: emergency / remaining clinical path.
- Historical: campus-scale blast because nothing was segmented. CHAKRAVYUH: isolate the five alerting hosts / infected VLAN, not the whole campus.
- Honesty on the card: those five hosts were **already encrypted**. This engine does not decrypt. The case is the isolation decision at first anomaly / given the segmentation finding.
- Sources: Rajya Sabha reply; Lok Sabha AU1837; Indian Express CERT-In reporting.

### 2.5 `synnovis` — June 2024 (cross-sector cascade)

- Qilin hit Synnovis (pathology / blood lab for London hospitals), not a hospital. Delayed bloods; King’s College confirmed a patient death with long wait for a blood test as a contributing factor. 10k+ appointments cancelled. $50M ransom demanded, not paid.
- Crown jewel: lab LIS / result-publish path. Protected: **ICU / ward blood-result pipeline** (infinite capacity).
- Historical: lab down → hospitals lose results (the dependency *is* the harm). CHAKRAVYUH: isolate the compromised lab-IT island; **never** cut the result path to the ICU.
- Sources: BBC; Reuters; King’s College Hospital trust statements.
- Keeper quote: *“A ransomware attack on a blood lab — not a hospital — contributed to a patient death through delayed results. That is a protected edge. Containment must never sever it.”*

**Q&A only (no graph this cycle):** WannaCry/NHS 2017 (collateral worm, kill-switch); Oldsmar 2021 (operator reversed a setpoint — why OT is human-gated).

Every case shows three numbers: CHAKRAVYUH cost, greedy isolate-alerting-hosts (only if strictly worse), historical/naive cost + whether it severs the protected load.

---

## 3. Product surface

Command centre is the product UI:

```
Case picker:  RedEcho | Colonial | Ukraine 2015 | AIIMS | Synnovis
Mode:         Observe only | Observe + Act
              Run → detect → attribute → cascade → cut
              Historical decision  vs  CHAKRAVYUH plan
              Approve (OT / high blast) → connector
              CERT-In draft · Audit chain · Copilot (read-only)
```

CLI: `chakravyuh demo --scenario colonial`. Default `demo` = RedEcho. `--hitl` = real pending (API already does this). Default CLI auto-approve is a narrated one-shot, not production.

CLI/UI comparison table (from the other plan — keep):

```
                       Min-cut                 Historical / naive
Actions                2                       halt OT / isolate jewel
Disruption             3.0                     108.0
Protected load kept    YES                     NO
```

Format tuple targets as `domain_controller -> ot_historian` in CLI, Slack, and the plan card.

---

## 4. Quality bar (engine cannot crash or lie)

Do these before the case library is worth showing.

### 4.1 Crashes (other plan — confirmed in code)

- [`ml/model.py`](src/chakravyuh/ml/model.py): wrap `train()` / `save()`; on disk failure keep in-memory model. Wrap `model.score()`; on exception fall back to `anomaly_score`.
- [`config.py`](src/chakravyuh/config.py): `_get_int` like `_get_float` so a bad `CHAKRAVYUH_API_PORT` does not kill startup.
- [`graph/interdiction.py`](src/chakravyuh/graph/interdiction.py) + orchestrator: if jewel is already in the frontier / cut is infinite, return a failed plan (“escalation required”), do not 500.
- [`cli.py`](src/chakravyuh/cli.py): `args.port if args.port is not None else settings.api_port` (`0` is valid).
- [`connectors/slack.py`](src/chakravyuh/connectors/slack.py): treat `list` and `tuple` as link targets.

### 4.2 Wrong answers (both plans)

- Empty frontier must **not** set `crown_jewel_protected=True` (today `cost_after` stays `inf`).
- API `_apply_actual_outcome`: `all([])` is True — require `len(executions) > 0` and every action executed for `*_now`. Same helper on analyze, approve, and GET.
- CERT-In draft: **proposed vs executed**. Pending OT cannot say “actions taken” / “protected: True.” Sectors from the graph, not hardcoded “Power (+ Health).”
- Copilot: do not assert the plan already executed; sanitize/truncate `history` (`.get`, max length) so a dashboard paste cannot prompt-inject; no-key path stays `llm_used=false`.
- History / [`store.py`](src/chakravyuh/store.py): persist `crown_jewel_protected_now` / `has_pending`. Deny must not stay green. Replace `assert lastrowid` (stripped under `-O`).
- MTTD: `None` when nothing detected, not `0`.
- Demo: guard `attacker_cost_before == inf` as `UNREACHABLE`. Verdict: do not require `cascade_averted` when there is no protected edge.
- [`response.py`](src/chakravyuh/agents/response.py): `isolated.add()` only after connector success.
- Approve endpoint: `.get()` on execution dicts so malformed rows are 400, not 500.
- Audit fail-safe: if `log()` fails, warn; do not silently skip the action with zero feedback.
- Attack graph: `asset()` / `edge_to_action()` raise a clear error, not a raw KeyError.

### 4.3 HITL honesty

API `respond` = real pending. CLI default = auto-approve. Document it. Add `demo --hitl`. No silent fully-autonomous OT on the API.

### 4.4 Algorithm honesty

RedEcho’s hospital edge is **downstream of the sink** — classical min-cut would not pick it anyway. Keep the 3 vs 108 hook. Add a unit-test graph (Colonial / Synnovis encode this in product) where the cheap path **is** protected so ∞ actually binds.

Greedy isolate-frontier baseline: implement; show only if strictly worse than min-cut on that case.

### 4.5 Packaging / CI / compose

- CI: `pip install -e ".[dev,api]"` so FastAPI/HITL tests actually run.
- Docker: `pip install ".[api,detect]"`.
- Compose: default = API + UI. Neo4j behind profile `full`. Do not block boot on Neo4j.
- `GET /readyz`: sklearn, LLM provider, Neo4j, store. Status line consumes it.
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md): LLM is copilot only, not attribution. `CybORGAdapter` is roadmap, not shipped.

### 4.6 Command centre

- Replay calls `init()` (reconnect), not only `reset()`.
- Lock **Run** while `has_pending`.
- Idle copy so the projector is not blank.
- Do not `display:none` the plan/Approve rail under 920px — stack instead.
- Use `escapeHtml()` on feed/plan (XSS).
- Generic map: `crown_jewel` + protected `service_load`, not a hardcoded `hospital` id.
- Soften Copilot when `/readyz` says LLM off.

---

## 5. Engineering

Reuse the orchestrator. Do not fork a second pipeline.

```
src/chakravyuh/scenarios/
  catalog.py
  redecho.py          # META only
  colonial.py
  ukraine2015.py
  aiims.py
  synnovis.py
```

`META`: `id`, `title`, `kind`, `sector`, `sources[]`, `disclaimer`.

API (analyze already has unused `scenario`):

- `GET /scenarios`
- `GET /scenario?id=colonial` → graph + events + historical + META
- `POST /incidents/analyze` `{ "scenario": "colonial", "mode": "respond" }`

Unknown id → 404.

Docs:

- `docs/CASES.md` — five cases, sources, claim / do-not-claim
- `docs/JUDGE_QA.md` — 10-minute stand-up
- `docs/WALKTHROUGH.md` — how to show the product in ten minutes

README: Case library section + fix any sentence the code makes false. No marketing rewrite.

Tests per case: protected edge never in the cut; cost < historical/naive; disclaimer on payload. Plus: empty frontier not protected; empty executions `*_now` false; pending CERT-In; deny history; on-path protected cut; `get_model` save failure does not crash.

---

## 6. What we say / never say

**Say**

- Solver is min-cut. Product is online + availability-as-capacity + protected deps + HITL + audit.
- RedEcho: C0043-inspired illustration, 3.0 vs 108.0, hospital uncut. Not a replay of Mumbai.
- Colonial: IT-only, they halted OT; finite cut keeps fuel moving.
- Ukraine 2015: MITRE C0028; stop before the HMI.
- Synnovis: lab → ICU blood results is a protected edge.
- Detection is IsolationForest. Attribution is ATT&CK lookup, not a second model.
- Default actuation is simulated. LLM never chooses the cut.

**Never say**

- We ingested victim telemetry / live CERT-In feed
- We prevented Mumbai 2020
- We would have kept eHospital fully up after encryption
- We invented attack-graph interdiction
- Fully autonomous OT
- Production SOC with auth (there is none)

**Money sentences**

1. “Incident-time min-cost s-t cut: capacity = operational `cut_cost`, protected deps = ∞.”
2. “RedEcho illustration: 2-action cut, **3.0 vs naive 108.0**, hospital load not severed.”
3. “Colonial reconstruction: they halted 5,500 miles of OT for an IT-only breach; the finite cut is revoke VPN + isolate IT.”
4. “Deterministic core; LLM never chooses the cut. OT is human-gated.”

---

## 7. Out of scope (this cycle)

- Live victim telemetry, fake SOC live-feeds
- OpTC / HAI / CybORG (~1TB)
- Production auth, live `RealAdapter` on OT
- Slack/webhook as actual firewall/AD (keep the connector interface)
- LangGraph rewrite, multi-crown-jewel solver
- Runnable WannaCry / Oldsmar graphs
- Committing API keys (venue `.env` only)

---

## 8. Order of work

1. Crash + lie fixes (4.1–4.4), tests.
2. Packaging: Docker `[detect]`, CI `[dev,api]`, compose without Neo4j, `/readyz`.
3. Command-centre reliability + generic map + comparison table + tuple formatting.
4. Scenario catalog + API/CLI/UI picker.
5. `colonial` + tests (show this second on stage).
6. `ukraine2015` + tests.
7. `aiims` + `synnovis` + tests (honest AIIMS card).
8. Greedy baseline if numbers are real.
9. `docs/CASES.md`, `JUDGE_QA.md`, `WALKTHROUGH.md`.
10. Full pytest + ruff. PR. Team reviews. **Do not merge to main from this agent.**

LLM key: not required to build. Copilot on a laptop: `GEMINI_API_KEY` in gitignored `.env` only.

---

## 9. Review checklist

- [ ] Five cases run in the catalog, each with sources and a disclaimer
- [ ] Colonial comparison card exists; no victim-telemetry claim
- [ ] Mumbai 2020 is not claimed as a prevented blackout
- [ ] AIIMS card admits encryption already happened
- [ ] Empty detection cannot print CONTAINED
- [ ] History / CERT-In match pending vs executed
- [ ] `get_model` save failure does not crash
- [ ] Case picker works without a hardcoded hospital node
- [ ] Copilot responds with retrieved context when no LLM key
- [ ] PR against main, not a push to main

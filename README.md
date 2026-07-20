<div align="center">

# चक्रव्यूह · CHAKRAVYUH

**Incident-time, cross-sector attack-path interdiction for critical national infrastructure.**

*When an attacker is already inside, don't just detect and alert — compute the **smallest** set of containment actions that provably cuts them off from the crown jewel, without taking the grid (or the hospital that depends on it) down.*

[![CI](https://github.com/your-org/chakravyuh/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/chakravyuh/actions)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)

</div>

---

## Why this exists

India's CERT-In handled **over 1.59 million cyber incidents in 2023**, climbing past **2 million in 2024**. Critical-infrastructure operators have been repeatedly probed and hit — power-sector pre-positioning by state-linked actors, and the **AIIMS Delhi ransomware** that took hospital systems down for days. Over **70% of government entities run end-of-life IT**.

Today's tools are good at *detecting* and *visualising* intrusions. What no one owns is the **decision at incident time**: given that an attacker is already moving laterally, *which minimal containment actions stop them from reaching the crown-jewel asset — while preserving the services other sectors depend on?* Isolating "everything that looks bad" can itself cause the outage you were trying to prevent (e.g. severing the grid segment a hospital draws from).

**CHAKRAVYUH** is a multi-agent platform for a national nodal SOC (think **NCIIPC / CERT-In**, with **CSIRT-Power / an SLDC** as the anchor pilot) that treats containment as a **minimum-cost cross-sector attack-path interdiction** problem and solves it live.

## The idea in one picture

```
 detection ──▶ attribution ──▶ cascade ──▶  INTERDICTION  ──▶ response ──▶ audit
 (UEBA, no    (MITRE ATT&CK) (cross-sector  (min-cost cut,   (SOAR +      (hash-
  signatures)                 impact)        availability-    human gate   chained,
                                             aware)           for OT)      CERT-In report)
```

The **interdiction** step is the novel core: we build a live attack graph, then compute the **minimum-cost cut** separating the attacker's frontier from the crown jewel, where each edge's cut cost is its **operational-disruption**, and any **protected cross-sector dependency** (a hospital's power draw) is given infinite capacity so it can **never** be severed. The result is the *least-disruptive* action set that contains the attack **and** averts the cascade — with every action logged to a tamper-evident audit trail and an auto-drafted CERT-In 6-hour report.

> **Novelty, honestly stated.** We don't claim to invent attack-graph interdiction. Classic interdiction is *offline hardening*; online intrusion-response work selects RL/POMDP policies on a *single* IT network; cross-sector cascade games model *physical* attacks. CHAKRAVYUH's contribution is doing all three at once: a **live-telemetry-driven, availability-aware, cross-sector interdiction cut** at incident time. See [`docs/NOVELTY.md`](docs/NOVELTY.md).

## Quickstart

```bash
git clone https://github.com/your-org/chakravyuh
cd chakravyuh
pip install -e ".[dev]"

# 1) Narrated cross-sector demo (RedEcho-style scenario) — zero config
python -m chakravyuh.demo

# 2) Full test-suite
pytest

# 3) REST API  (pip install -e ".[api]")
chakravyuh serve            # -> http://127.0.0.1:8080/docs
curl -s -X POST localhost:8080/incidents/analyze \
     -H 'content-type: application/json' -d '{"incident_id":"INC-1"}'

# 4) Command-centre dashboard (self-contained; just open it)
python -m http.server --directory dashboard 8081   # -> http://localhost:8081

# 5) Everything in containers
docker compose up --build   # API :8080  +  dashboard :8081
```

You should see the pipeline detect a low-and-slow intrusion, attribute it to ATT&CK techniques, flag the cross-sector cascade risk, compute a **2-action minimal cut** that blocks the attacker while preserving the hospital load (disruption **3.0 vs a naive baseline's 108.0**), execute it with OT actions human-gated, and verify the audit chain. The dashboard renders the network as the *chakravyuh* formation — concentric defensive rings with the crown jewel at the centre — and animates the breach, the predicted cross-sector cascade, and the interdiction that seals it.

**Zero config, zero keys, fully offline.** No API keys or datasets are needed for the demo, API, or dashboard. See [`docs/PREREQUISITES.md`](docs/PREREQUISITES.md) for optional LLM rationale and real-dataset evaluation.

## What's in the box

| Component | Module | Status |
|---|---|---|
| Domain schemas (typed contracts) | `chakravyuh.schemas` | ✅ stable |
| Attack graph model | `chakravyuh.graph.attack_graph` | ✅ |
| **Interdiction engine (min-cost cross-sector cut)** | `chakravyuh.graph.interdiction` | ✅ **the wedge** |
| Detection agent (UEBA, pluggable model) | `chakravyuh.agents.detection` | ✅ reference / 🔌 pluggable |
| Attribution agent (ATT&CK) | `chakravyuh.agents.attribution` | ✅ reference / 🔌 RAG-ready |
| Cascade agent (cross-sector impact) | `chakravyuh.agents.cascade` | ✅ |
| Interdiction agent | `chakravyuh.agents.interdiction_agent` | ✅ |
| Response / SOAR agent (human-gated) | `chakravyuh.agents.response` | ✅ |
| Compliance agent (CERT-In report) | `chakravyuh.agents.compliance` | ✅ |
| Audit agent (hash-chained) | `chakravyuh.agents.audit` | ✅ |
| Orchestrator (pipeline + fail-safe) | `chakravyuh.orchestrator` | ✅ |
| Infrastructure adapter interface + replay | `chakravyuh.adapters` | ✅ (replay) / 🔌 dataset & real stubs |
| REST API (FastAPI) | `chakravyuh.api` | ✅ |
| CLI (`demo` / `analyze` / `serve`) | `chakravyuh.cli` | ✅ |
| Optional LLM rationale (never in safety path) | `chakravyuh.llm` | ✅ interface / 🔌 keys optional |
| Command-centre dashboard (chakravyuh map) | `dashboard/` | ✅ |
| OpTC / HAI / CybORG dataset wiring | `chakravyuh.adapters` | 🛣️ roadmap |

## How it maps to the hackathon brief (Topic 7)

- **Behavioural anomaly detection, no signatures** → `DetectionAgent` (pluggable unsupervised model).
- **Correlate weak signals across IT *and* OT** → cross-sector attack graph + `CascadeAgent`.
- **Map attack progression to MITRE ATT&CK** → `AttributionAgent` (+ ATT&CK-for-ICS).
- **Orchestrate containment** → `InterdictionAgent` + `ResponseAgent` (with human gates).
- **Compress weeks → hours** → MTTD/MTTR proxies in the pipeline result.
- **Full auditability** → `AuditAgent` hash chain + `verify()`.

Full mapping incl. datasets and evaluation metrics: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md), [`docs/DATASETS.md`](docs/DATASETS.md), [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Roadmap

See [`docs/ROADMAP.md`](docs/ROADMAP.md). Near-term: real detectors on DARPA OpTC (IT) and HAI/SWaT (OT), a CybORG/CAGE live-attack adapter, a Neo4j ATT&CK knowledge graph + RAG over CVE/CERT-In advisories, and the command-centre dashboard.

## Research & IP

This project is designed as **one build with three payoffs** — a working system, a research paper (novel online cross-sector interdiction formulation + benchmark), and a patent-eligible mechanism. If you use it academically, please cite it — see [`CITATION.cff`](CITATION.cff). Prior-art positioning and the exact delta are documented in [`docs/NOVELTY.md`](docs/NOVELTY.md).

> ⚠️ **Safety & scope.** Autonomous actuation on OT is dangerous. CHAKRAVYUH **human-gates** all OT and high-blast-radius actions by design. The shipped scenario is a **synthetic simulation**; the RedEcho→Mumbai-outage link is explicitly unsubstantiated and is *not* claimed here. Do not connect the `RealAdapter` to production without a qualified OT-safety review.

## License

Apache-2.0. See [`LICENSE`](LICENSE). Contributions welcome — see [`CONTRIBUTING.md`](CONTRIBUTING.md).

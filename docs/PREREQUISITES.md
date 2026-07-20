# Prerequisites & Setup

This document covers everything needed to run CHAKRAVYUH — from the zero-config
offline demo to the full production-shaped deployment with datasets and LLM
rationale.

> **TL;DR — the core needs nothing but Python.** No API keys, no datasets, no
> GPU. Keys and data are only for optional capabilities, all clearly marked
> below.

---

## 1. System prerequisites

| Requirement | Minimum | Notes |
|---|---|---|
| Python | 3.10+ | 3.12 recommended |
| OS | Linux / macOS / Windows | pure-Python core, portable |
| RAM | 1 GB | for the demo/API; more only for real datasets |
| Disk | ~200 MB | code + deps; datasets are separate & large |
| GPU | none | not required (add one only for heavy detectors) |
| Docker | optional | for the containerised API + dashboard |
| Node.js | not required | dashboard is a single static HTML file |

## 2. Install tiers

Each tier is additive. Pick the smallest that covers what you need.

```bash
# Tier 0 — core (offline demo, pipeline, interdiction, tests)
pip install -e .

# Tier 1 — REST API + dashboard backend
pip install -e ".[api]"

# Tier 2 — real ML detectors (scikit-learn / scipy)
pip install -e ".[detect]"

# Tier 3 — optional LLM rationale
pip install -e ".[llm]"

# Everything (dev included)
pip install -e ".[all]"
```

## 3. Run surfaces

```bash
# Narrated CLI demo (Tier 0)
python -m chakravyuh.demo
chakravyuh demo

# Analyse and export an incident bundle (incident.json, report, audit)
chakravyuh analyze --out ./out

# REST API (Tier 1)
chakravyuh serve            # -> http://127.0.0.1:8080
curl -s localhost:8080/healthz
curl -s -X POST localhost:8080/incidents/analyze -H 'content-type: application/json' -d '{"incident_id":"INC-1"}'

# Command-centre dashboard — just open the file, or serve it:
python -m http.server --directory dashboard 8081   # -> http://localhost:8081

# Docker (API + dashboard)
docker compose up --build
```

## 4. API keys

**None are required for any core functionality.** Keys are only for the
optional LLM that writes natural-language analyst rationale — it never selects
containment actions and is never in the safety path.

| Variable | Needed when | How to get it |
|---|---|---|
| `ANTHROPIC_API_KEY` | `CHAKRAVYUH_LLM_PROVIDER=anthropic` | console.anthropic.com |
| `OPENAI_API_KEY` | `CHAKRAVYUH_LLM_PROVIDER=openai` | platform.openai.com |

Enable (optional):

```bash
export CHAKRAVYUH_LLM_PROVIDER=anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export CHAKRAVYUH_LLM_MODEL=claude-sonnet-4-6   # or your chosen model
pip install -e ".[llm]"
```

Never commit keys. Use environment variables or a secrets manager. `.env` is
git-ignored.

### Other configuration (all optional, all have defaults)

| Variable | Default | Meaning |
|---|---|---|
| `CHAKRAVYUH_ANOMALY_THRESHOLD` | `0.5` | detection sensitivity (0–1) |
| `CHAKRAVYUH_BLAST_RADIUS` | `5.0` | disruption above which an action is human-gated |
| `CHAKRAVYUH_API_HOST` | `127.0.0.1` | API bind host |
| `CHAKRAVYUH_API_PORT` | `8080` | API bind port |

## 5. Datasets (optional — for evaluation on real data)

The bundled synthetic scenario needs no downloads. To evaluate on benchmarks,
see [`DATASETS.md`](DATASETS.md). Summary of access:

| Dataset | Sector | Access | Note |
|---|---|---|---|
| DARPA OpTC | IT / APT | public (GitHub) | large (~GBs); IT detection + attribution |
| HAI | OT / power | public | labelled ICS attacks |
| SWaT / WADI | OT / water | **request form (iTrust)** | start early — approval takes time |
| CybORG / CAGE | simulation | public | closed-loop adaptive adversary |
| MITRE ATT&CK (+ICS) | knowledge | public (STIX) | replaces the offline lookup |
| NVD/CVE, CISA KEV | knowledge | public (API/JSON) | to weight exploit costs |

Put raw data under `data/raw/` (git-ignored). Respect each dataset's license.

## 6. Verifying your install

```bash
pip install -e ".[dev]"
pytest -q                 # expect: all tests pass
python -m chakravyuh.demo # expect: "CONTAINED, cascade averted, fully audited"
```

## 7. Safety preconditions (read before any real deployment)

- The `RealAdapter` is a **guarded stub** and must not be connected to
  production OT/ICS without a qualified operational-safety review (see
  [`../SECURITY.md`](../SECURITY.md)).
- Keep OT and high-blast-radius actions human-gated.
- The shipped scenario is synthetic; do not present it as real incident data.

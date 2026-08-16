# Roadmap

Current status (v0.1.0): a complete, tested reference pipeline with the novel
interdiction core, a real unsupervised detector, a live Neo4j knowledge graph,
RAG retrieval, a Gemini-backed Analyst Copilot, and a dashboard wired to the
live API — all running on a synthetic cross-sector scenario.

## Near term
- [x] **Adapter interface** (`InfrastructureAdapter`) with `ReplayAdapter` and a
      guarded stub `RealAdapter`. (dataset & CybORG adapters next)
- [x] **Real detector**: `chakravyuh.ml` — IsolationForest trained on a
      generated behavioural dataset (89% precision / 97% recall held-out).
      Swapping in OpTC (IT) / HAI-SWaT (OT) real data is still open — see
      `docs/DATASETS.md`; OpTC in particular is ~1TB on Google Drive with no
      bulk-download API, so this needs a manual pull, not an automated one.
- [ ] **Incremental attack-graph updating** from a live event stream (the graph
      currently comes from the scenario; make it grow from telemetry).
- [x] **ATT&CK/CVE/CERT-In-style knowledge graph** in Neo4j
      (`chakravyuh.knowledge.graph`) + TF-IDF RAG retrieval
      (`chakravyuh.rag`) + a read-only Analyst Copilot
      (`chakravyuh.agents.copilot`, Anthropic/OpenAI/Gemini). Swapping the
      curated seed set for the full STIX bundle + CISA KEV feed is still open.

## Mid term
- [x] **Command-centre dashboard** (`dashboard/`): chakravyuh-formation map,
      interdiction card with Approve, MTTD/MTTR, report + audit tabs, wired
      to the live API (history + copilot tabs included).
      (live-growing graph from a stream is next)
- [x] **Case library**: five runnable scenarios (`redecho`, `colonial`,
      `ukraine2015`, `aiims`, `synnovis`) through the same orchestrator.
      Public-source reconstructions, not victim telemetry.
- [ ] **CybORGAdapter** (closed-loop CAGE) — roadmap only; not shipped.
- [ ] **LangGraph orchestrator** variant behind the same interface.
- [ ] **Weighted exploit costs** from CVSS/EPSS/KEV; probabilistic paths
      (`-log p` edge weights).
- [ ] **Evaluation harness** implementing `docs/EVALUATION.md` with baselines.

## Longer term
- [ ] Multi-crown-jewel, multi-frontier interdiction (min multiway cut).
- [ ] Uncertainty-aware cuts (robust to detection error in the frontier).
- [ ] Federated deployment across sector CSIRTs with privacy-preserving TI
      sharing.

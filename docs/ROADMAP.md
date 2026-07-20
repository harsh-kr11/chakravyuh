# Roadmap

Current status (v0.1.0): a complete, tested reference pipeline with the novel
interdiction core, running on a synthetic cross-sector scenario.

## Near term
- [x] **Adapter interface** (`InfrastructureAdapter`) with `ReplayAdapter` and a
      guarded stub `RealAdapter`. (dataset & CybORG adapters next)
- [ ] **Real detectors**: plug an unsupervised IT detector (OpTC) and an ICS
      reconstruction detector (HAI/SWaT) into `DetectionAgent.score_event`.
- [ ] **Incremental attack-graph updating** from a live event stream (the graph
      currently comes from the scenario; make it grow from telemetry).
- [ ] **ATT&CK knowledge graph** in Neo4j from the STIX bundle + a RAG index
      over CVE/CISA-KEV/CERT-In advisories, replacing the offline lookup.

## Mid term
- [x] **Command-centre dashboard** (`dashboard/`): chakravyuh-formation map,
      interdiction card with Approve, MTTD/MTTR, report + audit tabs.
      (live-growing graph from a stream is next)
- [ ] **LangGraph orchestrator** variant behind the same interface.
- [ ] **Weighted exploit costs** from CVSS/EPSS/KEV; probabilistic paths
      (`-log p` edge weights).
- [ ] **Evaluation harness** implementing `docs/EVALUATION.md` with baselines.

## Longer term
- [ ] Multi-crown-jewel, multi-frontier interdiction (min multiway cut).
- [ ] Uncertainty-aware cuts (robust to detection error in the frontier).
- [ ] Federated deployment across sector CSIRTs with privacy-preserving TI
      sharing.

# Datasets

CHAKRAVYUH ships a small synthetic scenario so the demo and tests are
self-contained. To evaluate on real data, wire these open benchmarks through
the adapter interface (see `docs/ROADMAP.md`).

## IT / enterprise (detection + attribution + attack graph)
- **DARPA OpTC** (Operationally Transparent Cyber) — ~17.4B host/network
  events with a scripted multi-day APT campaign. Ground-truth red-team
  activity. Repo: `github.com/FiveDirections/OpTC-data`. Good for behavioural
  detection + ATT&CK attribution + frontier reconstruction.
- **Provenance-graph IDS baselines** to compare detection against: Kairos, MAGIC,
  Flash (IEEE S&P 2024 era), ORTHRUS (USENIX Security 2025).

## OT / ICS (cross-sector, physical-process telemetry)
- **HAI** (HIL-based Augmented ICS) — power+thermal testbed, labelled attacks.
- **SWaT** / **WADI** (iTrust, SUTD) — water-treatment/distribution testbeds
  with physical-process attacks. NOTE: **access requires a request form** to
  iTrust — start this early.
- ICS anomaly-detection baseline code: `github.com/pwwl/ics-anomaly-detection`.

## Closed-loop attacker simulation (response evaluation)
- **CybORG / CAGE Challenge** environments — a multi-agent gym for autonomous
  cyber-defense; lets the attacker *react* to our containment, so we can measure
  interdiction under an adaptive adversary rather than a fixed replay.

## Threat-intelligence knowledge
- **MITRE ATT&CK** + **ATT&CK for ICS** STIX 2.1 bundles (technique/tactic
  graph; production replaces the offline lookup in `chakravyuh/knowledge`).
- **NVD / CVE** + **CISA KEV** (known-exploited vulns) to weight exploit costs.
- **CERT-In advisories** (unstructured PDFs) — India-specific TI to enrich the
  RAG index; parse defensively.

## Handling & ethics
Do not commit raw datasets (see `.gitignore` — `data/raw/`). Some require
access agreements; respect their licenses. Never mix real infrastructure
telemetry into the shipped synthetic scenario or present it as such.

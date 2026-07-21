# Datasets

CHAKRAVYUH ships a small synthetic scenario so the demo and tests are
self-contained. To evaluate on real data, wire these open benchmarks through
the adapter interface (see `docs/ROADMAP.md`).

## IT / enterprise (detection + attribution + attack graph)
- **DARPA OpTC** (Operationally Transparent Cyber) — ~17.4B host/network
  events with a scripted multi-day APT campaign. Ground-truth red-team
  activity. Repo: `github.com/FiveDirections/OpTC-data`. Good for behavioural
  detection + ATT&CK attribution + frontier reconstruction.
  **Practical note:** the data itself (~1TB compressed) is hosted on Google
  Drive, not a bulk-downloadable host — there's no registration wall, but
  also no API for automated pulls. Plan on manually downloading the `short`
  subset (the folder meant for exactly this use case) via a browser rather
  than scripting it; the full `ecar`/`ecar-bro`/`bro` trees are tens of
  thousands of small per-second files.
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
- **Done, on a curated seed set:** `chakravyuh.knowledge.graph` is a real
  Neo4j graph (technique/tactic/mitigation/CVE/advisory nodes) that
  `chakravyuh.rag` retrieves over and the Analyst Copilot generates from.
  The seed data is a small, hand-picked set of real ATT&CK techniques and
  well-known CVEs (Zerologon, EternalBlue, Log4Shell) plus a few
  CERT-In-*style* illustrative advisories (explicitly not real published
  advisories — see the seed data's own comments in `graph.py`).
- **Open:** swap the seed set for the full **MITRE ATT&CK** + **ATT&CK for
  ICS** STIX 2.1 bundles, **NVD/CVE** + **CISA KEV** (to weight exploit
  costs), and real **CERT-In advisories** (unstructured PDFs — parse
  defensively, and don't present them as more current/authoritative than
  they are).

## Handling & ethics
Do not commit raw datasets (see `.gitignore` — `data/raw/`). Some require
access agreements; respect their licenses. Never mix real infrastructure
telemetry into the shipped synthetic scenario or present it as such.

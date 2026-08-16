# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/); versioning is SemVer.

## [0.2.0] - Unreleased

Product-readiness: a five-case library that runs in the engine, honest
HITL / CERT-In reporting, and packaging so the command centre boots without
Neo4j or an LLM key.

### Added
- Scenario catalog (`colonial`, `ukraine2015`, `aiims`, `synnovis`) plus
  RedEcho as a synthetic illustration. Dashboard picker, `GET /scenarios`,
  `GET /scenario?id=`, `demo --scenario`, `demo --hitl`.
- Greedy isolate-frontier baseline (shown only when strictly worse than min-cut).
- `GET /readyz` (detector, LLM, Neo4j, store).
- `docs/CASES.md`, `docs/JUDGE_QA.md`, `docs/WALKTHROUGH.md`, `docs/REVIEW.md`.

### Fixed
- Empty frontier / attacker-on-jewel no longer crash or report protected.
- `all([])` no longer marks empty executions as contained (`*_now` on analyze,
  approve, and GET).
- Observe-mode CERT-In tags actions **PROPOSED**, not HELD / DENIED.
- History list uses `crown_jewel_protected_now` / `has_pending`; deny is not green.
- Copilot sanitizes conversation history; no-key path stays `llm_used=false`.
- IsolationForest save/score failures fall back instead of crashing.
- Slack connector formats list/tuple link targets; `isolated` grows only on success.

### Changed
- Docker image installs `[api,detect]`. CI installs `[dev,api]` so FastAPI tests run.
- `docker compose up` is API + dashboard. Neo4j is `--profile full`.
- LLM is documented as copilot-only; `CybORGAdapter` is roadmap, not shipped.

## [0.1.0] - Unreleased
### Added
- Core domain schemas (`chakravyuh.schemas`).
- Attack-graph model and the minimum-cost cross-sector interdiction engine.
- Six agents: detection, attribution, cascade, interdiction, response, compliance, audit.
- Deterministic orchestrator with an audit-before-execute fail-safe.
- RedEcho-style cross-sector demo scenario and a narrated CLI demo.
- Hash-chained, tamper-evident audit log with `verify()`.
- Auto-drafted CERT-In 6-hour incident report.
- Test-suite and CI workflow.

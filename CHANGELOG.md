# Changelog

All notable changes to this project are documented here. Format loosely
follows [Keep a Changelog](https://keepachangelog.com/); versioning is SemVer.

## [0.1.0] - Unreleased
### Added
- Core domain schemas (`chakravyuh.schemas`).
- Attack-graph model and the minimum-cost cross-sector interdiction engine.
- Six agents: detection, attribution, cascade, interdiction, response, compliance, audit.
- Deterministic orchestrator with an audit-before-execute fail-safe.
- RedEcho-style cross-sector demo scenario and a narrated CLI demo.
- Hash-chained, tamper-evident audit log with `verify()`.
- Auto-drafted CERT-In 6-hour incident report.
- Test-suite (17 tests) and CI workflow.

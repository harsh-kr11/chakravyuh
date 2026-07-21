# Contributing to CHAKRAVYUH

Thanks for your interest! This project aims to be a clean, well-tested
reference for incident-time cross-sector attack-path interdiction.

## Ground rules
- **Safety first.** Any change touching response/actuation must keep OT and
  high-blast-radius actions human-gated. PRs that weaken gating will be
  declined unless they add an equivalent or stronger safeguard.
- **Tests required.** New behaviour needs tests. Run `make test` before
  pushing. Keep coverage from regressing.
- **Determinism.** Core detection/interdiction/audit logic must stay
  deterministic (seeded). LLMs are only for attribution reasoning and NL
  rationale, behind an interface.
- **No secrets, no live targets.** Never commit credentials, real network
  data, or connect adapters to production systems.

## Dev setup
```bash
python -m venv .venv && source .venv/bin/activate
make dev          # editable install with dev + detect extras
make test         # run the suite
make lint         # ruff
```

## Workflow
1. Open an issue describing the change.
2. Branch from `main`, keep PRs focused.
3. Ensure `make test lint` passes; update `CHANGELOG.md`.
4. Request review. Be kind in review.

## Commit style
Conventional-ish: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`.

## Areas we'd love help with
See `docs/ROADMAP.md` — real detectors trained on OpTC/HAI (today's model
trains on a generated dataset), the CybORG adapter, expanding the knowledge
graph beyond its curated seed set to the full ATT&CK STIX bundle + CISA KEV,
and real SOAR/EDR/firewall integrations behind `RealAdapter`.

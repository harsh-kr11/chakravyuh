# Security Policy

CHAKRAVYUH is defensive security software for critical infrastructure. We take
its integrity seriously.

## Reporting a vulnerability
**Please do not open a public issue for security vulnerabilities.** Instead,
email the maintainers (add a real address here) with details and, if possible,
a reproduction. We aim to acknowledge within 72 hours.

## Scope & responsible use
- This is a **research/reference** system. The `RealAdapter` is a stub by
  design and must not be connected to production OT/ICS without a qualified
  operational-safety review.
- All OT and high-blast-radius containment actions are **human-gated**. Do not
  ship changes that bypass these gates — including via a custom
  `chakravyuh.connectors.Connector`; a connector must only ever carry out an
  action that already went through the gate/approval flow, never decide or
  trigger one itself. See `docs/HITL_AND_MODES.md`.
- The shipped scenario is **synthetic**. Do not present it as real incident
  data.
- **The API has no authentication.** Anyone who can reach it — including
  `POST /incidents/{id}/approve` — can act as an approving analyst. Do not
  expose this API to an untrusted network. Put a real authenticating
  gateway in front of it before any deployment beyond a local/trusted
  environment; the `approver` field is a free-text label, not a verified
  identity, until that's done.
- CORS is wide open (`allow_origins=["*"]`) to support local dashboard
  development. Restrict this to your actual dashboard's origin in any
  shared or internet-facing deployment.

## Supported versions
Pre-1.0: only `main` receives fixes.

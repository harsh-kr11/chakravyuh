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
  ship changes that bypass these gates.
- The shipped scenario is **synthetic**. Do not present it as real incident
  data.

## Supported versions
Pre-1.0: only `main` receives fixes.

# Evaluation Protocol

The point is to show the interdiction decision is *better*, not just that a
pipeline runs. Report these, with baselines, on cross-sector scenarios.

## Detection & attribution (supporting cast)
- Anomaly detection rate / false-positive rate (baselines: Kairos, MAGIC,
  Flash, ORTHRUS on OpTC).
- ATT&CK **technique-level** attribution accuracy (precision/recall vs.
  ground-truth technique labels).

## Interdiction (the headline metric)
For each scenario compute, for CHAKRAVYUH and each baseline:
- **Containment success**: is the crown jewel provably separated from the
  attacker frontier? (boolean)
- **Availability cost**: total operational disruption of the chosen actions.
- **Efficiency**: attacker-path-cost increase achieved **per unit of
  availability disrupted** (higher is better).
- **Cascade averted**: did the action set avoid severing any protected
  cross-sector dependency? (boolean; the naive baseline typically fails this.)

### Baselines
1. **Greedy isolate-alerting-host** — isolate every host that raised an alert.
   (What many SOAR playbooks do.)
2. **Static min-cut hardening** — the offline interdiction cut computed once,
   ignoring the live frontier.
3. **Naive crown-jewel isolation** — cut everything incident to the crown jewel
   (implemented as `naive_containment_cost`; severs the hospital dependency).

## Response & operations
- **Automation coverage**: fraction of the containment executed without a human
  (vs. correctly gated for OT).
- **MTTD / MTTR** vs. a baseline SOC workflow (report the proxy from the
  pipeline result, plus wall-clock in the closed-loop CybORG setting).

## Adaptive adversary
Re-run interdiction inside CybORG so the attacker responds; report containment
success and availability cost under an adaptive red agent, not just replay.

## Reproducibility
Seed everything. Ship scenario configs. Report mean ± std over N seeds.

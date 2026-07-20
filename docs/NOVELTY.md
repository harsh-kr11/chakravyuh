# Novelty & Prior-Art Positioning

This document states, honestly and defensibly, what is and is not novel about
CHAKRAVYUH — so the claim survives technical judges, paper reviewers, and
patent examiners.

## The one-sentence claim
> An **incident-time**, **cross-sector**, **availability-aware** attack-path
> **interdiction** decision engine: given live detection telemetry, it computes
> the minimum-operational-cost set of containment actions that separates the
> attacker's current frontier from a crown-jewel asset while provably preserving
> protected cross-sector dependencies.

We do **not** claim to invent attack-graph interdiction, min-cut, Stackelberg
security games, or autonomous response. The contribution is the **composition**
and the **online, cross-sector, availability-constrained** setting.

## Three prior-art silos, and our delta

1. **Attack-graph interdiction / hardening (OFFLINE).**
   Nandi, Medal & Vadlamani "MINMAXBREACH" (*Computers & Operations Research*,
   2016); Durkota et al. "Hardening networks against strategic attackers using
   attack graph games" (*Computers & Security*, 2019); Mai et al. "Stackelberg
   Network Interdiction against a Boundedly Rational Adversary" (2023); the
   Noel/Jajodia minimum-cost hardening lineage.
   → **All are pre-incident** (which edges to patch/harden), single-enterprise,
   IT-only. **Our delta:** we run at *incident time* on a *live-updated* graph
   with an explicit *availability-disruption* objective.

2. **Online / incident-time response (SINGLE-SECTOR, POLICY-BASED).**
   Hammar & Stadler "Learning Near-Optimal Intrusion Responses Against Dynamic
   Attackers" (*IEEE TNSM*, 2024); Hammar "Optimal Security Response to Network
   Intrusions in IT Systems" (2025); Bayesian-attack-graph + MARL MTD work.
   → These act during intrusions but as **POMDP/RL policy selection** on a
   **single IT network**. **Our delta:** we formulate response as a
   **minimum-cost graph cut** on a live attack graph, and we reason
   **cross-sector**.

3. **Cross-sector cascade games (OFFLINE, PHYSICAL).**
   Wu & Zio "Attack-defense game of interdependent infrastructure systems
   considering cascading failures" (2025); power-gas cascade games (2026).
   → These model **physical/topological node attacks**, offline. **Our delta:**
   we operate on a **cyber attack graph** (exploit paths, ATT&CK techniques) at
   incident time, and the cross-sector term is a **containment constraint**
   (never sever a protected dependency), not just a payoff.

**The empty intersection** — live-telemetry-driven + minimal-availability-cost
interdiction cut + executed by a multi-agent system + cross-sector-cascade-aware
— is what CHAKRAVYUH occupies. Independent surveys (Zenitani, *Computers &
Security* 2023; Konsta et al. 2023) list "dynamic/real-time attack-graph
updating" and "analysis-to-optimal-action" as open problems, corroborating the
gap.

## Reviewer objections to pre-empt
- *"This is just min-cut."* — Yes, the solver is min-cut; the contribution is
  the **problem framing** (online, availability-as-capacity, protected
  dependencies as ∞-capacity, cross-sector) and the **end-to-end agentic
  system** around it, evaluated on cyber-defense benchmarks.
- *"Hammar already does online response."* — Different mechanism (POMDP/RL
  policy vs. graph cut), single-sector, no availability-cost cut, no protected
  cross-sector dependency constraint.
- *"Wu/Zio already do cross-sector."* — Physical node attacks, offline, no cyber
  attack graph, no incident-time containment selection.

## Patent note (for maintainers)
The composition above (live attack-graph re-estimation → availability-aware
min-cost interdiction cut → protected-dependency preservation → human-gated
execution → immutable audit) is candidate subject matter. **Open-sourcing under
Apache-2.0 includes a patent grant to users of *this* code and may constitute a
public disclosure** that starts grace-period/novelty clocks in some
jurisdictions. If patent protection is intended, consult counsel about filing a
provisional **before** public release, and about how the Apache-2.0 grant
interacts with your filing strategy.

## Evaluation is part of the novelty
Beyond the method, we provide an evaluation protocol (see
[`EVALUATION.md`](EVALUATION.md)) comparing the interdiction cut against a
greedy "isolate-the-alerting-host" baseline and a static min-cut hardening
baseline, on cross-sector scenarios — quantifying attacker-path-cost increase
per unit of availability disrupted, and cascade averted.

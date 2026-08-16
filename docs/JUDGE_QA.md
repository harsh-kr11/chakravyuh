# Judge Q&A (10 minutes)

Stand-up script for questions. Pair with [`WALKTHROUGH.md`](WALKTHROUGH.md)
and the never-say list in [`CASES.md`](CASES.md).

If you do not know, say so. Do not invent telemetry, victims, or autonomy.

---

## Why not just use existing SIEM?

SIEMs **detect and alert**. They do not compute *containment scope*.

The operator question after the alert is: which smallest set of actions cuts
the attacker off from the crown jewel **without** taking down the hospital,
the pipeline, or the ICU blood-result path. That is a min-cost s-t cut with
operational `cut_cost` as capacity and protected dependencies at ∞.

Show **Colonial**: they had detection. They still halted 5,500 miles of OT
for an IT-only breach because they could not see a finite cut.

Never say: we replace the SIEM.

## How is this different from a firewall rule?

A firewall rule is binary isolation: block this host / this subnet. It does
not know that `lab_lis → icu_blood_results` is a protected clinical
dependency, or that isolating the SCADA neighbourhood costs 108 while an
upstream cut costs 3.

Show **Synnovis**: the harm *is* the dependency. Naive isolate-jewel severs
the ICU result path. The min-cut does not.

Never say: we are a next-gen firewall.

## Have you tested on real data?

Public-source **reconstructions** run through the real engine, compared to
the historical decision. Not victim telemetry. Not a live CERT-In feed.

RedEcho is a **synthetic illustration** inspired by MITRE C0043 (no OT
access recorded). Colonial / Ukraine 2015 / AIIMS / Synnovis cite public
advisories and reporting. Each card has a disclaimer.

Never say: we ingested Colonial’s SIEM / AIIMS packet captures.

## What about fully autonomous response?

OT and high-blast-radius actions are **always human-gated**. There is no
API mode that skips the human for OT. That is deliberate.

Show **Oldsmar 2021** (Q&A only): a human reversed a dangerous setpoint in
seconds. Automation that writes OT without a gate is the failure mode.

CLI default `demo` auto-approves so a narration can finish; that is not
production. `demo --hitl` and API `mode=respond` leave OT pending.

Never say: fully autonomous OT.

## Did you prevent Mumbai 2020 / replay RedEcho?

No. C0043 is pre-positioning; MITRE records no OT access. The Mumbai
October 2020 outage is unsubstantiated as a cyber effect. We keep the
3.0 vs 108.0 illustration and say so on the card.

Use **Colonial** as the real thesis case instead.

## Would AIIMS eHospital have stayed up?

No. Five hosts were already encrypted. We do not decrypt. The case is:
given CERT-In’s segmentation finding, isolate the island — do not yank
emergency care as if it were a cuttable edge.

## Is the LLM choosing containment?

No. IsolationForest detects. ATT&CK lookup attributes. Min-cut plans.
The copilot is read-only and optional. No API key → `llm_used=false` plus
retrieved context. Venue default.

## Did you invent min-cut?

No. Classic interdiction is offline hardening. The product is
**incident-time**, **availability-as-capacity**, **protected cross-sector
deps**, **human-gated**, **audited**. See `docs/NOVELTY.md`.

## Is History green after a deny?

No. `crown_jewel_protected` is the plan on paper.
`crown_jewel_protected_now` is execution truth. Empty action lists are
not contained (`all([])` is True in Python; we require executions).

## Money sentences (drop naturally, do not recite as a list)

1. “Incident-time min-cost s-t cut: capacity = operational `cut_cost`, protected deps = ∞.”
2. “RedEcho illustration: 2-action cut, **3.0 vs naive 108.0**, hospital load not severed.”
3. “Colonial reconstruction: they halted 5,500 miles of OT for an IT-only breach; the finite cut is revoke VPN + isolate IT.”
4. “Deterministic core; LLM never chooses the cut. OT is human-gated.”

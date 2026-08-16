# Case library

Five cases run **in the orchestrator**. They are not slide-deck anecdotes.
Each module exposes `META`, `CROWN_JEWEL`, `build_graph()`, `telemetry_stream()`,
and `historical()`. Kind is `reconstruction` except RedEcho
(`synthetic_illustration`).

No case is live victim telemetry. No case is a live CERT-In feed.

CLI: `python -m chakravyuh.demo --scenario <id>`
API: `POST /incidents/analyze` with `{"scenario": "<id>"}`
Dashboard: case picker on load.

Must-ship for the thesis: `colonial` and `synnovis`. RedEcho stays as the
default walkthrough (3.0 vs 108.0). `ukraine2015` and `aiims` ship in the
same catalog shape.

---

## `redecho` — Indian power pre-positioning (synthetic illustration)

- **Sources:** [MITRE C0043](https://attack.mitre.org/campaigns/C0043/),
  [G1042 RedEcho](https://attack.mitre.org/groups/G1042/).
- **Claim:** Grid IT → OT SCADA with a hospital power dependency. Min-cut is
  two actions, disruption **3.0 vs naive 108.0**, hospital load uncut.
- **Do not claim:** We replayed RedEcho. We prevented Mumbai October 2020.
  C0043 reached OT (MITRE records no OT access). The Power Minister attributed
  Mumbai to human error; Recorded Future called the malware link unsubstantiated.
- **Say:** “Inspired by C0043 pre-positioning.” The hospital edge is
  *downstream of the sink* — classical min-cut would not pick it anyway; the
  3 vs 108 number is still the right demo hook.

## `colonial` — May 2021 (product thesis)

- **Sources:** [CISA AA21-131A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-131a);
  CEO Blount testimony (halted ~5,500 miles in ~15 minutes).
- **Claim:** DarkSide was **IT-only**. Operators halted pipeline OT because they
  could not see a finite cut. CHAKRAVYUH revokes the legacy VPN / isolates
  alerting IT; East-Coast fuel delivery is the protected edge (uncut).
- **Do not claim:** We have Colonial’s SIEM. OT was known compromised
  (CISA: not known hit). We would have kept pumps running in 2021 — we show
  that a finite IT cut *exists* on a public-source reconstruction.
- **Keeper:** Colonial paid $4.4M; the real cost was shutting a pipeline that
  did not need to be shut.

## `ukraine2015` — December 2015 (MITRE C0028)

- **Sources:** [MITRE C0028](https://attack.mitre.org/campaigns/C0028/),
  [CISA IR-ALERT-H-16-056-01](https://www.cisa.gov/news-events/ics-alerts/ir-alert-h-16-056-01).
- **Claim:** BlackEnergy → creds → ICS VPN → HMI → breakers. ~225k customers.
  Interdiction is **upstream of the HMI**, not the breaker circuit.
- **Do not claim:** We ingested Ukrainian grid telemetry. We would have kept
  the lights on in 2015.

## `aiims` — November 2022 (India hospital)

- **Sources:** parliamentary / contemporaneous CERT-In reporting (e.g. ~1.3 TB,
  five eHospital servers, improper segmentation, ~two weeks of paper ops).
- **Claim:** Isolate the alerting island / infected VLAN, not the whole campus.
  Emergency care is the protected load.
- **Do not claim:** We would have kept eHospital fully up. Those five hosts
  were **already encrypted**. This engine does not decrypt. The case is the
  isolation decision given no segmentation.

## `synnovis` — June 2024 (cross-sector cascade)

- **Sources:** contemporaneous reporting (BBC, Reuters) and King’s College
  Hospital trust statements. Qilin hit a **blood lab**, not a hospital.
  Delayed results contributed to a patient death.
- **Claim:** Lab LIS → ICU blood-result path is a **protected edge**. Isolate
  the compromised lab workstation; never cut the result feed.
- **Do not claim:** We have Synnovis or NHS telemetry. We would have saved
  that patient. The reconstruction argues containment scope, not clinical
  counterfactual.

---

## Q&A only (no graph in this catalog)

- **WannaCry / NHS 2017** — worm + kill-switch, not a min-cut problem.
- **Oldsmar 2021** — operator reversed a setpoint. Why OT is always human-gated.

---

## Honesty lines (never say)

- We ingested victim telemetry / a live CERT-In feed.
- We prevented Mumbai 2020 / “the demo replays RedEcho.”
- We would have kept eHospital fully up after encryption.
- We invented min-cut / fully autonomous OT / production auth.

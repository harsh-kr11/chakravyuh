# Case library

Five cases run **in the orchestrator**. They are public-source reconstructions
plus one synthetic illustration — not live victim telemetry, and not a live
CERT-In feed.

Each module exposes `META`, `CROWN_JEWEL`, `build_graph()`, `telemetry_stream()`,
and `historical()`. Kind is `reconstruction` except RedEcho
(`synthetic_illustration`).

```bash
python -m chakravyuh.demo --scenario colonial
```

API: `POST /incidents/analyze` with `{"scenario": "colonial"}`.
Dashboard: case picker on load.

---

## `redecho` — Indian power pre-positioning (synthetic illustration)

- **Sources:** [MITRE C0043](https://attack.mitre.org/campaigns/C0043/),
  [G1042 RedEcho](https://attack.mitre.org/groups/G1042/).
- **What it shows:** Grid IT → OT SCADA with a hospital power dependency.
  Min-cut is two actions, disruption **3.0 vs naive 108.0**, hospital load uncut.
- **What it is not:** A replay of RedEcho. A claim that we prevented Mumbai
  October 2020. MITRE records no OT access for C0043. The Mumbai outage is
  unsubstantiated as a cyber effect.

## `colonial` — May 2021

- **Sources:** [CISA AA21-131A](https://www.cisa.gov/news-events/cybersecurity-advisories/aa21-131a);
  CEO Blount testimony (halted ~5,500 miles in ~15 minutes).
- **What it shows:** DarkSide was **IT-only**. Operators halted pipeline OT
  because they could not see a finite cut. CHAKRAVYUH cuts on the IT side;
  East-Coast fuel delivery is the protected edge (uncut).
- **What it is not:** Colonial’s SIEM. A claim that OT was known compromised
  (CISA: not known hit). A claim we would have kept pumps running in 2021 —
  the reconstruction shows that a finite IT cut *exists*.

## `ukraine2015` — December 2015 (MITRE C0028)

- **Sources:** [MITRE C0028](https://attack.mitre.org/campaigns/C0028/),
  [CISA IR-ALERT-H-16-056-01](https://www.cisa.gov/news-events/ics-alerts/ir-alert-h-16-056-01).
- **What it shows:** BlackEnergy → creds → ICS VPN → HMI → breakers.
  Interdiction is **upstream of the HMI**, not the breaker circuit.
- **What it is not:** Ukrainian grid telemetry. A claim we would have kept
  the lights on in 2015.

## `aiims` — November 2022

- **Sources:** parliamentary / contemporaneous CERT-In reporting (e.g. ~1.3 TB,
  five eHospital servers, improper segmentation, ~two weeks of paper ops).
- **What it shows:** Isolate the alerting island / infected VLAN, not the
  whole campus. Emergency care is the protected load.
- **What it is not:** Decrypting the five hosts (they were already encrypted).
  A claim that eHospital would have stayed fully up.

## `synnovis` — June 2024

- **Sources:** contemporaneous reporting (BBC, Reuters) and King’s College
  Hospital trust statements. Qilin hit a **blood lab**, not a hospital.
- **What it shows:** Lab LIS → ICU blood-result path is a **protected edge**.
  Isolate the compromised lab workstation; never cut the result feed.
- **What it is not:** Synnovis or NHS telemetry. A clinical counterfactual
  about any patient.

---

## Not in the catalog (by design)

- **WannaCry / NHS 2017** — worm + kill-switch, not a min-cut problem.
- **Oldsmar 2021** — operator reversed a setpoint; relevant to why OT is
  human-gated, not modelled as a graph here.

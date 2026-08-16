# Ten-minute product walkthrough

Laptop on the projector. API + dashboard. No LLM key required.

```bash
pip install -e ".[dev,api]"
chakravyuh serve                          # :8080
python -m http.server --directory dashboard 8081
```

Open http://localhost:8081. Idle state should already show the case picker,
a one-liner, and the honesty disclaimer — not a blank map.

---

## 0:00–1:00 — what this is

CHAKRAVYUH answers: *smallest containment that still keeps the protected
load up.* Solver is min-cut. Product is incident-time + availability-aware
+ human-gated + audited. LLM is a copilot, not the cut.

## 1:00–3:00 — RedEcho illustration (default)

Leave the picker on RedEcho. Mode: **Observe + Act**. Run interdiction.

Point at: two actions, **3.0 vs 108.0**, hospital load uncut. OT actions
awaiting approval.

**Say:** inspired by C0043 pre-positioning. **Do not say:** we replayed
RedEcho or prevented Mumbai 2020.

Approve (or switch to Observe only on a replay if you want zero actuation).

## 3:00–6:00 — Colonial (the thesis)

Pick **Colonial Pipeline**. Run.

Historical card: they halted 5,500 miles of OT. CHAKRAVYUH: finite IT cut;
fuel delivery is the protected edge.

Keeper: *Colonial paid $4.4M; the real cost was shutting a pipeline that
did not need to be shut.*

If a judge asks “real data?”: public-source reconstruction, CISA AA21-131A,
not victim telemetry.

## 6:00–8:00 — Synnovis or HITL honesty

**Synnovis:** lab → ICU blood results is the protected edge. Naive
isolate-jewel severs it. Min-cut does not.

**Or** leave Colonial in **Observe + Act**, show History: pending is not
green. Deny one OT action; `crown_jewel_protected_now` is false. That is
the point of a human gate, not a bug.

## 8:00–10:00 — Q&A

Use [`JUDGE_QA.md`](JUDGE_QA.md). Copilot tab: if no key, it says so and
still returns retrieved ATT&CK context. Do not apologise for that — it is
the correct venue default.

Stretch if asked: Ukraine 2015 (cut before HMI), AIIMS (already encrypted;
isolation not decrypt).

---

## Fallback if the dashboard dies

```bash
python -m chakravyuh.demo --scenario colonial
python -m chakravyuh.demo --hitl
```

Same engine, narrated. `--hitl` is pending OT, not observe-only.

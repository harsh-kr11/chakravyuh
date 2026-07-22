# Integration: feeding CHAKRAVYUH real telemetry

CHAKRAVYUH never reaches into your systems and reads your logs itself — it
only ever analyzes events handed to it in a specific, small, JSON shape.
**Someone at your organization writes a small translator** that turns your
real logs into that shape and sends them over. This document is that
translator's contract.

This is intentionally plain HTTP + JSON — any language that can make a POST
request can integrate. No SDK, no CHAKRAVYUH-specific library required.

## 1. The event shape (the contract)

Fetch it live and authoritative from a running instance — it's generated
directly from the code, so it can never drift out of date with this doc:

```bash
curl -s localhost:8080/schema/telemetry-event | python3 -m json.tool
```

Which returns (abbreviated):

```json
{
  "title": "TelemetryEvent",
  "required": ["asset_id", "kind"],
  "properties": {
    "ts":             {"type": "string", "format": "date-time"},
    "asset_id":       {"type": "string"},
    "kind":           {"type": "string"},
    "features":       {"type": "object", "additionalProperties": {"type": "number"}},
    "is_malicious":   {"type": "boolean", "default": false},
    "technique_hint": {"type": ["string", "null"], "default": null}
  }
}
```

Field by field:

| Field | Required | What it means |
|---|---|---|
| `asset_id` | yes | Must match an id in the bundled topology today — see the limitation below. |
| `kind` | yes | A short label for the event category, e.g. `"auth"`, `"netflow"`, `"process"`. Free text; not matched against a fixed list. |
| `ts` | no | Event timestamp; defaults to now if omitted. |
| `features` | no | **This is the part that actually drives detection.** A flat map of behavioural signals, 0.0–1.0-ish scale, matching the schema in `chakravyuh.ml.features.FEATURE_NAMES`: `off_hours`, `failed_logins_1h`, `new_asset_pair`, `bytes_out_zscore`, `process_count_zscore`, `privilege_level`, `session_duration_zscore`. Missing keys default to 0 ("nothing unusual"). |
| `is_malicious` | no | Ground-truth label, for evaluation/scenario scripting only. Leave it out for real events — you don't know the ground truth at ingestion time, and detection doesn't use it. |
| `technique_hint` | no | See the honest caveat below — attribution currently depends on this being supplied. |

## 2. Sending events

```bash
curl -s -X POST localhost:8080/incidents/analyze \
  -H 'content-type: application/json' \
  -d '{
    "incident_id": "INC-REAL-1",
    "mode": "observe",
    "events": [
      {
        "asset_id": "it_jump_host",
        "kind": "auth",
        "features": {
          "off_hours": 1,
          "failed_logins_1h": 4,
          "new_asset_pair": 1,
          "bytes_out_zscore": 1.8,
          "process_count_zscore": 0.9,
          "privilege_level": 1,
          "session_duration_zscore": 0.6
        }
      }
    ]
  }'
```

Omit `events` entirely and CHAKRAVYUH uses its bundled demo scenario instead
— that's how the zero-config demo keeps working. Use `mode: "observe"`
while you're first testing a translator, so nothing gets executed while you
verify the shape is right; switch to `mode: "respond"` (the default) once
you're ready for the real human-in-the-loop flow.

## 3. A minimal example translator (Python, but the pattern is language-agnostic)

```python
import httpx

def translate_and_send(raw_log: dict) -> None:
    """raw_log: whatever your SIEM/EDR/app already emits."""
    event = {
        "asset_id": raw_log["hostname"],
        "kind": "auth",
        "features": {
            "off_hours": 1 if raw_log["hour"] < 6 or raw_log["hour"] > 20 else 0,
            "failed_logins_1h": raw_log.get("failed_logins_last_hour", 0),
            "new_asset_pair": 1 if raw_log.get("first_seen_connection") else 0,
            # ... map whatever signals you actually have; unmapped ones
            # default to 0, meaning "nothing unusual on this dimension".
        },
    }
    httpx.post(
        "http://localhost:8080/incidents/analyze",
        json={"incident_id": raw_log["incident_id"], "events": [event]},
    )
```

The exact same pattern works from any language — build the JSON object
shown above and POST it; there is nothing Python-specific about the wire
format.

## 4. Two honest limitations, so you don't hit them by surprise

**Attribution depends on `technique_hint` today.** The interdiction math
(detecting anomalies, reconstructing the attacker's frontier, computing the
minimal cut, checking the cross-sector cascade) works from `features` alone
and needs nothing else. But the MITRE ATT&CK technique names/tactics shown
in the result currently come from a direct lookup keyed on `technique_hint`
in the event — attribution isn't yet inferred purely from behavioural
patterns. If your translator can supply a best-guess ATT&CK id (e.g. from a
rule that already fired in your own SIEM), attribution will show it; if not,
the incident is still fully detected and contained, just with an empty
`techniques` list.

**The attack-graph topology is still the bundled one.** You can bring your
own *events*, but `asset_id` values must currently match nodes in the
bundled demo network (`it_jump_host`, `domain_controller`, `ot_scada_server`,
etc. — see `GET /scenario` for the full list). Wiring in your own real
topology (your own assets, your own network structure) is a natural next
step, not yet built — see `docs/ROADMAP.md`.

## 5. Standard formats (recommended direction, not yet built)

If you're choosing how to shape your own translator, consider having it
read from **[OCSF](https://ocsf.io)** (Open Cybersecurity Schema Framework)
rather than your tool's raw proprietary format if your tools already export
it — AWS Security Lake and a growing number of SIEM/EDR vendors do natively.
OCSF is open source, schema-driven, and has Python libraries on PyPI. Mapping
OCSF's schema onto `TelemetryEvent.features` above is real but
well-documented work, versus reinventing your own format from scratch.
CHAKRAVYUH does not currently ship an OCSF adapter — this is a
recommendation for how to build your translator well, not a claim that it's
already wired in.

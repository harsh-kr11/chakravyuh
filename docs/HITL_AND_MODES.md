# The two modes, human-in-the-loop, and plugging in your own actions

This is the plain-language guide to the part of CHAKRAVYUH that confuses
people fastest: what "Observe only" vs "Observe + Act" actually do, whether
the human-approval step is real, and how someone at a different company
would actually wire up their own real actions. If you read one doc before
adopting this project, read this one.

## 1. The two modes, side by side

| | **Observe only** | **Observe + Act** (default) |
|---|---|---|
| Detects anomalies, attributes ATT&CK techniques, checks cross-sector cascade risk | Yes | Yes |
| Computes the minimal containment plan and shows it | Yes | Yes |
| Writes the CERT-In report | Yes | Yes |
| Actually revokes a low-risk credential automatically | **No** | Yes |
| Actually touches anything OT/high-risk | **No, never** | Only after a real human clicks Approve |
| Anything happens to a real system | **Never** | Only via whatever connector you've configured (default: simulated) |

**Observe only** is the "just tell me what you'd do" mode — nothing is
executed, not even the safe stuff. Good for a first look, a demo to
skeptical stakeholders, or auditing what the system *would* have done
against historical data without any risk of it doing anything.

**Observe + Act** is the real thing: low-risk actions (e.g. revoking one
compromised login) happen immediately because they're judged safe enough to
automate; anything touching OT or otherwise flagged high-risk always stops
and waits for a real person to say yes or no. This is not a setting anyone
can quietly disable — it's built into the code (`requires_human_gate` on
every action), not a config flag.

There is deliberately **no third mode** that skips the human for everything.
That was a considered decision, not a missing feature — see
`docs/PREREQUISITES.md` and `SECURITY.md`.

## 2. Is the human-approval step actually real?

Yes — and this is worth being precise about, because an earlier version of
this project *looked* real but wasn't. Today:

1. `POST /incidents/analyze` computes the plan. Low-risk actions run
   immediately. Anything gated is marked `pending: true` and **nothing
   happens to it** — no auto-approval, no timer, nothing.
2. The pending action sits there, genuinely unresolved, until a separate,
   later `POST /incidents/{id}/approve` call arrives — a real HTTP request
   that only happens when a real person clicks a real button (in the
   dashboard) or your own system calls the endpoint directly.
3. Only at that point does anything execute.

You can verify this yourself: run an incident, then query
`GET /incidents/{id}` *before* approving anything — you'll see the gated
action still sitting at `executed: false, pending: true`. Nothing moves
until you tell it to.

## 3. What "the action is real" actually means — and Slack/webhooks explained simply

Three separate things get confused here, so let's separate them:

- **Who approves, and where:** always a real person, always through
  CHAKRAVYUH's own dashboard or API. This never involves Slack or a webhook.
  A person looks at the incident and clicks Approve or Deny. That's it.
- **What happens after approval:** something needs to actually *carry out*
  the action — revoke a credential, block a link. That "something" is a
  **connector**. By default, with no connector configured, this is
  simulated (a flag flips in memory, nothing external happens) — which is
  exactly right for a demo, and exactly wrong for a real deployment.
- **Why Slack/webhook exist as the first real connectors:** we don't have
  access to a real company's firewall or Active Directory to test against.
  A generic webhook (any URL that accepts a JSON POST) and Slack (which is
  *just* a specific webhook URL — no SDK, no special integration, literally
  `POST {"text": "..."} ` to a URL Slack gives you) are the safest possible
  things to point a real, working connector at: a real HTTP request
  genuinely happens, so the whole "approve → execute for real" pipeline is
  proven end-to-end — without the risk of "for real" meaning "cuts power to
  a hospital by mistake in a test." Neither is meant to be your production
  connector. Section 4 below is how you build that.

## 4. Plug-and-play: writing your own connector

This is the actual adoption story, and it's short on purpose. A connector
is one Python class:

```python
from chakravyuh.connectors.base import Connector, ConnectorResult
from chakravyuh.schemas import ContainmentAction

class ActiveDirectoryConnector(Connector):
    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    def execute(self, action: ContainmentAction, *, incident_id: str) -> ConnectorResult:
        # action.action_type is one of: isolate_host, block_link, revoke_credential
        # action.target is the asset id (or a (src, dst) pair for block_link)
        try:
            # ... call your real AD/firewall/EDR API here ...
            return ConnectorResult(ok=True, detail="revoked")
        except Exception as exc:
            return ConnectorResult(ok=False, detail=str(exc))
```

Wire it in wherever your deployment constructs the app (or extend
`chakravyuh.connectors.make_connector` to recognise a new
`CHAKRAVYUH_CONNECTOR=active_directory` value). That's the whole contract:
CHAKRAVYUH hands you an already-decided action and an incident id; you
report back whether it actually happened. You are never asked to decide
*which* action to take — that decision already happened, deterministically,
before your connector is ever called.

### Do we follow an industry standard here?

Honestly: no formal certification, but the *shape* of this deliberately
mirrors how real SOAR platforms (Splunk SOAR, Palo Alto XSOAR) structure
their "apps"/connectors — a fixed input (the action), a fixed output
(success/failure + detail), nothing else required. `ContainmentAction` and
`TelemetryEvent` are documented, machine-readable schemas
(`GET /schema/telemetry-event`), not a bespoke format you have to
reverse-engineer.

## 5. Multiple actions, partial accept/reject — and no, denial is not a flaw

A real incident can produce several actions in one plan — some low-risk
(auto-executed), some gated. An analyst can approve some and deny others.
Here's exactly what happens:

- Each action is tracked and resolved **independently** (`action_index` on
  `POST /incidents/{id}/approve`, or omit it to resolve every pending action
  the same way at once).
- The CERT-In report gets an **addendum**, appended after the fact, listing
  exactly who approved or denied what, and when. The original draft is
  never silently rewritten — you get an honest paper trail of the plan as
  proposed *and* the decisions made about it.
- The audit chain gets a `human_decision` record for every single decision,
  hash-linked to everything before it. This is what makes it possible to
  answer "why did this happen" months later.

**If an analyst denies a required action, the crown jewel may genuinely not
be protected — and the system says so, honestly, rather than pretending
otherwise.** Two fields matter here:

- `interdiction.crown_jewel_protected` — the *plan's* theoretical guarantee,
  assuming every action in it executes. This never changes after the fact;
  it's a property of the algorithm's output, useful for judging how good
  the plan was on paper.
- `interdiction.crown_jewel_protected_now` — the **real, current** answer,
  recomputed every time an action resolves. If anything required is still
  pending or was denied, this is `false`, full stop, even if the plan on
  paper looked perfect.

So: is a denial "a flaw"? **No — it's the entire point of human-in-the-loop.**
The system's job is to compute the best plan and honestly report what
actually happened, including when a human overrode it. A denial becoming
invisible in the report, or the system quietly claiming "SAFE" anyway,
would be the actual flaw. That's exactly the bug this project fixed: earlier,
`crown_jewel_protected` didn't update after a real denial, so an API caller
checking that field alone would get a wrong, falsely reassuring answer.
Anyone integrating against this API should check `crown_jewel_protected_now`
/ `cascade_averted_now`, not the plan-level fields, if they want to know
"is it actually safe right now."

## 5b. CLI vs API (same product, different defaults)

The API default is the real HITL path: `mode=respond` uses `pending_approval`,
so OT / high-blast actions sit pending until `POST /incidents/{id}/approve`.

The narrated CLI (`python -m chakravyuh.demo` / `chakravyuh demo`) defaults to
`auto_approve` so a one-shot walkthrough can finish without a second process.
That is a **demo convenience**, not production policy. Pass `--hitl` to
construct `Orchestrator(gate=pending_approval)` and leave gated actions
pending. `--hitl` is **not** observe-only: ungated (low-risk) actions still
execute; only OT / high-blast actions wait.

| Surface | Default gate | OT / high-blast |
|---|---|---|
| API `mode=respond` | `pending_approval` | waits for Approve |
| API `mode=observe` | n/a (nothing executes) | never runs |
| CLI `demo` | `auto_approve` | executes in the narration |
| CLI `demo --hitl` | `pending_approval` | stays pending |

There is still no silent “fully autonomous OT” mode on the API.

### What if the connector itself fails (not a human decision)?

Handled distinctly from a denial: if a human approves but the connector
call fails (network blip, target system down), the action stays `pending`
and is retryable — approving it again later will try again. A technical
failure and a human "no" are different things and are never conflated.

## 6. Is this production-ready? An honest checklist

**The "observe" flow (analyze → detect → attribute → report) is complete
and solid.** Real trained model, real graph algorithm, real audit chain,
real persistence, tested and live-verified end to end, including
through the dashboard.

**The HITL/action flow is functionally real and tested**, not a mockup —
genuine pending state, genuine separate approval call, genuine connector
dispatch, genuine retry-on-failure, genuine honest reporting of denials.

**What a real adopter still has to add before going live against real
infrastructure:**
- **Authentication.** Today, anyone who can reach the API can call
  `/approve`. There is no login, no token check, no tie between "who the
  API believes approved this" (`approver` is a free-text string) and any
  real identity. This is the single biggest gap between "works" and "safe
  to expose to the internet." Put it behind your own auth gateway/reverse
  proxy at minimum; wiring real auth into the API itself is future work.
- **A real connector for your systems.** Webhook/Slack are real but
  generic — you write the one that talks to *your* firewall/AD/EDR (see
  Section 4).
- **CORS is wide open** (`allow_origins=["*"]`) for local dashboard
  development. Tighten this to your actual dashboard's origin before any
  real deployment.
- **SQLite** is fine for one instance; move to Postgres if more than one
  process needs to write concurrently.
- **The attack-graph topology is still a bundled case**, not an uploaded
  customer graph. The picker has five topologies (`docs/CASES.md`). You can
  feed in your own events (`docs/INTEGRATION.md`) onto one of those graphs.

None of these are secret — they're the same boundaries called out in
`SECURITY.md` and `README.md`. This document exists so they're in one place,
in plain language, instead of scattered across files you'd have to already
know to go looking for.

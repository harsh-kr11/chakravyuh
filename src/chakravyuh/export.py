"""Serialization / export helpers for incident results."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .orchestrator import Orchestrator, PipelineResult


def result_to_dict(result: PipelineResult, orch: Orchestrator) -> dict[str, Any]:
    """Flatten a PipelineResult (+ audit log) into a JSON-serialisable dict."""
    p = result.plan
    return {
        "incident_id": result.context.incident_id,
        "anomalies": [a.model_dump(mode="json") for a in result.context.anomalies],
        "techniques": [t.model_dump(mode="json") for t in result.context.techniques],
        "attacker_frontier": result.context.attacker_frontier,
        "cascade": result.cascade.model_dump(mode="json"),
        "interdiction": {
            "actions": [a.model_dump(mode="json") for a in p.actions],
            "attacker_cost_before": p.attacker_cost_before,
            "attacker_cost_after": (
                None if p.attacker_cost_after == float("inf")
                else p.attacker_cost_after
            ),
            "availability_cost": p.availability_cost,
            "baseline_availability_cost": p.baseline_availability_cost,
            "greedy_availability_cost": p.greedy_availability_cost,
            "crown_jewel_protected": p.crown_jewel_protected,
            "cascade_averted": p.cascade_averted,
            "notes": p.notes,
        },
        "executions": [e.model_dump(mode="json") for e in result.executions],
        "metrics": {
            "mttd_steps": result.mttd_steps,
            "mttr_steps": result.mttr_steps,
        },
        "audit": {
            "ok": result.audit_ok,
            "records": orch.audit.export(),
        },
        "certin_report": result.certin_report,
    }


def write_bundle(
    result: PipelineResult, orch: Orchestrator, out_dir: str
) -> dict[str, str]:
    """Write incident.json, certin_report.txt and audit_log.json to out_dir."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    data = result_to_dict(result, orch)

    incident_path = out / "incident.json"
    incident_path.write_text(json.dumps(data, indent=2, default=str))

    report_path = out / "certin_report.txt"
    report_path.write_text(result.certin_report)

    audit_path = out / "audit_log.json"
    audit_path.write_text(json.dumps(orch.audit.export(), indent=2, default=str))

    return {
        "incident": str(incident_path),
        "report": str(report_path),
        "audit": str(audit_path),
    }

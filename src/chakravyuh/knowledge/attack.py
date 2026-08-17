"""A tiny, offline slice of MITRE ATT&CK (incl. ATT&CK for ICS).

In production this is replaced by a Neo4j knowledge graph built from the
official STIX 2.1 bundle + a RAG index over CVE / CERT-In advisories (see
docs/DATASETS.md). For a self-contained demo and deterministic tests we ship a
small hand-curated lookup keyed by technique id.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Technique:
    technique_id: str
    name: str
    tactic: str


TECHNIQUES: dict[str, Technique] = {
    "T1078": Technique("T1078", "Valid Accounts", "Initial Access"),
    "T1021": Technique("T1021", "Remote Services", "Lateral Movement"),
    "T1210": Technique("T1210", "Exploitation of Remote Services", "Lateral Movement"),
    "T1003": Technique("T1003", "OS Credential Dumping", "Credential Access"),
    "T1566": Technique("T1566", "Phishing", "Initial Access"),
    "T1133": Technique("T1133", "External Remote Services", "Initial Access"),
    "T1486": Technique("T1486", "Data Encrypted for Impact", "Impact"),
    "T1489": Technique("T1489", "Service Stop", "Impact"),
    # ATT&CK for ICS
    "T0812": Technique("T0812", "Default Credentials", "Lateral Movement (ICS)"),
    "T0855": Technique(
        "T0855", "Unauthorized Command Message", "Impair Process Control (ICS)"
    ),
    "T0831": Technique("T0831", "Manipulation of Control", "Impact (ICS)"),
}


def lookup(technique_id: str) -> Technique | None:
    return TECHNIQUES.get(technique_id)

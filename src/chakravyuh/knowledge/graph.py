"""Neo4j-backed ATT&CK / CVE / CERT-In-style knowledge graph.

Optional upgrade over the flat lookup in ``chakravyuh.knowledge.attack``:
when ``CHAKRAVYUH_NEO4J_URI`` is set and reachable, ``AttributionAgent`` and
the RAG retrieval layer (``chakravyuh.rag``) query this graph instead of the
static dict. If Neo4j is not configured or unreachable, callers fall back
automatically — the core pipeline never requires it (see docs/PREREQUISITES.md).

Seed data uses real, publicly documented identifiers: MITRE ATT&CK technique
and mitigation IDs, and well-known CVEs. The ``Advisory`` nodes are
explicitly labelled illustrative samples written in a CERT-In-advisory
style for this project's demo RAG corpus — they are not reproductions of any
actual published CERT-In advisory.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Settings, load_settings

TACTICS: list[tuple[str, str]] = [
    ("TA0001", "Initial Access"),
    ("TA0002", "Execution"),
    ("TA0003", "Persistence"),
    ("TA0004", "Privilege Escalation"),
    ("TA0006", "Credential Access"),
    ("TA0008", "Lateral Movement"),
    ("TA0011", "Command and Control"),
    ("TA0040", "Impact"),
]

# (technique_id, name, tactic_name)
TECHNIQUES: list[tuple[str, str, str]] = [
    ("T1078", "Valid Accounts", "Initial Access"),
    ("T1190", "Exploit Public-Facing Application", "Initial Access"),
    ("T1021", "Remote Services", "Lateral Movement"),
    ("T1210", "Exploitation of Remote Services", "Lateral Movement"),
    ("T1003", "OS Credential Dumping", "Credential Access"),
    ("T1071", "Application Layer Protocol", "Command and Control"),
    ("T1486", "Data Encrypted for Impact", "Impact"),
    # ATT&CK for ICS
    ("T0812", "Default Credentials", "Lateral Movement"),
    ("T0855", "Unauthorized Command Message", "Impact"),
    ("T0831", "Manipulation of Control", "Impact"),
]

MITIGATIONS: list[tuple[str, str]] = [
    ("M1032", "Multi-factor Authentication"),
    ("M1026", "Privileged Account Management"),
    ("M1037", "Filter Network Traffic"),
]

TECHNIQUE_MITIGATIONS: list[tuple[str, str]] = [
    ("T1078", "M1032"), ("T1078", "M1026"),
    ("T1021", "M1032"),
    ("T1003", "M1026"),
    ("T1071", "M1037"),
    ("T1210", "M1037"),
]

CVES: list[dict[str, str]] = [
    {
        "id": "CVE-2020-1472", "name": "Zerologon",
        "description": (
            "Elevation-of-privilege vulnerability in the Netlogon Remote "
            "Protocol (MS-NRPC) allowing an attacker to impersonate a "
            "domain controller and reset its machine account password."
        ),
        "cvss": "10.0",
    },
    {
        "id": "CVE-2017-0144", "name": "EternalBlue",
        "description": (
            "Remote code execution in Microsoft SMBv1 (MS17-010), exploited "
            "by WannaCry and NotPetya for rapid lateral movement."
        ),
        "cvss": "8.1",
    },
    {
        "id": "CVE-2021-44228", "name": "Log4Shell",
        "description": (
            "Remote code execution in Apache Log4j2 via JNDI lookups in "
            "logged input, reachable through any public-facing service "
            "that logs attacker-controlled strings."
        ),
        "cvss": "10.0",
    },
]

CVE_TECHNIQUES: list[tuple[str, str]] = [
    ("CVE-2020-1472", "T1078"),
    ("CVE-2017-0144", "T1210"),
    ("CVE-2021-44228", "T1190"),
]

# Illustrative CERT-In-style advisories — NOT reproductions of any actual
# published CERT-In advisory. Written for this project's demo RAG corpus.
ADVISORIES: list[dict] = [
    {
        "id": "ADV-SAMPLE-001",
        "title": "Targeting of power-sector OT via default ICS credentials",
        "text": (
            "[ILLUSTRATIVE SAMPLE - not an actual published CERT-In "
            "advisory] Threat actors have been observed attempting lateral "
            "movement into OT historian and SCADA systems using default or "
            "weak vendor credentials on exposed engineering interfaces. "
            "Power-sector operators should rotate default OT credentials, "
            "segment engineering workstations from the corporate domain, "
            "and enable MFA on all remote engineering access."
        ),
        "techniques": ["T0812"],
        "cves": [],
    },
    {
        "id": "ADV-SAMPLE-002",
        "title": "Domain controller compromise via Netlogon-class vulnerability",
        "text": (
            "[ILLUSTRATIVE SAMPLE - not an actual published CERT-In "
            "advisory] Unpatched domain controllers remain vulnerable to "
            "Netlogon elevation-of-privilege exploitation, enabling an "
            "attacker who has already gained an initial IT foothold to "
            "escalate to domain-admin-equivalent access and pivot toward "
            "OT/ICS segments trusted by the domain. Patch MS-NRPC-related "
            "advisories and enforce secure Netlogon channel mode."
        ),
        "techniques": ["T1078"],
        "cves": ["CVE-2020-1472"],
    },
    {
        "id": "ADV-SAMPLE-003",
        "title": (
            "Ransomware via public-facing application exploitation "
            "in healthcare-linked infrastructure"
        ),
        "text": (
            "[ILLUSTRATIVE SAMPLE - not an actual published CERT-In "
            "advisory] Exploitation of vulnerable public-facing "
            "applications (e.g. unpatched logging libraries) has been used "
            "as an initial-access vector preceding ransomware deployment "
            "against hospital and healthcare-linked systems, with "
            "downstream impact on any critical-infrastructure loads that "
            "depend on the affected network segment."
        ),
        "techniques": ["T1190", "T1486"],
        "cves": ["CVE-2021-44228"],
    },
]


@dataclass
class TechniqueContext:
    technique_id: str
    name: str
    tactic: str
    mitigations: list[str] = field(default_factory=list)
    cves: list[dict[str, str]] = field(default_factory=list)
    advisories: list[dict[str, str]] = field(default_factory=list)


class KnowledgeGraph:
    """Thin wrapper around the Neo4j driver for the ATT&CK/CVE/advisory graph."""

    def __init__(self, uri: str, user: str, password: str) -> None:
        from neo4j import GraphDatabase

        self._driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self) -> None:
        self._driver.close()

    def verify_connectivity(self) -> bool:
        try:
            self._driver.verify_connectivity()
            return True
        except Exception:
            return False

    # -- ingestion ----------------------------------------------------------#
    def ingest_seed_data(self) -> None:
        with self._driver.session() as session:
            # Schema modifications (constraints) can't share a transaction
            # with data writes in Neo4j 5 — two transactions, not one.
            session.execute_write(self._ingest_schema_tx)
            session.execute_write(self._ingest_data_tx)

    @staticmethod
    def _ingest_schema_tx(tx) -> None:
        for label, prop in [
            ("Technique", "id"), ("Tactic", "id"), ("CVE", "id"),
            ("Advisory", "id"), ("Mitigation", "id"),
        ]:
            tx.run(
                f"CREATE CONSTRAINT {label.lower()}_{prop} IF NOT EXISTS "
                f"FOR (n:{label}) REQUIRE n.{prop} IS UNIQUE"
            )

    @staticmethod
    def _ingest_data_tx(tx) -> None:
        for tid, name in TACTICS:
            tx.run("MERGE (t:Tactic {id:$id}) SET t.name=$name", id=tid, name=name)

        tactic_id_by_name = {name: tid for tid, name in TACTICS}
        for tech_id, name, tactic_name in TECHNIQUES:
            tx.run(
                "MERGE (t:Technique {id:$id}) SET t.name=$name "
                "WITH t MATCH (ta:Tactic {id:$tactic_id}) "
                "MERGE (t)-[:PART_OF]->(ta)",
                id=tech_id, name=name, tactic_id=tactic_id_by_name[tactic_name],
            )

        for mid, name in MITIGATIONS:
            tx.run("MERGE (m:Mitigation {id:$id}) SET m.name=$name", id=mid, name=name)
        for tech_id, mid in TECHNIQUE_MITIGATIONS:
            tx.run(
                "MATCH (t:Technique {id:$tid}), (m:Mitigation {id:$mid}) "
                "MERGE (t)-[:MITIGATED_BY]->(m)", tid=tech_id, mid=mid,
            )

        for cve in CVES:
            tx.run(
                "MERGE (c:CVE {id:$id}) SET c.name=$name, "
                "c.description=$description, c.cvss=$cvss",
                **cve,
            )
        for cve_id, tech_id in CVE_TECHNIQUES:
            tx.run(
                "MATCH (c:CVE {id:$cid}), (t:Technique {id:$tid}) "
                "MERGE (c)-[:ENABLES]->(t)", cid=cve_id, tid=tech_id,
            )

        for adv in ADVISORIES:
            tx.run(
                "MERGE (a:Advisory {id:$id}) SET a.title=$title, a.text=$text",
                id=adv["id"], title=adv["title"], text=adv["text"],
            )
            for tech_id in adv["techniques"]:
                tx.run(
                    "MATCH (a:Advisory {id:$aid}), (t:Technique {id:$tid}) "
                    "MERGE (a)-[:REFERENCES]->(t)", aid=adv["id"], tid=tech_id,
                )
            for cve_id in adv["cves"]:
                tx.run(
                    "MATCH (a:Advisory {id:$aid}), (c:CVE {id:$cid}) "
                    "MERGE (a)-[:REFERENCES]->(c)", aid=adv["id"], cid=cve_id,
                )

    # -- queries --------------------------------------------------------------#
    def lookup_technique(self, technique_id: str) -> TechniqueContext | None:
        with self._driver.session() as session:
            return session.execute_read(self._lookup_tx, technique_id)

    @staticmethod
    def _lookup_tx(tx, technique_id: str) -> TechniqueContext | None:
        rec = tx.run(
            "MATCH (t:Technique {id:$id})-[:PART_OF]->(ta:Tactic) "
            "RETURN t.id AS id, t.name AS name, ta.name AS tactic",
            id=technique_id,
        ).single()
        if rec is None:
            return None
        mitigations = [
            r["name"] for r in tx.run(
                "MATCH (:Technique {id:$id})-[:MITIGATED_BY]->(m:Mitigation) "
                "RETURN m.name AS name", id=technique_id,
            )
        ]
        cves = [
            {"id": r["id"], "name": r["name"], "description": r["description"]}
            for r in tx.run(
                "MATCH (c:CVE)-[:ENABLES]->(:Technique {id:$id}) "
                "RETURN c.id AS id, c.name AS name, c.description AS description",
                id=technique_id,
            )
        ]
        advisories = [
            {"id": r["id"], "title": r["title"], "text": r["text"]}
            for r in tx.run(
                "MATCH (a:Advisory)-[:REFERENCES]->(:Technique {id:$id}) "
                "RETURN DISTINCT a.id AS id, a.title AS title, a.text AS text",
                id=technique_id,
            )
        ]
        return TechniqueContext(
            technique_id=rec["id"], name=rec["name"], tactic=rec["tactic"],
            mitigations=mitigations, cves=cves, advisories=advisories,
        )

    def all_documents(self) -> list[dict[str, str]]:
        """Flatten the graph into retrievable text chunks for RAG."""
        with self._driver.session() as session:
            return session.execute_read(self._all_documents_tx)

    @staticmethod
    def _all_documents_tx(tx) -> list[dict[str, str]]:
        docs: list[dict[str, str]] = []
        for r in tx.run(
            "MATCH (t:Technique)-[:PART_OF]->(ta:Tactic) "
            "RETURN t.id AS id, t.name AS name, ta.name AS tactic"
        ):
            docs.append({
                "source": f"ATT&CK {r['id']}",
                "text": f"{r['id']} {r['name']} ({r['tactic']}).",
            })
        for r in tx.run(
            "MATCH (c:CVE) RETURN c.id AS id, c.name AS name, "
            "c.description AS description"
        ):
            docs.append({
                "source": f"CVE {r['id']}",
                "text": f"{r['id']} ({r['name']}): {r['description']}",
            })
        for r in tx.run(
            "MATCH (a:Advisory) RETURN a.id AS id, a.title AS title, a.text AS text"
        ):
            docs.append({
                "source": f"Advisory {r['id']} - {r['title']}",
                "text": r["text"],
            })
        return docs


_cached: KnowledgeGraph | None = None


def get_graph(settings: Settings | None = None) -> KnowledgeGraph | None:
    """Return a connected, seeded ``KnowledgeGraph``, or None if Neo4j is not
    configured or unreachable. Callers must fall back to
    ``chakravyuh.knowledge.attack`` when this returns None.
    """
    global _cached
    if _cached is not None:
        return _cached
    settings = settings or load_settings()
    if not settings.neo4j_enabled:
        return None
    try:
        kg = KnowledgeGraph(
            settings.neo4j_uri, settings.neo4j_user, settings.neo4j_password
        )
        if not kg.verify_connectivity():
            return None
        kg.ingest_seed_data()
    except Exception:
        return None
    _cached = kg
    return kg


def reset_cache() -> None:
    """Testing hook: forget (and close) the cached graph connection."""
    global _cached
    if _cached is not None:
        _cached.close()
    _cached = None

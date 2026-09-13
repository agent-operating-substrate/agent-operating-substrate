"""Forensic Autopsy Engine for failure analysis and candidate rule inscription."""

from __future__ import annotations
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import yaml

from aos.blackboard import post_event
from aos.matcher import infer_language
from aos.models import Invariant, InvariantRule, Provenance, Scope
from aos.validator import validate_rule_dict


@dataclass
class AutopsyReport:
    incident_id: str
    failure_type: str
    error_trace: str
    offending_files: list[str]
    false_assumption: str
    candidate_rule: InvariantRule


def synthesize_candidate_rule(
    rule_id: str,
    statement: str,
    rationale: str,
    paths: list[str],
    languages: Optional[list[str]] = None,
    incident_id: str = "",
    inscribing_agent: str = "forensic-auditor",
    git_commit: str = "HEAD",
    enforcement: str = "reject_diff",
    max_blast_radius_lines: Optional[int] = 30,
) -> InvariantRule:
    """Construct a candidate invariant rule from autopsy findings."""
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not incident_id:
        incident_id = f"inc-{int(datetime.now(timezone.utc).timestamp())}"

    # Auto-infer languages from paths if not provided
    resolved_languages: set[str] = set(languages) if languages else set()
    if not languages:
        for p in paths:
            inferred = infer_language(p)
            if inferred:
                resolved_languages.add(inferred)

    scope = Scope(
        paths=list(paths),
        languages=sorted(resolved_languages),
    )
    invariant = Invariant(
        statement=statement,
        rationale=rationale,
        enforcement=enforcement,
        max_blast_radius_lines=max_blast_radius_lines,
    )
    provenance = Provenance(
        incident_id=incident_id,
        git_commit=git_commit,
        inscribing_agent=inscribing_agent,
        peer_consensus_agent=None,
        created_at=now_iso,
        last_verified_at=now_iso,
        trigger_count=1,
    )

    return InvariantRule(
        id=rule_id,
        version=1,
        status="candidate",
        scope=scope,
        invariant=invariant,
        provenance=provenance,
    )


def inscribe_candidate(
    rule: InvariantRule,
    substrate_dir: Path | str = ".agents/substrate",
    event_log_path: Optional[Path | str] = None,
) -> Path:
    """Save a candidate rule to disk and broadcast an AUTOPSY_RECORD event."""
    sub_path = Path(substrate_dir)
    if (sub_path / ".agents" / "substrate").is_dir():
        sub_path = sub_path / ".agents" / "substrate"

    candidate_dir = sub_path / "candidate"
    candidate_dir.mkdir(parents=True, exist_ok=True)

    rule_dict = rule.to_dict()
    is_valid, errors = validate_rule_dict(rule_dict)
    if not is_valid:
        raise ValueError(f"Candidate rule schema is invalid: {'; '.join(errors)}")

    target_file = candidate_dir / f"{rule.id}.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(rule_dict, f, sort_keys=False)

    rule.file_path = target_file

    # Broadcast autopsy record on blackboard
    post_event(
        {
            "type": "AUTOPSY_RECORD",
            "sender": rule.provenance.inscribing_agent,
            "payload": {
                "incident_id": rule.provenance.incident_id,
                "rule_id": rule.id,
                "status": "candidate",
                "statement": rule.invariant.statement,
                "target_paths": rule.scope.paths,
            },
        },
        event_log_path=event_log_path,
    )

    return target_file


def promote_candidate(
    rule_id: str,
    peer_agent: str,
    substrate_dir: Path | str = ".agents/substrate",
    event_log_path: Optional[Path | str] = None,
) -> Optional[Path]:
    """Promote a candidate rule to active status after peer review."""
    sub_path = Path(substrate_dir)
    if (sub_path / ".agents" / "substrate").is_dir():
        sub_path = sub_path / ".agents" / "substrate"

    candidate_file = sub_path / "candidate" / f"{rule_id}.yaml"
    if not candidate_file.is_file():
        return None

    with open(candidate_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    data["status"] = "active"
    if "provenance" not in data:
        data["provenance"] = {}
    data["provenance"]["peer_consensus_agent"] = peer_agent
    data["provenance"]["last_verified_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    is_valid, errors = validate_rule_dict(data)
    if not is_valid:
        raise ValueError(f"Cannot promote rule with invalid schema: {'; '.join(errors)}")

    active_dir = sub_path / "active"
    active_dir.mkdir(parents=True, exist_ok=True)
    active_file = active_dir / f"{rule_id}.yaml"

    with open(active_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    candidate_file.unlink()

    # Broadcast promotion on blackboard
    post_event(
        {
            "type": "RULE_PROMOTED",
            "sender": peer_agent,
            "payload": {
                "rule_id": rule_id,
                "promoted_to": "active",
                "statement": data.get("invariant", {}).get("statement", ""),
            },
        },
        event_log_path=event_log_path,
    )

    return active_file

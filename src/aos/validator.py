"""Schema validation for invariant rules."""

from __future__ import annotations
from datetime import datetime
from typing import Any

ALLOWED_STATUSES = {"active", "candidate", "archive"}
ALLOWED_ENFORCEMENTS = {"reject_diff", "warn", "audit"}


def _validate_iso8601(val: str) -> bool:
    try:
        normalized = val.replace("Z", "+00:00")
        datetime.fromisoformat(normalized)
        return True
    except (ValueError, TypeError):
        return False


def validate_rule_dict(raw: Any) -> tuple[bool, list[str]]:
    """Validate a raw dictionary against the invariant rule schema.

    Returns:
        tuple[bool, list[str]]: (is_valid, list of error messages)
    """
    errors: list[str] = []

    if not isinstance(raw, dict):
        return False, ["Rule payload must be a mapping: received non-dict."]

    # Check top-level required keys
    required_top = ["id", "version", "status", "scope", "invariant", "provenance"]
    for key in required_top:
        if key not in raw:
            errors.append(f"Missing required top-level field: '{key}'.")

    # id validation
    rule_id = raw.get("id")
    if not isinstance(rule_id, str) or not rule_id.strip():
        errors.append("Field 'id' must be a non-empty string.")

    # version validation
    version = raw.get("version")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        errors.append("Field 'version' must be an integer >= 1.")

    # status validation
    status = raw.get("status")
    if status not in ALLOWED_STATUSES:
        errors.append(
            f"Field 'status' must be one of {sorted(ALLOWED_STATUSES)}: got {repr(status)}."
        )

    # scope validation
    scope = raw.get("scope")
    if not isinstance(scope, dict):
        errors.append("Field 'scope' must be a dictionary.")
    else:
        paths = scope.get("paths", [])
        if not isinstance(paths, list) or not all(isinstance(p, str) for p in paths):
            errors.append("Field 'scope.paths' must be a list of strings.")
        languages = scope.get("languages", [])
        if not isinstance(languages, list) or not all(isinstance(l, str) for l in languages):
            errors.append("Field 'scope.languages' must be a list of strings.")

    # invariant validation
    invariant = raw.get("invariant")
    if not isinstance(invariant, dict):
        errors.append("Field 'invariant' must be a dictionary.")
    else:
        statement = invariant.get("statement")
        if not isinstance(statement, str) or not statement.strip():
            errors.append("Field 'invariant.statement' must be a non-empty string.")

        rationale = invariant.get("rationale")
        if not isinstance(rationale, str) or not rationale.strip():
            errors.append("Field 'invariant.rationale' must be a non-empty string.")

        enforcement = invariant.get("enforcement")
        if enforcement not in ALLOWED_ENFORCEMENTS:
            errors.append(
                f"Field 'invariant.enforcement' must be one of {sorted(ALLOWED_ENFORCEMENTS)}: got {repr(enforcement)}."
            )

        blast_radius = invariant.get("max_blast_radius_lines")
        if blast_radius is not None:
            if not isinstance(blast_radius, int) or isinstance(blast_radius, bool) or blast_radius < 0:
                errors.append("Field 'invariant.max_blast_radius_lines' must be an integer >= 0.")

    # provenance validation
    prov = raw.get("provenance")
    if not isinstance(prov, dict):
        errors.append("Field 'provenance' must be a dictionary.")
    else:
        incident_id = prov.get("incident_id")
        if not isinstance(incident_id, str) or not incident_id.strip():
            errors.append("Field 'provenance.incident_id' must be a non-empty string.")

        git_commit = prov.get("git_commit")
        if not isinstance(git_commit, str) or not git_commit.strip():
            errors.append("Field 'provenance.git_commit' must be a non-empty string.")

        inscribing_agent = prov.get("inscribing_agent")
        if not isinstance(inscribing_agent, str) or not inscribing_agent.strip():
            errors.append("Field 'provenance.inscribing_agent' must be a non-empty string.")

        peer_agent = prov.get("peer_consensus_agent")
        if peer_agent is not None and (not isinstance(peer_agent, str) or not peer_agent.strip()):
            errors.append("Field 'provenance.peer_consensus_agent' must be a string if provided.")

        created_at = prov.get("created_at")
        if not isinstance(created_at, str) or not _validate_iso8601(created_at):
            errors.append("Field 'provenance.created_at' must be a valid ISO 8601 timestamp string.")

        last_verified_at = prov.get("last_verified_at")
        if not isinstance(last_verified_at, str) or not _validate_iso8601(last_verified_at):
            errors.append("Field 'provenance.last_verified_at' must be a valid ISO 8601 timestamp string.")

        trigger_count = prov.get("trigger_count", 0)
        if not isinstance(trigger_count, int) or isinstance(trigger_count, bool) or trigger_count < 0:
            errors.append("Field 'provenance.trigger_count' must be an integer >= 0.")

    return len(errors) == 0, errors

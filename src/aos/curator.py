"""Evolutionary rule curator for pruning, subsumption, and substrate hygiene."""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import yaml

from aos.blackboard import post_event
from aos.discovery import discover_rules
from aos.models import InvariantRule, Scope
from aos.validator import validate_rule_dict


@dataclass
class CurationAction:
    rule_id: str
    action_type: str
    reason: str
    superseded_by: Optional[str] = None


def is_path_subsumed(sub_pattern: str, super_pattern: str) -> bool:
    """Check if super_pattern universally covers sub_pattern."""
    if super_pattern in ("**/*", "**", "*"):
        return True
    if sub_pattern == super_pattern:
        return True
    if super_pattern.endswith("/**") and sub_pattern.startswith(super_pattern[:-3]):
        return True
    return False


def is_scope_subsumed(sub_scope: Scope, super_scope: Scope) -> bool:
    """Determine whether sub_scope is a strict subset of super_scope."""
    # Language coverage check
    if super_scope.languages:
        if not sub_scope.languages:
            return False
        super_langs = {l.lower() for l in super_scope.languages}
        sub_langs = {l.lower() for l in sub_scope.languages}
        if not sub_langs.issubset(super_langs):
            return False

    # Path coverage check
    if super_scope.paths:
        if not sub_scope.paths:
            return False
        for sub_p in sub_scope.paths:
            covered = any(is_path_subsumed(sub_p, sup_p) for sup_p in super_scope.paths)
            if not covered:
                return False

    return True


def archive_rule(
    rule: InvariantRule,
    reason: str,
    substrate_dir: Path | str = ".agents/substrate",
    event_log_path: Optional[Path | str] = None,
) -> Path:
    """Move a rule to archive status and log a blackboard event."""
    sub_path = Path(substrate_dir)
    if (sub_path / ".agents" / "substrate").is_dir():
        sub_path = sub_path / ".agents" / "substrate"

    archive_dir = sub_path / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)

    rule_dict = rule.to_dict()
    rule_dict["status"] = "archive"
    if "provenance" not in rule_dict:
        rule_dict["provenance"] = {}
    rule_dict["provenance"]["last_verified_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    target_file = archive_dir / f"{rule.id}.yaml"
    with open(target_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(rule_dict, f, sort_keys=False)

    if rule.file_path and rule.file_path.is_file():
        rule.file_path.unlink()

    rule.file_path = target_file
    rule.status = "archive"

    post_event(
        {
            "type": "RULE_ARCHIVED",
            "sender": "evolutionary-curator-v1",
            "payload": {
                "rule_id": rule.id,
                "reason": reason,
            },
        },
        event_log_path=event_log_path,
    )

    return target_file


def curate_substrate(
    substrate_dir: Path | str = ".agents/substrate",
    dry_run: bool = False,
    event_log_path: Optional[Path | str] = None,
) -> list[CurationAction]:
    """Inspect active rules for duplicate or subsumed invariants and prune them."""
    rules, _ = discover_rules(substrate_dir, statuses={"active"})
    actions: list[CurationAction] = []

    # Sort rules deterministically by id
    rules = sorted(rules, key=lambda r: r.id)

    # Detect subsumption: Rule B has identical statement but narrower scope than Rule A
    archived_ids: set[str] = set()
    for i, r_super in enumerate(rules):
        if r_super.id in archived_ids:
            continue
        for j, r_sub in enumerate(rules):
            if i == j or r_sub.id in archived_ids:
                continue
            # Compare statements
            same_statement = r_super.invariant.statement.strip().lower() == r_sub.invariant.statement.strip().lower()
            if same_statement and is_scope_subsumed(r_sub.scope, r_super.scope):
                reason = f"Subsumed by broader rule '{r_super.id}' with identical invariant statement."
                action = CurationAction(
                    rule_id=r_sub.id,
                    action_type="ARCHIVE_SUBSUMED",
                    reason=reason,
                    superseded_by=r_super.id,
                )
                actions.append(action)
                archived_ids.add(r_sub.id)
                if not dry_run:
                    archive_rule(
                        r_sub,
                        reason=reason,
                        substrate_dir=substrate_dir,
                        event_log_path=event_log_path,
                    )

    return actions

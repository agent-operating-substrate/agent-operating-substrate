"""Tests verifying evolutionary rule curation and subsumption pruning."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import read_events
from aos.curator import curate_substrate
from aos.discovery import discover_rules


def test_subsumption_pruning(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    event_log = tmp_path / ".agents" / "blackboard" / "events.jsonl"

    # Super rule: covers **/*
    super_rule = synthesize_candidate_rule(
        rule_id="sec-super-001",
        statement="Passwords must never be logged.",
        rationale="Prevents credential exposure in syslog.",
        paths=["**/*"],
        languages=[],
    )
    inscribe_candidate(super_rule, substrate_dir=substrate_dir, event_log_path=event_log)
    promote_candidate("sec-super-001", "peer-1", substrate_dir=substrate_dir, event_log_path=event_log)

    # Sub rule: narrower path src/auth/** with identical statement
    sub_rule = synthesize_candidate_rule(
        rule_id="sec-sub-002",
        statement="Passwords must never be logged.",
        rationale="Narrower rule that is redundant.",
        paths=["src/auth/**"],
        languages=["python"],
    )
    inscribe_candidate(sub_rule, substrate_dir=substrate_dir, event_log_path=event_log)
    promote_candidate("sec-sub-002", "peer-1", substrate_dir=substrate_dir, event_log_path=event_log)

    # Both are active initially
    active_before, _ = discover_rules(substrate_dir, statuses={"active"})
    assert len(active_before) == 2

    # Execute curation
    actions = curate_substrate(substrate_dir=substrate_dir, event_log_path=event_log)
    assert len(actions) == 1
    assert actions[0].rule_id == "sec-sub-002"
    assert actions[0].action_type == "ARCHIVE_SUBSUMED"

    # Sub rule is now in archive, super rule remains active
    active_after, _ = discover_rules(substrate_dir, statuses={"active"})
    assert len(active_after) == 1
    assert active_after[0].id == "sec-super-001"

    archived, _ = discover_rules(substrate_dir, statuses={"archive"})
    assert len(archived) == 1
    assert archived[0].id == "sec-sub-002"

    # Verify blackboard archival event
    archived_events = read_events(event_log_path=event_log, event_type="RULE_ARCHIVED")
    assert len(archived_events) == 1
    assert archived_events[0].payload["rule_id"] == "sec-sub-002"

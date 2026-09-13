"""Tests verifying failure autopsy and candidate rule inscription."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import read_events
from aos.discovery import discover_rules


def test_autopsy_inscription_and_promotion(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    event_log = tmp_path / ".agents" / "blackboard" / "events.jsonl"

    candidate = synthesize_candidate_rule(
        rule_id="mem-leak-001",
        statement="All file descriptors opened in daemon loops must use context managers.",
        rationale="Unclosed handles cause EMFILE resource exhaustion under continuous monitoring.",
        paths=["src/daemon/**"],
        languages=["python"],
        incident_id="inc-fd-exhaustion",
        inscribing_agent="forensic-sentry",
    )

    # Inscribe candidate
    candidate_path = inscribe_candidate(
        candidate,
        substrate_dir=substrate_dir,
        event_log_path=event_log,
    )
    assert candidate_path.is_file()

    # Discover candidate rules
    discovered_candidates, _ = discover_rules(substrate_dir, statuses={"candidate"})
    assert len(discovered_candidates) == 1
    assert discovered_candidates[0].id == "mem-leak-001"

    # Verify blackboard event
    events = read_events(event_log_path=event_log, event_type="AUTOPSY_RECORD")
    assert len(events) == 1
    assert events[0].payload["rule_id"] == "mem-leak-001"

    # Promote to active
    active_path = promote_candidate(
        rule_id="mem-leak-001",
        peer_agent="consensus-evaluator-v1",
        substrate_dir=substrate_dir,
        event_log_path=event_log,
    )
    assert active_path is not None
    assert active_path.is_file()
    assert not candidate_path.is_file()

    # Verify discovered active rules
    discovered_active, _ = discover_rules(substrate_dir, statuses={"active"})
    assert len(discovered_active) == 1
    assert discovered_active[0].id == "mem-leak-001"
    assert discovered_active[0].provenance.peer_consensus_agent == "consensus-evaluator-v1"

    # Verify blackboard promotion event
    promoted_events = read_events(event_log_path=event_log, event_type="RULE_PROMOTED")
    assert len(promoted_events) == 1
    assert promoted_events[0].payload["rule_id"] == "mem-leak-001"

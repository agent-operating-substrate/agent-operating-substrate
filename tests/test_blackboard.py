"""Tests verifying asynchronous blackboard event bus."""

from pathlib import Path
from aos.blackboard import BlackboardEvent, post_event, read_events


def test_blackboard_post_and_read(tmp_path: Path):
    event_log = tmp_path / "events.jsonl"

    ev1 = post_event(
        {
            "type": "INTENT_ANNOUNCEMENT",
            "sender": "worker-1",
            "payload": {"task": "refactor"},
        },
        event_log_path=event_log,
    )

    ev2 = post_event(
        {
            "type": "INVARIANT_INJECTION",
            "sender": "auditor-1",
            "payload": {"rules": ["rule-1"]},
        },
        event_log_path=event_log,
    )

    all_events = read_events(event_log_path=event_log)
    assert len(all_events) == 2
    assert all_events[0].type == "INTENT_ANNOUNCEMENT"
    assert all_events[0].sender == "worker-1"
    assert all_events[1].type == "INVARIANT_INJECTION"
    assert all_events[1].sender == "auditor-1"


def test_blackboard_filtering(tmp_path: Path):
    event_log = tmp_path / "events.jsonl"

    post_event({"type": "EVENT_A", "sender": "agent-alpha"}, event_log_path=event_log)
    post_event({"type": "EVENT_B", "sender": "agent-alpha"}, event_log_path=event_log)
    post_event({"type": "EVENT_A", "sender": "agent-beta"}, event_log_path=event_log)

    only_a = read_events(event_log_path=event_log, event_type="EVENT_A")
    assert len(only_a) == 2
    assert all(e.type == "EVENT_A" for e in only_a)

    only_beta = read_events(event_log_path=event_log, sender="agent-beta")
    assert len(only_beta) == 1
    assert only_beta[0].sender == "agent-beta"

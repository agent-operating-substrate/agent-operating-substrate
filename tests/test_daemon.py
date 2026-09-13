"""Tests verifying the autonomous background daemon."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import post_event, read_events
from aos.daemon import SubstrateDaemon


def test_daemon_intercepts_intent_and_injects_invariants(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    event_log = tmp_path / ".agents" / "blackboard" / "events.jsonl"

    # Setup active rule
    rule = synthesize_candidate_rule(
        rule_id="simd-align-001",
        statement="SIMD buffers must be 32-byte aligned.",
        rationale="AVX memory fault prevention.",
        paths=["src/simd/**"],
        languages=["cpp"],
    )
    inscribe_candidate(rule, substrate_dir=substrate_dir, event_log_path=event_log)
    promote_candidate("simd-align-001", "peer-reviewer", substrate_dir=substrate_dir, event_log_path=event_log)

    # Initialize daemon
    daemon = SubstrateDaemon(root_dir=tmp_path, event_log_path=event_log, curation_interval=9999.0)

    # Worker announces intent
    post_event(
        {
            "type": "INTENT_ANNOUNCEMENT",
            "sender": "worker-agent",
            "payload": {
                "intent_id": "intent-optimize-simd",
                "description": "Refactor SIMD kernel routines",
                "target_files": ["src/simd/kernel.cpp"],
            },
        },
        event_log_path=event_log,
    )

    # Run single daemon tick
    generated = daemon.tick()
    assert len(generated) == 1
    inj = generated[0]
    assert inj.type == "INVARIANT_INJECTION"
    assert inj.sender == "daemon-auditor-agent"
    assert inj.payload["intent_id"] == "intent-optimize-simd"
    assert "simd-align-001" in inj.payload["applicable_rules"]

    # Subsequent tick must be idempotent and produce no duplicate injections
    repeat_generated = daemon.tick()
    assert len(repeat_generated) == 0

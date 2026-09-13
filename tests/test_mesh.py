"""Tests verifying multi-agent peer mesh collaboration."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.mesh import simulate_mesh_cycle


def test_peer_mesh_converged_cycle(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    event_log = tmp_path / ".agents" / "blackboard" / "events.jsonl"

    # Setup clean target file
    simd_file = tmp_path / "src" / "simd" / "kernel.cpp"
    simd_file.parent.mkdir(parents=True)
    simd_file.write_text("// clean kernel code\nint x = 0;\n", encoding="utf-8")

    # Run mesh simulation
    result = simulate_mesh_cycle(
        root_dir=tmp_path,
        intent_id="intent-test-mesh",
        target_files=["src/simd/kernel.cpp"],
        event_log_path=event_log,
    )

    assert result.status == "converged"
    types = [e.type for e in result.events]
    assert "INTENT_ANNOUNCEMENT" in types
    assert "INVARIANT_INJECTION" in types
    assert "ADVERSARIAL_CHALLENGE" in types
    assert "PEER_CRITIQUE" in types
    assert "PEER_CONVERGENCE" in types


def test_peer_mesh_rejection_cycle(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    event_log = tmp_path / ".agents" / "blackboard" / "events.jsonl"

    # Setup active rule forbidding em dashes
    rule = synthesize_candidate_rule(
        rule_id="punct-001",
        statement="Zero em dashes in all prose.",
        rationale="Punctuation invariant.",
        paths=["**/*"],
        languages=[],
    )
    inscribe_candidate(rule, substrate_dir=substrate_dir, event_log_path=event_log)
    promote_candidate("punct-001", "peer", substrate_dir=substrate_dir, event_log_path=event_log)

    # Setup offending file
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("// offending em dash \u2014 here\n", encoding="utf-8")

    result = simulate_mesh_cycle(
        root_dir=tmp_path,
        intent_id="intent-reject-mesh",
        target_files=["bad.py"],
        event_log_path=event_log,
    )

    assert result.status == "rejected"
    critiques = [e for e in result.events if e.type == "PEER_CRITIQUE"]
    assert len(critiques) == 1
    assert critiques[0].payload["verdict"] == "REJECT_DIFF"
    assert "PEER_CONVERGENCE" not in [e.type for e in result.events]

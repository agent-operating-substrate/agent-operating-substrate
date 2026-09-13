"""Tests verifying harness projection and syncing."""

from pathlib import Path
from aos.harness import format_rules_for_prompt, inject_into_file, sync_harnesses
from aos.models import InvariantRule, Scope, Invariant, Provenance


def test_format_rules_for_prompt():
    rule = InvariantRule(
        id="test-rule-001",
        version=1,
        status="active",
        scope=Scope(paths=["src/**"], languages=["python"]),
        invariant=Invariant(
            statement="No globals allowed.",
            rationale="Pollutes namespace.",
            enforcement="reject_diff",
        ),
        provenance=Provenance(
            incident_id="inc-1",
            git_commit="abc",
            inscribing_agent="tester",
            created_at="2026-09-08T18:00:00Z",
            last_verified_at="2026-09-08T18:00:00Z",
        ),
    )
    rendered = format_rules_for_prompt([rule])
    assert "Active Substrate Invariants" in rendered
    assert "[test-rule-001]" in rendered
    assert "No globals allowed." in rendered


def test_inject_into_file_preserves_surrounding_content(tmp_path: Path):
    target = tmp_path / "CLAUDE.md"
    target.write_text("# My Custom Claude Instructions\nSome personal rules.\n", encoding="utf-8")

    inject_into_file(target, "Injected rule block.")
    updated = target.read_text(encoding="utf-8")

    assert "# My Custom Claude Instructions" in updated
    assert "Injected rule block." in updated

    # Second injection replaces block without duplication
    inject_into_file(target, "Updated rule block.")
    second_updated = target.read_text(encoding="utf-8")
    assert "Updated rule block." in second_updated
    assert "Injected rule block." not in second_updated
    assert "# My Custom Claude Instructions" in second_updated

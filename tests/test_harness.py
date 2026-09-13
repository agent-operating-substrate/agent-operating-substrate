"""Tests verifying harness projection and syncing."""

from pathlib import Path
import yaml
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


def test_format_rules_with_guidance_and_lessons(tmp_path: Path):
    from aos.blackboard import post_event
    rule = InvariantRule(
        id="py-no-wildcard-import-002",
        version=1,
        status="active",
        scope=Scope(paths=["**/*.py"], languages=["python"]),
        invariant=Invariant(
            statement="Wildcard imports ('from module import *') are prohibited.",
            rationale="Pollutes module namespace.",
            enforcement="reject_diff",
        ),
        provenance=Provenance(
            incident_id="inc-wildcard",
            git_commit="HEAD",
            inscribing_agent="tester",
            created_at="2026-09-08T18:00:00Z",
            last_verified_at="2026-09-08T18:00:00Z",
        ),
    )
    post_event(
        {
            "type": "PRE_COMMIT_BLOCKED",
            "sender": "barrier",
            "payload": {
                "rule_id": "py-no-wildcard-import-002",
                "file_path": "src/bad_file.py",
                "message": "Wildcard import from os detected.",
            },
        },
        root_dir=tmp_path,
    )

    rendered = format_rules_for_prompt([rule], root_dir=tmp_path)
    assert "Compliant Pattern" in rendered
    assert "Strictly Forbidden" in rendered
    assert "Proactive Guardrail Memory: Recent Interceptions" in rendered
    assert "src/bad_file.py" in rendered


def test_sync_harnesses_universal_targets(tmp_path: Path):
    sub_dir = tmp_path / ".agents" / "substrate" / "active"
    sub_dir.mkdir(parents=True, exist_ok=True)
    rule_dict = {
        "id": "sec-credentials-001",
        "version": 1,
        "status": "active",
        "scope": {"paths": ["**/*"], "languages": ["python"]},
        "invariant": {
            "statement": "Never hardcode raw API tokens.",
            "rationale": "Security hygiene.",
            "enforcement": "reject_diff",
        },
        "provenance": {
            "incident_id": "inc-01", "git_commit": "abc", "inscribing_agent": "tester",
            "created_at": "2026-09-08T18:00:00Z", "last_verified_at": "2026-09-08T18:00:00Z",
        },
    }
    with open(sub_dir / "sec-credentials-001.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(rule_dict, f)

    targets = ["gemini", "gemini_root", "codex", "codex_root", "aider", "cline", "roo", "amazonq", "agents"]
    synced = sync_harnesses(root_dir=tmp_path, harnesses=targets)

    for t in targets:
        assert t in synced
        assert synced[t].is_file()
        content = synced[t].read_text(encoding="utf-8")
        assert "AOS_INVARIANTS_START" in content
        assert "sec-credentials-001" in content
        assert "Never hardcode raw API tokens." in content


def test_format_rules_for_prompt_tool_specific_headers():
    rule = InvariantRule(
        id="test-rule-002", version=1, status="active",
        scope=Scope(paths=["**/*"], languages=["python"]),
        invariant=Invariant(statement="No eval calls.", rationale="Security.", enforcement="reject_diff"),
        provenance=Provenance(
            incident_id="inc-2", git_commit="cde", inscribing_agent="tester",
            created_at="2026-09-08T18:00:00Z", last_verified_at="2026-09-08T18:00:00Z",
        ),
    )
    assert "# Google Gemini & Antigravity Instructions" in format_rules_for_prompt([rule], target="gemini")
    assert "# OpenAI Codex & ChatGPT Developer Instructions" in format_rules_for_prompt([rule], target="codex")
    assert "# Aider Repository Invariants & Conventions" in format_rules_for_prompt([rule], target="aider")
    assert "# Cline System Rules & Invariants" in format_rules_for_prompt([rule], target="cline")
    assert "# Roo Code System Invariants" in format_rules_for_prompt([rule], target="roo")
    assert "# Amazon Q Developer Rules" in format_rules_for_prompt([rule], target="amazonq")
    assert "# Universal Agent Operating Guidelines" in format_rules_for_prompt([rule], target="agents")
    assert "description: Machine-enforced" in format_rules_for_prompt([rule], target="cursor_mdc")

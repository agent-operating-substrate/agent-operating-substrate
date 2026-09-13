"""Tests for 1-shot repository onboarding and status inspection."""

from __future__ import annotations
from pathlib import Path
import pytest

from aos.blackboard import post_event
from aos.cli import main
from aos.harness import START_MARKER


def test_init_installs_packs_syncs_harnesses_and_installs_hook(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that aos init automatically installs packs, syncs harnesses, and installs pre-commit hook."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    # Pre-create Python indicator and existing prompt file
    (tmp_path / "main.py").write_text("print('hello world')\n", encoding="utf-8")
    (tmp_path / "CLAUDE.md").write_text(
        "# Team Guidelines\n* Must avoid raw credentials in source files.\n",
        encoding="utf-8",
    )

    exit_code = main(["init", "--root", str(tmp_path)])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "Agent Operating Substrate (AOS) Initialized" in out
    assert "Python" in out
    assert "Installed Packs:" in out
    assert "active invariants" in out
    assert "Connected AI Tools:" in out
    assert "Claude Code (CLAUDE.md)" in out
    assert "Universal Agents (AGENTS.md)" in out
    assert "Pre-Commit Hook:     Installed (.git/hooks/pre-commit) [Active]" in out
    assert "aos status" in out
    assert "aos ui" in out

    # Check active invariant rules exist
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    assert active_dir.is_dir()
    rule_files = list(active_dir.glob("*.yaml")) + list(active_dir.glob("*.yml"))
    assert len(rule_files) > 0

    # Check pre-commit hook is installed
    hook_file = git_dir / "hooks" / "pre-commit"
    assert hook_file.is_file()
    hook_content = hook_file.read_text(encoding="utf-8")
    assert "aos hook run" in hook_content

    # Check harnesses were synced
    claude_file = tmp_path / "CLAUDE.md"
    assert START_MARKER in claude_file.read_text(encoding="utf-8")
    agents_file = tmp_path / "AGENTS.md"
    assert agents_file.is_file()
    assert START_MARKER in agents_file.read_text(encoding="utf-8")


def test_init_bare_mode(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that --bare mode initializes empty substrate without installing packs or hooks."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    exit_code = main(["init", "--root", str(tmp_path), "--bare"])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "None (--bare mode)" in out
    assert "Skipped (--bare mode)" in out

    active_dir = tmp_path / ".agents" / "substrate" / "active"
    assert active_dir.is_dir()
    rule_files = list(active_dir.glob("*.yaml"))
    assert len(rule_files) == 0

    hook_file = git_dir / "hooks" / "pre-commit"
    assert not hook_file.exists()


def test_status_when_uninitialized(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that aos status outputs clean diagnostics when substrate is not yet initialized."""
    exit_code = main(["status", "--root", str(tmp_path)])
    assert exit_code == 1

    out = capsys.readouterr().out
    assert "Agent Operating Substrate (AOS) Status" in out
    assert "[OFF] Substrate not initialized" in out
    assert "Overall Health: [OFF]" in out


def test_status_when_initialized(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that aos status displays all sections with OK status indicators."""
    git_dir = tmp_path / ".git"
    git_dir.mkdir(parents=True, exist_ok=True)

    main(["init", "--root", str(tmp_path)])
    capsys.readouterr()

    exit_code = main(["status", "--root", str(tmp_path)])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "Agent Operating Substrate (AOS) Status" in out
    assert "[Substrate Core]" in out
    assert "[OK] Initialized (.agents/)" in out
    assert "[AI Agent Harnesses]" in out
    assert "[OK] Synced (AGENTS.md)" in out
    assert "[Git Integrity Barrier]" in out
    assert "[OK] Present (.git/)" in out
    assert "[OK] Installed and active (.git/hooks/pre-commit)" in out
    assert "[Blackboard & Incidents]" in out
    assert "[OK] 0 barrier incidents recorded" in out
    assert "Overall Health: [OK] Substrate operational and guardrails active." in out


def test_doctor_command_alias(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that aos doctor executes diagnostic health checks identically to aos status."""
    main(["init", "--root", str(tmp_path)])
    capsys.readouterr()

    exit_code = main(["doctor", "--root", str(tmp_path)])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "Agent Operating Substrate (AOS) Status" in out
    assert "[Substrate Core]" in out
    assert "[OK] Initialized (.agents/)" in out


def test_status_with_blackboard_incidents(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that aos status reports recent blocked commits and autopsies from blackboard."""
    main(["init", "--root", str(tmp_path)])
    capsys.readouterr()

    post_event(
        {
            "type": "PRE_COMMIT_BLOCKED",
            "sender": "git-pre-commit-barrier",
            "payload": {
                "rule_id": "sec-no-secrets-001",
                "file_path": "src/config.py",
                "message": "Hardcoded token detected",
            },
        },
        root_dir=tmp_path,
    )

    exit_code = main(["status", "--root", str(tmp_path)])
    assert exit_code == 0

    out = capsys.readouterr().out
    assert "[WARN] 1 barrier incident(s) recorded:" in out
    assert "PRE_COMMIT_BLOCKED" in out
    assert "sec-no-secrets-001" in out
    assert "src/config.py" in out

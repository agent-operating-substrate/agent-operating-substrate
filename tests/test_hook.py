"""Tests verifying universal git hook installation and lifecycle."""

from pathlib import Path
from aos.hook import install_git_hook, uninstall_git_hook


def test_git_hook_lifecycle(tmp_path: Path):
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    hook_path = install_git_hook(root_dir=tmp_path)
    assert hook_path.is_file()
    content = hook_path.read_text(encoding="utf-8")
    assert "aos hook run" in content

    # Test uninstall
    removed = uninstall_git_hook(root_dir=tmp_path)
    assert removed is True
    assert not hook_path.is_file()


def test_pre_commit_records_failure_and_syncs_harness(tmp_path: Path):
    from aos.hook import run_pre_commit_check
    from aos.packs import install_pack
    from aos.blackboard import read_events
    import aos.hook

    install_pack("python-core", root_dir=tmp_path, promote=True)

    src_file = tmp_path / "src" / "test.py"
    src_file.parent.mkdir(parents=True, exist_ok=True)
    src_file.write_text("from os import *\n", encoding="utf-8")

    orig_get_staged = aos.hook.get_staged_files
    aos.hook.get_staged_files = lambda root: ["src/test.py"]
    try:
        ret = run_pre_commit_check(root_dir=tmp_path)
        assert ret == 1

        events = read_events(root_dir=tmp_path, event_type="PRE_COMMIT_BLOCKED")
        assert len(events) >= 1
        assert events[0].payload["rule_id"] == "py-no-wildcard-import-002"

        cursor_rules = tmp_path / ".cursorrules"
        assert cursor_rules.is_file()
        prompt_content = cursor_rules.read_text(encoding="utf-8")
        assert "Proactive Guardrail Memory: Recent Interceptions" in prompt_content
        assert "py-no-wildcard-import-002" in prompt_content
    finally:
        aos.hook.get_staged_files = orig_get_staged

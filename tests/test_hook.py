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

"""Integration test demonstrating the end-to-end autonomous pair-programming loop."""

from pathlib import Path
import subprocess
from aos.cli import main
from aos.hook import run_pre_commit_check
from aos.enforcer import enforce_all, auto_fix_file
from aos.harness import sync_harnesses
from aos.packs import install_pack


def test_autonomous_interception_memory_and_remediation_loop(tmp_path: Path):
    # Step 1: Initialize substrate in temporary project directory
    ret_init = main(["--root", str(tmp_path), "init"])
    assert ret_init == 0

    # Install python-core pack
    install_pack("python-core", root_dir=tmp_path, promote=True)

    # Step 2: Sync harnesses and verify prescriptive guidance
    sync_harnesses(root_dir=tmp_path)
    claude_md = tmp_path / "CLAUDE.md"
    assert claude_md.is_file()
    prompt_text = claude_md.read_text(encoding="utf-8")
    assert "Active Substrate Invariants" in prompt_text
    assert "py-no-wildcard-import-002" in prompt_text
    assert "Compliant Pattern:" in prompt_text

    # Step 3: Simulate agent generating code with violations
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    code_file = src_dir / "service.py"
    violating_code = (
        "from os import *\n"
        "\n"
        "def run_job():\n"
        "    print('Starting background job')\n"
    )
    code_file.write_text(violating_code, encoding="utf-8")

    # Step 4: Enforcer detects violations
    violations = enforce_all(["src/service.py"], root_dir=tmp_path)
    assert len(violations) >= 1
    assert any(v.rule_id == "py-no-wildcard-import-002" for v in violations)

    # Initialize a mock git repository to test pre-commit barrier
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(["git", "add", "src/service.py"], cwd=str(tmp_path), capture_output=True, check=True)

    # Step 5: Git pre-commit barrier intercepts and rejects commit
    exit_code = run_pre_commit_check(root_dir=tmp_path)
    assert exit_code == 1

    # Step 6: Verify self-improvement loop: prompt harnesses now contain proactive memory
    updated_claude_md = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "Proactive Guardrail Memory: Recent Interceptions" in updated_claude_md
    assert "py-no-wildcard-import-002" in updated_claude_md

    # Step 7: Deterministic auto-remediation resolves violations
    fixed = auto_fix_file(code_file, root_dir=tmp_path)
    assert len(fixed) >= 1
    remediated_code = code_file.read_text(encoding="utf-8")
    assert "from os import *" not in remediated_code
    assert "import os" in remediated_code

    # Step 8: Re-evaluate and verify pre-commit passes clean
    subprocess.run(["git", "add", "src/service.py"], cwd=str(tmp_path), capture_output=True, check=True)
    clean_exit = run_pre_commit_check(root_dir=tmp_path)
    assert clean_exit == 0

"""Tests verifying autonomous execution and failure autopsy inscription."""

import sys
from pathlib import Path
from aos.discovery import discover_rules
from aos.executor import execute_and_autopsy


def test_executor_success_produces_no_autopsy(tmp_path: Path):
    cmd = [sys.executable, "-c", "print('hello world')"]
    code, autopsy_path = execute_and_autopsy(cmd, root_dir=tmp_path)
    assert code == 0
    assert autopsy_path is None


def test_executor_failure_triggers_autopsy_inscription(tmp_path: Path):
    cmd = [sys.executable, "-c", "raise RuntimeError('memory allocation failure')"]
    code, autopsy_path = execute_and_autopsy(cmd, root_dir=tmp_path)
    assert code != 0
    assert autopsy_path is not None
    assert autopsy_path.is_file()

    # Discover candidate rules
    candidates, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"candidate"})
    assert len(candidates) == 1
    assert "memory allocation failure" in candidates[0].invariant.statement

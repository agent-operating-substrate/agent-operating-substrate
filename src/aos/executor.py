"""Autonomous execution wrapper: runs commands and triggers automated failure autopsy."""

from __future__ import annotations
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

from aos.autopsy import inscribe_candidate, synthesize_candidate_rule


def execute_and_autopsy(
    command: list[str],
    root_dir: Path | str = ".",
    auto_inscribe: bool = True,
    inscribing_agent: str = "execution-sentry",
) -> tuple[int, Optional[Path]]:
    """Execute a shell command, intercept failures, and automatically synthesize candidate rules."""
    root = Path(root_dir)

    # Strip leading delimiter if passed by argument parser
    clean_cmd = list(command)
    if clean_cmd and clean_cmd[0] == "--":
        clean_cmd = clean_cmd[1:]

    if not clean_cmd:
        print("No command provided to aos exec.", file=sys.stderr)
        return 1, None

    # On Windows, resolve python executable
    if clean_cmd[0] == "python":
        clean_cmd[0] = sys.executable

    res = subprocess.run(
        clean_cmd,
        cwd=str(root),
        capture_output=True,
        text=True,
    )

    if res.stdout:
        sys.stdout.write(res.stdout)
    if res.stderr:
        sys.stderr.write(res.stderr)

    if res.returncode == 0 or not auto_inscribe:
        return res.returncode, None

    # On failure, synthesize autopsy record
    timestamp_id = int(time.time())
    rule_id = f"autopsy-fail-{timestamp_id}"
    cmd_name = Path(clean_cmd[0]).stem if clean_cmd else "process"

    # Extract salient error lines
    err_output = (res.stderr or res.stdout or "Command failed with non-zero exit.").strip()
    error_summary = err_output.splitlines()[-1] if err_output.splitlines() else err_output
    if len(error_summary) > 120:
        error_summary = error_summary[:117] + "..."

    statement = f"Operations involving '{cmd_name}' must avoid regression: {error_summary}"
    rationale = f"Automated autopsy captured non-zero exit code {res.returncode} from command: {' '.join(clean_cmd)}."

    candidate_rule = synthesize_candidate_rule(
        rule_id=rule_id,
        statement=statement,
        rationale=rationale,
        paths=["**/*"],
        languages=[],
        incident_id=f"inc-exec-{timestamp_id}",
        inscribing_agent=inscribing_agent,
    )

    candidate_path = inscribe_candidate(
        candidate_rule,
        substrate_dir=root / ".agents" / "substrate",
    )

    print(f"\nAOS AUTONOMOUS AUTOPSY INSCRIBED: {candidate_path}", file=sys.stderr)
    return res.returncode, candidate_path

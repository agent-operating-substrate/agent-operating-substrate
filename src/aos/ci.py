"""CI/CD integration engine for GitHub Actions and GitLab pipelines."""

from __future__ import annotations
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from aos.enforcer import Violation, enforce_all
from aos.harness import sync_harnesses


@dataclass
class CIReport:
    checked_files: list[str]
    violations: list[Violation]
    status: str

    def to_markdown(self) -> str:
        lines = [
            "## AOS Invariant Verification Report",
            "",
            f"**Status**: {'PASSED' if self.status == 'passed' else 'FAILED'}",
            f"**Files Evaluated**: {len(self.checked_files)}",
            f"**Violations Detected**: {len(self.violations)}",
            "",
        ]
        if not self.violations:
            lines.append("All modified files strictly comply with active substrate invariants.")
        else:
            lines.append("### Invariant Violations")
            for v in self.violations:
                loc = f":{v.line_number}" if v.line_number else ""
                lines.append(f"* **[{v.rule_id}]** `{v.file_path}{loc}`: {v.message} (`{v.enforcement}`)")
        lines.append("")
        return "\n".join(lines)


def get_git_changed_files(base_ref: str = "origin/main", root_dir: Path | str = ".") -> list[str]:
    """Retrieve list of files changed relative to base ref."""
    root = Path(root_dir)
    try:
        res = subprocess.run(
            ["git", "diff", "--name-only", "--diff-filter=ACM", f"{base_ref}...HEAD"],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
        return [f.strip() for f in res.stdout.splitlines() if f.strip()]
    except Exception:
        # Fallback to local staged or modified files
        try:
            res = subprocess.run(
                ["git", "diff", "--name-only", "--diff-filter=ACM", "HEAD"],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=True,
            )
            return [f.strip() for f in res.stdout.splitlines() if f.strip()]
        except Exception:
            return []


def run_ci_check(
    files: Optional[list[str]] = None,
    base_ref: str = "origin/main",
    auto_sync: bool = False,
    root_dir: Path | str = ".",
) -> CIReport:
    """Run comprehensive CI check, sync harnesses if requested, and write step summary."""
    root = Path(root_dir)
    target_files = files if files else get_git_changed_files(base_ref=base_ref, root_dir=root)

    if auto_sync:
        sync_harnesses(root_dir=root)

    violations = enforce_all(target_files, root_dir=root)
    reject_violations = [v for v in violations if v.enforcement == "reject_diff"]

    status = "failed" if reject_violations else "passed"
    report = CIReport(
        checked_files=target_files,
        violations=violations,
        status=status,
    )

    # Write to GITHUB_STEP_SUMMARY if available
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if summary_path:
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(report.to_markdown() + "\n")
        except Exception:
            pass

    return report

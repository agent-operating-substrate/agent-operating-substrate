"""CI/CD integration engine for GitHub Actions and GitLab pipelines."""

from __future__ import annotations
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import json
import urllib.error
import urllib.request

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

    def to_gatekeeper_markdown(self, root_dir: Path | str = ".") -> str:
        return generate_gatekeeper_markdown(self, root_dir=root_dir)


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


def review_pr_diff(diff_content: str, root_dir: Path | str = ".") -> dict[str, Any]:
    """Analyze unified git diff, evaluate against active invariants, and format PR review comments."""
    from aos.engine import RuleEngine
    from aos.enforcer import check_content_violations
    from aos.harness import get_rule_guidance

    root = Path(root_dir)
    engine = RuleEngine(root_dir=root)
    comments: list[dict[str, Any]] = []
    current_file: Optional[str] = None
    file_lines: list[str] = []

    def evaluate_file(file_path: str, lines: list[str]) -> None:
        content = "\n".join(lines)
        matched = engine.match_file(file_path, status="active")
        violations = check_content_violations(file_path, content, matched)
        for v in violations:
            rule_obj = next((r for r in matched if r.id == v.rule_id), None)
            compliant = get_rule_guidance(rule_obj)[0] if rule_obj else None
            sugg = f"\n\n**Compliant Pattern**: `{compliant}`" if compliant else ""
            comments.append({
                "file_path": v.file_path,
                "line_number": v.line_number or 1,
                "rule_id": v.rule_id,
                "message": v.message,
                "comment_body": f"### Invariant Barrier [{v.rule_id}]\n\n{v.message}{sugg}",
            })

    for line in diff_content.splitlines():
        if line.startswith("+++ b/"):
            if current_file and file_lines:
                evaluate_file(current_file, file_lines)
            current_file = line[6:].strip()
            file_lines = []
        elif current_file and line.startswith("+") and not line.startswith("+++"):
            file_lines.append(line[1:])

    if current_file and file_lines:
        evaluate_file(current_file, file_lines)

    return {
        "status": "changes_requested" if comments else "approved",
        "comments_count": len(comments),
        "comments": comments,
    }


AOS_GATEKEEPER_MARKER = "<!-- AOS_GATEKEEPER_COMMENT -->"


def get_violation_guidance(v: Violation, root_dir: Path | str = ".") -> str:
    """Determine prescriptive guidance for an invariant violation."""
    try:
        from aos.engine import RuleEngine
        from aos.harness import get_rule_guidance
        engine = RuleEngine(root_dir=root_dir)
        rule = next((r for r in engine.discover_rules() if r.id == v.rule_id), None)
        if rule:
            compliant, _ = get_rule_guidance(rule)
            if compliant:
                return compliant
    except Exception:
        pass

    rid = v.rule_id.lower()
    msg = v.message.lower()
    stmt = (v.statement or "").lower()
    comb = f"{rid} {msg} {stmt}"
    if "wildcard" in comb:
        return "import specific_module or from module import specific_symbol"
    if "secret" in comb or "api key" in comb or "token" in comb or "password" in comb:
        return "os.environ.get('API_KEY') or pass via secure configuration"
    if "print" in comb or "logging" in comb:
        return "logger = logging.getLogger(__name__); logger.info(...)"
    if "bare-except" in comb or "bare except" in comb:
        return "except SpecificException as exc: logger.warning('...', exc_info=exc)"
    if "async" in comb and ("blocking" in comb or "sleep" in comb):
        return "await asyncio.sleep(...) or run blocking calls in worker threads"
    if "any" in comb or "explicit 'any'" in comb:
        return "use unknown, generics, or an explicit interface/type"
    if "floating-promise" in comb:
        return "await asyncCall(), void asyncCall(), or asyncCall().catch(...)"
    if "unsafe" in comb:
        return "add preceding '// SAFETY: explanation of memory invariants' comment"
    if "error-wrap" in comb or "%w" in comb:
        return 'fmt.Errorf("context message: %w", err)'
    if "punct" in comb or "em dash" in comb or "em-dash" in comb:
        return "use colons, commas, semicolons, parentheses, or separate sentences"
    if "blast-radius" in comb or "blast radius" in comb or "surgical" in comb:
        return "keep diffs surgical and focused strictly on the assigned task"
    if v.statement:
        return v.statement
    return f"Run `aos enforce --fix {v.file_path}`"


def generate_gatekeeper_markdown(report: CIReport, root_dir: Path | str = ".") -> str:
    """Generate sticky PR comment markdown for CI gatekeeper evaluation."""
    lines: list[str] = [AOS_GATEKEEPER_MARKER]
    if report.status == "passed" and not report.violations:
        lines.extend([
            "## 🛡️ AOS Guardrails Gatekeeper: Passed",
            "",
            "![AOS Gatekeeper](https://img.shields.io/badge/AOS_Gatekeeper-Passed-brightgreen)",
            "",
            "All modified files strictly comply with machine-enforced invariants.",
            "",
            "| Metric | Result |",
            "| :--- | :--- |",
            "| **Status** | Passed |",
            f"| **Files Evaluated** | {len(report.checked_files)} |",
            "| **Violations Detected** | 0 |",
            "",
        ])
    else:
        lines.extend([
            "## 🛡️ AOS Guardrails Gatekeeper: Invariant Violations Detected",
            "",
            "![AOS Gatekeeper](https://img.shields.io/badge/AOS_Gatekeeper-Failed-red)",
            "",
            f"The Gatekeeper detected {len(report.violations)} invariant violation(s) across {len(report.checked_files)} evaluated file(s).",
            "",
            "| Severity | Rule ID | File | Line | Message | Remediation Guidance |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])
        for v in report.violations:
            loc = str(v.line_number) if v.line_number else "-"
            guidance = get_violation_guidance(v, root_dir=root_dir)
            msg = v.message.replace("|", "\\|").strip()
            guidance_clean = guidance.replace("|", "\\|").strip()
            lines.append(f"| `{v.enforcement}` | `{v.rule_id}` | `{v.file_path}` | {loc} | {msg} | {guidance_clean} |")

        lines.extend([
            "",
            "> **Remediation Tip**: Run `aos enforce --fix <file>` locally to automatically remediate safe invariant violations.",
            "",
        ])

    return "\n".join(lines)


format_gatekeeper_comment = generate_gatekeeper_markdown


def post_pr_comment(
    report: CIReport,
    pr_number: Optional[int] = None,
    token: Optional[str] = None,
    repo: Optional[str] = None,
    api_url: Optional[str] = None,
    root_dir: Path | str = ".",
) -> bool:
    """Post or update sticky PR comment with gatekeeper verification results."""
    token = token or os.environ.get("GITHUB_TOKEN")
    if not token:
        return False

    repo = repo or os.environ.get("GITHUB_REPOSITORY")
    if not repo:
        return False

    if pr_number is None:
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        if event_path and Path(event_path).is_file():
            try:
                with open(event_path, "r", encoding="utf-8") as f:
                    event_data = json.load(f)
                if isinstance(event_data, dict):
                    pr_obj = event_data.get("pull_request")
                    if isinstance(pr_obj, dict) and "number" in pr_obj:
                        pr_number = pr_obj["number"]
                    elif "issue" in event_data and isinstance(event_data["issue"], dict) and "number" in event_data["issue"]:
                        pr_number = event_data["issue"]["number"]
                    elif "number" in event_data:
                        pr_number = event_data["number"]
            except Exception:
                pass

    if pr_number is None:
        return False

    api_base = (api_url or os.environ.get("GITHUB_API_URL", "https://api.github.com")).rstrip("/")
    comment_body = generate_gatekeeper_markdown(report, root_dir=root_dir)

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "AOS-Gatekeeper",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    try:
        comments_url = f"{api_base}/repos/{repo}/issues/{pr_number}/comments"
        req_list = urllib.request.Request(comments_url, headers=headers, method="GET")
        with urllib.request.urlopen(req_list) as resp:
            comments_data = json.loads(resp.read().decode("utf-8"))

        existing_id: Optional[int] = None
        if isinstance(comments_data, list):
            for c in comments_data:
                if isinstance(c, dict) and AOS_GATEKEEPER_MARKER in c.get("body", ""):
                    existing_id = c.get("id")
                    break

        post_headers = dict(headers)
        post_headers["Content-Type"] = "application/json"
        payload = json.dumps({"body": comment_body}).encode("utf-8")

        if existing_id is not None:
            patch_url = f"{api_base}/repos/{repo}/issues/comments/{existing_id}"
            req_patch = urllib.request.Request(patch_url, data=payload, headers=post_headers, method="PATCH")
            with urllib.request.urlopen(req_patch) as resp:
                return resp.status in (200, 201)
        else:
            req_post = urllib.request.Request(comments_url, data=payload, headers=post_headers, method="POST")
            with urllib.request.urlopen(req_post) as resp:
                return resp.status in (200, 201)
    except Exception:
        return False


def run_gatekeeper(
    base_ref: str = "origin/main",
    post_comment: bool = True,
    fail_on_violation: bool = True,
    root_dir: Path | str = ".",
    pr_number: Optional[int] = None,
    token: Optional[str] = None,
    repo: Optional[str] = None,
    api_url: Optional[str] = None,
) -> int:
    """Execute CI check, post sticky comment, and return gatekeeper exit code."""
    root = Path(root_dir)
    report = run_ci_check(base_ref=base_ref, root_dir=root)

    if post_comment:
        post_pr_comment(
            report=report,
            pr_number=pr_number,
            token=token,
            repo=repo,
            api_url=api_url,
            root_dir=root,
        )

    has_violations = report.status != "passed" or bool(report.violations)
    if has_violations and fail_on_violation:
        return 1
    return 0


DEFAULT_GITHUB_WORKFLOW = """name: AOS Guardrails

on:
  pull_request:
    branches: [ master, main ]
  push:
    branches: [ master, main ]

permissions:
  pull-requests: write
  contents: read

jobs:
  verify-invariants:
    name: Verify Substrate Invariants
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install AOS
        run: |
          python -m pip install --upgrade pip
          pip install -e .

      - name: Verify Invariants
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          python -m aos ci run --auto-sync --comment
"""


def install_ci_workflow(root_dir: Path | str = ".") -> Path:
    """Install GitHub Actions workflow in .github/workflows/aos-guardrails.yml."""
    root = Path(root_dir)
    wf_dir = root / ".github" / "workflows"
    wf_dir.mkdir(parents=True, exist_ok=True)
    target = wf_dir / "aos-guardrails.yml"
    target.write_text(DEFAULT_GITHUB_WORKFLOW, encoding="utf-8")
    return target


def uninstall_ci_workflow(root_dir: Path | str = ".") -> bool:
    """Remove GitHub Actions workflow if installed."""
    target = Path(root_dir) / ".github" / "workflows" / "aos-guardrails.yml"
    if target.is_file():
        target.unlink()
        return True
    return False


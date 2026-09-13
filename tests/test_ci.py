"""Tests verifying CI/CD runner and step summary reporting."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.ci import CIReport, run_ci_check


def test_ci_report_markdown():
    report = CIReport(
        checked_files=["src/test.py"],
        violations=[],
        status="passed",
    )
    md = report.to_markdown()
    assert "PASSED" in md
    assert "**Files Evaluated**: 1" in md
    assert "**Violations Detected**: 0" in md


def test_ci_check_with_files(tmp_path: Path):
    substrate_dir = tmp_path / ".agents" / "substrate"
    rule = synthesize_candidate_rule(
        rule_id="punct-001",
        statement="Zero em dashes in all prose.",
        rationale="Punctuation invariant.",
        paths=["**/*"],
        languages=[],
    )
    inscribe_candidate(rule, substrate_dir=substrate_dir)
    promote_candidate("punct-001", "peer", substrate_dir=substrate_dir)

    # Clean file passes
    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 42\n", encoding="utf-8")

    report = run_ci_check(files=["clean.py"], root_dir=tmp_path)
    assert report.status == "passed"
    assert len(report.violations) == 0

    # Violating file fails
    bad_file = tmp_path / "bad.py"
    bad_file.write_text("# bad line \u2014 em dash\n", encoding="utf-8")

    report_bad = run_ci_check(files=["bad.py"], root_dir=tmp_path)
    assert report_bad.status == "failed"
    assert len(report_bad.violations) == 1


def test_review_pr_diff(tmp_path: Path):
    from aos.ci import review_pr_diff
    from aos.packs import install_pack

    install_pack("python-core", root_dir=tmp_path, promote=True)

    diff = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -1,3 +1,4 @@
+from os import *
+def compute():
+    print("logging output")
"""
    result = review_pr_diff(diff, root_dir=tmp_path)
    assert result["status"] == "changes_requested"
    assert result["comments_count"] >= 1
    assert any("py-no-wildcard-import-002" in c["rule_id"] for c in result["comments"])
    assert any("Compliant Pattern" in c["comment_body"] for c in result["comments"])

"""Tests verifying deterministic invariant enforcement."""

from pathlib import Path
from aos.enforcer import check_file_violations, enforce_all
from aos.engine import RuleEngine


def test_enforcer_detects_em_dash_violation(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)

    rule_file = active_dir / "punct-rule.yaml"
    rule_file.write_text(
        """
id: "aos-punct-001"
version: 1
status: "active"
scope:
  paths: ["**/*"]
  languages: []
invariant:
  statement: "Zero em dashes in all prose."
  rationale: "Clean punctuation."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-1"
  git_commit: "abc"
  inscribing_agent: "tester"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    bad_file = tmp_path / "bad.py"
    # Write line containing an em dash \u2014
    bad_file.write_text("# This line has an em dash \u2014 here\nx = 1\n", encoding="utf-8")

    good_file = tmp_path / "good.py"
    good_file.write_text("# This line has a colon: here\nx = 1\n", encoding="utf-8")

    violations_bad = check_file_violations(bad_file, root_dir=tmp_path)
    assert len(violations_bad) == 1
    assert violations_bad[0].rule_id == "aos-punct-001"
    assert violations_bad[0].line_number == 1
    assert violations_bad[0].enforcement == "reject_diff"

    violations_good = check_file_violations(good_file, root_dir=tmp_path)
    assert len(violations_good) == 0


def test_enforcer_detects_secrets_and_sqli(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    sec_rule = active_dir / "sec-rule.yaml"
    sec_rule.write_text(
        """
id: "sec-secrets-001"
version: 1
status: "active"
scope:
  paths: ["**/*"]
invariant:
  statement: "Never commit secrets or api keys."
  rationale: "Prevents credential theft."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-sec"
  git_commit: "abc1"
  inscribing_agent: "tester"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    leak_file = tmp_path / "leak.py"
    leak_file.write_text('api_key = "sk-1234567890abcdef1234567890abcdef"\n', encoding="utf-8")

    violations = check_file_violations(leak_file, root_dir=tmp_path)
    assert len(violations) >= 1
    assert violations[0].rule_id == "sec-secrets-001"
    assert "secret" in violations[0].message.lower()


def test_enforcer_detects_wildcards_and_blast_radius(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    arch_rule = active_dir / "arch-rule.yaml"
    arch_rule.write_text(
        """
id: "py-no-wildcard"
version: 1
status: "active"
scope:
  paths: ["**/*"]
invariant:
  statement: "Wildcard imports are prohibited."
  rationale: "Namespace cleanliness."
  enforcement: "reject_diff"
  max_blast_radius_lines: 5
provenance:
  incident_id: "inc-arch"
  git_commit: "abc2"
  inscribing_agent: "tester"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    wc_file = tmp_path / "wc.py"
    wc_file.write_text("from math import *\n", encoding="utf-8")
    violations_wc = check_file_violations(wc_file, root_dir=tmp_path)
    assert any(v.rule_id == "py-no-wildcard" and "wildcard" in v.message.lower() for v in violations_wc)

    large_file = tmp_path / "large.py"
    large_file.write_text("\n".join([f"x_{i} = {i}" for i in range(10)]), encoding="utf-8")
    violations_large = check_file_violations(large_file, root_dir=tmp_path)
    assert any("blast radius" in v.message.lower() for v in violations_large)


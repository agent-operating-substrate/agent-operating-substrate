"""Tests verifying rule discovery and engine functionality."""

import pytest
from pathlib import Path
from aos.discovery import discover_rules, load_rule_file
from aos.engine import RuleEngine


def test_discover_canonical_active_rule(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)
    rule_file = active_dir / "perf-001.yaml"
    rule_file.write_text(
        """
id: "perf-001"
version: 1
status: "active"
scope:
  paths: ["src/perf/**"]
  languages: ["python"]
invariant:
  statement: "Do not use blocking I/O in worker loops."
  rationale: "Causes event loop starvation."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-1"
  git_commit: "deadbeef"
  inscribing_agent: "agent-1"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
  trigger_count: 0
""",
        encoding="utf-8",
    )

    rules, diagnostics = discover_rules(tmp_path)
    assert len(diagnostics) == 0
    assert len(rules) == 1
    assert rules[0].id == "perf-001"
    assert rules[0].status == "active"


def test_discovery_handles_corrupt_yaml(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)
    bad_file = active_dir / "bad.yaml"
    bad_file.write_text("invalid: yaml: [unclosed", encoding="utf-8")

    good_file = active_dir / "good.yaml"
    good_file.write_text(
        """
id: "good-001"
version: 1
status: "active"
scope:
  paths: []
  languages: []
invariant:
  statement: "Valid statement."
  rationale: "Valid rationale."
  enforcement: "warn"
provenance:
  incident_id: "inc-2"
  git_commit: "123456"
  inscribing_agent: "agent-2"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    rules, diagnostics = discover_rules(tmp_path)
    # The valid rule should still be discovered
    assert len(rules) == 1
    assert rules[0].id == "good-001"
    # Diagnostics must record the corrupt file error
    assert len(diagnostics) >= 1
    assert any("bad.yaml" in d for d in diagnostics)


def test_rule_engine_integration(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)
    rule_file = active_dir / "sec-001.yaml"
    rule_file.write_text(
        """
id: "sec-001"
version: 1
status: "active"
scope:
  paths: ["src/auth/**"]
  languages: ["python"]
invariant:
  statement: "Password hashes must use argon2id."
  rationale: "SHA256 is vulnerable to GPU attacks."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-auth-1"
  git_commit: "abcdef"
  inscribing_agent: "security-agent"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    engine = RuleEngine(root_dir=tmp_path)
    matches = engine.match_file("src/auth/login.py")
    assert len(matches) == 1
    assert matches[0].id == "sec-001"

    no_matches = engine.match_file("src/utils/math.py")
    assert len(no_matches) == 0

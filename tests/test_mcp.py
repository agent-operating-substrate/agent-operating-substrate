"""Tests verifying Model Context Protocol (MCP) server handlers."""

import json
from pathlib import Path
from aos.mcp import get_tool_definitions, handle_tool_call


def test_mcp_tool_definitions():
    tools = get_tool_definitions()
    names = {t["name"] for t in tools}
    assert "aos_rules_check" in names
    assert "aos_rules_list" in names
    assert "aos_autopsy" in names
    assert "aos_blackboard_post" in names


def test_mcp_handle_rules_list(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)
    rule_file = active_dir / "rule-mcp.yaml"
    rule_file.write_text(
        """
id: "mcp-001"
version: 1
status: "active"
scope:
  paths: ["**/*"]
  languages: []
invariant:
  statement: "Sample MCP rule."
  rationale: "Tested."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-mcp"
  git_commit: "abc"
  inscribing_agent: "mcp-test"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    res_str = handle_tool_call("aos_rules_list", {"status": "active"}, tmp_path)
    data = json.loads(res_str)
    assert len(data) == 1
    assert data[0]["id"] == "mcp-001"


def test_mcp_handle_rules_check(tmp_path: Path):
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True)
    rule_file = active_dir / "rule-mcp.yaml"
    rule_file.write_text(
        """
id: "mcp-check-001"
version: 1
status: "active"
scope:
  paths: ["src/simd/**"]
  languages: ["cpp"]
invariant:
  statement: "Align buffer."
  rationale: "AVX requirement."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-mcp"
  git_commit: "abc"
  inscribing_agent: "mcp-test"
  created_at: "2026-09-08T18:00:00Z"
  last_verified_at: "2026-09-08T18:00:00Z"
""",
        encoding="utf-8",
    )

    res_str = handle_tool_call("aos_rules_check", {"files": ["src/simd/kernel.cpp"]}, tmp_path)
    data = json.loads(res_str)
    assert "src/simd/kernel.cpp" in data["matches"]
    assert len(data["matches"]["src/simd/kernel.cpp"]) == 1
    assert data["matches"]["src/simd/kernel.cpp"][0]["id"] == "mcp-check-001"

"""Tests verifying curated invariant rule packs."""

from pathlib import Path
from aos.discovery import discover_rules
from aos.packs import install_pack, list_available_packs


def test_list_packs():
    packs = list_available_packs()
    assert "security-owasp" in packs
    assert "python-clean-architecture" in packs
    assert "performance-simd" in packs
    assert packs["security-owasp"] >= 2


def test_install_pack(tmp_path: Path):
    installed = install_pack("security-owasp", root_dir=tmp_path, promote=True)
    assert len(installed) >= 2
    assert all(p.is_file() for p in installed)

    active_rules, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"active"})
    rule_ids = {r.id for r in active_rules}
    assert "sec-sql-injection-001" in rule_ids
    assert "sec-secret-leak-002" in rule_ids

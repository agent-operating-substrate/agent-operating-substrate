"""Tests verifying curated invariant rule packs."""

from pathlib import Path
from aos.discovery import discover_rules
from aos.packs import install_pack, list_available_packs


def test_list_packs():
    packs = list_available_packs()
    assert "security-core" in packs
    assert "python-core" in packs
    assert "typescript-core" in packs
    assert "general-hygiene" in packs
    assert "rust-core" in packs
    assert "go-core" in packs
    assert packs["security-core"] == 4
    assert packs["python-core"] == 4
    assert packs["typescript-core"] == 4
    assert packs["general-hygiene"] == 3


def test_install_pack(tmp_path: Path):
    installed = install_pack("security-core", root_dir=tmp_path, promote=True)
    assert len(installed) == 4
    assert all(p.is_file() for p in installed)

    active_rules, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"active"})
    rule_ids = {r.id for r in active_rules}
    assert "sec-sql-injection-001" in rule_ids
    assert "sec-no-secrets-001" in rule_ids

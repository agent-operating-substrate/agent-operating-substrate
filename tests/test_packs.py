"""Tests verifying curated invariant rule packs."""

from pathlib import Path
from aos.discovery import discover_rules
from aos.packs import install_pack, list_available_packs, uninstall_pack


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


def test_uninstall_pack(tmp_path: Path):
    install_pack("security-core", root_dir=tmp_path, promote=True)
    active_before, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"active"})
    assert len(active_before) == 4

    uninstalled = uninstall_pack("security-core", root_dir=tmp_path, archive=True)
    assert len(uninstalled) == 4
    assert all(p.is_file() for p in uninstalled)

    active_after, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"active"})
    assert len(active_after) == 0

    archived, _ = discover_rules(tmp_path / ".agents" / "substrate", statuses={"archive"})
    assert len(archived) == 4


def test_recommend_packs(tmp_path: Path):
    from aos.packs import recommend_packs
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text("{}", encoding="utf-8")

    recommended = recommend_packs(tmp_path)
    assert "security-core" in recommended
    assert "general-hygiene" in recommended
    assert "python-core" in recommended
    assert "typescript-core" in recommended

"""Tests verifying enterprise cross-repository fleet synchronization."""

from pathlib import Path
from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.cli import main
from aos.engine import RuleEngine
from aos.fleet import (
    export_fleet_bundle,
    import_fleet_bundle,
    list_fleet_rules,
    publish_to_fleet,
    sync_from_fleet,
)


def test_cross_repo_fleet_sync(tmp_path: Path):
    fleet_db = tmp_path / "enterprise_fleet.db"
    repo_a = tmp_path / "repo_a"
    repo_b = tmp_path / "repo_b"

    # Setup Repo A with an active invariant
    sub_a = repo_a / ".agents" / "substrate"
    rule = synthesize_candidate_rule(
        rule_id="org-sec-001",
        statement="All database credentials must use AWS Secrets Manager.",
        rationale="Prevents plaintext credential leakage in config files.",
        paths=["config/**"],
        languages=["yaml", "json"],
    )
    inscribe_candidate(rule, substrate_dir=sub_a)
    promote_candidate("org-sec-001", "sec-team", substrate_dir=sub_a)

    # Publish rule from Repo A to Fleet Ledger
    published = publish_to_fleet(
        rule_id="org-sec-001",
        repo_root=repo_a,
        origin_repo_id="service-billing",
        fleet_db_path=fleet_db,
    )
    assert published is True

    # Check fleet ledger listing
    fleet_rules = list_fleet_rules(fleet_db_path=fleet_db)
    assert len(fleet_rules) == 1
    assert fleet_rules[0]["id"] == "org-sec-001"
    assert fleet_rules[0]["origin_repo"] == "service-billing"

    # Sync into empty Repo B
    synced = sync_from_fleet(repo_root=repo_b, fleet_db_path=fleet_db)
    assert synced == 1

    # Verify Repo B rule engine discovers and enforces the rule
    engine_b = RuleEngine(root_dir=repo_b)
    matches_b = engine_b.match_file("config/database.yaml")
    assert len(matches_b) == 1
    assert matches_b[0].id == "org-sec-001"
    assert "AWS Secrets Manager" in matches_b[0].invariant.statement


def test_fleet_bundle_export_and_import(tmp_path: Path):
    fleet_db_1 = tmp_path / "fleet_1.db"
    fleet_db_2 = tmp_path / "fleet_2.db"
    bundle_path = tmp_path / "bundle.json"
    repo = tmp_path / "repo"

    sub = repo / ".agents" / "substrate"
    rule = synthesize_candidate_rule(
        rule_id="corp-zero-trust-01",
        statement="Zero trust network calls only.",
        rationale="Prevents lateral movement.",
        paths=["services/**"],
    )
    inscribe_candidate(rule, substrate_dir=sub)
    promote_candidate("corp-zero-trust-01", "sec-lead", substrate_dir=sub)

    publish_to_fleet("corp-zero-trust-01", repo_root=repo, origin_repo_id="auth-srv", fleet_db_path=fleet_db_1)

    # Export bundle
    exported = export_fleet_bundle(fleet_db_path=fleet_db_1, output_path=bundle_path)
    assert exported == 1
    assert bundle_path.is_file()

    # Import bundle into fresh database
    imported = import_fleet_bundle(bundle_path=bundle_path, fleet_db_path=fleet_db_2)
    assert imported == 1

    # Verify listing in fresh database
    rules_2 = list_fleet_rules(fleet_db_path=fleet_db_2)
    assert len(rules_2) == 1
    assert rules_2[0]["id"] == "corp-zero-trust-01"


def test_cli_fleet_export_import(tmp_path: Path, capsys):
    fleet_db = tmp_path / "fleet.db"
    bundle_path = tmp_path / "bundle.json"
    repo = tmp_path / "repo"

    sub = repo / ".agents" / "substrate"
    rule = synthesize_candidate_rule(
        rule_id="cli-rule-01",
        statement="Audit all user actions.",
        rationale="SOC2 requirement.",
        paths=["src/**"],
    )
    inscribe_candidate(rule, substrate_dir=sub)
    promote_candidate("cli-rule-01", "sec-auditor", substrate_dir=sub)

    # Publish via CLI
    exit_pub = main(["--root", str(repo), "fleet", "publish", "cli-rule-01", "--db", str(fleet_db)])
    assert exit_pub == 0

    # Export via CLI
    exit_exp = main(["fleet", "export", "--db", str(fleet_db), "--output", str(bundle_path)])
    assert exit_exp == 0
    assert bundle_path.is_file()

    # Import via CLI into new db
    fleet_db_new = tmp_path / "fleet_new.db"
    exit_imp = main(["fleet", "import", str(bundle_path), "--db", str(fleet_db_new)])
    assert exit_imp == 0

    captured = capsys.readouterr().out
    assert "Imported 1 rule(s)" in captured



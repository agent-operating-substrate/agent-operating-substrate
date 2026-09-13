"""Unit and integration tests for repository ingestion and convention extraction."""

from __future__ import annotations
import json
from pathlib import Path

from aos.cli import main
from aos.ingest import scan_repository_conventions, ingest_repository


def test_scan_empty_repo(tmp_path: Path):
    report = scan_repository_conventions(tmp_path)
    assert report.detected_languages == []
    assert report.detected_frameworks == []
    assert report.scanned_config_files == []
    assert report.existing_instruction_files == []
    assert report.synthesized_rules == []


def test_scan_typescript_react_repo(tmp_path: Path):
    tsconfig = tmp_path / "tsconfig.json"
    tsconfig.write_text(
        json.dumps({"compilerOptions": {"strict": True, "target": "es2022"}}),
        encoding="utf-8",
    )
    pkg = tmp_path / "package.json"
    pkg.write_text(
        json.dumps({
            "name": "sample-web",
            "dependencies": {"react": "^18.2.0", "next": "^14.0.0"},
        }),
        encoding="utf-8",
    )

    report = scan_repository_conventions(tmp_path)
    assert "typescript" in report.detected_languages
    assert "javascript" in report.detected_languages
    assert "react" in report.detected_frameworks
    assert "nextjs" in report.detected_frameworks

    rule_ids = [r["id"] for r in report.synthesized_rules]
    assert "ts-strict-typing" in rule_ids
    assert "react-hooks-deps" in rule_ids
    assert "nextjs-client-boundary" in rule_ids


def test_scan_python_fastapi_repo(tmp_path: Path):
    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[project]
name = "api-service"
dependencies = [
    "fastapi>=0.100.0",
    "uvicorn>=0.23.0",
]
""",
        encoding="utf-8",
    )

    report = scan_repository_conventions(tmp_path)
    assert "python" in report.detected_languages
    assert "fastapi" in report.detected_frameworks

    rule_ids = [r["id"] for r in report.synthesized_rules]
    assert "fastapi-pydantic-schemas" in rule_ids


def test_scan_rust_and_go_repos(tmp_path: Path):
    rust_dir = tmp_path / "rust_proj"
    rust_dir.mkdir()
    (rust_dir / "Cargo.toml").write_text('[package]\nname = "my-crate"\n', encoding="utf-8")

    rust_report = scan_repository_conventions(rust_dir)
    assert "rust" in rust_report.detected_languages
    assert any(r["id"] == "rust-unsafe-audit" for r in rust_report.synthesized_rules)

    go_dir = tmp_path / "go_proj"
    go_dir.mkdir()
    (go_dir / "go.mod").write_text("module example.com/service\n\ngo 1.22\n", encoding="utf-8")

    go_report = scan_repository_conventions(go_dir)
    assert "go" in go_report.detected_languages
    assert any(r["id"] == "go-error-wrapping" for r in go_report.synthesized_rules)


def test_scan_team_instruction_files(tmp_path: Path):
    claude_md = tmp_path / "CLAUDE.md"
    claude_md.write_text(
        """# Project Guidelines

<!-- AOS_INVARIANTS_START -->
- Old invariant rule to ignore
<!-- AOS_INVARIANTS_END -->

- Never log customer passwords or credit card numbers in plaintext.
- Always validate incoming webhook signatures before processing events.
""",
        encoding="utf-8",
    )

    report = scan_repository_conventions(tmp_path)
    assert "CLAUDE.md" in report.existing_instruction_files
    statements = [r["statement"] for r in report.synthesized_rules]
    assert any("passwords" in s.lower() for s in statements)
    assert any("webhook" in s.lower() for s in statements)
    assert not any("old invariant rule" in s.lower() for s in statements)


def test_ingest_repository_candidate_and_promote(tmp_path: Path):
    cargo = tmp_path / "Cargo.toml"
    cargo.write_text('[package]\nname = "substrate-test"\n', encoding="utf-8")

    # Ingest without promotion: writes to candidate/
    report_cand = ingest_repository(tmp_path, auto_promote=False)
    assert len(report_cand.synthesized_rules) >= 1
    cand_file = tmp_path / ".agents" / "substrate" / "candidate" / "rust-unsafe-audit.yaml"
    assert cand_file.is_file()

    # Ingest with promotion: writes to active/
    report_prom = ingest_repository(tmp_path, auto_promote=True)
    active_file = tmp_path / ".agents" / "substrate" / "active" / "rust-unsafe-audit.yaml"
    assert active_file.is_file()

    # Verify blackboard event
    events_file = tmp_path / ".agents" / "blackboard" / "events.jsonl"
    assert events_file.is_file()
    events_text = events_file.read_text(encoding="utf-8")
    assert "REPO_INGESTED" in events_text


def test_cli_ingest_command(tmp_path: Path, monkeypatch, capsys):
    (tmp_path / "Cargo.toml").write_text('[package]\nname = "cli-crate"\n', encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    # Dry run
    exit_dry = main(["ingest", "--dry-run"])
    assert exit_dry == 0
    captured_dry = capsys.readouterr().out
    assert "Detected languages: rust" in captured_dry
    assert "Proposed" in captured_dry

    # Promote run
    exit_prom = main(["ingest", "--promote"])
    assert exit_prom == 0
    captured_prom = capsys.readouterr().out
    assert "Ingested" in captured_prom
    assert "as active:" in captured_prom


def test_ingest_with_recommended_packs(tmp_path: Path):
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'test'\n", encoding="utf-8")
    report = ingest_repository(tmp_path, auto_promote=True, install_recommended_packs=True)
    assert "python-core" in report.recommended_packs

    active_dir = tmp_path / ".agents" / "substrate" / "active"
    assert (active_dir / "py-no-wildcard-import-002.yaml").is_file()
    assert (active_dir / "sec-no-secrets-001.yaml").is_file()


def test_zero_em_dashes_in_ingest_files():
    ingest_code = Path("src/aos/ingest.py").read_text(encoding="utf-8")
    test_code = Path("tests/test_ingest.py").read_text(encoding="utf-8")
    assert "\u2014" not in ingest_code, "Em dash found in src/aos/ingest.py"
    assert "\u2013" not in ingest_code, "En dash found in src/aos/ingest.py"
    assert "\u2014" not in test_code, "Em dash found in tests/test_ingest.py"
    assert "\u2013" not in test_code, "En dash found in tests/test_ingest.py"

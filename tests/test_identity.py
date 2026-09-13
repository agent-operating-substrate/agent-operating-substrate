"""Tests for autonomous agent identity and supervisory mailbox subsystem."""

from pathlib import Path
from aos.cli import main
from aos.identity import get_vault_path, list_identities, save_identity


def test_vault_persistence(tmp_path: Path):
    vault_file = get_vault_path(root_dir=tmp_path)
    assert not vault_file.exists()

    record = {
        "persona": "aos-agent-test",
        "name": "AOS Agent (Test)",
        "handle": "aos-agent-test",
        "address": "test-agent@example.com",
        "password": "secret-password-123",
        "webmail_url": "https://mail.tm",
        "created_at": "2026-09-13T08:00:00Z",
    }
    save_identity(record, root_dir=tmp_path)
    assert vault_file.is_file()

    loaded = list_identities(root_dir=tmp_path)
    assert len(loaded) == 1
    assert loaded[0]["persona"] == "aos-agent-test"
    assert loaded[0]["address"] == "test-agent@example.com"
    assert loaded[0]["password"] == "secret-password-123"


def test_cli_identity_list(tmp_path: Path, capsys):
    ret_empty = main(["--root", str(tmp_path), "identity", "list"])
    assert ret_empty == 0
    out_empty = capsys.readouterr().out
    assert "No autonomous agent identities in vault" in out_empty

    record = {
        "persona": "aos-agent-auditor",
        "name": "AOS Agent (Auditor)",
        "handle": "aos-agent-auditor",
        "address": "auditor@example.com",
        "password": "audit-password-456",
        "webmail_url": "https://mail.tm",
    }
    save_identity(record, root_dir=tmp_path)

    ret_listed = main(["--root", str(tmp_path), "identity", "list"])
    assert ret_listed == 0
    out_listed = capsys.readouterr().out
    assert "aos-agent-auditor" in out_listed
    assert "auditor@example.com" in out_listed


def test_zero_em_dashes_in_identity():
    identity_file = Path("src/aos/identity.py")
    if identity_file.is_file():
        content = identity_file.read_text(encoding="utf-8")
        assert "\u2014" not in content, "Found forbidden em dash in src/aos/identity.py"

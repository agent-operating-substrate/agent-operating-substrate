"""Enterprise Fleet Invariant Mesh: cross-repository synchronization ledger."""

from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
import yaml

from aos.engine import RuleEngine
from aos.models import InvariantRule


def get_fleet_connection(fleet_db_path: Path | str) -> sqlite3.Connection:
    """Initialize SQLite fleet ledger schema if not exists."""
    path = Path(fleet_db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fleet_rules (
                id TEXT PRIMARY KEY,
                version INTEGER,
                status TEXT,
                rule_yaml TEXT,
                origin_repo TEXT,
                published_at TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS fleet_repos (
                repo_id TEXT PRIMARY KEY,
                repo_path TEXT,
                last_synced_at TEXT
            )
            """
        )
    return conn


def publish_to_fleet(
    rule_id: str,
    repo_root: Path | str = ".",
    origin_repo_id: str = "default-repo",
    fleet_db_path: Path | str = ".agents/fleet.db",
) -> bool:
    """Publish a local active rule to the organization fleet ledger."""
    engine = RuleEngine(root_dir=repo_root)
    rule = engine.get_rule_by_id(rule_id)
    if not rule:
        return False

    rule_dict = rule.to_dict()
    rule_yaml = yaml.safe_dump(rule_dict, sort_keys=False)
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    conn = get_fleet_connection(fleet_db_path)
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO fleet_rules (id, version, status, rule_yaml, origin_repo, published_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (rule.id, rule.version, rule.status, rule_yaml, origin_repo_id, now_iso),
        )
    conn.close()
    return True


def list_fleet_rules(fleet_db_path: Path | str = ".agents/fleet.db") -> list[dict[str, Any]]:
    """List all global invariant rules stored in the fleet ledger."""
    conn = get_fleet_connection(fleet_db_path)
    rows = conn.execute("SELECT id, version, status, origin_repo, published_at FROM fleet_rules").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def sync_from_fleet(
    repo_root: Path | str = ".",
    fleet_db_path: Path | str = ".agents/fleet.db",
) -> int:
    """Pull all active fleet rules into local .agents/substrate/active/."""
    root = Path(repo_root)
    active_dir = root / ".agents" / "substrate" / "active"
    active_dir.mkdir(parents=True, exist_ok=True)

    conn = get_fleet_connection(fleet_db_path)
    rows = conn.execute("SELECT id, rule_yaml FROM fleet_rules WHERE status = 'active'").fetchall()
    conn.close()

    synced_count = 0
    for row in rows:
        rule_id = row["id"]
        rule_yaml = row["rule_yaml"]
        target_file = active_dir / f"{rule_id}.yaml"
        target_file.write_text(rule_yaml, encoding="utf-8")
        synced_count += 1

    return synced_count


def export_fleet_bundle(
    fleet_db_path: Path | str = ".agents/fleet.db",
    output_path: Path | str = ".agents/fleet-bundle.json",
) -> int:
    """Export all registered fleet rules to a portable JSON bundle file."""
    conn = get_fleet_connection(fleet_db_path)
    rows = conn.execute("SELECT id, version, status, rule_yaml, origin_repo, published_at FROM fleet_rules").fetchall()
    conn.close()

    bundle = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "rules": [dict(r) for r in rows],
    }

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
    return len(rows)


def import_fleet_bundle(
    bundle_path: Path | str,
    fleet_db_path: Path | str = ".agents/fleet.db",
) -> int:
    """Import rules from a fleet bundle file into the local fleet ledger."""
    bundle_file = Path(bundle_path)
    if not bundle_file.is_file():
        raise FileNotFoundError(f"Fleet bundle not found at {bundle_path}")

    data = json.loads(bundle_file.read_text(encoding="utf-8"))
    rules = data.get("rules", [])

    conn = get_fleet_connection(fleet_db_path)
    with conn:
        for r in rules:
            conn.execute(
                """
                INSERT OR REPLACE INTO fleet_rules (id, version, status, rule_yaml, origin_repo, published_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    r["id"],
                    r.get("version", 1),
                    r.get("status", "active"),
                    r["rule_yaml"],
                    r.get("origin_repo", "bundle-import"),
                    r.get("published_at", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
                ),
            )
    conn.close()
    return len(rules)



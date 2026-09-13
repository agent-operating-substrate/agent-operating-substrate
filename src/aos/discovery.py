"""Rule discovery and loading from the substrate filesystem."""

from __future__ import annotations
from pathlib import Path
from typing import Optional
import yaml

from aos.models import InvariantRule
from aos.validator import validate_rule_dict


def load_rule_file(file_path: Path) -> tuple[Optional[InvariantRule], list[str]]:
    """Load, parse, and validate a single rule file from disk."""
    if not file_path.is_file():
        return None, [f"File not found: {file_path}"]

    try:
        content = file_path.read_text(encoding="utf-8")
        data = yaml.safe_load(content)
    except Exception as exc:
        return None, [f"Failed to parse YAML in {file_path}: {exc}"]

    if not isinstance(data, dict):
        return None, [f"Expected mapping in {file_path}, got {type(data).__name__}"]

    is_valid, errors = validate_rule_dict(data)
    if not is_valid:
        prefixed = [f"Validation failure in {file_path}: {err}" for err in errors]
        return None, prefixed

    rule = InvariantRule.from_dict(data, file_path=file_path)
    return rule, []


def discover_rules(
    substrate_dir: Path | str,
    statuses: Optional[set[str]] = None,
) -> tuple[list[InvariantRule], list[str]]:
    """Discover all invariant rules in the substrate directory tree.

    Args:
        substrate_dir: Path to .agents/substrate/ or repository root.
        statuses: Optional filter for rule status (e.g. {'active'}).

    Returns:
        tuple: (list of valid InvariantRule instances, list of error messages)
    """
    base = Path(substrate_dir)
    if (base / ".agents" / "substrate").is_dir():
        base = base / ".agents" / "substrate"

    rules: list[InvariantRule] = []
    diagnostics: list[str] = []

    subdirs = ["active", "candidate", "archive"]
    target_dirs = [base / sub for sub in subdirs if (base / sub).is_dir()]

    # If none of the subdirs exist, inspect base itself
    if not target_dirs and base.is_dir():
        target_dirs = [base]

    for directory in target_dirs:
        for ext in ("*.yaml", "*.yml"):
            for file_path in sorted(directory.glob(ext)):
                rule, errors = load_rule_file(file_path)
                if errors:
                    diagnostics.extend(errors)
                if rule is not None:
                    if statuses is None or rule.status in statuses:
                        rules.append(rule)

    return rules, diagnostics

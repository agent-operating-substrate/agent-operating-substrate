"""Harness projection engine: compiles substrate invariants into any agent harness."""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from aos.engine import RuleEngine
from aos.models import InvariantRule

START_MARKER = "<!-- AOS_INVARIANTS_START -->"
END_MARKER = "<!-- AOS_INVARIANTS_END -->"


def format_rules_for_prompt(rules: list[InvariantRule]) -> str:
    """Format active invariant rules as prompt instructions for any LLM."""
    if not rules:
        return "No active invariant rules in substrate."

    lines = [
        "## Active Substrate Invariants (Machine-Enforced)",
        "The following invariants are actively enforced by the Agent Operating Substrate.",
        "You must strictly obey these constraints in every proposed patch:",
        "",
    ]
    for r in sorted(rules, key=lambda x: x.id):
        lines.append(f"### [{r.id}] (Enforcement: {r.invariant.enforcement})")
        lines.append(f"* Statement: {r.invariant.statement}")
        lines.append(f"* Rationale: {r.invariant.rationale}")
        if r.scope.paths:
            lines.append(f"* Paths: {', '.join(r.scope.paths)}")
        if r.scope.languages:
            lines.append(f"* Languages: {', '.join(r.scope.languages)}")
        if r.invariant.max_blast_radius_lines is not None:
            lines.append(f"* Max blast radius lines: {r.invariant.max_blast_radius_lines}")
        lines.append("")
    return "\n".join(lines).strip()


def inject_into_file(target_path: Path, rendered_content: str) -> None:
    """Inject formatted invariants between markers, or append if markers do not exist."""
    block = f"{START_MARKER}\n{rendered_content}\n{END_MARKER}"
    if target_path.exists():
        existing = target_path.read_text(encoding="utf-8")
        if START_MARKER in existing and END_MARKER in existing:
            prefix = existing.split(START_MARKER)[0]
            suffix = existing.split(END_MARKER)[1]
            new_text = prefix + block + suffix
        else:
            new_text = existing.rstrip() + "\n\n" + block + "\n"
    else:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        new_text = block + "\n"

    target_path.write_text(new_text, encoding="utf-8")


def sync_harnesses(
    root_dir: Path | str = ".",
    harnesses: Optional[list[str]] = None,
) -> dict[str, Path]:
    """Sync active substrate rules into all target agent harness configuration files."""
    root = Path(root_dir)
    engine = RuleEngine(root_dir=root)
    active_rules = engine.get_rules(status="active")
    rendered = format_rules_for_prompt(active_rules)

    available_targets: dict[str, Path] = {
        "cursor": root / ".cursorrules",
        "cursor_mdc": root / ".cursor" / "rules" / "aos-invariants.mdc",
        "windsurf": root / ".windsurfrules",
        "copilot": root / ".github" / "copilot-instructions.md",
        "claude": root / "CLAUDE.md",
    }

    selected = harnesses if harnesses else list(available_targets.keys())
    updated: dict[str, Path] = {}

    for name in selected:
        if name in available_targets:
            target_path = available_targets[name]
            inject_into_file(target_path, rendered)
            updated[name] = target_path

    return updated

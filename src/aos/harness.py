"""Harness projection engine: compiles substrate invariants into any agent harness."""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from aos.engine import RuleEngine
from aos.models import InvariantRule

START_MARKER = "<!-- AOS_INVARIANTS_START -->"
END_MARKER = "<!-- AOS_INVARIANTS_END -->"


def get_rule_guidance(rule: InvariantRule) -> tuple[Optional[str], Optional[str]]:
    """Return prescriptive compliant and forbidden patterns for known invariant categories."""
    rid = rule.id.lower()
    stmt = rule.invariant.statement.lower()

    if "wildcard" in rid or "wildcard" in stmt:
        return ("import specific_module or from module import specific_symbol", "from module import *")
    if "secret" in rid or "token" in stmt or "password" in stmt:
        return ("os.environ.get('API_KEY') or pass via secure configuration", "hardcoding raw API keys, secrets, or tokens in source files")
    if "print" in rid or "logging" in stmt:
        return ("logger = logging.getLogger(__name__); logger.info(...)", "calling print(...) in application and library modules")
    if "bare-except" in rid or "bare except" in stmt or "suppress" in stmt:
        return ("except SpecificException as exc: logger.warning('...', exc_info=exc)", "bare 'except:' or 'except Exception: pass'")
    if "async" in rid and ("blocking" in stmt or "sleep" in stmt):
        return ("await asyncio.sleep(...) or run blocking calls in worker threads", "calling time.sleep or synchronous I/O inside async def functions")
    if "any" in rid or "explicit 'any'" in stmt:
        return ("use unknown, generics, or an explicit interface/type", "declaring variables, parameters, or return types as explicit 'any'")
    if "floating-promise" in rid or "promises must be awaited" in stmt:
        return ("await asyncCall(), void asyncCall(), or asyncCall().catch(...)", "leaving asynchronous promises floating without await or .catch()")
    if "unsafe" in rid or "safety:" in stmt:
        return ("add preceding '// SAFETY: explanation of memory invariants' comment", "undocumented unsafe blocks or functions")
    if "error-wrap" in rid or "%w" in stmt:
        return ("fmt.Errorf(\"context message: %w\", err)", "discarding errors or returning unwrapped bare errors")
    if "punct" in rid or "em dash" in stmt or "em-dash" in stmt:
        return ("use colons, commas, semicolons, parentheses, or separate sentences", "using em dashes in prose, documentation, comments, or commit messages")
    if "blast-radius" in rid or "surgical" in stmt or "contiguous" in stmt:
        return ("keep diffs surgical and focused strictly on the assigned task", "unsolicited broad refactoring or mass formatting changes")
    return (None, None)


def format_rules_for_prompt(
    rules: list[InvariantRule],
    root_dir: Optional[Path | str] = None,
) -> str:
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
        compliant, forbidden = get_rule_guidance(r)
        if compliant:
            lines.append(f"* Compliant Pattern: {compliant}")
        if forbidden:
            lines.append(f"* Strictly Forbidden: {forbidden}")
        if r.scope.paths:
            lines.append(f"* Paths: {', '.join(r.scope.paths)}")
        if r.scope.languages:
            lines.append(f"* Languages: {', '.join(r.scope.languages)}")
        if r.invariant.max_blast_radius_lines is not None:
            lines.append(f"* Max blast radius lines: {r.invariant.max_blast_radius_lines}")
        lines.append("")

    if root_dir is not None:
        try:
            from aos.blackboard import read_events
            events = read_events(root_dir=root_dir)
            recent_lessons: list[str] = []
            seen_rules: set[str] = set()
            for ev in reversed(events):
                if ev.type in ("AUTOPSY_RECORD", "PRE_COMMIT_BLOCKED"):
                    p = ev.payload or {}
                    rid = p.get("rule_id") or ""
                    msg = p.get("message") or p.get("statement") or ""
                    loc = p.get("file_path") or ""
                    if rid and rid not in seen_rules:
                        seen_rules.add(rid)
                        loc_str = f" in {loc}" if loc else ""
                        recent_lessons.append(f"* Intercepted [{rid}]{loc_str}: {msg}")
                        if len(recent_lessons) >= 5:
                            break
            if recent_lessons:
                lines.append("## Proactive Guardrail Memory: Recent Interceptions")
                lines.append("The following failure modes were recently intercepted by repository barriers.")
                lines.append("Ensure your implementation proactively avoids these exact patterns:")
                for lesson in recent_lessons:
                    lines.append(lesson)
                lines.append("")
        except Exception:
            pass

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
    rendered = format_rules_for_prompt(active_rules, root_dir=root)

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

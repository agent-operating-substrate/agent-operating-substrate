"""Deterministic invariant enforcer: validates file content and diffs against active rules."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Optional

from aos.engine import RuleEngine
from aos.models import InvariantRule


@dataclass
class Violation:
    file_path: str
    rule_id: str
    message: str
    enforcement: str
    line_number: Optional[int] = None
    statement: str = ""
    snippet: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "file_path": self.file_path,
            "rule_id": self.rule_id,
            "message": self.message,
            "enforcement": self.enforcement,
            "line_number": self.line_number,
            "statement": self.statement,
            "snippet": self.snippet,
        }



def check_stream_violations(
    file_path: str,
    lines: Any,
    rules: list[InvariantRule],
) -> list[Violation]:
    """Single-pass streaming inspection of lines against invariant rules."""
    violations: list[Violation] = []

    # Filter rules by capability to avoid unnecessary regex checks
    punct_rules = [
        r for r in rules
        if "em dash" in f"{r.invariant.statement} {r.invariant.rationale}".lower()
        or "zero em dashes" in f"{r.invariant.statement} {r.invariant.rationale}".lower()
    ]
    blast_rules = [
        r for r in rules
        if r.invariant.max_blast_radius_lines and r.invariant.max_blast_radius_lines > 0
    ]
    secret_rules = [
        r for r in rules
        if any(k in f"{r.invariant.statement} {r.invariant.rationale}".lower() for k in ("secret", "api key", "password", "credential", "private key"))
    ]
    sqli_rules = [
        r for r in rules
        if "sql" in f"{r.invariant.statement} {r.invariant.rationale}".lower()
        and any(k in f"{r.invariant.statement} {r.invariant.rationale}".lower() for k in ("inject", "parameter", "interpolation", "bind variable"))
    ]
    rce_rules = [
        r for r in rules
        if any(k in f"{r.invariant.statement} {r.invariant.rationale}".lower() for k in ("eval()", "exec()", "arbitrary code", "dynamic code"))
    ]
    wc_rules = [
        r for r in rules
        if "wildcard" in f"{r.invariant.statement} {r.invariant.rationale}".lower()
        or "import *" in f"{r.invariant.statement} {r.invariant.rationale}".lower()
    ]
    print_rules = [
        r for r in rules
        if "no-print" in r.id.lower()
        or ("print" in f"{r.invariant.statement} {r.invariant.rationale}".lower() and ("structured log" in f"{r.invariant.statement} {r.invariant.rationale}".lower() or "logging" in f"{r.invariant.statement} {r.invariant.rationale}".lower()))
    ]

    dash_char = chr(8212)
    en_dash_char = chr(8211)

    secret_regexes = [
        re.compile(r"""(?i)(api[_-]?key|secret|password|auth_token)\s*[:=]\s*["'][A-Za-z0-9_\-]{6,}["']"""),
        re.compile(r"""ghp_[A-Za-z0-9]{30,}"""),
        re.compile(r"""sk-[A-Za-z0-9]{20,}"""),
        re.compile(r"""-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"""),
    ] if secret_rules else []

    sql_regexes = [
        re.compile(r"""(?:execute|cursor\.execute|raw_query)\s*\(\s*f["'].*SELECT""", re.IGNORECASE),
        re.compile(r"""f["'].*SELECT\s+.*FROM.*\{""", re.IGNORECASE),
        re.compile(r"""["'].*SELECT\s+.*FROM.*["']\s*[%+]""", re.IGNORECASE),
    ] if sqli_rules else []

    rce_regexes = [
        re.compile(r"""\beval\s*\("""),
        re.compile(r"""\bexec\s*\("""),
    ] if rce_rules else []

    wc_regex = re.compile(r"""^\s*from\s+[\w\.]+\s+import\s+\*""") if wc_rules else None
    print_regex = re.compile(r"""^\s*print\s*\(.*\)""") if print_rules else None

    line_count = 0
    blast_overflow_line: dict[str, tuple[int, str]] = {}

    for idx, raw_line in enumerate(lines, start=1):
        line_count = idx
        line = raw_line.rstrip("\r\n")

        for rule in blast_rules:
            limit = rule.invariant.max_blast_radius_lines or 0
            if idx == limit + 1 and rule.id not in blast_overflow_line:
                blast_overflow_line[rule.id] = (idx, line.strip()[:100])

        if punct_rules and (dash_char in line or en_dash_char in line):
            for rule in punct_rules:
                violations.append(
                    Violation(
                        file_path=file_path,
                        rule_id=rule.id,
                        line_number=idx,
                        snippet=line.strip()[:100],
                        statement=rule.invariant.statement,
                        message=f"Violation of '{rule.id}': Forbidden dash punctuation detected on line {idx}.",
                        enforcement=rule.invariant.enforcement,
                    )
                )

        if secret_regexes:
            for rx in secret_regexes:
                if rx.search(line):
                    for rule in secret_rules:
                        violations.append(
                            Violation(
                                file_path=file_path,
                                rule_id=rule.id,
                                line_number=idx,
                                snippet=line.strip()[:100],
                                statement=rule.invariant.statement,
                                message=f"Violation of '{rule.id}': Hardcoded secret pattern detected on line {idx}.",
                                enforcement=rule.invariant.enforcement,
                            )
                        )
                    break

        if sql_regexes:
            for rx in sql_regexes:
                if rx.search(line):
                    for rule in sqli_rules:
                        violations.append(
                            Violation(
                                file_path=file_path,
                                rule_id=rule.id,
                                line_number=idx,
                                snippet=line.strip()[:100],
                                statement=rule.invariant.statement,
                                message=f"Violation of '{rule.id}': SQL query uses unparameterized string formatting on line {idx}.",
                                enforcement=rule.invariant.enforcement,
                            )
                        )
                    break

        if rce_regexes:
            for rx in rce_regexes:
                if rx.search(line):
                    for rule in rce_rules:
                        violations.append(
                            Violation(
                                file_path=file_path,
                                rule_id=rule.id,
                                line_number=idx,
                                snippet=line.strip()[:100],
                                statement=rule.invariant.statement,
                                message=f"Violation of '{rule.id}': Forbidden dynamic execution call detected on line {idx}.",
                                enforcement=rule.invariant.enforcement,
                            )
                        )
                    break

        if wc_regex and wc_regex.search(line):
            for rule in wc_rules:
                violations.append(
                    Violation(
                        file_path=file_path,
                        rule_id=rule.id,
                        line_number=idx,
                        snippet=line.strip()[:100],
                        statement=rule.invariant.statement,
                        message=f"Violation of '{rule.id}': Prohibited wildcard import on line {idx}.",
                        enforcement=rule.invariant.enforcement,
                    )
                )

        if print_regex and print_regex.search(line):
            for rule in print_rules:
                violations.append(
                    Violation(
                        file_path=file_path,
                        rule_id=rule.id,
                        line_number=idx,
                        snippet=line.strip()[:100],
                        statement=rule.invariant.statement,
                        message=f"Violation of '{rule.id}': Raw print call detected on line {idx}; structured logging required.",
                        enforcement=rule.invariant.enforcement,
                    )
                )

    for rule in blast_rules:
        limit = rule.invariant.max_blast_radius_lines or 0
        if line_count > limit:
            overflow_idx, overflow_snip = blast_overflow_line.get(rule.id, (limit + 1, ""))
            violations.append(
                Violation(
                    file_path=file_path,
                    rule_id=rule.id,
                    line_number=overflow_idx,
                    snippet=overflow_snip,
                    statement=rule.invariant.statement,
                    message=f"Violation of '{rule.id}': Content exceeds maximum blast radius of {limit} lines ({line_count} lines detected).",
                    enforcement=rule.invariant.enforcement,
                )
            )

    return violations


def check_content_violations(
    file_path: str,
    content: str,
    rules: list[InvariantRule],
) -> list[Violation]:
    """Inspect text content against a set of active invariant rules."""
    lines = content.splitlines(keepends=True) if content else []
    return check_stream_violations(file_path, lines, rules)


def check_file_violations(
    file_path: str | Path,
    root_dir: Path | str = ".",
    engine: Optional[RuleEngine] = None,
) -> list[Violation]:
    """Inspect a single file against all applicable active invariant rules."""
    root = Path(root_dir)
    target = root / file_path if not Path(file_path).is_absolute() else Path(file_path)
    rel_path = str(target.relative_to(root)).replace("\\", "/") if target.is_relative_to(root) else str(target)

    if not target.is_file():
        return []

    if engine is None:
        engine = RuleEngine(root_dir=root)

    matching_rules = engine.match_file(rel_path, status="active")
    if not matching_rules:
        return []

    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            return check_stream_violations(rel_path, f, matching_rules)
    except Exception:
        # If binary or unreadable, skip text inspections
        return []



def enforce_all(
    file_paths: list[str],
    root_dir: Path | str = ".",
) -> list[Violation]:
    """Run invariant checks across all specified files."""
    root = Path(root_dir)
    engine = RuleEngine(root_dir=root)
    all_violations: list[Violation] = []

    for p in file_paths:
        violations = check_file_violations(p, root_dir=root, engine=engine)
        all_violations.extend(violations)

    return all_violations

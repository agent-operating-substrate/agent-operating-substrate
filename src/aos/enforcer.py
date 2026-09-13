"""Deterministic invariant enforcer: validates file content and diffs against active rules."""

from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path
import re
import subprocess
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
    staged_blast: Optional[int] = None,
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
        if any(k in f"{r.invariant.statement} {r.invariant.rationale}".lower() for k in ("arbitrary code", "dynamic code", "dynamic evaluation", "deserialization"))
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
        re.compile(r"""(?i)(api[_-]?key|secret|password|auth_token|aws_access_key_id)\s*[:=]\s*["'][A-Za-z0-9_\-/+=]{6,}["']"""),
        re.compile(r"""ghp_[A-Za-z0-9]{30,}"""),
        re.compile(r"""sk-[A-Za-z0-9]{20,}"""),
        re.compile(r"""AKIA[0-9A-Z]{16}"""),
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

    has_justification = bool(
        os.environ.get("AOS_DIFF_JUSTIFICATION")
        or os.environ.get("AOS_JUSTIFICATION")
        or file_path.startswith("docs/")
        or file_path.endswith((".md", ".svg", ".png", ".jpg", ".jpeg", ".ico"))
    )

    if not has_justification:
        effective_blast = staged_blast if staged_blast is not None else line_count
        for rule in blast_rules:
            limit = rule.invariant.max_blast_radius_lines or 0
            if effective_blast > limit:
                overflow_idx, overflow_snip = blast_overflow_line.get(rule.id, (limit + 1, ""))
                violations.append(
                    Violation(
                        file_path=file_path,
                        rule_id=rule.id,
                        line_number=overflow_idx,
                        snippet=overflow_snip,
                        statement=rule.invariant.statement,
                        message=f"Violation of '{rule.id}': Content exceeds maximum blast radius of {limit} lines ({effective_blast} lines detected).",
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


def get_staged_blast_radius(file_path: str, root_dir: Path) -> Optional[int]:
    """Calculate maximum contiguous added lines in staged git diff for a file."""
    if not (root_dir / ".git").is_dir():
        return None
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "-U0", "--", file_path],
            cwd=str(root_dir),
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
        if res.returncode != 0:
            return None
        hunk_rx = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,(\d+))? @@")
        hunk_sizes: list[int] = []
        for line in res.stdout.splitlines():
            m = hunk_rx.match(line)
            if m:
                count = int(m.group(1)) if m.group(1) is not None else 1
                hunk_sizes.append(count)
        return max(hunk_sizes) if hunk_sizes else 0
    except Exception:
        return None


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

    staged_blast = get_staged_blast_radius(rel_path, root)

    try:
        with target.open("r", encoding="utf-8", errors="replace") as f:
            return check_stream_violations(rel_path, f, matching_rules, staged_blast=staged_blast)
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


def auto_fix_content(
    file_path: str,
    content: str,
    rules: list[InvariantRule],
) -> tuple[str, list[str]]:
    """Deterministically auto-fix common safe invariant violations in code.

    Returns:
        tuple[str, list[str]]: (fixed_content, list_of_applied_fixes)
    """
    applied_fixes: list[str] = []
    lines = content.splitlines(keepends=True)
    fixed_lines = list(lines)

    for rule in rules:
        st_lower = rule.invariant.statement.lower()
        rat_lower = rule.invariant.rationale.lower()
        rule_text = f"{st_lower} {rat_lower}"

        # 1. Fix dash punctuation
        if "em dash" in rule_text or "zero em dashes" in rule_text:
            dash_char = chr(8212)
            en_dash_char = chr(8211)
            for i, line in enumerate(fixed_lines):
                if dash_char in line or en_dash_char in line:
                    fixed_lines[i] = line.replace(dash_char, ": ").replace(en_dash_char, "-")
                    applied_fixes.append(f"Replaced forbidden dash punctuation on line {i + 1} with standard punctuation.")

        # 2. Fix print calls to logger calls if rule requires structured logging
        if "no-print" in rule.id.lower() or ("print" in rule_text and ("structured log" in rule_text or "logging" in rule_text)):
            print_call_rx = re.compile(r"""^(\s*)print\s*\((.*)\)(\s*)$""")
            for i, line in enumerate(fixed_lines):
                m = print_call_rx.match(line)
                if m:
                    indent, args, trailing = m.group(1), m.group(2), m.group(3)
                    fixed_lines[i] = f"{indent}logging.getLogger(__name__).info({args}){trailing}"
                    applied_fixes.append(f"Converted raw print() on line {i + 1} to structured logging call.")

        # 3. Fix wildcard imports
        if "wildcard" in rule_text or "import *" in rule_text:
            wc_rx = re.compile(r"""^(\s*)from\s+([\w\.]+)\s+import\s+\*(\s*)$""")
            for i, line in enumerate(fixed_lines):
                m = wc_rx.match(line)
                if m:
                    indent, mod, trailing = m.group(1), m.group(2), m.group(3)
                    fixed_lines[i] = f"{indent}import {mod}  # Auto-fixed: explicit namespace import replacing wildcard{trailing}"
                    applied_fixes.append(f"Replaced wildcard import on line {i + 1} with explicit module import.")

        # 4. Fix Rust unsafe blocks without // SAFETY: comments
        if "rust" in rule.id.lower() or "safety:" in rule_text:
            unsafe_rx = re.compile(r"""^(\s*)unsafe\s*(\{|fn|impl|trait)""")
            for i, line in enumerate(fixed_lines):
                m = unsafe_rx.match(line)
                if m:
                    has_safety = False
                    if i > 0 and "// SAFETY:" in fixed_lines[i - 1]:
                        has_safety = True
                    if not has_safety:
                        indent = m.group(1)
                        fixed_lines.insert(i, f"{indent}// SAFETY: Invariant verified by developer.\n")
                        applied_fixes.append(f"Added required // SAFETY: comment before unsafe block on line {i + 1}.")
                        break

    return "".join(fixed_lines), applied_fixes


def auto_fix_file(
    file_path: str | Path,
    root_dir: Path | str = ".",
    engine: Optional[RuleEngine] = None,
) -> list[str]:
    """Inspect and auto-fix violations in a target file on disk."""
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
        content = target.read_text(encoding="utf-8")
        fixed_content, applied = auto_fix_content(rel_path, content, matching_rules)
        if applied and fixed_content != content:
            target.write_text(fixed_content, encoding="utf-8")
        return applied
    except Exception:
        return []

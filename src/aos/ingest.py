"""Automated repository ingestion and convention extraction engine."""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time
from typing import Any
import yaml

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import post_event


@dataclass
class IngestionReport:
    detected_languages: list[str] = field(default_factory=list)
    detected_frameworks: list[str] = field(default_factory=list)
    scanned_config_files: list[str] = field(default_factory=list)
    existing_instruction_files: list[str] = field(default_factory=list)
    synthesized_rules: list[dict[str, Any]] = field(default_factory=list)
    recommended_packs: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "detected_languages": self.detected_languages,
            "detected_frameworks": self.detected_frameworks,
            "scanned_config_files": self.scanned_config_files,
            "existing_instruction_files": self.existing_instruction_files,
            "recommended_packs": self.recommended_packs,
            "synthesized_rules_count": len(self.synthesized_rules),
            "synthesized_rules": self.synthesized_rules,
        }


def scan_repository_conventions(root_dir: Path | str = ".") -> IngestionReport:
    """Inspect repository manifests and instruction files to derive tailored invariants."""
    root = Path(root_dir)
    report = IngestionReport()
    detected_rules: list[dict[str, Any]] = []

    # 1. Check TypeScript / JavaScript ecosystems
    tsconfig = root / "tsconfig.json"
    if tsconfig.is_file():
        report.detected_languages.append("typescript")
        report.scanned_config_files.append("tsconfig.json")
        try:
            ts_text = tsconfig.read_text(encoding="utf-8", errors="ignore")
            clean_ts = re.sub(r"//.*", "", ts_text)
            ts_data = json.loads(clean_ts)
            co = ts_data.get("compilerOptions", {})
            if co.get("strict", False) or co.get("noImplicitAny", False):
                detected_rules.append({
                    "id": "ts-strict-typing",
                    "statement": "TypeScript code must maintain strict type safety: avoid explicit any casts or unvalidated dynamic properties.",
                    "rationale": "Enforce strict compiler options declared in tsconfig.json across all AI edits.",
                    "paths": ["src/**/*.ts", "src/**/*.tsx"],
                    "languages": ["typescript"],
                    "enforcement": "reject_diff",
                })
        except Exception:
            pass

    pkg_json = root / "package.json"
    if pkg_json.is_file():
        report.scanned_config_files.append("package.json")
        try:
            pkg_data = json.loads(pkg_json.read_text(encoding="utf-8", errors="ignore"))
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            if "react" in deps:
                report.detected_frameworks.append("react")
                if "javascript" not in report.detected_languages:
                    report.detected_languages.append("javascript")
                detected_rules.append({
                    "id": "react-hooks-deps",
                    "statement": "React components must obey the rules of hooks and specify complete dependency arrays in useEffect and useMemo.",
                    "rationale": "Prevents stale closure bugs and infinite re-render cycles in React components.",
                    "paths": ["src/**/*.jsx", "src/**/*.tsx"],
                    "languages": ["javascript", "typescript"],
                    "enforcement": "reject_diff",
                })
            if "next" in deps:
                report.detected_frameworks.append("nextjs")
                detected_rules.append({
                    "id": "nextjs-client-boundary",
                    "statement": "Interactive components utilizing state or browser hooks must explicitly declare the 'use client' directive.",
                    "rationale": "Next.js App Router enforces strict server and client component boundaries.",
                    "paths": ["src/app/**/*.tsx", "src/components/**/*.tsx"],
                    "languages": ["typescript", "javascript"],
                    "enforcement": "reject_diff",
                })
        except Exception:
            pass

    # 2. Check Python ecosystems
    pyproject = root / "pyproject.toml"
    reqs = root / "requirements.txt"
    is_python = False
    py_text = ""

    if pyproject.is_file():
        is_python = True
        report.scanned_config_files.append("pyproject.toml")
        py_text += pyproject.read_text(encoding="utf-8", errors="ignore")

    if reqs.is_file():
        is_python = True
        report.scanned_config_files.append("requirements.txt")
        py_text += reqs.read_text(encoding="utf-8", errors="ignore")

    if is_python:
        report.detected_languages.append("python")
        if "fastapi" in py_text.lower():
            report.detected_frameworks.append("fastapi")
            detected_rules.append({
                "id": "fastapi-pydantic-schemas",
                "statement": "FastAPI route handlers must define explicit Pydantic request and response models for typed I/O contracts.",
                "rationale": "Ensures runtime schema validation and automatic OpenAPI documentation generation.",
                "paths": ["src/**/*.py", "app/**/*.py"],
                "languages": ["python"],
                "enforcement": "reject_diff",
            })
        if "django" in py_text.lower():
            report.detected_frameworks.append("django")
            detected_rules.append({
                "id": "django-atomic-writes",
                "statement": "Mutating database operations across multiple models must execute within transaction.atomic() blocks.",
                "rationale": "Guarantees database consistency and prevents partial write corruptions.",
                "paths": ["src/**/*.py"],
                "languages": ["python"],
                "enforcement": "reject_diff",
            })

    # 3. Check Rust
    cargo = root / "Cargo.toml"
    if cargo.is_file():
        report.detected_languages.append("rust")
        report.scanned_config_files.append("Cargo.toml")
        detected_rules.append({
            "id": "rust-unsafe-audit",
            "statement": "Unsafe blocks in Rust must include a preceding '// SAFETY:' comment explaining pointer or memory validity invariants.",
            "rationale": "Audit requirement ensuring memory safety invariants are documented at each unsafe boundary.",
            "paths": ["src/**/*.rs"],
            "languages": ["rust"],
            "enforcement": "reject_diff",
        })

    # 4. Check Go
    gomod = root / "go.mod"
    if gomod.is_file():
        report.detected_languages.append("go")
        report.scanned_config_files.append("go.mod")
        detected_rules.append({
            "id": "go-error-wrapping",
            "statement": "Go functions must explicitly check and wrap returned errors using fmt.Errorf with %w.",
            "rationale": "Preserves error call chains and enables errors.Is / errors.As inspection in Go services.",
            "paths": ["**/*.go"],
            "languages": ["go"],
            "enforcement": "reject_diff",
        })

    # 5. Scan Existing Team Instruction Files
    instruction_candidates = [
        "CLAUDE.md",
        "AGENTS.md",
        ".cursorrules",
        "CONTRIBUTING.md",
        ".github/copilot-instructions.md",
    ]
    for instr_name in instruction_candidates:
        instr_path = root / instr_name
        if instr_path.is_file():
            report.existing_instruction_files.append(instr_name)
            try:
                instr_text = instr_path.read_text(encoding="utf-8", errors="ignore")
                clean_instr = re.sub(r"<!-- AOS_INVARIANTS_START -->.*?<!-- AOS_INVARIANTS_END -->", "", instr_text, flags=re.DOTALL)
                rule_lines = re.findall(r"^(?:[-*]|\d+\.)\s+([A-Z][^\n]{15,120})", clean_instr, re.MULTILINE)
                for idx, r_stmt in enumerate(rule_lines[:3], 1):
                    safe_id = re.sub(r"[^a-z0-9]+", "-", instr_name.lower().replace(".", "-")).strip("-")
                    r_id = f"team-{safe_id}-rule-{idx}"
                    clean_stmt = r_stmt.strip()
                    if not clean_stmt.endswith("."):
                        clean_stmt += "."
                    if not any(d["statement"] == clean_stmt for d in detected_rules):
                        detected_rules.append({
                            "id": r_id,
                            "statement": clean_stmt,
                            "rationale": f"Extracted from team repository instructions in {instr_name}.",
                            "paths": ["**/*"],
                            "languages": [],
                            "enforcement": "reject_diff",
                        })
            except Exception:
                pass

    from aos.packs import recommend_packs
    report.recommended_packs = recommend_packs(root_dir=root)
    report.synthesized_rules = detected_rules
    return report


def ingest_repository(
    root_dir: Path | str = ".",
    auto_promote: bool = False,
    install_recommended_packs: bool = False,
) -> IngestionReport:
    """Scan repository conventions and inscribe synthesized invariants into the substrate."""
    root = Path(root_dir)
    report = scan_repository_conventions(root_dir=root)
    sub_dir = root / ".agents" / "substrate"

    for rule_data in report.synthesized_rules:
        candidate = synthesize_candidate_rule(
            rule_id=rule_data["id"],
            statement=rule_data["statement"],
            rationale=rule_data.get("rationale", "Synthesized via repository ingestion scan."),
            paths=rule_data.get("paths", ["**/*"]),
            languages=rule_data.get("languages", []),
            enforcement=rule_data.get("enforcement", "reject_diff"),
            incident_id=f"ingest-{int(time.time())}",
            inscribing_agent="repo-ingestion-engine",
        )

        inscribe_candidate(candidate, substrate_dir=sub_dir)
        if auto_promote:
            promote_candidate(candidate.id, peer_agent="repo-ingestion-engine", substrate_dir=sub_dir)

    if install_recommended_packs:
        from aos.packs import install_pack
        for p in report.recommended_packs:
            install_pack(p, root_dir=root, promote=auto_promote)

    post_event(
        {
            "type": "REPO_INGESTED",
            "sender": "repo-ingestion-engine",
            "payload": {
                "detected_languages": report.detected_languages,
                "detected_frameworks": report.detected_frameworks,
                "scanned_config_files": report.scanned_config_files,
                "existing_instruction_files": report.existing_instruction_files,
                "synthesized_count": len(report.synthesized_rules),
                "auto_promoted": auto_promote,
            },
        },
        root_dir=root,
    )

    return report

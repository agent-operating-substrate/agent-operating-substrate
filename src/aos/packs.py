"""Curated invariant rule packs for domain-specific best practices."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import yaml

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule

CURATED_PACKS: dict[str, list[dict[str, Any]]] = {
    "security-owasp": [
        {
            "id": "sec-sql-injection-001",
            "statement": "SQL queries must use parameterized bind variables, never raw string interpolation or concatenation.",
            "rationale": "Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go", "java"],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-secret-leak-002",
            "statement": "API keys, secrets, private certificates, and passwords must never be committed to source files.",
            "rationale": "Hardcoded credentials in Git histories result in credential compromise and audit failure.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-ssrf-003",
            "statement": "Outbound HTTP requests constructed from dynamic input must validate targets against an allowlist and block private network ranges.",
            "rationale": "Unvalidated network requests allow SSRF attacks targeting cloud metadata services and internal infrastructure.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go"],
            "enforcement": "reject_diff",
        },
    ],
    "python-clean-architecture": [
        {
            "id": "py-no-print-001",
            "statement": "Core library and domain modules must utilize structured logging instead of standard print statements.",
            "rationale": "Direct print calls pollute stdout and prevent log aggregation in production environments.",
            "paths": ["src/**"],
            "languages": ["python"],
            "enforcement": "warn",
        },
        {
            "id": "py-no-wildcard-import-002",
            "statement": "Wildcard imports ('from module import *') are strictly prohibited.",
            "rationale": "Wildcard imports cause namespace pollution, mask circular dependencies, and degrade linter performance.",
            "paths": ["src/**", "tests/**"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
        {
            "id": "py-boundary-isolation-003",
            "statement": "Domain models and business logic must not import from infrastructure or presentation layers.",
            "rationale": "Clean architecture requires dependency inversion: domain cores must remain completely decoupled from I/O.",
            "paths": ["src/**/domain/**", "src/**/models/**"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
        {
            "id": "py-type-annotations-004",
            "statement": "Public functions, methods, and classes must provide explicit parameter and return type annotations.",
            "rationale": "Static typing prevents runtime errors and provides clear machine-readable contracts for AI coding agents.",
            "paths": ["src/**"],
            "languages": ["python"],
            "enforcement": "warn",
        },
    ],
    "performance-simd": [
        {
            "id": "perf-avx-align-001",
            "statement": "PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries.",
            "rationale": "Unaligned memory loads trigger general protection faults under high-throughput vector execution.",
            "paths": ["src/geometry/simd/**", "include/geometry/simd/**"],
            "languages": ["cpp", "cuda"],
            "enforcement": "reject_diff",
        },
        {
            "id": "perf-zero-copy-002",
            "statement": "High-throughput streaming loops and packet parsers must operate on memory views or slices without heap reallocations.",
            "rationale": "Intermediate buffer allocations degrade cache locality and introduce latency spikes in hot execution paths.",
            "paths": ["src/**/streaming/**", "src/**/simd/**"],
            "languages": ["python", "cpp", "rust"],
            "enforcement": "warn",
        },
    ],
    "universal-security": [
        {
            "id": "sec-secret-leak-002",
            "statement": "API keys, secrets, private certificates, and passwords must never be committed to source files.",
            "rationale": "Hardcoded credentials in Git histories result in credential compromise and audit failure.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-sql-injection-001",
            "statement": "SQL queries must use parameterized bind variables, never raw string interpolation or concatenation.",
            "rationale": "Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go", "java"],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-rce-eval-004",
            "statement": "Direct execution of dynamic input strings via eval(), exec(), or unsanitized shell commands is strictly prohibited.",
            "rationale": "Arbitrary code execution vulnerabilities result from dynamic evaluation of untrusted strings.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript"],
            "enforcement": "reject_diff",
        },
    ],
    "web-typescript": [
        {
            "id": "ts-no-any-001",
            "statement": "TypeScript variables, parameters, and return types must avoid explicit any and use unknown or generic constraints.",
            "rationale": "Any types disable compiler type checking and allow runtime type errors to propagate silently.",
            "paths": ["src/**/*.ts", "src/**/*.tsx"],
            "languages": ["typescript"],
            "enforcement": "reject_diff",
        },
        {
            "id": "ts-floating-promises-002",
            "statement": "Async promises must be awaited, returned, or explicitly handled with a catch clause.",
            "rationale": "Floating unhandled promises cause silent async failures and unhandled promise rejections.",
            "paths": ["src/**/*.ts", "src/**/*.tsx"],
            "languages": ["typescript"],
            "enforcement": "reject_diff",
        },
    ],
    "python-fastapi": [
        {
            "id": "fastapi-pydantic-001",
            "statement": "FastAPI endpoint handlers must specify explicit Pydantic response_model and typed request payloads.",
            "rationale": "Enforces runtime data validation, automatic serialization, and clean OpenAPI schema generation.",
            "paths": ["src/**/*.py", "app/**/*.py"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
    ],
    "react-modern": [
        {
            "id": "react-hooks-deps-001",
            "statement": "React hooks must declare exhaustive dependencies and avoid mutations of component state during rendering.",
            "rationale": "Missing dependencies cause stale closure bugs and unpredictable re-rendering loops.",
            "paths": ["src/**/*.jsx", "src/**/*.tsx"],
            "languages": ["javascript", "typescript"],
            "enforcement": "reject_diff",
        },
    ],
    "go-standard": [
        {
            "id": "go-error-wrap-001",
            "statement": "Go functions must inspect non-nil error values and return wrapped errors with fmt.Errorf and %w.",
            "rationale": "Preserves call context and enables errors.Is and errors.As inspection across package boundaries.",
            "paths": ["**/*.go"],
            "languages": ["go"],
            "enforcement": "reject_diff",
        },
    ],
    "rust-safety": [
        {
            "id": "rust-unsafe-safety-doc-001",
            "statement": "Every unsafe block in Rust must include a preceding '// SAFETY:' comment documenting invariant validity.",
            "rationale": "Audit requirement ensuring memory safety invariants are documented at each unsafe boundary.",
            "paths": ["src/**/*.rs"],
            "languages": ["rust"],
            "enforcement": "reject_diff",
        },
    ],
}


def list_available_packs() -> dict[str, int]:
    """Return dictionary of pack names and rule counts."""
    return {name: len(rules) for name, rules in CURATED_PACKS.items()}


def install_pack(
    pack_name: str,
    root_dir: Path | str = ".",
    promote: bool = True,
) -> list[Path]:
    """Install all rules from a curated pack into the substrate."""
    if pack_name not in CURATED_PACKS:
        raise ValueError(f"Unknown pack '{pack_name}'. Available: {list(CURATED_PACKS.keys())}")

    root = Path(root_dir)
    substrate_dir = root / ".agents" / "substrate"
    installed_paths: list[Path] = []

    for item in CURATED_PACKS[pack_name]:
        rule = synthesize_candidate_rule(
            rule_id=item["id"],
            statement=item["statement"],
            rationale=item["rationale"],
            paths=item["paths"],
            languages=item.get("languages", []),
            incident_id=f"pack-{pack_name}",
            inscribing_agent="pack-installer",
            enforcement=item.get("enforcement", "reject_diff"),
        )
        saved = inscribe_candidate(rule, substrate_dir=substrate_dir)
        if promote:
            promoted = promote_candidate(rule.id, peer_agent="pack-curator", substrate_dir=substrate_dir)
            if promoted:
                installed_paths.append(promoted)
        else:
            installed_paths.append(saved)

    return installed_paths

"""Curated invariant rule packs for domain-specific best practices."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Optional
import yaml

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule

CURATED_PACKS: dict[str, list[dict[str, Any]]] = {
    # Universal Open-Source Core Packs
    "security-core": [
        {
            "id": "sec-no-secrets-001",
            "statement": "API keys, private certificates, authentication tokens, and secrets must never be committed to source files or repository configuration.",
            "rationale": "Hardcoded credentials in Git histories result in credential compromise, security audit failure, and unauthorized system access.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-sql-injection-001",
            "statement": "SQL queries must use parameterized bind variables; raw string concatenation, format strings, or template interpolation is prohibited.",
            "rationale": "Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities allowing unauthorized data extraction or destruction.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go", "rust", "java", "csharp", "php", "ruby"],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-ssrf-prevention-001",
            "statement": "Outbound HTTP and network requests constructed from dynamic user input must validate hostnames against an allowlist and block private or link-local IP addresses.",
            "rationale": "Unvalidated outbound network requests permit SSRF attacks targeting cloud instance metadata services and internal microservices.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go", "rust", "java"],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-safe-deserialization-001",
            "statement": "Untrusted dynamic input must not be processed with insecure deserialization primitives (pickle.loads, marshal, unsafe yaml.load) or arbitrary dynamic code evaluation (eval, exec).",
            "rationale": "Insecure deserialization and arbitrary eval calls allow attackers to execute arbitrary code via gadget chains and dynamic interpretation.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript"],
            "enforcement": "reject_diff",
        },
    ],
    "python-core": [
        {
            "id": "py-no-wildcard-import-002",
            "statement": "Wildcard imports ('from module import *') are prohibited; all imported symbols must be explicitly named or imported via the module namespace.",
            "rationale": "Wildcard imports pollute module namespaces, mask circular dependencies, hide symbol origins, and break static analysis.",
            "paths": ["**/*.py"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
        {
            "id": "py-structured-logging-001",
            "statement": "Application, service, and core library code must use structured logging frameworks rather than standard print statements.",
            "rationale": "Raw print statements lack log level metadata, bypass centralized observability aggregation, and pollute stdout streams.",
            "paths": ["src/**/*.py", "lib/**/*.py", "app/**/*.py"],
            "languages": ["python"],
            "enforcement": "warn",
        },
        {
            "id": "py-no-bare-except-002",
            "statement": "Catching Exception or bare except blocks must not silently suppress errors with pass; catch specific exception classes and log or re-raise errors.",
            "rationale": "Silent exception swallowing hides fatal runtime errors, interrupts, and bugs, making forensic debugging and root-cause analysis impossible.",
            "paths": ["**/*.py"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
        {
            "id": "py-async-no-blocking-io-003",
            "statement": "Asynchronous functions (async def) must not invoke synchronous blocking I/O calls such as time.sleep, synchronous requests, or blocking filesystem operations.",
            "rationale": "Blocking operations in coroutines stall the main asyncio event loop, starving concurrent tasks and destroying service throughput.",
            "paths": ["**/*.py"],
            "languages": ["python"],
            "enforcement": "reject_diff",
        },
    ],
    "typescript-core": [
        {
            "id": "ts-no-any-001",
            "statement": "TypeScript variables, parameters, and return types must avoid explicit 'any'; use 'unknown', union types, generic constraints, or explicit interfaces instead.",
            "rationale": "The 'any' type disables compiler type checking, concealing potential runtime type errors and eliminating editor refactoring safety.",
            "paths": ["**/*.ts", "**/*.tsx"],
            "languages": ["typescript"],
            "enforcement": "reject_diff",
        },
        {
            "id": "ts-floating-promises-002",
            "statement": "Asynchronous promises must be awaited, returned to the caller, or explicitly handled with a .catch() callback or void operator.",
            "rationale": "Floating unhandled promises produce unhandled promise rejections, race conditions, and silently dropped async failures.",
            "paths": ["**/*.ts", "**/*.tsx"],
            "languages": ["typescript"],
            "enforcement": "reject_diff",
        },
        {
            "id": "react-hooks-deps-001",
            "statement": "React hooks (useEffect, useMemo, useCallback) must declare exhaustive dependencies and must not mutate component state during rendering.",
            "rationale": "Omitted dependencies cause stale closures and out-of-sync UI state, while state mutations in render cause infinite re-render loops.",
            "paths": ["src/**/*.jsx", "src/**/*.tsx", "app/**/*.tsx"],
            "languages": ["javascript", "typescript"],
            "enforcement": "reject_diff",
        },
        {
            "id": "ts-clean-imports-004",
            "statement": "TypeScript modules must use explicit relative or mapped aliases, avoiding circular imports and deep imports into private internal module subpaths.",
            "rationale": "Circular and poorly bounded imports cause undefined runtime values, increase bundled bundle size, and degrade tree shaking.",
            "paths": ["**/*.ts", "**/*.tsx"],
            "languages": ["typescript"],
            "enforcement": "warn",
        },
    ],
    "general-hygiene": [
        {
            "id": "gh-deps-sync-001",
            "statement": "Changes to package dependency manifests (package.json, pyproject.toml, Cargo.toml, go.mod) must include synchronized updates to corresponding lockfiles.",
            "rationale": "Desynchronized dependency manifests and lockfiles cause irreproducible builds, CI failures, and unexpected environment drift.",
            "paths": ["package.json", "pyproject.toml", "Cargo.toml", "go.mod", "requirements*.txt"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "gh-no-artifacts-credentials-002",
            "statement": "Build artifacts, compiled binaries, bytecode (.pyc, .class), local environment configuration files (.env), and IDE directories must not be committed to version control.",
            "rationale": "Committing build outputs and local environment files bloats repository history, triggers merge conflicts, and leaks local configuration secrets.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "gh-blast-radius-limit-003",
            "statement": "Automated agent changes must maintain surgical precision by touching only required lines, maintaining single-task contiguous changes within 50 lines without unsolicited refactoring.",
            "rationale": "Enforces surgical diff discipline to ensure modifications are reviewable, verifiable, and free from unintended regressions.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
    ],
    "rust-core": [
        {
            "id": "rust-unsafe-safety-doc-001",
            "statement": "Every unsafe block, unsafe function, or unsafe trait implementation in Rust must include a preceding '// SAFETY:' comment documenting invariant validity.",
            "rationale": "Audit requirement ensuring memory safety invariants and preconditions are explicitly documented at each unsafe boundary to verify soundness.",
            "paths": ["**/*.rs"],
            "languages": ["rust"],
            "enforcement": "reject_diff",
        },
        {
            "id": "rust-no-unwrap-in-lib-002",
            "statement": "Production Rust library and service code must not invoke .unwrap() or .expect() on Option or Result; propagate errors using '?' or handle them explicitly.",
            "rationale": "Calling unwrap or expect panics the executing thread on unexpected conditions, crashing services without opportunity for graceful recovery.",
            "paths": ["src/**/*.rs", "lib/**/*.rs"],
            "languages": ["rust"],
            "enforcement": "reject_diff",
        },
    ],
    "go-core": [
        {
            "id": "go-error-wrap-001",
            "statement": "Go functions returning an error must have that error checked; discarding errors via blank identifier '_' is prohibited, and returned errors must be wrapped with contextual information using fmt.Errorf with %w.",
            "rationale": "Preserves error context across package boundaries and enables errors.Is and errors.As inspection in caller packages.",
            "paths": ["**/*.go"],
            "languages": ["go"],
            "enforcement": "reject_diff",
        },
        {
            "id": "go-context-propagation-002",
            "statement": "Go functions performing I/O operations, network requests, database transactions, or concurrent tasks must accept context.Context as their first parameter and honor cancellation.",
            "rationale": "Missing context propagation leads to orphaned goroutines, resource leaks, and unresponsive cancellation signals during server shutdowns or request timeouts.",
            "paths": ["**/*.go"],
            "languages": ["go"],
            "enforcement": "reject_diff",
        },
    ],
    # Compatibility Aliases
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
            "id": "sec-no-secrets-001",
            "statement": "API keys, secrets, private certificates, and passwords must never be committed to source files.",
            "rationale": "Hardcoded credentials in Git histories result in credential compromise and audit failure.",
            "paths": ["**/*"],
            "languages": [],
            "enforcement": "reject_diff",
        },
        {
            "id": "sec-ssrf-prevention-001",
            "statement": "Outbound HTTP requests constructed from dynamic input must validate targets against an allowlist and block private network ranges.",
            "rationale": "Unvalidated network requests allow SSRF attacks targeting cloud metadata services and internal infrastructure.",
            "paths": ["**/*"],
            "languages": ["python", "javascript", "typescript", "go"],
            "enforcement": "reject_diff",
        },
    ],
    "python-clean-architecture": [
        {
            "id": "py-structured-logging-001",
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
    ],
    "universal-security": [
        {
            "id": "sec-no-secrets-001",
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
            "id": "sec-safe-deserialization-001",
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

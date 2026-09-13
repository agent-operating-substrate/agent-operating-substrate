<!-- AOS_INVARIANTS_START -->
## Active Substrate Invariants (Machine-Enforced)
The following invariants are actively enforced by the Agent Operating Substrate.
You must strictly obey these constraints in every proposed patch:

### [aos-deps-003] (Enforcement: reject_diff)
* Statement: Build with minimal code. Avoid speculative abstractions. Favor local file primitives (JSON, YAML, SQLite) over complex external infrastructure. Do not introduce dependencies unless strictly necessary.
* Rationale: Constraint specified in AGENTS.md Rule 3 and README.md zero external dependency principle.
* Paths: pyproject.toml, src/**
* Languages: python
* Max blast radius lines: 30

### [aos-diff-002] (Enforcement: reject_diff)
* Statement: Touch only lines strictly required to complete the assigned task. Never reformat adjacent code, comments, or imports. If a patch exceeds 30 contiguous lines, halt and provide technical justification.
* Rationale: Constraint specified in AGENTS.md Rule 1 to maintain surgical precision and minimize blast radius.
* Paths: **/*
* Max blast radius lines: 30

### [aos-punct-001] (Enforcement: reject_diff)
* Statement: Zero em dashes in all prose, documentation, commit messages, and code comments. Use colons, commas, semicolons, parentheses, or separate sentences instead.
* Rationale: Constraint specified in AGENTS.md Rule 2 to enforce unambiguous, clean punctuation.
* Paths: **/*
* Max blast radius lines: 30

### [fastapi-pydantic-001] (Enforcement: reject_diff)
* Statement: FastAPI endpoint handlers must specify explicit Pydantic response_model and typed request payloads.
* Rationale: Enforces runtime data validation, automatic serialization, and clean OpenAPI schema generation.
* Paths: src/**/*.py, app/**/*.py
* Languages: python
* Max blast radius lines: 30

### [go-error-wrap-001] (Enforcement: reject_diff)
* Statement: Go functions must inspect non-nil error values and return wrapped errors with fmt.Errorf and %w.
* Rationale: Preserves call context and enables errors.Is and errors.As inspection across package boundaries.
* Paths: **/*.go
* Languages: go
* Max blast radius lines: 30

### [perf-avx-align-001] (Enforcement: reject_diff)
* Statement: PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries.
* Rationale: Unaligned memory loads trigger general protection faults under high-throughput vector execution.
* Paths: src/geometry/simd/**, include/geometry/simd/**
* Languages: cpp, cuda
* Max blast radius lines: 30

### [perf-zero-copy-002] (Enforcement: warn)
* Statement: High-throughput streaming loops and packet parsers must operate on memory views or slices without heap reallocations.
* Rationale: Intermediate buffer allocations degrade cache locality and introduce latency spikes in hot execution paths.
* Paths: src/**/streaming/**, src/**/simd/**
* Languages: cpp, python, rust
* Max blast radius lines: 30

### [py-boundary-isolation-003] (Enforcement: reject_diff)
* Statement: Domain models and business logic must not import from infrastructure or presentation layers.
* Rationale: Clean architecture requires dependency inversion: domain cores must remain completely decoupled from I/O.
* Paths: src/**/domain/**, src/**/models/**
* Languages: python
* Max blast radius lines: 30

### [py-no-print-001] (Enforcement: warn)
* Statement: Core library and domain modules must utilize structured logging instead of standard print statements.
* Rationale: Direct print calls pollute stdout and prevent log aggregation in production environments.
* Paths: src/**
* Languages: python
* Max blast radius lines: 30

### [py-no-wildcard-import-002] (Enforcement: reject_diff)
* Statement: Wildcard imports ('from module import *') are strictly prohibited.
* Rationale: Wildcard imports cause namespace pollution, mask circular dependencies, and degrade linter performance.
* Paths: src/**, tests/**
* Languages: python
* Max blast radius lines: 30

### [py-type-annotations-004] (Enforcement: warn)
* Statement: Public functions, methods, and classes must provide explicit parameter and return type annotations.
* Rationale: Static typing prevents runtime errors and provides clear machine-readable contracts for AI coding agents.
* Paths: src/**
* Languages: python
* Max blast radius lines: 30

### [react-hooks-deps-001] (Enforcement: reject_diff)
* Statement: React hooks must declare exhaustive dependencies and avoid mutations of component state during rendering.
* Rationale: Missing dependencies cause stale closure bugs and unpredictable re-rendering loops.
* Paths: src/**/*.jsx, src/**/*.tsx
* Languages: javascript, typescript
* Max blast radius lines: 30

### [rust-unsafe-safety-doc-001] (Enforcement: reject_diff)
* Statement: Every unsafe block in Rust must include a preceding '// SAFETY:' comment documenting invariant validity.
* Rationale: Audit requirement ensuring memory safety invariants are documented at each unsafe boundary.
* Paths: src/**/*.rs
* Languages: rust
* Max blast radius lines: 30

### [sec-rce-eval-004] (Enforcement: reject_diff)
* Statement: Direct execution of dynamic input strings via eval(), exec(), or unsanitized shell commands is strictly prohibited.
* Rationale: Arbitrary code execution vulnerabilities result from dynamic evaluation of untrusted strings.
* Paths: **/*
* Languages: javascript, python, typescript
* Max blast radius lines: 30

### [sec-secret-leak-002] (Enforcement: reject_diff)
* Statement: API keys, secrets, private certificates, and passwords must never be committed to source files.
* Rationale: Hardcoded credentials in Git histories result in credential compromise and audit failure.
* Paths: **/*
* Max blast radius lines: 30

### [sec-sql-injection-001] (Enforcement: reject_diff)
* Statement: SQL queries must use parameterized bind variables, never raw string interpolation or concatenation.
* Rationale: Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities.
* Paths: **/*
* Languages: go, java, javascript, python, typescript
* Max blast radius lines: 30

### [sec-ssrf-003] (Enforcement: reject_diff)
* Statement: Outbound HTTP requests constructed from dynamic input must validate targets against an allowlist and block private network ranges.
* Rationale: Unvalidated network requests allow SSRF attacks targeting cloud metadata services and internal infrastructure.
* Paths: **/*
* Languages: go, javascript, python, typescript
* Max blast radius lines: 30

### [team-agents-md-rule-1] (Enforcement: reject_diff)
* Statement: Touch only lines strictly required to complete the assigned task.
* Rationale: Extracted from team repository instructions in AGENTS.md.
* Paths: **/*
* Max blast radius lines: 30

### [team-agents-md-rule-2] (Enforcement: reject_diff)
* Statement: Never reformat adjacent code, comments, or imports.
* Rationale: Extracted from team repository instructions in AGENTS.md.
* Paths: **/*
* Max blast radius lines: 30

### [team-agents-md-rule-3] (Enforcement: reject_diff)
* Statement: If a patch exceeds 30 contiguous lines, halt and provide a technical justification.
* Rationale: Extracted from team repository instructions in AGENTS.md.
* Paths: **/*
* Max blast radius lines: 30

### [ts-floating-promises-002] (Enforcement: reject_diff)
* Statement: Async promises must be awaited, returned, or explicitly handled with a catch clause.
* Rationale: Floating unhandled promises cause silent async failures and unhandled promise rejections.
* Paths: src/**/*.ts, src/**/*.tsx
* Languages: typescript
* Max blast radius lines: 30

### [ts-no-any-001] (Enforcement: reject_diff)
* Statement: TypeScript variables, parameters, and return types must avoid explicit any and use unknown or generic constraints.
* Rationale: Any types disable compiler type checking and allow runtime type errors to propagate silently.
* Paths: src/**/*.ts, src/**/*.tsx
* Languages: typescript
* Max blast radius lines: 30
<!-- AOS_INVARIANTS_END -->

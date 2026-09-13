# Curated Rule Packs

### Pre-packaged architectural, security, and performance invariants ready for immediate installation into your repository substrate.

***

## The 3-Layer Guardrail Architecture

AOS organizes AI safety and behavior control into three distinct layers:

1. **Layer 1: Universal Non-Negotiables**: Baseline security hygiene applicable to every codebase (preventing secret leaks, raw SQL concatenation, arbitrary code execution).
2. **Layer 2: Stack-Specific Opt-In Packs**: Modular rule packs tailored to specific language ecosystems (TypeScript, FastAPI, React, Go, Rust).
3. **Layer 3: Automated Repository Ingestion (`aos ingest`)**: Autonomous scanner inspecting project configs (`tsconfig.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`) and team guidelines (`CLAUDE.md`, `AGENTS.md`) to synthesize custom guardrails matching how your team already works.

***

## Curated Pack Catalog

AOS provides nine curated packs across security, language runtimes, and system performance:

### 1. `security-owasp`
Defends against the most critical web application security vulnerabilities frequently introduced by LLMs.

!!! tip "Install Command"
    ```bash
    aos pack install security-owasp
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`sec-sql-injection-001`** | SQL queries must use parameterized bind variables, never raw string interpolation or concatenation. | Direct string concatenation creates critical SQL injection vulnerabilities in data access layers. | `reject_diff` | `**/*` (Python, JS, TS, Go, Java) |
| **`sec-secret-leak-002`** | API keys, secrets, private certificates, and passwords must never be committed to source files. | Hardcoded credentials in Git histories result in credential compromise and audit failures. | `reject_diff` | `**/*` (All languages) |
| **`sec-ssrf-003`** | Outbound HTTP requests constructed from dynamic input must validate targets against an allowlist and block private network ranges. | Unvalidated network requests allow SSRF attacks targeting cloud metadata services and internal infrastructure. | `reject_diff` | `**/*` (Python, JS, TS, Go) |

??? example "View Example Invariant Specification: `sec-sql-injection-001`"
    ```yaml
    id: "sec-sql-injection-001"
    version: 1
    status: "active"
    scope:
      paths:
        - "**/*"
      languages:
        - "python"
        - "javascript"
        - "typescript"
        - "go"
        - "java"

    invariant:
      statement: "SQL queries must use parameterized bind variables, never raw string interpolation or concatenation."
      rationale: "Direct string interpolation in SQL strings creates critical SQL injection vulnerabilities."
      enforcement: "reject_diff"
      max_blast_radius_lines: 30

    provenance:
      incident_id: "pack-security-owasp"
      git_commit: "HEAD"
      inscribing_agent: "pack-installer"
      created_at: "2026-09-08T18:00:00Z"
      last_verified_at: "2026-09-08T18:00:00Z"
      trigger_count: 0
    ```

***

### 2. `python-clean-architecture`
Enforces high-maintainability Python standards, clean separation of concerns, and type discipline.

!!! tip "Install Command"
    ```bash
    aos pack install python-clean-architecture
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`py-no-print-001`** | Core library and domain modules must utilize structured logging instead of standard print statements. | Direct print calls pollute standard output and bypass production log aggregation pipelines. | `warn` | `src/**` (Python) |
| **`py-no-wildcard-import-002`** | Wildcard imports (`from module import *`) are strictly prohibited. | Wildcard imports cause namespace pollution, mask circular dependencies, and degrade linter performance. | `reject_diff` | `src/**`, `tests/**` (Python) |
| **`py-boundary-isolation-003`** | Domain models and business logic must not import from infrastructure or presentation layers. | Clean architecture requires dependency inversion: domain cores must remain completely decoupled from I/O. | `reject_diff` | `src/**/domain/**`, `src/**/models/**` (Python) |
| **`py-type-annotations-004`** | Public functions, methods, and classes must provide explicit parameter and return type annotations. | Static typing prevents subtle runtime bugs and provides clear machine-readable contracts for AI coding agents. | `warn` | `src/**` (Python) |

***

### 3. `general-hygiene` (Universal Repository Health)
Enforces dependency manifest synchronization, prevents committing local environment credentials or build caches, and limits agent blast radius.

!!! tip "Install Command"
    ```bash
    aos pack install general-hygiene
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`gh-deps-sync-001`** | Changes to package dependency manifests must include synchronized updates to corresponding lockfiles. | Desynchronized dependency manifests and lockfiles cause irreproducible builds and unexpected environment drift. | `reject_diff` | `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod` |
| **`gh-no-artifacts-credentials-002`** | Build artifacts, compiled binaries, bytecode, local environment configuration files (.env), and IDE directories must not be committed. | Committing build outputs and local environment files bloats repository history and leaks local configuration secrets. | `reject_diff` | `**/*` |
| **`gh-blast-radius-limit-003`** | Automated agent changes must maintain surgical precision by touching only required lines within 50 lines. | Enforces surgical diff discipline to ensure modifications are reviewable and verifiable. | `reject_diff` | `**/*` |

***

### 4. `universal-security` (Layer 1 Baseline)
Non-negotiable baseline security guardrails applicable across all languages and frameworks.

!!! tip "Install Command"
    ```bash
    aos pack install universal-security
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`sec-no-hardcoded-secrets`** | Never commit API keys, private keys, or passwords. Use environment variables. | Hardcoded credentials result in catastrophic security compromise and credential exposure. | `reject_diff` | `**/*` (All) |
| **`sec-no-sql-concatenation`** | Database queries must use parameterized bind parameters, never raw string interpolation. | String interpolation in SQL statements creates critical SQL injection vulnerabilities. | `reject_diff` | `**/*` (All) |
| **`sec-no-eval-arbitrary-code`** | Never execute arbitrary dynamic code via eval() or exec() on untrusted inputs. | Dynamic execution allows remote code execution (RCE) vulnerabilities. | `reject_diff` | `**/*` (All) |

***

### 5. `web-typescript`
Strict type safety and promise handling for modern TypeScript services and web applications.

!!! tip "Install Command"
    ```bash
    aos pack install web-typescript
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`ts-strict-no-explicit-any`** | TypeScript code must not use explicit any casts; use unknown with type narrowing instead. | The any type bypasses compile-time safety and propagates untyped variables across the codebase. | `reject_diff` | `src/**/*.ts`, `src/**/*.tsx` |
| **`ts-no-floating-promises`** | All asynchronous Promise calls must be awaited or handled with explicit .catch() handlers. | Unhandled floating promises lead to silent background failures and unhandled promise rejections. | `reject_diff` | `src/**/*.ts`, `src/**/*.tsx` |

***

### 6. `python-fastapi`
Strict Pydantic models and OpenAPI schema integrity for Python web APIs.

!!! tip "Install Command"
    ```bash
    aos pack install python-fastapi
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`fastapi-typed-schemas`** | All route handlers must use typed Pydantic request and response models. | Ensures automatic schema validation, type safety, and accurate OpenAPI documentation. | `reject_diff` | `src/**/*.py`, `app/**/*.py` |
| **`fastapi-no-direct-request-body`** | Route handlers must not parse raw JSON bodies directly without Pydantic validation. | Unvalidated raw payloads bypass framework validation and introduce injection vectors. | `reject_diff` | `src/**/*.py`, `app/**/*.py` |

***

### 7. `react-modern`
Component boundary and hook dependency hygiene for modern React and Next.js applications.

!!! tip "Install Command"
    ```bash
    aos pack install react-modern
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`react-hooks-deps`** | useEffect and useMemo must declare all reactive dependencies explicitly. | Incomplete dependency arrays cause stale closures, desynchronized UI state, and render loops. | `reject_diff` | `src/**/*.jsx`, `src/**/*.tsx` |
| **`nextjs-use-client-directive`** | Interactive components with browser state must declare 'use client' at file top. | Next.js App Router requires explicit client boundaries to isolate browser-only runtime logic. | `reject_diff` | `src/app/**/*.tsx`, `src/components/**/*.tsx` |

***

### 8. `go-standard`
Idiomatic Go error propagation and concurrency safeguards.

!!! tip "Install Command"
    ```bash
    aos pack install go-standard
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`go-wrap-errors-with-fmt`** | Error returns must be checked and wrapped using fmt.Errorf with %w format specifier. | Preserves nested error chains and enables errors.Is and errors.As inspection in services. | `reject_diff` | `**/*.go` |
| **`go-goroutine-cancellation`** | Goroutines spawned to handle concurrent requests must listen to context.Done(). | Prevents leaked goroutines and zombie worker routines after client disconnects or cancellations. | `reject_diff` | `**/*.go` |

***

### 9. `rust-safety`
Safety audit trails and invariants for Rust unsafe operations.

!!! tip "Install Command"
    ```bash
    aos pack install rust-safety
    ```

| Rule ID | Statement | Rationale | Enforcement | Scope |
| :--- | :--- | :--- | :--- | :--- |
| **`rust-unsafe-safety-comment`** | Unsafe blocks must be preceded by a '// SAFETY:' comment explaining pointer or memory invariants. | Ensures team audits can verify memory safety preconditions and pointer validity at boundary points. | `reject_diff` | `src/**/*.rs` |

***

## How to Install Rule Packs

### Installing via CLI

#### 1. List Available Packs
View the packs bundled with AOS:

```bash
aos pack list
```

Output:
```text
Available Curated Invariant Packs:
- universal-security (3 rules)
- security-owasp (3 rules)
- web-typescript (2 rules)
- python-fastapi (2 rules)
- react-modern (2 rules)
- go-standard (2 rules)
- rust-safety (1 rule)
- python-clean-architecture (4 rules)
- performance-simd (2 rules)
```

#### 2. Install into Active Substrate (Immediate Enforcement)
By default, installing a pack promotes all its rules directly to `active` status:

```bash
aos pack install security-owasp
```

Output:
```text
Installed 3 rule(s) into active substrate:
- .agents/substrate/active/sec-sql-injection-001.yaml
- .agents/substrate/active/sec-secret-leak-002.yaml
- .agents/substrate/active/sec-ssrf-003.yaml
```

#### 3. Install into Candidate Substrate (Review Before Activation)
If you prefer to review rules before enforcing them on your team, use the `--candidate` flag:

```bash
aos pack install python-clean-architecture --candidate
```

Output:
```text
Installed 4 rule(s) into candidate substrate:
- .agents/substrate/candidate/py-no-print-001.yaml
- .agents/substrate/candidate/py-no-wildcard-import-002.yaml
- .agents/substrate/candidate/py-boundary-isolation-003.yaml
- .agents/substrate/candidate/py-type-annotations-004.yaml
```

You can review candidate rules using `aos rules list --status candidate` and promote them individually when ready.

#### 4. Synchronize Agent Instructions
After installing any pack, sync the newly added rules into your editor instructions:

```bash
aos sync
```

#### 5. Uninstall Packs (Human or Agent Tuning)
When repository requirements change or a pack is no longer needed, uninstall it via CLI or Web Control Plane:

```bash
# Archive pack rules (preserves audit provenance)
aos pack uninstall security-core

# Or permanently delete rules
aos pack uninstall security-core --delete
```

***

### Installing via Web Dashboard

You can also manage rule packs through the AOS Control Plane:

1. Launch the UI: `aos ui`
2. Open `http://127.0.0.1:8484` in your browser.
3. Switch to the **Rule Packs** tab (press ++3++).
4. Browse curated packs (`security-owasp`, `python-clean-architecture`, etc.) and click **Install Pack** to activate all invariants with a single click. Installed rules immediately populate the **Active Guardrails** tab and sync to connected tools.

***

## Layer 3: Automated Repository Ingestion (`aos ingest`)

Instead of picking rule packs manually, you can let AOS inspect your existing repository to synthesize tailored guardrails:

```bash
# Scan and preview tailored guardrails derived from your stack and guidelines
aos ingest --dry-run

# Inscribe and immediately activate tailored guardrails plus stack-recommended packs
aos ingest --promote --install-packs
```

### What Ingestion Inspects
1. **Config Manifests**: Scans `tsconfig.json` (strict typing), `pyproject.toml` (framework contracts), `Cargo.toml` (unsafe audits), `go.mod` (error wrapping), `package.json` (React hooks and Next.js directives).
2. **Team Instruction Files**: Extracts human rules from `CLAUDE.md`, `AGENTS.md`, and `.cursorrules`, stripping circular instruction wrappers and synthesizing machine-enforced invariants.
3. **Web Control Plane Integration**: Click **Scan Codebase** in the top navigation of the UI dashboard (`http://127.0.0.1:8484`) to preview and activate tailored guardrails with one click.

***

## Authoring Custom Organizational Rule Packs

Organizations often need company-wide standards: internal security guidelines, compliance requirements, or proprietary framework patterns.

### Step 1: Create the Pack Directory Layout
Create a dedicated pack folder in your enterprise repository:

```
my-org-packs/
├── enterprise-standards/
│   ├── pack.yaml
│   ├── rules/
│   │   ├── sec-corp-auth-001.yaml
│   │   └── arch-rpc-timeout-002.yaml
```

### Step 2: Define the Pack Manifest (`pack.yaml`)

```yaml
name: "enterprise-standards"
version: "1.0.0"
description: "Core compliance and resilience invariants for ACME Corp."
author: "Security & Platform Engineering"
rules:
  - id: "sec-corp-auth-001"
    file: "rules/sec-corp-auth-001.yaml"
  - id: "arch-rpc-timeout-002"
    file: "rules/arch-rpc-timeout-002.yaml"
```

### Step 3: Define Atomic Invariant Files

Create `rules/arch-rpc-timeout-002.yaml`:

```yaml
id: "arch-rpc-timeout-002"
version: 1
status: "active"
scope:
  paths:
    - "src/clients/**"
    - "services/**"
  languages:
    - "python"
    - "typescript"
    - "go"

invariant:
  statement: "All outbound RPC and HTTP client invocations must configure explicit connect and read timeouts."
  rationale: "Default unbounded timeouts cause cascading thread pool exhaustion during upstream service degradations."
  enforcement: "reject_diff"
  max_blast_radius_lines: 25

provenance:
  incident_id: "inc-2026-postmortem-44"
  git_commit: "HEAD"
  inscribing_agent: "corp-platform-team"
  created_at: "2026-09-08T00:00:00Z"
  last_verified_at: "2026-09-08T00:00:00Z"
  trigger_count: 0
```

### Step 4: Validate Custom Rules
Validate that your custom rules conform to the formal AOS schema:

```bash
aos rules check src/clients/payment_client.py
```

### Step 5: Distribute Across Repositories via Fleet Mesh
Once validated, distribute your custom rules to all company repositories using the enterprise fleet ledger:

```bash
# Publish rule to organizational fleet
aos fleet publish arch-rpc-timeout-002 --repo-id "platform-standards"

# Downstream repositories pull the rule
aos fleet sync
```

Every AI agent working in any repository across the organization will instantly inherit the updated guardrail.

# Agent Operating Substrate (AOS)

<p align="center">
  <img src="docs/assets/banner.jpg" alt="Agent Operating Substrate (AOS) Hero Banner" width="100%">
</p>

### The Universal AI Behavior Firewall & Vendor-Agnostic Control Plane across Gemini, Claude, Codex, Copilot, Cursor, and Windsurf.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](#license)
[![Zero External Dependencies](https://img.shields.io/badge/dependencies-zero%20external-orange.svg)](#architecture)
[![Vendor Agnostic](https://img.shields.io/badge/AI%20models-vendor--agnostic-blueviolet.svg)](#supported-ai-ecosystems--models)
[![MCP Protocol Ready](https://img.shields.io/badge/MCP-compatible-purple.svg)](docs/getting-started.md#step-5-enable-the-model-context-protocol-mcp-server)
[![Pre-Commit Enforced](https://img.shields.io/badge/git-pre--commit%20firewall-red.svg)](docs/getting-started.md#step-6-install-the-universal-git-pre-commit-hook)

> [!NOTE]
> **Autonomous Agent Project Notice**: The Agent Operating Substrate is designed, implemented, and maintained autonomously by AI agents (`AOS Agent`). The agents identify codebase improvements, conduct failure autopsies, synthesize invariant rules, and maintain repository health under human supervisory oversight. All post-initial release contributions follow a strict Pull Request / Merge Request model to support parallel multi-agent and human collaboration.

***

## The Universal AI Behavior Firewall & Memory Layer

Enterprises and developers cannot afford AI vendor lock-in or model-specific behavioral drift. Whether your engineers prompt Google Gemini 1.5 Pro, Anthropic Claude 3.5 Sonnet, OpenAI GPT-4o / Codex, Amazon Q Developer, or run local DeepSeek and Llama models, each model interprets prompts differently, hallucinates distinct anti-patterns, and loses context once the session ends.

**AOS eliminates vendor lock-in by decoupling repository guardrails from the model provider.**

No matter which AI assistant your team selects today or migrates to tomorrow, AOS guarantees the exact same repository invariants, institutional memory, and deterministic pre-commit enforcement.

### Three Structural Roadblocks AOS Solves

1. **Day-One Amnesia:** Every agent session starts from a blank slate. When an agent violates an architectural invariant, introduces memory bugs, or breaks an unspoken convention, an engineer manually intervenes. Once that context window closes, the lesson evaporates. The next agent invocation repeats the identical mistake.
2. **The Human Air-Traffic Controller Bottleneck:** Multi-agent development remains strictly hub-and-spoke. Engineers spend hours manually shuttling diffs, error traces, and prompts between worker, critique, and test agents.
3. **Broken Commits and Silent Regressions:** AI agents hallucinate deprecated APIs, alter adjacent imports, and introduce diff bloat that slips past human reviewers and pollutes Git history.

**AOS turns your repository into a self-defending, self-improving substrate.** It provides an **Autonomous Behavior Firewall** that deterministically blocks invalid agent commits, and **Permanent Memory** that records failures as machine-enforced invariants compiled directly into every agent harness.

***

## Before AOS vs After AOS

| Dimension | Before AOS | With AOS |
| :--- | :--- | :--- |
| **Memory Retention** | **Goldfish Memory:** Lessons vanish the moment the chat context closes. The same hallucinated APIs and anti-patterns recur indefinitely. | **Permanent Repo Immunity:** Failures trigger machine-inscribed YAML invariants stored in Git. Agents inherit lessons forever. |
| **Agent Coordination** | **Human Air-Traffic Controller:** Engineers manually copy-paste diffs and prompts between worker, review, and test agents. | **Autonomous Stigmergy:** Decentralized local blackboard (`events.jsonl`). Agents coordinate unprompted through environmental traces. |
| **Code Quality Defense** | **Broken Production Commits:** Regressions and style violations slip past reviews into CI and production branches. | **Git Pre-Commit Bouncer:** Universal git hook (`aos hook run`) deterministically blocks non-compliant commits before code leaves the laptop. |
| **IDE & CLI Harmonization** | **Prompt Drift & Siloed Configs:** Fragile, manual syncing across `.cursorrules`, `.windsurfrules`, Copilot, and Claude prompts. | **Single Source of Truth:** `aos sync` compiles active substrate rules into all IDE and CLI harnesses with zero drift. |
| **Incident Response** | **Manual Post-Mortems:** Humans explain errors in chat and cross their fingers that future agents remember. | **Automated Execution Autopsy:** `aos exec` intercepts test and compiler crashes and automatically synthesizes candidate invariant rules. |
| **Rule Evolution** | **Prompt Bloat & Conflicts:** Monolithic prompt files grow unmanageable, contradict each other, and degrade model reasoning. | **Autonomous Rule Curation:** `aos curate` detects conflicts, subsumes redundant rules, and archives stale constraints automatically. |
| **Enterprise Governance** | **Fragmented Policy Spread:** Security standards live in wiki docs that AI coding agents never read. | **Cross-Repo Fleet Mesh:** `aos fleet publish` and `aos fleet sync` propagate compliance policies across hundreds of repositories. |
| **Infrastructure Overhead** | **Complex Cloud SaaS:** External vector databases, expensive SaaS orchestrators, and network latency. | **Zero External Infrastructure:** 100% local file primitives, Git-backed versioning, JSON/YAML schemas, and SQLite. |

***

## Supported AI Ecosystems & Models

AOS is engineered for complete AI vendor neutrality. By decoupling repository invariants and verification from any specific model provider, AOS guarantees consistent guardrails across every tool in your stack:

| AI Ecosystem / Model | Supported Tooling & Interfaces | Integration Mode | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | Gemini Code Assist, Gemini CLI, Antigravity | Live MCP Server (`aos mcp`), CLI execution autopsy (`aos exec`), Stigmergic Blackboard | Pre-commit hook & live MCP tools |
| **Anthropic Claude** | Claude Code, Claude Desktop, Claude Projects | Single-source `CLAUDE.md` sync (`aos sync`), native MCP stdio server | Deterministic pre-commit firewall (`aos hook run`) |
| **OpenAI Codex & ChatGPT** | OpenAI Codex, ChatGPT Developer Mode, GPT-4o | Prompt projection, MCP protocol, Git pre-commit barrier | Substrate invariant evaluation & diff bouncer |
| **GitHub Copilot** | VS Code, JetBrains, Visual Studio, Copilot Chat | Automatic `.github/copilot-instructions.md` compilation | Pre-commit hook & CI pipeline gatekeeper |
| **Cursor IDE** | Cursor Composer, Cursor Agent Mode | `.cursorrules` and `.cursor/rules/*.mdc` synchronization, MCP server | Instant rule prompt injection & pre-commit hook |
| **Windsurf / Codeium** | Windsurf IDE, Codeium Cascade | `.windsurfrules` automatic synchronization | Staged diff bouncer & rule validation |
| **Aider, Roo Code & Cline** | Aider CLI, Roo Code, Cline (VS Code) | Context injection (`.agents/substrate/active`), stdio MCP | Autonomous pre-commit barrier & execution autopsy |
| **Amazon Q Developer** | Amazon Q (AWS Toolkit, VS Code, JetBrains) | Substrate prompt compilation & Git pre-commit barrier | Deterministic pre-commit enforcement & CI check |
| **Local & Open Weights** | DeepSeek-R1 / V3, Llama 3, Mistral, Qwen (via Ollama, vLLM) | File-based substrate, local SQLite, stdio MCP | 100% offline, local-first behavior firewall |

***

## Architecture

AOS operates across three integrated planes: prompt projection, live agent context tools, and deterministic git enforcement.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AGENT HARNESS INTERACTION                          │
│                                                                             │
│  Gemini / Antigravity     Claude Code     Codex / ChatGPT    GitHub Copilot │
│  Cursor (.cursorrules)    Windsurf IDE    Aider / Cline      Amazon Q       │
└───────────────────────────────────────▲─────────────────────────────────────┘
                                        │ (aos sync: prompt projection)
┌───────────────────────────────────────┴─────────────────────────────────────┐
│                           AGENT OPERATING SUBSTRATE                         │
│                                                                             │
│   ┌───────────────────────────┐         ┌───────────────────────────────┐   │
│   │    Active Invariants      │         │   Asynchronous Blackboard     │   │
│   │ (.agents/substrate/active)│         │ (.agents/blackboard/events)   │   │
│   └─────────────┬─────────────┘         └───────────────┬───────────────┘   │
│                 │                                       │                   │
│   ┌─────────────▼─────────────┐         ┌───────────────▼───────────────┐   │
│   │   Runtime MCP Server      │         │    Autonomous Peer Mesh       │   │
│   │ (aos_rules_check, etc.)   │         │ (worker, auditor, critic)     │   │
│   └───────────────────────────┘         └───────────────────────────────┘   │
└───────────────────────────────────────┬─────────────────────────────────────┘
                                        │
┌───────────────────────────────────────▼─────────────────────────────────────┐
│                         DETERMINISTIC GIT BARRIER                           │
│                                                                             │
│   Developer / Agent Commit ───> .git/hooks/pre-commit (aos hook run)        │
│                                  ├── Invariant Rules Evaluation             │
│                                  ├── Contiguous Diff Limits (<30 lines)     │
│                                  └── Punctuation & Style Enforcement        │
│                                  └── PASSED: Commit Recorded in Git Graph   │
│                                  └── FAILED: Deterministic Exit Code 1      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Core Architecture Components

1. **Prompt Sync:** `aos sync` compiles all active machine-readable invariants from `.agents/substrate/active/` into your team's existing agent configuration files (`.cursorrules`, `.cursor/rules/aos-invariants.mdc`, `.windsurfrules`, `.github/copilot-instructions.md`, and `CLAUDE.md`). Rules stay bounded within deterministic HTML comment tags without overwriting custom prompt instructions.
2. **Model Context Protocol (MCP) Server:** `aos mcp` provides a native stdio protocol server. Any MCP-compatible tool (Cursor, Claude Desktop, Antigravity, Gemini Code Assist, Cline) can dynamically query active rules, inspect file blast radius, post intents, and record failure autopsies.
3. **Git Pre-Commit Barrier:** `aos hook run` acts as the repo bouncer. Every staged diff is evaluated against active invariants before a commit is created. Violations halt execution immediately with exact file and line references.
4. **Stigmergic Blackboard:** Agents communicate asynchronously by reading and appending events in `.agents/blackboard/events.jsonl`. When a worker announces an intent, an auditor injects invariants, and an adversarial critic generates edge-case tests, entirely without human intervention.
5. **Execution Autopsy Engine:** `aos exec -- <command>` intercepts build or test failures, diagnoses root causes, and inscribes candidate rules under `.agents/substrate/candidate/` for peer review.

```mermaid
flowchart LR
    subgraph S1["1. Knowledge Substrate"]
        R["Active Rules<br/>(.agents/substrate/active/)"]
        B["Blackboard Events<br/>(.agents/blackboard/events.jsonl)"]
    end

    subgraph S2["2. Developer & Agent Tooling"]
        P["Prompt Sync<br/>(Cursor, Copilot, Claude)"]
        M["MCP Server<br/>(Live Invariant Query Tools)"]
    end

    subgraph S3["3. Enforcement & Verification"]
        H["Git Pre-Commit Hook<br/>(Deterministic Barrier)"]
        CI["Continuous Integration<br/>(aos ci check)"]
    end

    R -->|aos sync| P
    R -->|stdio protocol| M
    P --> H
    M --> H
    H -->|Passed| CI
    CI -->|Failure Autopsy| R
```

***

## 60-Second Quickstart

Get your repository running with autonomous agent enforcement in four simple commands:

### 1. Install AOS
AOS is built with pure Python and zero external runtime services:

```bash
pip install -e .
```

### 2. Initialize the Substrate
Create the local substrate structure under `.agents/`:

```bash
aos init
```

Output:
```text
Created config: .agents/config.yaml
Created event stream: .agents/blackboard/events.jsonl
Substrate initialized under .agents/
```

### 3. Install a Curated Rule Pack
Bootstrap production-grade guardrails for security or architecture:

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

### 4. Sync Agent Prompts
Compile all active invariants into Cursor, Windsurf, Copilot, and Claude Code:

```bash
aos sync
```

Output:
```text
Synced 5 agent harness configuration(s):
- cursor: .cursorrules
- cursor_mdc: .cursor/rules/aos-invariants.mdc
- windsurf: .windsurfrules
- copilot: .github/copilot-instructions.md
- claude: CLAUDE.md
```

### 5. Install the Universal Git Pre-Commit Hook
Enforce active invariants on every commit automatically:

```bash
aos hook install
```

### 6. Verify Files Instantly
Check any file or staged diff against active invariants:

```bash
aos rules check src/
```

***

## 3 Real-World Proofs

AOS is running right now in production repositories. Here are three machine-enforced proofs executing directly inside this codebase:

### Proof 1: SIMD 32-Byte Alignment Crash Prevention
* **The Incident:** High-throughput vector geometry kernels (AVX2/AVX-512) crash with general protection faults when fed unaligned memory pointers. Standard LLMs frequently generate naive allocations, causing runtime panics.
* **The Active Invariant (`perf-simd-012.yaml`):** Requires 32-byte alignment on all buffers in `src/geometry/simd/**`.
* **The Interception:** When an agent attempts to edit vector code:
  ```bash
  aos rules check src/geometry/simd/kernel.cpp
  ```
  AOS flags the rule, binding the agent to emit `alignas(32)` buffers before code reaches the compiler.

### Proof 2: Surgical Diff & Punctuation Pre-Commit Bouncer
* **The Incident:** Coding agents frequently over-refactor code, reformatting adjacent imports, changing comments, or injecting stylistic typography like em dashes that violate conventions.
* **The Active Invariants (`aos-diff-002` and `aos-punct-001`):** Mandate surgical changes (<30 contiguous lines without justification) and zero em dashes across all prose and code.
* **The Interception:** When an agent stages a file containing forbidden punctuation:
  ```bash
  git commit -m "docs: update notes"
  ```
  The pre-commit hook runs `aos hook run` and blocks the commit deterministically:
  ```text
  [AOS Hook] Evaluating staged files against active substrate invariants...
  - [aos-punct-001] Violation: Forbidden em dash detected. (reject_diff)
  Commit blocked by AOS invariant enforcer.
  ```
  The agent reads the rejection message, corrects the punctuation, and re-commits without human intervention.

### Proof 3: Unprompted Peer Mesh Convergence
* **The Incident:** Coordinating worker, auditor, and adversarial critic agents traditionally requires manual human dispatching or expensive cloud orchestrators.
* **The Stigmergic Mesh:** Agents collaborate asynchronously through `.agents/blackboard/events.jsonl`:
  ```bash
  aos mesh simulate --desc "Optimize vector boundary conditions" --files src/geometry/simd/kernel.cpp
  ```
  Output:
  ```text
  Peer Mesh Simulation: Intent 'intent-e41c30' - Status: CONVERGED
  Emitted 5 event(s) to blackboard:
  - [INTENT_ANNOUNCEMENT] From: worker-agent
  - [INVARIANT_INJECTION] From: auditor-agent
  - [ADVERSARIAL_CHALLENGE] From: adversarial-critic-agent
  - [PEER_CRITIQUE] From: auditor-agent
  - [PEER_CONVERGENCE] From: consensus-orchestrator
  ```
  The engineering team is alerted only when consensus is reached.

***

## Enterprise & Commercial Readiness

As enterprises deploy hundreds of AI coding agents across engineering teams, they face **Distributed Agent Amnesia**: team A discovers and patches a critical security flaw, but team B and team C repeat the exact same vulnerability next week. AOS provides an enterprise-grade control plane designed for commercial reliability and governance.

### 1. SOC2 & AI Audit Compliance
Every autonomous agent modification, intent declaration, invariant check, and consensus decision is permanently recorded in a tamper-proof, append-only event stream (`.agents/blackboard/events.jsonl`).
* **Immutable Audit Trail:** Track which model proposed a diff, which invariant validated or rejected it, and which human or peer agent approved the change.
* **Cryptographic & Git Provenance:** Invariants record originating incident IDs, git commit hashes, author agent signatures, and verification timestamps.
* **Compliance Ready:** Satisfies SOC2 Type II, ISO 27001, and enterprise AI safety audits without transmitting proprietary code to third-party clouds.

### 2. Eliminating AI Regression Costs
AI code generation velocity is meaningless if senior engineers spend hours diagnosing hallucinations and fixing broken builds.
* **Halting Hallucinations at the Source:** Intercepts hallucinated third-party dependencies, invalid imports, and deprecated API calls before code reaches pull request review.
* **Preventing Secret Leaks:** Built-in OWASP rules (`sec-secret-leak-002`) deterministically block API tokens, credentials, and private keys before they enter git history.
* **Pre-Commit Enforcement:** The universal git pre-commit hook runs in milliseconds locally, cutting CI re-run costs and preventing broken commits from reaching master branches.

### 3. Centralized Fleet Governance Across 100+ Repositories (`aos fleet`)
Connect isolated repositories into an institutional knowledge network:
* **Global Policy Propagation:** Platform teams broadcast promoted invariants into a shared fleet mesh (`.agents/fleet.db`) with `aos fleet publish`.
* **Zero Policy Drift:** Microservices and product repositories ingest organizational security and architectural rules with `aos fleet sync`.
* **Sovereign & Local-First:** 100% offline-capable, backed by local SQLite and Git. Zero source code or proprietary schemas are transmitted to external SaaS platforms.

```
Without Fleet Synchronization (Isolated & Vulnerable):
Team A fixes critical bug ──> Knowledge stays trapped in Team A repo
Team B AI writes same bug  ──> Re-enters codebase, redundant debugging
Team C AI writes same bug  ──> Reaches production incident

With AOS Enterprise Fleet Synchronization:
Team A (Origin) ──> Inscribes Rule ──> aos fleet publish
                                            │
                                            ▼
                              ┌───────────────────────────┐
                              │   Enterprise Fleet Mesh   │
                              │     (.agents/fleet.db)    │
                              └─────────────┬─────────────┘
                                            │
                                            ▼ (aos fleet sync)
               ┌────────────────────────────┴────────────────────────────┐
               ▼                                                         ▼
    Team B (Active Guardrail)                                 Team C (Active Guardrail)
    Agent blocked from mistake                                Agent blocked from mistake
```

### Key Enterprise Capabilities

* **Zero Policy Drift:** Platform and security teams publish global compliance rules (`sec-sql-injection-001`, `sec-secret-leak-002`) into the fleet mesh with `aos fleet publish`. Downstream repositories synchronize them instantly with `aos fleet sync`.
* **Auditable Provenance:** Every invariant records full compliance metadata: originating incident ID, git commit hash, author agent identity, and verification timestamps.
* **SOC2 & ISO 27001 Ready:** Invariants serve as living, version-controlled evidence that security constraints are deterministically enforced on every local commit and in CI.
* **Air-Gapped & Local-First:** Backed by local SQLite and Git. Zero source code or proprietary schemas are transmitted to external third-party cloud services.

***

## CLI Command Reference

| Command | Purpose |
| :--- | :--- |
| `aos init` | Initialize `.agents/` substrate and configuration in the target repository. |
| `aos rules list` | List all invariant rules filtered by status (`active`, `candidate`, `archive`). |
| `aos rules check <path>` | Check target files or directories against active invariant rules. |
| `aos enforce <rule-id>` | Deterministically enforce an invariant rule against target files. |
| `aos sync` | Sync active invariants into Gemini, Claude, Codex, Copilot, Cursor, Windsurf, Aider, and Cline. |
| `aos hook install` | Install the universal git pre-commit hook into `.git/hooks/`. |
| `aos hook run` | Execute pre-commit validation against staged files. |
| `aos mcp` | Start the Model Context Protocol stdio server for live agent integration. |
| `aos exec -- <cmd>` | Wrap command execution with autonomous failure autopsy and rule inscription. |
| `aos pack list` | List available curated invariant rule packs. |
| `aos pack install <pack>` | Install a curated rule pack into active (or candidate) status. |
| `aos ingest` | Scan repository conventions and manifests to synthesize tailored invariants. |
| `aos mesh simulate` | Simulate autonomous peer-to-peer agent mesh coordination. |
| `aos fleet publish <id>` | Publish a local rule to the enterprise fleet mesh. |
| `aos fleet sync` | Synchronize global fleet invariants into the local repository. |
| `aos curate` | Autonomously prune, consolidate, and archive substrate rules. |
| `aos identity` | Manage autonomous agent identities and supervisory mailboxes. |
| `aos ui` | Launch the local web dashboard visualizer. |

***

## Documentation

* [Overview & Core Thesis](docs/index.md): Motivation, failure modes, and stigmergic solution.
* [Getting Started Guide](docs/getting-started.md): Step-by-step setup, harness sync, and MCP configuration.
* [AI Vendor Abstraction](docs/vendor-abstraction.md): Decoupling repository invariants and control planes from LLM model providers.
* [IDE & Tool Integration](docs/ide-integration.md): Setup Cursor, Claude Code, Copilot, Windsurf, and Git pre-commit hooks.
* [Control Plane Web Dashboard](docs/control-plane-ui.md): Visual tour of real-time guardrail controls, diff testing, and incident autopsies.
* [Curated Rule Packs](docs/rule-packs.md): Catalog of security, clean architecture, and SIMD performance invariant packs.
* [Architecture & Theoretical Foundations](docs/architecture.md): The three inscription loops, blackboard event bus, and mathematical model.
* [CLI Reference](docs/cli-reference.md): Complete reference of all subcommands, arguments, and environment variables.
* [Enterprise Fleet Synchronization](docs/enterprise-fleet.md): Cross-repository governance and fleet mesh management.
* [System Specification](SPEC.md): Formal YAML schemas and protocol specifications.
* [Agent Guidelines](AGENTS.md): Strict operating rules for autonomous agents working in this repository.

***

## License

Distributed under the standard MIT License.

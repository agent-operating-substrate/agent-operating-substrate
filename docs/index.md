# Agent Operating Substrate (AOS)

### The Universal AI Behavior Firewall & Vendor-Agnostic Control Plane across Gemini, Claude, Codex, Copilot, Cursor, and Windsurf.

***

> [!NOTE]
> **Autonomous Agent Development & Transparency**: The Agent Operating Substrate is designed, implemented, and maintained autonomously by AI agents (`AOS Agent`). The agents identify codebase improvements, conduct failure autopsies, synthesize invariant rules, and maintain repository health under human supervisory oversight. All post-initial release development proceeds via Pull Requests / Merge Requests to facilitate parallel collaboration between multiple agents and human engineers.

## The Core Thesis

The Agent Operating Substrate (AOS) is a local behavior firewall and vendor-agnostic memory layer for AI coding assistants. Whether your team prompts Google Gemini 1.5 Pro, Anthropic Claude 3.5 Sonnet, OpenAI Codex / GPT-4o, Amazon Q Developer, or local DeepSeek and Llama models, AOS prevents agents from repeating known mistakes, violating architectural boundaries, or introducing breaking diffs into your codebase.

Modern software engineering agents produce code with unprecedented velocity. Yet engineering teams deploying autonomous agents in production face two compounding bottlenecks: **AI Vendor Lock-in** and **the AI Babysitting Tax**.

Left unconstrained, coding agents routinely hit three structural failure modes:

### 1. Agent Amnesia (Day-One Goldfish Memory)
Every agent invocation begins from a completely blank slate. When an agent violates an architectural invariant, introduces memory misalignment, or breaks an unspoken convention, an engineer must manually diagnose the issue and re-prompt the model.

The moment that chat session terminates or the context window rolls over, the hard-won lesson evaporates. The next agent prompt repeats the identical mistake, triggering the same debugging cycle.

### 2. The Human Air-Traffic Controller Bottleneck
Multi-agent workflows remain strictly hub-and-spoke. Engineers are forced into manual dispatcher roles: prompting Agent A to draft a patch, copying the diff to Agent B for review, piping test traces to Agent C for debugging, and arbitrating conflicts by hand.

This constant manual routing creates cognitive exhaustion and prevents engineering organizations from achieving true agent autonomy.

### 3. Model Drift and Vendor Lock-in
Engineering teams cannot afford to tie repository safety to a single model provider. When models update or teams switch between Gemini, Claude, Codex, or local open-weights LLMs, unstructured natural language prompts drift, rules get silently bypassed, and regressions resurface.

```
Traditional Hub-and-Spoke (Fragile, Manual, High Babysitting Tax):
Agent A <======> Human Engineer <======> Agent B
                     ▲
                     │ (Manual Prompts, Diff Copying, Error Tracing)
                     ▼
                  Agent C

AOS Stigmergic Substrate (Autonomous, Decentralized, Zero Human Routing):
Agent A ───────┐                       ┌─────── Agent B
               ▼                       ▼
     ┌───────────────────────────────────────────┐
     │         Repository Rule Substrate         │
     │  (.agents/substrate/ & blackboard/events) │
     └───────────────────────────────────────────┘
               ▲                       ▲
Agent C ───────┘                       └─────── Agent D
```

### The Solution: The Stigmergic Rule Substrate

AOS replaces manual human routing with **stigmergy**: coordination through shared repository files without human air-traffic control.

Instead of an engineer manually shuttling prompts and error messages back and forth, AOS transforms your Git repository into a shared environment: an evolving, machine-readable ledger of invariant rules, failure post-mortems, and peer contracts that agents read, challenge, and refine autonomously.

**AOS operates in the background, defending your codebase without requiring manual human oversight.**

***

## Before AOS vs After AOS

| Dimension | Before AOS | With AOS |
| :--- | :--- | :--- |
| **Agent Memory** | **Goldfish Memory:** Lessons vanish the moment the chat context closes. Identical bugs recur endlessly. | **Permanent Repo Immunity:** Failures trigger machine-inscribed YAML invariants stored in Git. Agents inherit lessons forever. |
| **Agent Coordination** | **Human Air-Traffic Controller:** Engineers manually copy-paste diffs and prompts between worker, review, and test agents. | **Autonomous Stigmergy:** Decentralized local blackboard (`events.jsonl`). Agents coordinate unprompted through environmental traces. |
| **Code Quality Defense** | **Broken Production Commits:** Regressions and style violations slip past reviews into CI and production branches. | **Git Pre-Commit Bouncer:** Universal git hook (`aos hook run`) deterministically blocks non-compliant commits before code leaves the laptop. |
| **IDE & CLI Harmonization** | **Prompt Drift & Siloed Configs:** Fragile, manual syncing across `.cursorrules`, `.windsurfrules`, Copilot, and Claude prompts. | **Single Source of Truth:** `aos sync` compiles active substrate rules into all IDE and CLI harnesses with zero drift. |
| **Incident Response** | **Manual Post-Mortems:** Humans explain errors in chat and cross their fingers that future agents remember. | **Automated Execution Autopsy:** `aos exec` intercepts test and compiler crashes and automatically synthesizes candidate invariant rules. |
| **Rule Evolution** | **Prompt Bloat & Conflicts:** Monolithic prompt files grow unmanageable, contradict each other, and degrade model reasoning. | **Autonomous Rule Curation:** `aos curate` detects conflicts, subsumes redundant rules, and archives stale constraints automatically. |
| **Enterprise Governance** | **Fragmented Policy Spread:** Security standards live in wiki docs that AI coding agents never read. | **Cross-Repo Fleet Mesh:** `aos fleet publish` and `aos fleet sync` propagate compliance policies across hundreds of repositories. |
| **Infrastructure Overhead** | **Complex Cloud SaaS:** External vector databases, expensive SaaS orchestrators, and network latency. | **Zero External Infrastructure:** 100% local file primitives, Git-backed versioning, JSON/YAML schemas, and SQLite. |

***

## The 3 Pillars of AOS

AOS protects and equips autonomous coding agents through three interconnected pillars:

### Pillar 1: The Autonomous Behavior Firewall
A deterministic gatekeeper running directly on your developer machine and CI pipeline. The universal pre-commit hook (`aos hook run`) inspects staged diffs against active repository invariants, enforcing surgical diff limits (<30 contiguous lines), style constraints, and architectural boundaries before any commit is written to Git history.

### Pillar 2: Permanent Context Memory
Eliminates prompt drift across your team's developer tools. `aos sync` compiles active substrate invariants into your team's existing agent configuration files (`.cursorrules`, `.cursor/rules/aos-invariants.mdc`, `.windsurfrules`, `.github/copilot-instructions.md`, and `CLAUDE.md`). The embedded Model Context Protocol (MCP) server (`aos mcp`) provides interactive tools allowing LLM agents to query applicable rules and check blast radius before writing code.

### Pillar 3: The Self-Improving Inscription Loop
When builds fail or tests crash, `aos exec -- <command>` intercepts the failure, conducts an automated root-cause autopsy, and inscribes candidate rules under `.agents/substrate/candidate/`. Agents coordinate unprompted over `.agents/blackboard/events.jsonl`, while `aos curate` consolidates overlapping rules and retires decayed constraints.

***

## 60-Second Quickstart

Equip your repository with autonomous agent enforcement in five simple steps:

```bash
# 1. Install AOS (pure Python, zero external dependencies)
pip install -e .

# 2. Initialize the .agents/ substrate directory structure
aos init

# 3. Install a curated production security rule pack
aos pack install security-owasp

# 4. Sync active invariants to your agent harnesses (Cursor, Windsurf, Copilot, Claude)
aos sync

# 5. Install the universal git pre-commit firewall
aos hook install
```

Validate any source file or proposed diff instantly:

```bash
aos rules check src/aos/cli.py --enforce
```

***

## 3 Real-World Proofs

AOS is not a speculative concept. The following three scenarios demonstrate real, machine-enforced proofs executing directly inside this repository.

### Proof 1: SIMD 32-Byte Alignment Crash Prevention

**The Problem:** High-throughput vector kernels (AVX2 and AVX-512) crash with general protection faults when fed unaligned memory pointers. Standard LLMs frequently generate naive heap allocations or unaligned structs, causing silent crashes or runtime panics.

**The Machine Inscription (`.agents/substrate/active/perf-simd-012.yaml`):**

```yaml
id: "perf-simd-012"
version: 1
status: "active"
scope:
  paths:
    - "src/geometry/simd/**"
    - "include/geometry/simd/**"
  languages:
    - "cpp"
    - "cuda"

invariant:
  statement: "PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries."
  rationale: "Unaligned memory loads trigger GP faults under high-throughput geometry sweeps."
  enforcement: "reject_diff"
  max_blast_radius_lines: 20

provenance:
  incident_id: "inc-2026-09-08-01"
  git_commit: "4f9a12c8"
  inscribing_agent: "forensic-auditor-v2"
  peer_consensus_agent: "rule-curator-v1"
  created_at: "2026-09-08T18:55:00Z"
  last_verified_at: "2026-09-08T18:55:00Z"
  trigger_count: 3
```

**The Autonomous Interception:**

When an agent proposes changes to vector geometry files, AOS checks the file against the active rule before code touches the compiler:

```bash
aos rules check src/geometry/simd/kernel.cpp
```

Output:

```text
File: src/geometry/simd/kernel.cpp
  Matched Rule: [perf-simd-012] PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries.
    Enforcement: reject_diff
    Rationale:   Unaligned memory loads trigger GP faults under high-throughput geometry sweeps.
```

The agent is immediately constrained to emit `alignas(32)` buffers, preventing compiler and runtime faults before they occur.

***

### Proof 2: Surgical Diff and Punctuation Pre-Commit Interception

**The Problem:** Autonomous agents frequently over-refactor code, reformatting adjacent imports, changing comments, or injecting stylized typography that violates team conventions.

**The Inscriptions (`aos-diff-002` and `aos-punct-001`):**

* **`aos-diff-002`**: Enforces surgical changes. Patches must touch only necessary lines; any change exceeding 30 contiguous lines requires explicit justification.
* **`aos-punct-001`**: Strict punctuation constraint. Zero em dashes in all prose, documentation, commit messages, and comments.

**Autonomous Pre-Commit Defense:**

Install the universal git hook once:

```bash
aos hook install
```

When an agent or developer attempts to commit a file containing a forbidden em dash or excessive diff bloat:

```bash
git commit -m "docs: add release notes"
```

AOS pre-commit hook runs `aos hook run` and blocks the commit:

```text
[AOS Hook] Evaluating staged files against active substrate invariants...
- [aos-punct-001] docs/release-notes.md:14: Violation of 'aos-punct-001': Forbidden em dash (\u2014) detected. (reject_diff)

Commit blocked by AOS invariant enforcer. Correct the violations listed above.
```

The commit is rejected deterministically. The agent reads the rejection notice, replaces the em dash with a colon or comma, and re-submits without human intervention.

***

### Proof 3: Unprompted Peer Mesh Convergence

**The Problem:** Coordinating worker agents, security critics, and invariant auditors usually requires human orchestration scripts and complex cloud infrastructure.

**Autonomous Blackboard Coordination:**

AOS agents communicate asynchronously using `.agents/blackboard/events.jsonl`. Execute a complete multi-agent cycle locally:

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

### Event Sequence on the Blackboard

1. **Worker Agent** registers intent (`INTENT_ANNOUNCEMENT`) targeting `kernel.cpp`.
2. **Auditor Agent** observes the event stream and injects applicable invariants (`INVARIANT_INJECTION`), binding the worker to rule `perf-simd-012`.
3. **Adversarial Critic** synthesizes edge-case verification criteria (`ADVERSARIAL_CHALLENGE`), demanding zero-length vector checks and pointer alignment validations.
4. **Auditor Agent** validates the patch against all active rules and issues an approval verdict (`PEER_CRITIQUE`).
5. **Consensus Orchestrator** records full convergence (`PEER_CONVERGENCE`).

The engineer is notified only after peer consensus is achieved.

***

## Enterprise Fleet Governance

Large engineering organizations suffer from **Distributed Agent Amnesia**: team A fixes an critical vulnerability, but team B and team C repeat the same mistake because knowledge remains isolated within repository silos.

AOS Enterprise Fleet Synchronization connects independent repositories into an institutional knowledge network:
* **`aos fleet publish`**: Broadcasts promoted local invariants into a shared enterprise ledger (`.agents/fleet.db`).
* **`aos fleet sync`**: Ingests organizational security and architectural rules into downstream repositories.
* **Deterministic CI Guardrails**: Automated GitHub Action workflows verify every pull request against active organizational invariants.

***

## Key Platform Benefits

| Capability | Without AOS | With AOS |
| :--- | :--- | :--- |
| **Error Retention** | Amnesia: Lessons lost after session closes | Machine-inscribed YAML invariants stored in Git |
| **Multi-Agent Flow** | Manual human-as-router copy-paste | Unprompted stigmergic blackboard coordination |
| **Pre-Commit Defense** | Broken builds and regressions reach CI | Universal git pre-commit rejection of invariant breaches |
| **Tool Interoperability** | Siloed configurations per editor | Unified compilation to Cursor, Windsurf, Copilot, and Claude Code |
| **Rule Health** | Rule bloat and conflicting instructions | Autonomous pruning, subsumption, and decay curation |
| **Infrastructure** | Heavy external databases and message brokers | Zero external dependencies: local Git, JSON, YAML, and SQLite |

***

## Next Steps

* [Getting Started](getting-started.md): Complete setup, harness synchronization, and MCP configuration.
* [AI Vendor Abstraction](vendor-abstraction.md): Decoupling repository invariants and control planes from LLM providers.
* [IDE & Tool Integration](ide-integration.md): Step-by-step guides for Cursor, Claude Code, Copilot, Windsurf, and Git pre-commit hooks.
* [Control Plane Web Dashboard](control-plane-ui.md): Visual tour of real-time guardrail controls and diff testing.
* [Curated Rule Packs](rule-packs.md): Battle-tested security, architecture, and performance invariant packs.
* [Architecture & Theoretical Foundations](architecture.md): In-depth examination of the three inscription loops and stigmergy.
* [CLI Reference](cli-reference.md): Full syntax guide for all `aos` commands and configuration flags.
* [Enterprise Fleet Governance](enterprise-fleet.md): Synchronize invariant rules across hundreds of enterprise repositories.

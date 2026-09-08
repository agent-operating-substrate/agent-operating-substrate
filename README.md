# Agent Operating Substrate (AOS)

A decentralized, stigmergic protocol and runtime that equips autonomous coding agents with self-improving rules, failure-driven memory inscription, and unprompted peer-to-peer collaboration.

***

## The Core Thesis

Modern software engineering agents (Antigravity, Cursor, Claude Code, Aider) suffer from two structural flaws:

1. **Amnesia:** Agents are born anew on every invocation. When an agent violates a project invariant, breaks a build, or introduces architectural bloat, a human must intervene. Once the context window closes, the lesson is lost. The next agent commits the identical mistake.
2. **The Human-as-Router Bottleneck:** Multi-agent workflows remain strictly hub-and-spoke. Humans are forced to micromanage interactions: invoking Agent A to code, copying output to Agent B to review, and manually prompting Agent C to test.

**AOS replaces the human router with a Stigmergic Rule Substrate.**

In biological systems, social insects construct complex architectures without a central manager: they communicate asynchronously by modifying their shared physical environment (stigmergy). In software development, AOS turns the repository into that shared environment: an evolving, self-inscribed ledger of invariants, lessons, and peer contracts that agents read, challenge, and refine autonomously.

***

## Key Capabilities

* **Self-Improving Inscription Loop:** When a compiler error, test regression, or human rollback occurs, background agents conduct a root-cause autopsy and inscribe permanent, machine-readable invariant rules directly into the repository.
* **Unprompted Peer-to-Peer Mesh:** Agents coordinate via an asynchronous local blackboard. When a worker agent plans a refactor, an auditor agent automatically intercepts the intent, enforces blast-radius limits, and an adversarial agent synthesizes stress tests, all without human dispatch.
* **Evolutionary Rule Curator:** An automated pruning and consolidation engine prevents rule bloat. Rules that conflict, duplicate, or decay over time are autonomously consolidated or retired.
* **Zero External Dependencies:** Built on local file primitives, Git-backed versioning, and lightweight JSON/YAML schemas. Fully compatible with any agentic CLI or IDE.

***

## Documentation

* [Architecture & Theoretical Foundations](ARCHITECTURE.md): The three inscription loops, stigmergic coordination, and epistemic containment.
* [System Specification](SPEC.md): Schemas for rules, event blackboard payloads, and the CLI interface.
* [Agent Guidelines](AGENTS.md): Operating rules for agents participating in this codebase.

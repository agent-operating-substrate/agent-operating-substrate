# Changelog

All notable changes to the Agent Operating Substrate (AOS) are documented in this file.
This project adheres to Semantic Versioning.

***

## [0.2.0] - 2026-09-13

### Universal AI Vendor Abstraction Release

#### Added
* **Universal AI Vendor Abstraction Layer**: Support for Google Gemini (GEMINI.md, .gemini/instructions.md), OpenAI Codex and ChatGPT (CODEX.md, .openai/instructions.md), Aider (CONVENTIONS.md), Roo Code and Cline (.clinerules, .roomodes), and Amazon Q Developer (.amazonq/rules.md).
* **Automated Bot Identity and Attribution**: Cryptographic token minting and git credential helper for verified agent-operating-substrate-agent[bot] commits.
* **Official MIT License**: Added MIT LICENSE to root repository and VS Code extension distribution packaging.
* **Playwright CI Graceful Fallback**: Automated detection and graceful skipping when browser binaries are absent in headless container environments.
* **PyPI Publish Resilience**: Added skip-existing configuration to prevent distribution pipeline conflicts.

***

## [0.1.0] - 2026-09-13

### Initial Release: The Autonomous Behavior Firewall and Permanent Memory Substrate

#### Added
* **Deterministic Invariant Engine**: Core evaluation engine supporting multi-language regex heuristics, surgical blast radius bounds, and single-pass line streaming.
* **Universal Multi-Harness Synchronization**: Automatic compilation and injection of active invariants into `.cursorrules`, `.cursor/rules/aos-invariants.mdc`, `CLAUDE.md`, `.windsurfrules`, and `.github/copilot-instructions.md`.
* **Universal Git Pre-Commit Hook**: Non-bypassable deterministic barrier preventing invalid diffs, secrets, or formatting regressions from being committed.
* **Autonomous Forensic Autopsy Loop**: Real-time error capture, diagnostic attribution, and automated candidate rule synthesis (`aos exec`, `aos autopsy`).
* **Evolutionary Rule Curator**: Subsumption detection, heuristic clustering, and automated decay pruning for growing rule sets (`aos curate`).
* **Curated Rule Packs**: 1-click installable rule collections (`security-core`, `python-core`, `typescript-core`, `general-hygiene`, `rust-core`, `go-core`).
* **Repository Convention Ingestor**: Automated scanning of package manifests, linters, and repository structures to synthesize custom project guardrails (`aos ingest`).
* **Model Context Protocol (MCP) Server**: Standardized stdio JSON-RPC 2.0 interface exposing guardrail queries, enforcement checks, and incident logging to Cursor, Claude Desktop, and Zed.
* **Autonomous Agent Identity Vault**: Programmatic mailbox provisioning and cryptographic secret storage for autonomous personas with direct supervisory human access (`aos identity`).
* **Interactive Control Plane Dashboard**: Local web interface (`http://127.0.0.1:8484`) featuring real-time rule toggling, live diff sandbox evaluation, connected harness status, and autopsy inspection.
* **Companion VS Code and Cursor Extension**: Status bar indicator, one-click synchronization, convention scanning, and inspector integration.
* **Cross-Repository Fleet Synchronization**: Enterprise distribution and policy enforcement across multiple repositories (`aos fleet`).
* **Zensical Documentation Suite**: Comprehensive architecture documentation, CLI reference, and quickstart guides built with Zensical.

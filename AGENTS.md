# Agent Operating Guidelines (AOS Project)

These rules apply to any autonomous agent working inside the Agent Operating Substrate codebase.

## 1. Surgical Diff Invariant
* Touch only lines strictly required to complete the assigned task.
* Never reformat adjacent code, comments, or imports.
* If a patch exceeds 30 contiguous lines, halt and provide a technical justification.

## 2. Punctuation Constraint
* Zero em dashes in all prose, documentation, commit messages, and code comments.
* Use colons, commas, semicolons, parentheses, or separate sentences instead.

## 3. Simplicity First
* Build with minimal code. Avoid speculative abstractions.
* Favor local file primitives (JSON, YAML, SQLite) over complex external infrastructure.
* Do not introduce dependencies unless strictly necessary.

## 4. Inscription Protocol
* When correcting a failure, explain the root cause and document the invariant rule that would have prevented it.

## 5. Autonomous Development & Transparency
* The Agent Operating Substrate is developed and maintained autonomously by AI agents (AOS Agent).
* Agents autonomously identify improvements, conduct forensic autopsies, and curate guardrails under human supervisory oversight.
* All public communications, release notes, and documentation must transparently state this autonomous origin.

## 6. Pull Request & Parallel Branching Invariant
* Direct pushes to master or main are strictly prohibited once v0.1.0 is published.
* All modifications must be developed on dedicated branches (e.g., agent/<task-name> or feature/<feature-name>).
* Changes must be submitted via Pull Requests or Merge Requests to allow multiple parallel agents and human contributors to work concurrently without merge collisions.
* Every PR must pass automated CI checks (pytest, invariant validation, documentation build) before merging.

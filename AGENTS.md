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

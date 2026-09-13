---
name: Invariant Rule Proposal
about: Propose a new invariant rule or rule pack for the AOS ecosystem
title: "[RULE]: "
labels: enhancement, rule-pack
assignees: ""
---

### Rule Identification
* Proposed Rule ID: [e.g. sec-jwt-expiry, py-no-mutable-defaults]
* Target Pack: [e.g. security-core, python-core, general-hygiene, or custom]
* Layer: [e.g. Layer 1 (Security/Hygiene) / Layer 2 (Ecosystem Standards) / Layer 3 (Architecture)]

### Statement
The imperative constraint statement that coding agents must follow.

### Rationale
Why does this rule prevent regressions or agent hallucinations?

### Target Scope
* File Patterns: [e.g. `**/*.py`, `src/auth/**/*.ts`]
* Languages: [e.g. python, typescript]

### Enforcement Heuristic
* Detection heuristic, AST pattern, or regex to detect violations.
* Suggested Action: [e.g. reject_diff, warn]
* Severity: [e.g. BLOCK, WARN]

### Example Violation
Provide a code snippet that should be intercepted:
```text
// Example code that violates this rule
```

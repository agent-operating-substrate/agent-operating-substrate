# Contributing to Agent Operating Substrate (AOS)

Thank you for your interest in contributing to the Agent Operating Substrate! AOS is an open-source behavior control plane and permanent memory substrate for AI coding agents such as Cursor, GitHub Copilot, and Claude Code.

***

## Core Philosophy and Invariants

Every contributor (human developer or autonomous coding agent) must respect the repository invariants:

1. **Punctuation Constraint**: Zero em dashes in all prose, documentation, commit messages, and code comments. Use colons, commas, semicolons, parentheses, or separate sentences instead.
2. **Surgical Diff Invariant**: Touch only lines strictly required to complete the assigned task. Never reformat adjacent code, comments, or imports. If a patch exceeds 30 contiguous lines, provide a clear technical justification.
3. **Simplicity First**: Rely on local file primitives (YAML, JSON, SQLite) and the Python standard library. Avoid speculative abstractions or heavy external dependencies.
4. **Deterministic Verification**: Every bug fix, guardrail, or feature must include automated tests in `tests/`.

***

## Local Development Setup

### 1. Prerequisites
* Python 3.11 or higher
* Git 2.30 or higher
* Node.js 18+ (only if packaging the VS Code extension)

### 2. Clone and Environment Setup
```bash
git clone https://github.com/aos-agent/agent-operating-substrate.git
cd agent-operating-substrate

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Linux / macOS:
source venv/bin/activate

# Install development dependencies and editable package
pip install -e .
pip install pytest pyyaml build
```

### 3. Verify Test Suite
Run the full test suite to ensure all tests pass:
```bash
pytest
```

***

## Authoring Invariant Rules

Rules are declarative YAML files stored in `.agents/substrate/active/` or contributed to curated rule packs in `src/aos/packs.py`.

### Rule Schema
```yaml
id: my-rule-identifier
layer: 1
statement: "Imperative constraint statement that agents must obey."
rationale: "Why this constraint matters for safety, performance, or consistency."
scope:
  file_patterns:
    - "**/*.py"
  languages:
    - python
enforcement:
  action: reject_diff
  severity: BLOCK
metadata:
  inscribed_by: aos-agent-curator
  trigger_count: 0
```

### Testing Rules
You can test any rule against a target file or patch using the CLI:
```bash
# Check matching rules for a specific file path
aos rules check src/auth/login.py

# Run enforcement on current working tree diff
aos enforce --staged
```

***

## Documentation

Documentation is built with Zensical. To build the documentation locally:
```bash
zensical build
# Or serve locally with live reload:
zensical serve -a 127.0.0.1:8000
```

***

## Submitting Pull Requests & Parallel Workflows

To support concurrent contributions from multiple autonomous agents and human developers in parallel, all post-v0.1.0 changes must follow the Pull Request / Merge Request model:

1. **Dedicated Branch**: Never push directly to `master` or `main`. Always branch off `master` with an informative name (e.g., `agent/<task-name>` or `feature/<feature-name>`).
2. **Deterministic Verification**: Ensure `pytest` passes with 100% success rate and `zensical build` succeeds.
3. **Punctuation Invariant**: Check that no em dashes exist in any modified files.
4. **Conventional Commits**: Keep commit messages concise and aligned with conventional commits format (`feat:`, `fix:`, `docs:`, `ci:`, `test:`).
5. **PR Review and Merge**: Open a Pull Request on GitHub. GitHub Actions CI will automatically run tests, build documentation, and verify package builds before review and merging.

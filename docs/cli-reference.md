# CLI Reference

**Complete, authoritative reference for the `aos` command-line interface.**

***

## Global Options

All `aos` commands accept the following global option:

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `--root <path>` | Path | `.` | Target repository root directory containing `.agents/`. |
| `-h, --help` | Flag | | Display command-line help information and exit. |

***

## Command Index

* [`aos init`](#aos-init): Initialize the substrate directory layout and configuration.
* [`aos rules`](#aos-rules): Inspect and match machine-readable invariant rules.
* [`aos enforce`](#aos-enforce): Deterministically validate files against all active rules.
* [`aos sync`](#aos-sync): Compile active rules into agent prompt harnesses.
* [`aos hook`](#aos-hook): Manage the universal Git pre-commit verification hook.
* [`aos mcp`](#aos-mcp): Launch the Model Context Protocol (MCP) stdio server.
* [`aos daemon`](#aos-daemon): Run the autonomous background auditor and curator daemon.
* [`aos mesh`](#aos-mesh): Simulate unprompted peer-to-peer agent mesh coordination.
* [`aos autopsy`](#aos-autopsy): Synthesize and inscribe an invariant rule from a failure.
* [`aos curate`](#aos-curate): Prune, subsume, and archive substrate rules.
* [`aos exec`](#aos-exec): Execute commands with automated failure autopsy interception.
* [`aos pack`](#aos-pack): Inspect and install curated domain rule packs.
* [`aos ci`](#aos-ci): Run automated CI pipeline checks against Git base refs.
* [`aos fleet`](#aos-fleet): Publish and sync rules with the enterprise fleet ledger.
* [`aos blackboard`](#aos-blackboard): Inspect events on the local peer blackboard.
* [`aos ui`](#aos-ui): Start the local Control Plane web dashboard.

***

## aos init

Initialize the `.agents/` substrate directory layout and default configuration.

```bash
aos init [--root <path>]
```

### Description
Creates the following directories and files if they do not already exist:
* `.agents/substrate/active/`
* `.agents/substrate/candidate/`
* `.agents/substrate/archive/`
* `.agents/blackboard/intents/`
* `.agents/blackboard/critiques/`
* `.agents/blackboard/events.jsonl`
* `.agents/config.yaml`

### Example
```bash
aos init
```

### Exit Codes
* `0`: Substrate created or verified successfully.

***

## aos rules

Inspect and evaluate substrate invariant rules.

### aos rules list

List discovered invariant rules in the substrate.

```bash
aos rules list [--status active|candidate|archive]
```

#### Example
```bash
aos rules list --status active
```

Output:
```text
Found 4 rule(s):
[ACTIVE] aos-punct-001 (v1) (.agents/substrate/active/aos-punct-001.yaml)
  Statement:   Zero em dashes in all prose, documentation, commit messages, and code comments. Use colons, commas, semicolons, parentheses, or separate sentences instead.
  Enforcement: reject_diff
  Paths:       **/*

[ACTIVE] perf-simd-012 (v1) (.agents/substrate/active/perf-simd-012.yaml)
  Statement:   PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries.
  Enforcement: reject_diff
  Paths:       src/geometry/simd/**, include/geometry/simd/**
  Languages:   cpp, cuda
```

### aos rules check

Check target files against active invariant rules.

```bash
aos rules check <files...> [--enforce] [--fail-on-match]
```

#### Options
* `--enforce`: Perform deterministic content validation against matching rules.
* `--fail-on-match`: Return non-zero exit code if any rule matches the file path.

#### Example
```bash
aos rules check src/geometry/simd/kernel.cpp --enforce
```

### Exit Codes
* `0`: Clean execution, no violations detected.
* `1`: Invariant violations detected (when `--enforce` is set).

***

## aos enforce

Deterministically validate one or more files against all applicable active invariant rules.

```bash
aos enforce <files...>
```

### Example
```bash
aos enforce docs/index.md src/aos/cli.py
```

Output on clean check:
```text
All files passed invariant verification.
```

Output on violation:
```text
Detected 1 invariant violation(s):
- [aos-punct-001] docs/draft.md:24: Violation of 'aos-punct-001': Forbidden em dash (\u2014) detected. (reject_diff)
```

### Exit Codes
* `0`: All files strictly comply with active rules.
* `1`: One or more invariant violations detected.

***

## aos sync

Compile and inject active substrate invariants into target agent harness configuration files.

```bash
aos sync [--harnesses <comma-separated-list>]
```

### Supported Harnesses
* `cursor`: Writes to `.cursorrules` at repository root.
* `cursor_mdc`: Writes to `.cursor/rules/aos-invariants.mdc`.
* `windsurf`: Writes to `.windsurfrules` at repository root.
* `copilot`: Writes to `.github/copilot-instructions.md`.

### Example
```bash
aos sync --harnesses cursor,windsurf,copilot
```

Output:
```text
Synced 3 agent harness configuration(s):
- cursor: .cursorrules
- windsurf: .windsurfrules
- copilot: .github/copilot-instructions.md
```

### Exit Codes
* `0`: Sync completed successfully.

***

## aos hook

Manage the universal Git pre-commit verification hook.

### Subcommands
* `aos hook install`: Installs an executable Git hook at `.git/hooks/pre-commit`.
* `aos hook uninstall`: Removes the AOS pre-commit hook.
* `aos hook run`: Runs pre-commit invariant validation on currently staged Git files.

### Example
```bash
# Install hook
aos hook install

# Verify staged files manually
aos hook run
```

### Exit Codes
* `0`: Hook installed or staged files verified clean.
* `1`: Staged files violate active invariants.

***

## aos mcp

Launch the standard Model Context Protocol (MCP) server over standard I/O (stdio).

```bash
aos mcp
```

### Supported Protocol
* Protocol Version: `2024-11-05`
* Transport: Stdio JSON-RPC

### Exposed Tools
1. `aos_rules_check`: Match file paths against active rules and test for violations.
2. `aos_rules_list`: List rules by status (`active`, `candidate`, `archive`).
3. `aos_autopsy`: Inscribe candidate rules from failure traces.
4. `aos_blackboard_post`: Broadcast events to the local blackboard.

***

## aos daemon

Run the background autonomous daemon that continuously listens for blackboard events and performs periodic curation.

```bash
aos daemon start [--interval <seconds>] [--curation-interval <seconds>] [--once]
```

### Options
* `--interval <seconds>`: Polling interval for new blackboard events (default: 2.0s).
* `--curation-interval <seconds>`: Frequency of substrate curation cycles (default: 300.0s).
* `--once`: Execute a single polling cycle and exit immediately (useful for testing).

### Example
```bash
aos daemon start --interval 1.0 --once
```

Output:
```text
Daemon executed single tick: generated 0 reaction(s).
```

### Exit Codes
* `0`: Clean execution or single tick completed.

***

## aos mesh

Simulate an unprompted peer-to-peer agent mesh coordination cycle on the blackboard.

```bash
aos mesh simulate [--intent-id <id>] [--desc <description>] [--files <paths...>]
```

### Options
* `--intent-id <id>`: Custom intent identifier (generated if omitted).
* `--desc <text>`: Description of worker intent.
* `--files <paths...>`: Target files the worker intends to modify.

### Example
```bash
aos mesh simulate --desc "Refactor SIMD normal calculation" --files src/geometry/simd/kernel.cpp
```

Output:
```text
Peer Mesh Simulation: Intent 'intent-5f21a0' - Status: CONVERGED
Emitted 5 event(s) to blackboard:
- [INTENT_ANNOUNCEMENT] From: worker-agent
- [INVARIANT_INJECTION] From: auditor-agent
- [ADVERSARIAL_CHALLENGE] From: adversarial-critic-agent
- [PEER_CRITIQUE] From: auditor-agent
- [PEER_CONVERGENCE] From: consensus-orchestrator
```

### Exit Codes
* `0`: Peer mesh converged with all invariants approved.
* `1`: Peer critique rejected proposed patch.

***

## aos autopsy

Synthesize and inscribe an invariant rule derived from an execution failure or human rollback.

```bash
aos autopsy --id <rule-id> \
            --statement <directive> \
            --rationale <justification> \
            --paths <globs...> \
            [--languages <langs...>] \
            [--incident <incident-id>] \
            [--agent <agent-name>] \
            [--promote]
```

### Options
* `--id <string>`: Unique rule identifier (e.g., `perf-simd-012`). Required.
* `--statement <string>`: Concise invariant directive. Required.
* `--rationale <string>`: Technical justification for the invariant. Required.
* `--paths <globs...>`: Path patterns the rule applies to. Required.
* `--languages <langs...>`: Optional language identifiers.
* `--incident <string>`: Incident ticket or Git commit identifier (default: `inc-manual`).
* `--agent <string>`: Name of inscribing agent (default: `forensic-auditor`).
* `--promote`: Immediately promote rule from `candidate/` to `active/`.

### Example
```bash
aos autopsy --id "perf-simd-013" \
            --statement "AVX-512 gather routines must verify base pointer alignment." \
            --rationale "Unaligned gather loads cause CPU pipeline stalls." \
            --paths "src/geometry/simd/**" \
            --languages "cpp" "cuda" \
            --promote
```

Output:
```text
Candidate rule inscribed: .agents/substrate/candidate/perf-simd-013.yaml
Rule promoted to active: .agents/substrate/active/perf-simd-013.yaml
```

### Exit Codes
* `0`: Rule successfully synthesized and saved.

***

## aos curate

Execute evolutionary pruning, subsumption, and decay archival on rules in the substrate.

```bash
aos curate [--dry-run]
```

### Options
* `--dry-run`: Inspect and report pending curation actions without modifying files.

### Example
```bash
aos curate --dry-run
```

Output:
```text
Substrate clean: zero curation actions required (DRY RUN).
```

### Exit Codes
* `0`: Curation completed.

***

## aos exec

Execute an arbitrary shell command, intercept failures, and automatically synthesize candidate invariant rules.

```bash
aos exec [--no-autopsy] -- <command...>
```

### Options
* `--no-autopsy`: Suppress automatic candidate rule generation on non-zero exit codes.

### Example
```bash
aos exec -- pytest tests/
```

### Exit Codes
* Matches the exit code of the executed command.

***

## aos pack

Manage curated domain invariant rule packs.

### Subcommands
* `aos pack list`: List all bundled rule packs and rule counts.
* `aos pack install <pack-name> [--candidate]`: Install rules from a pack into active (or candidate) substrate.

### Example
```bash
# List available packs
aos pack list

# Install and activate OWASP security invariants
aos pack install security-owasp

# Install as candidate for review before activation
aos pack install python-clean-architecture --candidate
```

### Exit Codes
* `0`: Packs listed or installed successfully.
* `1`: Pack not found.

***

## aos ci

CI/CD integration command for GitHub Actions and GitLab pipelines.

```bash
aos ci run [--base <git-ref>] [--auto-sync] [--files <paths...>]
```

### Subcommands
* `aos ci run [--base <git-ref>] [--auto-sync] [--files <paths...>]`: Run invariant checks against modified files.
* `aos ci review [--diff <path>]`: Analyze unified pull request diff and generate inline review comments with compliant code patterns.
* `aos ci install`: Install GitHub Actions CI guardrail workflow into `.github/workflows/aos-guardrails.yml`.
* `aos ci uninstall`: Remove GitHub Actions CI guardrail workflow.

### Options for `aos ci run`
* `--base <git-ref>`: Base Git reference to diff against (default: `origin/main`).
* `--auto-sync`: Sync agent prompt harnesses before running verification.
* `--files <paths...>`: Explicit list of files to check instead of Git diff.

### Example
```bash
aos ci run --base origin/main
```

Output:
```text
## AOS Invariant Verification Report

**Status**: PASSED
**Files Evaluated**: 12
**Violations Detected**: 0

All modified files strictly comply with active substrate invariants.
```

### Exit Codes
* `0`: Invariant check or review passed.
* `1`: Invariant violations detected.


***

## aos fleet

Manage cross-repository enterprise fleet synchronization.

### Subcommands
* `aos fleet list [--db <path>]`: List rules registered in the organization fleet database.
* `aos fleet publish <rule-id> [--repo-id <id>] [--db <path>]`: Publish a local active rule to the fleet ledger.
* `aos fleet sync [--db <path>]`: Pull active fleet rules into local active substrate.
* `aos fleet export [--db <path>] [--output <path>]`: Export fleet rules to a portable JSON bundle.
* `aos fleet import <bundle-path> [--db <path>]`: Import rules from a JSON bundle into the fleet database.

### Options
* `--db <path>`: Path to fleet SQLite ledger (default: `.agents/fleet.db`).
* `--repo-id <id>`: Origin repository identifier (default: `local-repo`).

### Example
```bash
# Publish local rule to fleet ledger
aos fleet publish perf-simd-012 --repo-id "engine-core"

# Sync fleet rules into another repository
aos fleet sync
```

### Exit Codes
* `0`: Fleet operation completed successfully.
* `1`: Rule not found or database error.

***

## aos blackboard

Inspect events recorded on the local blackboard event stream.

```bash
aos blackboard list [--type <type>] [--sender <sender>]
```

### Options
* `--type <type>`: Filter events by type (e.g., `INTENT_ANNOUNCEMENT`, `PEER_CRITIQUE`).
* `--sender <sender>`: Filter events by agent sender (e.g., `worker-agent`, `auditor-agent`).

### Example
```bash
aos blackboard list --type PEER_CONVERGENCE
```

Output:
```text
Found 1 event(s):
[2026-09-08T18:56:14Z] (PEER_CONVERGENCE) From: consensus-orchestrator (ID: evt-0c4a11)
  Payload: {"intent_id": "intent-492", "status": "READY_FOR_HUMAN_NOTIFY", "participating_agents": ["worker-agent", "auditor-agent", "adversarial-critic-agent"]}
```

### Exit Codes
* `0`: Events listed successfully.

***

## aos ui

Launch the local Control Plane web dashboard in your browser.

```bash
aos ui [--port <port>] [--root <path>]
```

### Options
* `--port <port>`: HTTP port to listen on (default: `8484`).
* `--root <path>`: Repository root directory containing `.agents/` (default: `.`).

### Example
```bash
aos ui --port 8484
```

Output:
```text
AOS Control Plane active at http://127.0.0.1:8484/
```

### Description
Starts a local HTTP server providing:
* Real-time overview of active, candidate, and archived invariants.
* Toggle switches to activate or archive rules instantaneously.
* Form modal to author new invariants with formal schema validation.
* Connected AI tool status monitoring (Cursor, Windsurf, Copilot, Claude Code, Git hooks) and one-click synchronization.
* Incident autopsy and peer critique timeline with raw blackboard event inspection.
* Guardrail Inspector to test file paths against active rules before editing code.

### Exit Codes
* `0`: Server exited cleanly on termination signal.

***

## aos ingest

Scan repository manifests, linters, and existing team instruction files to derive and synthesize tailored invariants.

```bash
aos ingest [--dry-run] [--promote] [--root <path>]
```

### Options
* `--dry-run`: Inspect and display proposed guardrails without modifying substrate files.
* `--promote`: Inscribe and immediately promote synthesized guardrails to active status (default: candidate status).
* `--root <path>`: Repository root directory to inspect (default: `.`).

### Example
```bash
# Preview what AOS detects in the repository
aos ingest --dry-run

# Inscribe and immediately activate tailored rules
aos ingest --promote
```

### Exit Codes
* `0`: Scan and ingestion completed successfully.

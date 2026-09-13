# Control Plane Web Dashboard

### A local visual command center for inspecting active guardrails, synchronizing AI tools, testing file scopes, and reviewing incident autopsies.

***

## Overview

The AOS Control Plane Web Dashboard gives engineering teams complete, transparent visibility into the rules governing their autonomous AI coding agents. 

Rather than treating AI behavioral boundaries as opaque prompt magic, the dashboard exposes:
* **The Living Invariant Ledger:** Which rules are active, candidate, or archived in `.agents/substrate/`.
* **Tool Connectivity:** The sync status of Cursor, Windsurf, GitHub Copilot, Claude Code, and the Git pre-commit barrier.
* **Failure Autopsies & Incidents:** A real-time timeline of intercepted bugs, compiler crashes, and peer critiques recorded on the local blackboard.
* **Guardrail Inspector & Live Tester:** An interactive utility to test target file paths and diffs against active guardrails before writing code.

To start the local dashboard:

```bash
aos ui --port 8484
```

Then open `http://127.0.0.1:8484` in your browser.

***

## Dashboard Architecture & Visual Tour

The interface is structured into five primary command views:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  [AOS]  AI Behavior Control Plane       [● Protection Active] [+ Add Rule]  │
│         Real-time guardrails and memory for Cursor, Copilot & Claude Code   │
├───────────────────┬───────────────────┬───────────────────┬─────────────────┤
│ Active Guardrails │ Connected Tools   │ Blocked Incidents │ Enforcement     │
│       4 rules     │      5 / 5        │     3 events      │ Strict Pre-Cmt  │
├───────────────────┴───────────────────┴───────────────────┴─────────────────┤
│ [1. Guardrails] [2. AI Tools] [3. Rule Packs] [4. Incidents] [5. Inspector] │
│                                                                             │
│  [Search rules...  /]   [All] [Active] [Candidate] [Archive]                │
│                                                                             │
│  ┌───────────────────────────────┐     ┌─────────────────────────────────┐  │
│  │ sec-sql-injection-001 [BLOCK] │     │ perf-simd-012          [BLOCK]  │  │
│  │ Parameterized SQL queries     │     │ 32-byte alignment for AVX2      │  │
│  │ Scope: src/**                 │     │ Scope: src/geometry/simd/**     │  │
│  │ [● Toggle: Active]            │     │ [● Toggle: Active]              │  │
│  └───────────────────────────────┘     └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1. Top Metrics Bar

The top cards provide instant visibility into your repository health:

* **Active Guardrails:** Count of machine-enforced rules in `.agents/substrate/active/`. The subtext displays rules currently in candidate or archive status.
* **Connected AI Tools:** Number of synchronized agent harnesses detected in the project (e.g. 5 of 5 connected).
* **Total Blocked Incidents:** Cumulative count of diff rejections, pre-commit halts, and forensic autopsies logged in `.agents/blackboard/events.jsonl`.
* **Enforcement Mode:** Current posture of the substrate (e.g. Strict Pre-Commit, rejecting non-compliant commits deterministically).

***

## Managing Guardrails

### Browsing and Filtering Rules

The **Active Guardrails** tab (Shortcut: `1`) organizes rules into clean, interactive cards.

1. **Quick Search:** Press `/` anywhere in the dashboard to focus the search bar. Filter instantly by rule ID, statement keywords, or file path patterns.
2. **Status Filters:** Use the filter chips (`All`, `Active`, `Candidate`, `Archive`) to isolate rules at specific lifecycle stages.

### Toggling Guardrail Status

Every rule card features a live toggle switch in the top-right corner.

* **Flipping to Inactive (Archive):** Moves the YAML file from `.agents/substrate/active/` to `.agents/substrate/archive/`. The rule is immediately excluded from future `aos sync` operations and pre-commit checks.
* **Flipping to Active:** Moves the YAML file back into `.agents/substrate/active/` and triggers a `RULE_TOGGLED` event on the blackboard.
* **Zero Delay:** State changes take effect on the local filesystem instantly without requiring a server reboot.

### Inspecting Rule Provenance & Metadata

Click anywhere on a rule card (outside the toggle switch) to expand its provenance drawer:

* **Inscribing Agent:** Identifies which agent created the rule (e.g. `pack-installer`, `control-plane-ui`, or `forensic-auditor`).
* **Git Commit Origin:** The exact commit SHA where the failure or rule was established.
* **Trigger Count:** How many times this rule blocked an invalid diff or intercepted a compiler error.
* **Last Verified Timestamp:** When the rule was last checked against the repository.
* **Incident ID:** Cross-reference identifier linking back to forensic autopsy notes.

### Creating a New Guardrail

Click the **+ Add Guardrail** button in the header to open the creation modal:

| Field | Description | Example |
| :--- | :--- | :--- |
| **Rule Identifier** | Unique slug for the rule | `sec-no-eval-001` |
| **Enforcement Action** | Severity policy: `BLOCK` (reject diff), `WARN` (advisory), or `AUDIT` (passive log) | `BLOCK (reject_diff)` |
| **Invariant Statement** | Non-negotiable directive that code must obey | `Direct use of eval() and exec() is prohibited.` |
| **Rationale** | Architectural or security justification | `Prevents arbitrary remote code execution.` |
| **Scope Paths** | Comma-separated glob patterns | `src/**/*.py, api/**/*.py` |
| **Languages** | Comma-separated language identifiers | `python, javascript` |

When you click **Save Guardrail**:
1. The backend validates the inputs against the formal AOS schema (`src/aos/validator.py`).
2. It generates a standardized YAML file in `.agents/substrate/active/<id>.yaml`.
3. It posts a `RULE_CREATED` event to `.agents/blackboard/events.jsonl`.
4. A notification toast confirms successful inscription.

***

## Connected AI Tools Tab

The **Connected AI Tools** tab (Shortcut: `2`) provides centralized management of all prompt harnesses:

| Tool | Monitored Path | Purpose |
| :--- | :--- | :--- |
| **Cursor IDE** | `.cursorrules` | Project instructions for Cursor Composer and Chat. |
| **Claude Code** | `CLAUDE.md` | System context for the Claude Code CLI. |
| **GitHub Copilot** | `.github/copilot-instructions.md` | Context for VS Code and JetBrains Copilot Chat. |
| **Windsurf IDE** | `.windsurfrules` | Guidelines for the Windsurf Cascade agent. |
| **Git Pre-Commit Hook** | `.git/hooks/pre-commit` | Deterministic local commit rejection barrier. |

### Real Actions Behind the Buttons

The buttons in this interface execute concrete system tasks:

* **Sync All Tools Now:** Executes `aos sync`, updating the bounded markdown sections in all five files simultaneously.
* **Install Git Hook:** Directly creates the executable `.git/hooks/pre-commit` script configured to run `aos hook run`.

***

## Curated Rule Packs Tab

The **Rule Packs** tab (Shortcut: `3`) allows you to deploy battle-tested engineering standards with a single click:

* **Pack Catalog Cards:** Displays available packs (`security-owasp`, `python-clean-architecture`, `performance-simd`) with rule counts and descriptions.
* **1-Click Install:** Installs all invariants from the pack directly into `.agents/substrate/active/`, making them immediately enforceable.
* **Uninstall Cleanly:** Removes pack rules from the substrate when you want to unbind constraints.
* **Instant Sync Integration:** Automatically triggers configuration updates across your connected AI harnesses.

***

## AI Incidents & Autopsy Tab

The **AI Incidents** tab (Shortcut: `4`) provides a transparent audit trail of every time AOS caught a mistake:

* **Failure Autopsies (`AUTOPSY_RECORD`):** Generated when `aos exec` wraps a crashing build or test. AOS isolates the error and proposes candidate rules.
* **Peer Critic Rejections (`PEER_CRITIQUE`):** Generated when an auditor agent rejects a proposed worker patch during stigmergic mesh coordination.
* **Raw Blackboard Events:** Expand any incident to view the exact JSON payload stored in `.agents/blackboard/events.jsonl`.

***

## Guardrail Inspector & Live Diff Sandbox

The **Guardrail Inspector** tab (Shortcut: `5`) features both path scope checking and an interactive code tester.

### 1. Live Code & Diff Enforcement Sandbox
Simulate the pre-commit bouncer directly in your browser before committing:

1. **Target File Path:** Enter the destination path (e.g. `src/aos/sample.py` or `src/geometry/simd/kernel.cpp`).
2. **Code Snippet / Patch:** Paste your proposed code or diff into the editor.
3. **One-Click Sample Presets:**
    * **Test Em-Dash Violation:** Loads Python code containing a forbidden em dash, demonstrating immediate rejection by rule `aos-punct-001`.
    * **Test Valid Python Code:** Loads clean, type-annotated code, demonstrating an `ALLOWED` verdict.
4. **Evaluate Patch:** Click **Evaluate Patch** to run the deterministic rule engine.
5. **Instant Verdict:**
    * **BLOCKED (Reject Diff):** Displays exact invariant violations, matched line numbers, code snippets, and remediation steps.
    * **ALLOWED (Clean Diff):** Confirms that all active repository guardrails are satisfied.

### 2. Path Scope Inspection
Enter any relative file path to discover which active invariants will constrain an agent when editing that file.

***

!!! tip "Sub-Millisecond Keyboard Navigation"
    The control plane dashboard includes native hotkeys for rapid engineering workflows. Press ++slash++ to immediately search active invariants, use ++1++ through ++5++ to jump between views, and dismiss any modal instantly with ++escape++.

## Keyboard Shortcuts

Navigate the control plane efficiently using keyboard shortcuts:

| Key | Action |
| :--- | :--- |
| ++1++ | Switch to **Active Guardrails** tab |
| ++2++ | Switch to **Connected AI Tools** tab |
| ++3++ | Switch to **Rule Packs** tab |
| ++4++ | Switch to **AI Incidents** tab |
| ++5++ | Switch to **Guardrail Inspector & Tester** tab |
| ++slash++ | Focus search bar in Guardrails tab |
| ++escape++ | Close open modal or clear search focus |

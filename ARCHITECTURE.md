# Architecture & Theoretical Foundations

## 1. The Stigmergic Paradigm

In classical multi-agent architectures, agents communicate via explicit point-to-point RPCs or centralized orchestrators (the hub-and-spoke pattern). This fails in software engineering because codebases are too large, asynchronous, and heterogeneous.

AOS adopts **stigmergy**: indirect, decentralized coordination mediated through trace modifications in the shared environment.

```
       ┌────────────────────────────────────────────────────────┐
       │                Shared Repository Canvas                │
       │  (Codebase, Git Graph, and .agents/rule-substrate/)    │
       └───────▲───────────────────────┬────────────────────────┘
               │                       │
     Inscribes Invariant       Reads Active Boundary
               │                       │
       ┌───────┴──────┐        ┌───────▼──────┐
       │ Scribe Agent │        │ Worker Agent │
       └───────▲──────┘        └───────┬──────┘
               │                       │
     Root-Cause Autopsy        Intent Announcement
               │                       │
       ┌───────┴──────┐        ┌───────▼──────┐
       │ Auditing Hook│        │ Critic Agent │
       └──────────────┘        └──────────────┘
```

When an agent acts, it leaves traces:
1. **Code Diffs:** The physical modification to source files.
2. **Inscriptions:** Atomic rule declarations that constrain future agent behavior.
3. **Blackboard Events:** Ephemeral signals broadcasting intent, review critiques, and verification gates.

***

## 2. The Three Inscription Loops

AOS operates three nested autonomous loops:

### Loop 1: The Execution Loop (Fast Cycle, Seconds to Minutes)
The Worker Agent proposes a patch to solve a given task. Before applying the patch, it queries the local substrate for rules matching its target path and language domain.

### Loop 2: The Forensic Autopsy Loop (Triggered on Failure)
When an operation fails (non-zero compiler exit, broken test assertion, linter failure, or human rejection via `git checkout`), the Autopsy engine halts execution:
1. **Failure Extraction:** Isolates the exact error trace and offending diff hunk.
2. **False Assumption Diagnosis:** Determines what belief the agent held that was invalid.
3. **Atomic Inscription Synthesis:** Formulates a single machine-readable invariant rule preventing that exact assumption.
4. **Peer Review:** A peer agent verifies that the proposed rule is neither overly broad nor hyper-specific to a one-off typo.

### Loop 3: The Evolutionary Pruning Loop (Background Cycle)
Rules must not accumulate indefinitely. An autonomous Curator Agent runs periodically to maintain the health of the rule substrate:
* **Subsumption:** If Rule B is a strict subset of Rule A, Rule B is pruned.
* **Decay & Archival:** Rules untouched across $N$ commits are placed in probationary archive status.
* **Contradiction Arbitration:** When two rules propose conflicting directives, the Curator generates a counterfactual test case to determine which rule produces sounder code.

***

## 3. The Unprompted Peer Mesh (The Blackboard)

Human developers should not have to manually coordinate agents. AOS provides a local event bus (`.agents/blackboard/` or SQLite ledger):

1. **Intent Registration:** Worker Agent publishes `intent: refactor_mesh_normals`.
2. **Automatic Interception:**
   * Invariant Auditor inspects relevant rules and posts constraints directly to the intent thread.
   * Adversarial Fuzzer schedules boundary testing against the target module.
3. **Peer Convergence:** Worker Agent iterates with Critic Agent until all inscribed invariants pass.
4. **Human Notification:** The human is only alerted when peer consensus is reached or when an irreconcilable contradiction requires human judgment.

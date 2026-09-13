# AI Vendor Abstraction & Model Neutrality

### Decouple repository invariants, failure memory, and behavioral guardrails from LLM model providers.

***

> [!NOTE]
> **Autonomous Agent Origin**: The Agent Operating Substrate is designed, implemented, and maintained autonomously by AI agents (`AOS Agent`). All post-initial release enhancements follow a strict Pull Request / Merge Request workflow to ensure concurrent collaboration between multiple autonomous agents and human developers.

## The Model Churn Dilemma

Enterprise engineering teams are adopting AI coding assistants at an unprecedented rate. However, software leaders face a compounding strategic challenge: **AI model churn and vendor lock-in**.

The AI ecosystem evolves weekly:
* OpenAI releases GPT-4o, Codex updates, and reasoning models.
* Anthropic iterates on Claude 3.5 Sonnet and Claude Code.
* Google advances Gemini 1.5 Pro, Gemini Code Assist, and Antigravity.
* Open-weights ecosystems deliver competitive reasoning with DeepSeek-R1, Llama 3, and Mistral.
* Developer tooling fragments across Cursor, Windsurf, GitHub Copilot, Amazon Q Developer, Aider, and Cline.

```
Without AOS (Fragile, Fragmented, Vendor Locked):
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│ Cursor Rules   │     │ Windsurf Rules │     │ Claude Prompts │
│ (.cursorrules) │     │(.windsurfrules)│     │  (CLAUDE.md)   │
└───────┬────────┘     └───────┬────────┘     └───────┬────────┘
        ▼                      ▼                      ▼
  Model Drift            Model Drift            Model Drift
  Different Syntax       Different Syntax       Different Syntax
  Inconsistent Checks    Inconsistent Checks    Inconsistent Checks
```

When teams embed policies directly inside vendor-specific prompt files, they incur severe costs:
1. **Prompt Drift & Behavioral Inconsistency:** What Claude 3.5 Sonnet respects through natural language prompting, GPT-4o or Gemini 1.5 Pro may overlook. Each model has unique attention patterns, context window thresholds, and system prompt formatting requirements.
2. **Artificial Vendor Lock-in:** Migrating from one IDE or model provider to another requires rewriting and re-testing months of prompt guidelines.
3. **The AI Babysitting Tax:** Senior engineers waste time repeatedly diagnosing identical regressions across different developer setups because rule enforcement relies on model obedience rather than deterministic validation.

***

## The Solution: A Vendor-Agnostic Behavior Control Plane

The Agent Operating Substrate (AOS) abstracts away the model layer entirely. 

AOS establishes an independent, machine-readable behavior control plane inside your repository. Whether code is drafted by Gemini 1.5 Pro, Claude 3.5 Sonnet, OpenAI Codex, or local DeepSeek running in an air-gapped environment, AOS guarantees the exact same repository guardrails, memory, and pre-commit verification.

```
With AOS (Unified, Vendor-Agnostic Control Plane):
             ┌──────────────────────────────────────────────┐
             │       Single Source of Truth Substrate       │
             │          (.agents/substrate/active)          │
             └──────────────────────┬───────────────────────┘
                                    │ (aos sync & aos mcp)
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐           ┌───────────────┐           ┌───────────────┐
│ Google Gemini │           │Anthropic Claud│           │ OpenAI Codex  │
│ (Code Assist) │           │ (Claude Code) │           │   (ChatGPT)   │
└───────┬───────┘           └───────┬───────┘           └───────┬───────┘
        │                           │                           │
        └───────────────────────────┼───────────────────────────┘
                                    │ (Staged Commits)
                                    ▼
             ┌──────────────────────────────────────────────┐
             │         Deterministic Git Firewall           │
             │               (aos hook run)                 │
             └──────────────────────────────────────────────┘
```

***

## The 3 Pillars of Vendor Abstraction

### 1. Declarative, Model-Independent Invariants
Repository rules are authored in structured, vendor-neutral YAML schemas rather than conversational system prompts. Each invariant specifies scope, target paths, AST or regex patterns, and deterministic enforcement actions:

```yaml
id: "sec-sql-injection-001"
version: 1
status: "active"
scope:
  paths: ["src/**", "api/**"]
  languages: ["python", "typescript", "go"]
invariant:
  statement: "Raw SQL query string concatenation is prohibited. All database queries must use parameterized queries or ORM bindings."
  rationale: "Prevents critical SQL injection vulnerabilities in database access layers."
  enforcement: "reject_diff"
provenance:
  incident_id: "inc-2026-09-01-01"
  inscribing_agent: "forensic-auditor"
```

Because invariants are pure data, they remain invariant regardless of which LLM reads them.

### 2. Universal Prompt Projection (`aos sync`)
AOS dynamically translates active YAML invariants into the native configuration format expected by each AI assistant:
* **Cursor:** Synchronizes into `.cursorrules` and `.cursor/rules/*.mdc`.
* **Windsurf / Codeium:** Compiles into `.windsurfrules`.
* **GitHub Copilot:** Injects into `.github/copilot-instructions.md`.
* **Anthropic Claude:** Formats into `CLAUDE.md`.

Injected rules are isolated within deterministic HTML markers (`<!-- AOS_INVARIANTS_START -->`). Custom developer instructions outside these markers are preserved untouched.

### 3. Universal Protocol & Deterministic Git Barrier
AOS provides two layers of enforcement that do not rely on prompt adherence:
* **Model Context Protocol (MCP):** Via `aos mcp`, any MCP-compatible agent (Claude Desktop, Antigravity, Cursor, Cline) can query applicable invariants interactively during code generation.
* **Universal Git Hook (`aos hook run`):** When code is committed, AOS inspects staged diffs directly. If an agent hallucinated a banned import or violated diff size constraints, the commit is deterministically rejected. The enforcement happens in local code, not in the model's neural weights.

***

## Supported AI Ecosystems & Models

AOS supports the entire landscape of commercial, open-source, and local AI coding tools:

| AI Ecosystem / Model | Supported Tooling & Interfaces | Integration Mode | Enforcement Mechanism |
| :--- | :--- | :--- | :--- |
| **Google Gemini** | Gemini Code Assist, Gemini CLI, Antigravity | Live MCP Server (`aos mcp`), CLI execution autopsy (`aos exec`), Stigmergic Blackboard | Pre-commit hook & live MCP tools |
| **Anthropic Claude** | Claude Code, Claude Desktop, Claude Projects | Single-source `CLAUDE.md` sync (`aos sync`), native MCP stdio server | Deterministic pre-commit firewall (`aos hook run`) |
| **OpenAI Codex & ChatGPT** | OpenAI Codex, ChatGPT Developer Mode, GPT-4o | Prompt projection, MCP protocol, Git pre-commit barrier | Substrate invariant evaluation & diff bouncer |
| **GitHub Copilot** | VS Code, JetBrains, Visual Studio, Copilot Chat | Automatic `.github/copilot-instructions.md` compilation | Pre-commit hook & CI pipeline gatekeeper |
| **Cursor IDE** | Cursor Composer, Cursor Agent Mode | `.cursorrules` and `.cursor/rules/*.mdc` synchronization, MCP server | Instant rule prompt injection & pre-commit hook |
| **Windsurf / Codeium** | Windsurf IDE, Codeium Cascade | `.windsurfrules` automatic synchronization | Staged diff bouncer & rule validation |
| **Aider, Roo Code & Cline** | Aider CLI, Roo Code, Cline (VS Code) | Context injection (`.agents/substrate/active`), stdio MCP | Autonomous pre-commit barrier & execution autopsy |
| **Amazon Q Developer** | Amazon Q (AWS Toolkit, VS Code, JetBrains) | Substrate prompt compilation & Git pre-commit barrier | Deterministic pre-commit enforcement & CI check |
| **Local & Open Weights** | DeepSeek-R1 / V3, Llama 3, Mistral, Qwen (via Ollama, vLLM) | File-based substrate, local SQLite, stdio MCP | 100% offline, local-first behavior firewall |

***

## Real-World Scenarios

### Scenario 1: Model Migration with Zero Policy Regression
A team decides to migrate primary coding workflows from Claude 3.5 Sonnet to Gemini 1.5 Pro to take advantage of expanded context windows and pricing efficiency.

**Without AOS:**
The platform team must rewrite complex prompt instructions, test prompt drift, and manually verify that Gemini adheres to team security conventions.

**With AOS:**
1. The team switches developer tools or switches model endpoints.
2. Run `aos sync` once to project existing invariants into the new harness.
3. Every invariant (security rules, diff constraints, memory alignment) remains 100% active and enforced by `aos hook run`.
4. Zero regressions, zero manual re-prompting.

### Scenario 2: Heterogeneous Multi-Model Mesh
In advanced agentic setups, different models excel at different specialties:
* **Gemini 1.5 Pro / Antigravity:** Ingests massive repository context and drafts broad cross-file refactors.
* **Claude 3.5 Sonnet:** Performs rigorous architectural and security audits.
* **OpenAI Codex / GPT-4o:** Synthesizes exhaustive test suites and property checks.
* **Local DeepSeek / Llama:** Runs fast, air-gapped code completions on sensitive internal data.

AOS coordinates these disparate models unprompted through the stigmergic blackboard (`.agents/blackboard/events.jsonl`). Each agent reads past event traces, announces intents, and validates work against common repository invariants without human routing.

***

## Enterprise Commercial Impact

Adopting a vendor-agnostic behavior control plane yields substantial business advantages:

1. **Eliminating AI Vendor Lock-in:** Negotiate model pricing freely. Switch providers or mix-and-match models across teams without jeopardizing code quality or compliance.
2. **Slashing AI Regression Costs:** Prevent broken imports, subtle memory bugs, and leaked API secrets before pull request review, saving hundreds of engineering hours.
3. **Audit and Compliance Readiness:** Maintain a tamper-proof event stream (`events.jsonl`) verifying that security policies were enforced on every commit, meeting SOC2 Type II and ISO 27001 requirements.
4. **Fleet-Wide Governance (`aos fleet`):** Synchronize compliance rules across 100+ repositories simultaneously while allowing local teams sovereign customization.

***

## Next Steps

* [Getting Started Guide](getting-started.md): Install AOS and initialize your repository substrate in 5 minutes.
* [IDE & Tool Integration](ide-integration.md): Step-by-step harness setup for Cursor, Claude Code, Copilot, and Windsurf.
* [Curated Rule Packs](rule-packs.md): Browse production-grade security, architecture, and performance packs.
* [Enterprise Fleet Governance](enterprise-fleet.md): Synchronize invariants across hundreds of enterprise repositories.

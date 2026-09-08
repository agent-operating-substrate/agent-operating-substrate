# System Specification & Data Formats

## 1. Directory Structure

Repositories utilizing AOS maintain an autonomous substrate under `.agents/`:

```
.agents/
├── substrate/
│   ├── active/            # Actively enforced invariant rules
│   │   ├── geom-001.yaml
│   │   └── perf-014.yaml
│   ├── candidate/         # Inscriptions awaiting peer consensus
│   └── archive/           # Pruned or subsumed historical rules
├── blackboard/
│   ├── intents/           # Active worker intents
│   ├── critiques/         # Peer auditor reviews
│   └── events.jsonl       # Asynchronous event stream
└── config.yaml            # AOS daemon settings and agent bindings
```

***

## 2. Invariant Rule Schema (`.agents/substrate/active/*.yaml`)

Every inscribed rule is stored as an atomic YAML declaration:

```yaml
id: "perf-simd-012"
version: 1
status: "active"
scope:
  paths:
    - "src/geometry/simd/**"
    - "include/geometry/simd/**"
  languages:
    - "cpp"
    - "cuda"

invariant:
  statement: "PointBuffer structures passed to AVX2/AVX-512 kernels must be aligned to 32-byte boundaries."
  rationale: "Unaligned memory loads trigger GP faults under high-throughput geometry sweeps."
  enforcement: "reject_diff"
  max_blast_radius_lines: 20

provenance:
  incident_id: "inc-2026-09-08-01"
  git_commit: "4f9a12c8"
  inscribing_agent: "forensic-auditor-v2"
  peer_consensus_agent: "rule-curator-v1"
  created_at: "2026-09-08T18:55:00Z"
  last_verified_at: "2026-09-08T18:55:00Z"
  trigger_count: 3
```

***

## 3. Blackboard Event Protocol

Agents communicate by appending JSON objects to `.agents/blackboard/events.jsonl`:

```json
{
  "event_id": "evt-109283",
  "timestamp": "2026-09-08T18:56:10Z",
  "type": "INTENT_ANNOUNCEMENT",
  "sender": "worker-agent",
  "payload": {
    "intent_id": "intent-492",
    "description": "Optimize Voronoi boundary relaxation for AVX2",
    "target_files": ["src/geometry/voronoi.cpp"]
  }
}
```

Auditor agents listen to this stream and append response events without human intervention:

```json
{
  "event_id": "evt-109284",
  "timestamp": "2026-09-08T18:56:12Z",
  "type": "INVARIANT_INJECTION",
  "sender": "auditor-agent",
  "payload": {
    "intent_id": "intent-492",
    "applicable_rules": ["perf-simd-012", "geom-004"],
    "required_checks": ["valgrind-clean", "max_diff_lines: 25"]
  }
}
```

***

## 4. CLI Interface (The `aos` Tool)

```bash
# Initialize substrate in current repository
aos init

# Start background autonomous peer daemon
aos daemon start

# Run manual failure autopsy and inscribe new candidate rule
aos autopsy --incident <commit-or-log>

# Trigger autonomous curation and pruning of active rules
aos curate --dry-run
```

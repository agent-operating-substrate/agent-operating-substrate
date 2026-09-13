"""Multi-agent peer mesh simulator: unprompted peer-to-peer coordination."""

from __future__ import annotations
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from aos.blackboard import BlackboardEvent, get_default_event_log, post_event, read_events
from aos.engine import RuleEngine
from aos.enforcer import enforce_all


@dataclass
class MeshSimulationResult:
    intent_id: str
    status: str
    events: list[BlackboardEvent]


def simulate_mesh_cycle(
    root_dir: Path | str = ".",
    intent_id: str = "",
    description: str = "Refactor geometric normal calculation",
    target_files: Optional[list[str]] = None,
    proposed_content: Optional[str] = None,
    event_log_path: Optional[Path | str] = None,
) -> MeshSimulationResult:
    """Simulate complete unprompted multi-agent peer mesh cycle on the blackboard."""
    root = Path(root_dir)
    log_path = Path(event_log_path) if event_log_path else get_default_event_log(root)

    if not intent_id:
        intent_id = f"intent-{uuid.uuid4().hex[:6]}"
    if target_files is None:
        target_files = ["src/geometry/simd/kernel.cpp"]

    events_produced: list[BlackboardEvent] = []

    # 1. Worker Agent: Intent Registration
    ev_intent = post_event(
        {
            "type": "INTENT_ANNOUNCEMENT",
            "sender": "worker-agent",
            "payload": {
                "intent_id": intent_id,
                "description": description,
                "target_files": target_files,
            },
        },
        event_log_path=log_path,
    )
    events_produced.append(ev_intent)

    # 2. Auditor Agent: Automatic Invariant Interception
    engine = RuleEngine(root_dir=root)
    matched_rules_map = engine.match_files(target_files, status="active")
    applicable_rule_ids: list[str] = []
    for f, rules in matched_rules_map.items():
        for r in rules:
            if r.id not in applicable_rule_ids:
                applicable_rule_ids.append(r.id)

    ev_injection = post_event(
        {
            "type": "INVARIANT_INJECTION",
            "sender": "auditor-agent",
            "payload": {
                "intent_id": intent_id,
                "applicable_rules": applicable_rule_ids,
                "target_files": target_files,
            },
        },
        event_log_path=log_path,
    )
    events_produced.append(ev_injection)

    # 3. Adversarial Critic: Synthesize Edge-Case Test Boundary
    ev_critique = post_event(
        {
            "type": "ADVERSARIAL_CHALLENGE",
            "sender": "adversarial-critic-agent",
            "payload": {
                "intent_id": intent_id,
                "boundary_assertions": [
                    "Must handle zero-length vector gracefully",
                    "Must verify 32-byte alignment boundary on input pointers",
                ],
            },
        },
        event_log_path=log_path,
    )
    events_produced.append(ev_critique)

    # 4. Auditor Agent: Review Proposed Patch
    # Check violations across target files
    violations = enforce_all(target_files, root_dir=root)
    if violations:
        ev_review = post_event(
            {
                "type": "PEER_CRITIQUE",
                "sender": "auditor-agent",
                "payload": {
                    "intent_id": intent_id,
                    "verdict": "REJECT_DIFF",
                    "violations": [
                        {"rule_id": v.rule_id, "file": v.file_path, "message": v.message}
                        for v in violations
                    ],
                },
            },
            event_log_path=log_path,
        )
        events_produced.append(ev_review)
        status = "rejected"
    else:
        ev_review = post_event(
            {
                "type": "PEER_CRITIQUE",
                "sender": "auditor-agent",
                "payload": {
                    "intent_id": intent_id,
                    "verdict": "APPROVED",
                    "message": "All active substrate invariants verified clean.",
                },
            },
            event_log_path=log_path,
        )
        events_produced.append(ev_review)

        # 5. Consensus Convergence
        ev_consensus = post_event(
            {
                "type": "PEER_CONVERGENCE",
                "sender": "consensus-orchestrator",
                "payload": {
                    "intent_id": intent_id,
                    "status": "READY_FOR_HUMAN_NOTIFY",
                    "participating_agents": [
                        "worker-agent",
                        "auditor-agent",
                        "adversarial-critic-agent",
                    ],
                },
            },
            event_log_path=log_path,
        )
        events_produced.append(ev_consensus)
        status = "converged"

    return MeshSimulationResult(
        intent_id=intent_id,
        status=status,
        events=events_produced,
    )

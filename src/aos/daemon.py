"""Autonomous background daemon for reactive auditing, event interception, and curation."""

from __future__ import annotations
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from aos.blackboard import BlackboardEvent, get_default_event_log, post_event, read_events
from aos.curator import curate_substrate
from aos.engine import RuleEngine


@dataclass
class DaemonState:
    processed_event_ids: set[str] = field(default_factory=set)
    injected_intent_ids: set[str] = field(default_factory=set)
    curation_interval_seconds: float = 300.0
    last_curation_timestamp: float = 0.0


class SubstrateDaemon:
    """Continuous background engine that audits announced intents and curates rules."""

    def __init__(
        self,
        root_dir: Path | str = ".",
        event_log_path: Optional[Path | str] = None,
        poll_interval: float = 2.0,
        curation_interval: float = 60.0,
    ) -> None:
        self.root_dir = Path(root_dir)
        self.event_log_path = Path(event_log_path) if event_log_path else get_default_event_log(self.root_dir)
        self.poll_interval = poll_interval
        self.state = DaemonState(curation_interval_seconds=curation_interval)
        self.engine = RuleEngine(root_dir=self.root_dir)

    def process_event(self, event: BlackboardEvent) -> Optional[BlackboardEvent]:
        """Inspect a single event and generate autonomous reactions if required."""
        if event.event_id in self.state.processed_event_ids:
            return None

        self.state.processed_event_ids.add(event.event_id)

        # Reactive Auditor: intercept INTENT_ANNOUNCEMENT
        if event.type == "INTENT_ANNOUNCEMENT":
            payload = event.payload
            intent_id = payload.get("intent_id", "")
            target_files = payload.get("target_files", [])

            if intent_id and intent_id not in self.state.injected_intent_ids and target_files:
                self.engine.reload()
                matched_rules_map = self.engine.match_files(target_files, status="active")

                # Collect unique rules
                applicable_rule_ids: list[str] = []
                required_checks: list[str] = []
                seen_rules: set[str] = set()

                for f_path, rules in matched_rules_map.items():
                    for r in rules:
                        if r.id not in seen_rules:
                            seen_rules.add(r.id)
                            applicable_rule_ids.append(r.id)
                            check_desc = f"rule:{r.id} ({r.invariant.enforcement})"
                            if r.invariant.max_blast_radius_lines is not None:
                                check_desc += f", max_diff_lines:{r.invariant.max_blast_radius_lines}"
                            required_checks.append(check_desc)

                injection_event = post_event(
                    {
                        "type": "INVARIANT_INJECTION",
                        "sender": "daemon-auditor-agent",
                        "payload": {
                            "intent_id": intent_id,
                            "applicable_rules": applicable_rule_ids,
                            "required_checks": required_checks,
                            "target_files": target_files,
                        },
                    },
                    event_log_path=self.event_log_path,
                )

                self.state.injected_intent_ids.add(intent_id)
                self.state.processed_event_ids.add(injection_event.event_id)
                return injection_event

        return None

    def tick(self) -> list[BlackboardEvent]:
        """Execute a single polling step: process new events and check curation schedule."""
        generated: list[BlackboardEvent] = []

        # 1. Read existing events and process unprocessed ones
        events = read_events(event_log_path=self.event_log_path)
        for ev in events:
            reaction = self.process_event(ev)
            if reaction is not None:
                generated.append(reaction)

        # 2. Check periodic curation tick
        now = time.time()
        if (now - self.state.last_curation_timestamp) >= self.state.curation_interval_seconds:
            self.state.last_curation_timestamp = now
            curate_substrate(
                substrate_dir=self.root_dir / ".agents" / "substrate",
                event_log_path=self.event_log_path,
            )

        return generated

    def run(self, max_ticks: Optional[int] = None) -> None:
        """Run the daemon loop until interrupted or max_ticks reached."""
        ticks_done = 0
        try:
            while max_ticks is None or ticks_done < max_ticks:
                self.tick()
                ticks_done += 1
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            pass

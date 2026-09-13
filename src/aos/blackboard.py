"""Asynchronous local blackboard event bus for peer-to-peer agent coordination."""

from __future__ import annotations
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator, Optional


@dataclass
class BlackboardEvent:
    type: str
    sender: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = ""
    timestamp: str = ""

    def __post_init__(self) -> None:
        if not self.event_id:
            prefix = int(time.time() * 1000)
            short_id = uuid.uuid4().hex[:6]
            self.event_id = f"evt-{prefix}-{short_id}"
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "type": self.type,
            "sender": self.sender,
            "payload": self.payload,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BlackboardEvent:
        return cls(
            event_id=str(data.get("event_id", "")),
            timestamp=str(data.get("timestamp", "")),
            type=str(data.get("type", "")),
            sender=str(data.get("sender", "")),
            payload=dict(data.get("payload", {})),
        )


def get_default_event_log(root_dir: Path | str = ".") -> Path:
    """Resolve path to default events.jsonl ledger."""
    root = Path(root_dir)
    return root / ".agents" / "blackboard" / "events.jsonl"


def post_event(
    event: BlackboardEvent | dict[str, Any],
    event_log_path: Optional[Path | str] = None,
    root_dir: Path | str = ".",
) -> BlackboardEvent:
    """Append an event to the local blackboard ledger."""
    if isinstance(event, dict):
        event_obj = BlackboardEvent.from_dict(event)
        # Ensure event_id and timestamp are populated
        if not event_obj.event_id or not event_obj.timestamp:
            event_obj = BlackboardEvent(
                type=event.get("type", "UNKNOWN"),
                sender=event.get("sender", "anonymous"),
                payload=event.get("payload", {}),
                event_id=event.get("event_id", ""),
                timestamp=event.get("timestamp", ""),
            )
    else:
        event_obj = event

    target_path = Path(event_log_path) if event_log_path else get_default_event_log(root_dir)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    line = json.dumps(event_obj.to_dict(), separators=(",", ":"))
    with open(target_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    return event_obj


def read_events(
    event_log_path: Optional[Path | str] = None,
    event_type: Optional[str] = None,
    sender: Optional[str] = None,
    root_dir: Path | str = ".",
) -> list[BlackboardEvent]:
    """Read all events from the ledger matching optional filters."""
    target_path = Path(event_log_path) if event_log_path else get_default_event_log(root_dir)
    if not target_path.is_file():
        return []

    events: list[BlackboardEvent] = []
    with open(target_path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                data = json.loads(stripped)
                ev = BlackboardEvent.from_dict(data)
                if event_type is not None and ev.type != event_type:
                    continue
                if sender is not None and ev.sender != sender:
                    continue
                events.append(ev)
            except Exception:
                # Ignore corrupted lines to prevent ledger read halts
                continue

    return events

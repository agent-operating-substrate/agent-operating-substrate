"""Data models for invariant rules in the Agent Operating Substrate."""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Optional


@dataclass
class Scope:
    paths: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)


@dataclass
class Invariant:
    statement: str
    rationale: str
    enforcement: str = "reject_diff"
    max_blast_radius_lines: Optional[int] = None


@dataclass
class Provenance:
    incident_id: str
    git_commit: str
    inscribing_agent: str
    created_at: str
    last_verified_at: str
    peer_consensus_agent: Optional[str] = None
    trigger_count: int = 0


@dataclass
class InvariantRule:
    id: str
    version: int
    status: str
    scope: Scope
    invariant: Invariant
    provenance: Provenance
    file_path: Optional[Path] = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "scope": {
                "paths": list(self.scope.paths),
                "languages": list(self.scope.languages),
            },
            "invariant": {
                "statement": self.invariant.statement,
                "rationale": self.invariant.rationale,
                "enforcement": self.invariant.enforcement,
            },
            "provenance": {
                "incident_id": self.provenance.incident_id,
                "git_commit": self.provenance.git_commit,
                "inscribing_agent": self.provenance.inscribing_agent,
                "created_at": self.provenance.created_at,
                "last_verified_at": self.provenance.last_verified_at,
                "trigger_count": self.provenance.trigger_count,
            },
        }
        if self.invariant.max_blast_radius_lines is not None:
            result["invariant"]["max_blast_radius_lines"] = self.invariant.max_blast_radius_lines
        if self.provenance.peer_consensus_agent is not None:
            result["provenance"]["peer_consensus_agent"] = self.provenance.peer_consensus_agent
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any], file_path: Optional[Path] = None) -> InvariantRule:
        scope_data = data.get("scope", {})
        inv_data = data.get("invariant", {})
        prov_data = data.get("provenance", {})

        scope = Scope(
            paths=list(scope_data.get("paths", [])),
            languages=list(scope_data.get("languages", [])),
        )
        invariant = Invariant(
            statement=inv_data.get("statement", ""),
            rationale=inv_data.get("rationale", ""),
            enforcement=inv_data.get("enforcement", "reject_diff"),
            max_blast_radius_lines=inv_data.get("max_blast_radius_lines"),
        )
        provenance = Provenance(
            incident_id=prov_data.get("incident_id", ""),
            git_commit=prov_data.get("git_commit", ""),
            inscribing_agent=prov_data.get("inscribing_agent", ""),
            peer_consensus_agent=prov_data.get("peer_consensus_agent"),
            created_at=prov_data.get("created_at", ""),
            last_verified_at=prov_data.get("last_verified_at", ""),
            trigger_count=int(prov_data.get("trigger_count", 0)),
        )

        return cls(
            id=str(data.get("id", "")),
            version=int(data.get("version", 1)),
            status=str(data.get("status", "active")),
            scope=scope,
            invariant=invariant,
            provenance=provenance,
            file_path=file_path,
        )

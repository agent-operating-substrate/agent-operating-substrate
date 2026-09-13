"""Unified Rule Engine coordinator for the Agent Operating Substrate."""

from __future__ import annotations
from pathlib import Path
from typing import Optional

from aos.discovery import discover_rules
from aos.matcher import get_rule_prefixes, match_rule, normalize_path
from aos.models import InvariantRule


class RuleEngine:
    """Core engine responsible for loading, indexing, and matching substrate rules."""

    def __init__(self, root_dir: Path | str = ".") -> None:
        self.root_dir = Path(root_dir)
        possible_substrate = self.root_dir / ".agents" / "substrate"
        if possible_substrate.is_dir():
            self.substrate_dir = possible_substrate
        else:
            self.substrate_dir = self.root_dir

        self.rules: list[InvariantRule] = []
        self.diagnostics: list[str] = []
        self._prefix_index: dict[str, dict[str, list[InvariantRule]]] = {}
        self._indexed_rules_count: int = -1
        self.reload()

    def _build_index(self) -> None:
        self._prefix_index = {}
        for rule in self.rules:
            status_index = self._prefix_index.setdefault(rule.status, {})
            for pfx in get_rule_prefixes(rule):
                status_index.setdefault(pfx, []).append(rule)
        self._indexed_rules_count = len(self.rules)

    def _ensure_index(self) -> None:
        if self._indexed_rules_count != len(self.rules):
            self._build_index()

    def reload(self) -> tuple[int, list[str]]:
        """Reload all rules from the substrate directory."""
        self.rules, self.diagnostics = discover_rules(self.substrate_dir)
        self._build_index()
        return len(self.rules), self.diagnostics

    def get_rules(self, status: Optional[str] = None) -> list[InvariantRule]:
        """Return rules filtered by status (e.g. 'active', 'candidate', 'archive')."""
        if status is None:
            return list(self.rules)
        return [r for r in self.rules if r.status == status]

    def get_rule_by_id(self, rule_id: str) -> Optional[InvariantRule]:
        """Look up a rule by its unique identifier."""
        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        return None

    def _get_candidates(self, norm_path: str, status: str) -> list[InvariantRule]:
        self._ensure_index()
        status_index = self._prefix_index.get(status)
        if not status_index:
            return []

        universal = status_index.get("", [])
        if len(status_index) == 1 and "" in status_index:
            return list(universal)

        candidates: list[InvariantRule] = list(universal)
        seen_ids = {r.id for r in universal}

        idx = 0
        while True:
            idx = norm_path.find("/", idx)
            if idx == -1:
                break
            pfx = norm_path[: idx + 1]
            rules_at_pfx = status_index.get(pfx)
            if rules_at_pfx:
                for r in rules_at_pfx:
                    if r.id not in seen_ids:
                        seen_ids.add(r.id)
                        candidates.append(r)
            idx += 1

        return candidates

    def match_file(
        self,
        target_path: str,
        language: Optional[str] = None,
        status: str = "active",
    ) -> list[InvariantRule]:
        """Find rules matching a target file path and language."""
        norm_path = normalize_path(target_path)
        candidates = self._get_candidates(norm_path, status=status)
        return [r for r in candidates if match_rule(r, norm_path, language)]

    def match_files(
        self,
        file_paths: list[str],
        status: str = "active",
    ) -> dict[str, list[InvariantRule]]:
        """Find matching rules for multiple file paths."""
        self._ensure_index()
        results: dict[str, list[InvariantRule]] = {}
        for path in file_paths:
            results[path] = self.match_file(path, status=status)
        return results

"""Matching engine for invariant rule scopes (paths and languages)."""

from __future__ import annotations
import glob
import re
from functools import lru_cache
from pathlib import Path
from typing import Optional

from aos.models import InvariantRule

EXTENSION_LANGUAGE_MAP: dict[str, str] = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".hxx": "cpp",
    ".h": "cpp",
    ".c": "c",
    ".cu": "cuda",
    ".cuh": "cuda",
    ".rs": "rust",
    ".go": "go",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".ts": "typescript",
    ".mts": "typescript",
    ".cts": "typescript",
    ".java": "java",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".sh": "bash",
    ".bash": "bash",
}


@lru_cache(maxsize=4096)
def _compile_glob(pattern: str) -> re.Pattern[str]:
    # Normalize slashes in pattern
    normalized_pattern = pattern.replace("\\", "/")
    regex_str = glob.translate(normalized_pattern, recursive=True, include_hidden=True)
    return re.compile(regex_str)


@lru_cache(maxsize=4096)
def normalize_path(path: str) -> str:
    """Normalize file path to POSIX style without leading relative prefixes."""
    p = path.replace("\\", "/")
    if p.startswith("./"):
        p = p[2:]
    return p


def match_path(pattern: str, target_path: str) -> bool:
    """Match a target path against a glob pattern with globstar (**) support."""
    normalized = normalize_path(target_path)
    regex = _compile_glob(pattern)
    return bool(regex.match(normalized))


@lru_cache(maxsize=4096)
def infer_language(file_path: str) -> Optional[str]:
    """Infer the programming language identifier from a file path extension."""
    dot_idx = file_path.rfind(".")
    if dot_idx == -1:
        return None
    slash_idx = max(file_path.rfind("/"), file_path.rfind("\\"))
    if dot_idx <= slash_idx:
        return None
    suffix = file_path[dot_idx:].lower()
    return EXTENSION_LANGUAGE_MAP.get(suffix)


@lru_cache(maxsize=4096)
def extract_path_prefix(pattern: str) -> str:
    """Extract literal directory prefix before any glob wildcard character."""
    norm = normalize_path(pattern)
    wildcard_indices = [norm.find(ch) for ch in ("*", "?", "[") if norm.find(ch) != -1]
    limit = min(wildcard_indices) if wildcard_indices else len(norm)
    literal_prefix = norm[:limit]
    slash_idx = literal_prefix.rfind("/")
    if slash_idx != -1:
        return literal_prefix[: slash_idx + 1]
    return ""


def get_rule_prefixes(rule: InvariantRule) -> list[str]:
    """Extract path prefixes associated with a rule."""
    if not rule.scope.paths:
        return [""]
    prefixes: list[str] = []
    for pat in rule.scope.paths:
        pfx = extract_path_prefix(pat)
        if pfx == "":
            return [""]
        prefixes.append(pfx)
    return prefixes


def match_rule(
    rule: InvariantRule,
    target_path: str,
    target_language: Optional[str] = None,
) -> bool:
    """Check if an invariant rule applies to the specified file and language."""
    norm_path = normalize_path(target_path)

    # Path scope check
    if rule.scope.paths:
        path_matched = any(match_path(pat, norm_path) for pat in rule.scope.paths)
        if not path_matched:
            return False

    # Language scope check
    if rule.scope.languages:
        resolved_lang = target_language.lower() if target_language else infer_language(norm_path)
        if not resolved_lang:
            return False
        if not any(lang.lower() == resolved_lang for lang in rule.scope.languages):
            return False

    return True

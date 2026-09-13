"""Agent Operating Substrate (AOS) core package."""

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import BlackboardEvent, post_event, read_events
from aos.ci import CIReport, run_ci_check
from aos.curator import archive_rule, curate_substrate
from aos.daemon import SubstrateDaemon
from aos.discovery import discover_rules
from aos.engine import RuleEngine
from aos.enforcer import Violation, check_file_violations, enforce_all
from aos.executor import execute_and_autopsy
from aos.fleet import list_fleet_rules, publish_to_fleet, sync_from_fleet
from aos.harness import (
    detect_configured_harnesses,
    format_rules_for_prompt,
    inject_into_file,
    sync_harnesses,
)
from aos.hook import install_git_hook, run_pre_commit_check, uninstall_git_hook
from aos.matcher import infer_language, match_path, match_rule
from aos.mcp import run_mcp_server
from aos.mesh import MeshSimulationResult, simulate_mesh_cycle
from aos.models import Invariant, InvariantRule, Provenance, Scope
from aos.packs import CURATED_PACKS, install_pack, list_available_packs
from aos.ui import start_ui_server
from aos.validator import validate_rule_dict

__all__ = [
    "InvariantRule",
    "Scope",
    "Invariant",
    "Provenance",
    "validate_rule_dict",
    "match_rule",
    "match_path",
    "infer_language",
    "discover_rules",
    "RuleEngine",
    "BlackboardEvent",
    "post_event",
    "read_events",
    "synthesize_candidate_rule",
    "inscribe_candidate",
    "promote_candidate",
    "curate_substrate",
    "archive_rule",
    "format_rules_for_prompt",
    "inject_into_file",
    "sync_harnesses",
    "detect_configured_harnesses",
    "Violation",
    "check_file_violations",
    "enforce_all",
    "install_git_hook",
    "uninstall_git_hook",
    "run_pre_commit_check",
    "run_mcp_server",
    "SubstrateDaemon",
    "MeshSimulationResult",
    "simulate_mesh_cycle",
    "CIReport",
    "run_ci_check",
    "publish_to_fleet",
    "list_fleet_rules",
    "sync_from_fleet",
    "execute_and_autopsy",
    "CURATED_PACKS",
    "list_available_packs",
    "install_pack",
    "start_ui_server",
]

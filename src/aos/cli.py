"""CLI interface for the Agent Operating Substrate."""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import post_event, read_events
from aos.ci import (
    install_ci_workflow,
    review_pr_diff,
    run_ci_check,
    uninstall_ci_workflow,
)
from aos.curator import curate_substrate
from aos.daemon import SubstrateDaemon
from aos.engine import RuleEngine
from aos.enforcer import auto_fix_file, enforce_all
from aos.executor import execute_and_autopsy
from aos.fleet import (
    export_fleet_bundle,
    import_fleet_bundle,
    list_fleet_rules,
    publish_to_fleet,
    sync_from_fleet,
)
from aos.harness import START_MARKER, detect_configured_harnesses, sync_harnesses
from aos.hook import install_git_hook, run_pre_commit_check, uninstall_git_hook
from aos.mcp import run_mcp_server
from aos.mesh import simulate_mesh_cycle
from aos.packs import install_pack, list_available_packs, recommend_packs, uninstall_pack
from aos.ui import start_ui_server

DEFAULT_CONFIG_YAML = """version: 1
substrate:
  path: ".agents/substrate"
  auto_archive_days: 90
blackboard:
  path: ".agents/blackboard"
  event_log: ".agents/blackboard/events.jsonl"
daemon:
  poll_interval_seconds: 5
"""


def cmd_init(args: argparse.Namespace) -> int:
    """Initialize substrate directory layout, install packs, and sync agent harnesses."""
    root = Path(args.root)
    dirs = [
        root / ".agents" / "substrate" / "active",
        root / ".agents" / "substrate" / "candidate",
        root / ".agents" / "substrate" / "archive",
        root / ".agents" / "blackboard" / "intents",
        root / ".agents" / "blackboard" / "critiques",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

    config_path = root / ".agents" / "config.yaml"
    if not config_path.exists():
        config_path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")

    event_log = root / ".agents" / "blackboard" / "events.jsonl"
    if not event_log.exists():
        event_log.touch()

    is_bare = getattr(args, "bare", False)
    installed_packs: list[str] = []
    detected_stack_parts: list[str] = []
    synced_harnesses: dict[str, Path] = {}
    hook_status = "Skipped (--bare mode)" if is_bare else "Skipped (no .git directory)"

    if not is_bare:
        # 1. Ingest existing team guidelines if prompt files exist
        prompt_candidates = [
            ".cursorrules",
            "CLAUDE.md",
            "AGENTS.md",
            ".windsurfrules",
            "CONTRIBUTING.md",
            ".github/copilot-instructions.md",
            "GEMINI.md",
            "CODEX.md",
            "CONVENTIONS.md",
            ".clinerules",
            ".roomodes",
        ]
        has_prompts = any((root / p).is_file() for p in prompt_candidates)
        if has_prompts:
            from aos.ingest import ingest_repository_conventions
            ingest_repository_conventions(root_dir=root, auto_promote=True)

        # 2. Detect repository language/frameworks via recommend_packs()
        recommended = recommend_packs(root_dir=root)
        for p in recommended:
            install_pack(p, root_dir=root, promote=True)
            installed_packs.append(p)

        if "python-core" in recommended:
            detected_stack_parts.append("Python")
        if "typescript-core" in recommended:
            detected_stack_parts.append("TypeScript")
        if "rust-core" in recommended:
            detected_stack_parts.append("Rust")
        if "go-core" in recommended:
            detected_stack_parts.append("Go")

        try:
            from aos.ingest import scan_repository_conventions
            rep = scan_repository_conventions(root_dir=root)
            for lang in rep.detected_languages:
                detected_stack_parts.append(lang.title())
            for fw in rep.detected_frameworks:
                detected_stack_parts.append(fw.title())
        except Exception:
            pass

        # 3. Automatically project invariants into all detected harnesses via sync_harnesses()
        detected_harnesses = detect_configured_harnesses(root_dir=root)
        to_sync = list(dict.fromkeys(detected_harnesses + ["agents", "cursor", "claude"]))
        synced_harnesses = sync_harnesses(root_dir=root, harnesses=to_sync)

        # 4. If a .git directory exists and not --bare, automatically install the git pre-commit hook
        git_dir = root / ".git"
        if git_dir.is_dir():
            try:
                install_git_hook(root_dir=root)
                hook_status = "Installed (.git/hooks/pre-commit) [Active]"
            except Exception as exc:
                hook_status = f"Failed to install ({exc})"

    engine = RuleEngine(root_dir=root)
    active_count = len(engine.get_rules(status="active"))

    stack_display = ", ".join(dict.fromkeys(detected_stack_parts)) if detected_stack_parts else "Generic / Language-Agnostic"
    if is_bare:
        packs_display = "None (--bare mode)"
    else:
        packs_display = f"{', '.join(installed_packs) if installed_packs else 'None'} ({active_count} active invariants)"

    name_labels = {
        "cursor": "Cursor (.cursorrules)",
        "cursor_mdc": "Cursor (.cursor/rules)",
        "claude": "Claude Code (CLAUDE.md)",
        "copilot": "GitHub Copilot (.github/copilot-instructions.md)",
        "windsurf": "Windsurf (.windsurfrules)",
        "gemini": "Gemini (.gemini/instructions.md)",
        "gemini_root": "Gemini (GEMINI.md)",
        "codex": "OpenAI Codex (.openai/instructions.md)",
        "codex_root": "OpenAI Codex (CODEX.md)",
        "aider": "Aider (CONVENTIONS.md)",
        "cline": "Cline (.clinerules)",
        "roo": "Roo Code (.roomodes)",
        "amazonq": "Amazon Q (.amazonq/rules.md)",
        "agents": "Universal Agents (AGENTS.md)",
    }
    tools_list = [name_labels.get(h, h) for h in synced_harnesses.keys()]
    tools_display = ", ".join(tools_list) if tools_list else "None"

    print("=" * 70)
    print("           Agent Operating Substrate (AOS) Initialized")
    print("=" * 70)
    print(f"  Detected Stack:      {stack_display}")
    print(f"  Installed Packs:     {packs_display}")
    print(f"  Connected AI Tools:  {tools_display}")
    print(f"  Pre-Commit Hook:     {hook_status}")
    print("-" * 70)
    print("  Next Steps:")
    print("    - Run 'aos status' (or 'aos doctor') to verify guardrails")
    print("    - Run 'aos ui' to launch the visualizer dashboard")
    print("=" * 70)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    """Inspect substrate health, rule counts, harness synchronization, and incident status."""
    root = Path(args.root)
    agents_dir = root / ".agents"
    config_file = agents_dir / "config.yaml"
    event_file = agents_dir / "blackboard" / "events.jsonl"

    print("=" * 70)
    print("                 Agent Operating Substrate (AOS) Status")
    print("=" * 70)

    # 1. Check Substrate Core Status
    print("\n[Substrate Core]")
    if not agents_dir.is_dir():
        print("  Status:            [OFF] Substrate not initialized (.agents/ missing)")
        print("  Active Invariants: [OFF] 0 active rules")
        print("  Candidate Rules:   [OFF] 0 candidate rules")
        print("  Archived Rules:    [OFF] 0 archived rules")
        print("\n" + "=" * 70)
        print("Overall Health: [OFF] Substrate not initialized. Run 'aos init' to set up.")
        print("=" * 70)
        return 1

    print("  Status:            [OK] Initialized (.agents/)")
    if config_file.is_file():
        print("  Configuration:     [OK] .agents/config.yaml")
    else:
        print("  Configuration:     [WARN] .agents/config.yaml missing")

    engine = RuleEngine(root_dir=root)
    active_rules = engine.get_rules(status="active")
    candidate_rules = engine.get_rules(status="candidate")
    archive_rules = engine.get_rules(status="archive")

    if active_rules:
        print(f"  Active Invariants: [OK] {len(active_rules)} active rules")
    else:
        print("  Active Invariants: [WARN] 0 active rules (run 'aos pack install <pack>')")

    print(f"  Candidate Rules:   [OK] {len(candidate_rules)} candidate rules")
    print(f"  Archived Rules:    [OK] {len(archive_rules)} archived rules")

    # 2. Check AI Harnesses Status
    print("\n[AI Agent Harnesses]")
    harness_checks: list[tuple[str, list[Path]]] = [
        ("Universal Agents", [root / "AGENTS.md"]),
        ("Claude Code", [root / "CLAUDE.md"]),
        ("Cursor", [root / ".cursorrules", root / ".cursor" / "rules" / "aos-invariants.mdc"]),
        ("GitHub Copilot", [root / ".github" / "copilot-instructions.md"]),
        ("Windsurf", [root / ".windsurfrules"]),
        ("Gemini", [root / "GEMINI.md", root / ".gemini" / "instructions.md"]),
        ("OpenAI Codex", [root / "CODEX.md", root / ".openai" / "instructions.md"]),
        ("Aider", [root / "CONVENTIONS.md"]),
        ("Cline", [root / ".clinerules"]),
        ("Roo Code", [root / ".roomodes"]),
        ("Amazon Q", [root / ".amazonq" / "rules.md"]),
    ]

    for tool_name, check_paths in harness_checks:
        found_path: Path | None = None
        for p in check_paths:
            if p.is_file():
                found_path = p
                break

        if found_path is not None:
            rel = found_path.relative_to(root)
            content = found_path.read_text(encoding="utf-8", errors="ignore")
            if START_MARKER in content:
                print(f"  {tool_name:18}: [OK] Synced ({rel})")
            else:
                print(f"  {tool_name:18}: [WARN] Present but not synced ({rel}; run 'aos sync')")
        else:
            first_rel = check_paths[0].relative_to(root)
            print(f"  {tool_name:18}: [OFF] Not configured ({first_rel})")

    # 3. Check Git Pre-Commit Hook Status
    print("\n[Git Integrity Barrier]")
    git_dir = root / ".git"
    hook_ok = False
    if git_dir.is_dir():
        print("  Git Repository:    [OK] Present (.git/)")
        hook_path = git_dir / "hooks" / "pre-commit"
        if hook_path.is_file():
            content = hook_path.read_text(encoding="utf-8", errors="ignore")
            if "aos hook run" in content or "aos" in content:
                print("  Pre-Commit Hook:   [OK] Installed and active (.git/hooks/pre-commit)")
                hook_ok = True
            else:
                print("  Pre-Commit Hook:   [WARN] Hook present without AOS guard (.git/hooks/pre-commit)")
        else:
            print("  Pre-Commit Hook:   [WARN] Not installed (run 'aos hook install')")
    else:
        print("  Git Repository:    [OFF] Not a git repository")
        print("  Pre-Commit Hook:   [OFF] N/A (no .git directory)")

    # 4. Check Blackboard Incidents
    print("\n[Blackboard & Incidents]")
    events = read_events(root_dir=root)
    if event_file.is_file():
        print(f"  Event Stream:      [OK] {event_file.relative_to(root)} ({len(events)} events)")
    else:
        print("  Event Stream:      [WARN] Event log missing")

    incident_types = {"PRE_COMMIT_BLOCKED", "AUTOPSY_RECORD", "ENFORCEMENT_VIOLATION"}
    incidents = [e for e in events if e.type in incident_types]
    if incidents:
        print(f"  Recent Incidents:  [WARN] {len(incidents)} barrier incident(s) recorded:")
        for ev in list(reversed(incidents))[:5]:
            p = ev.payload or {}
            rid = p.get("rule_id", "unknown")
            loc = p.get("file_path", "")
            loc_str = f" in {loc}" if loc else ""
            msg = p.get("message") or p.get("statement") or ""
            msg_snippet = f": {msg}" if msg else ""
            print(f"    * [{ev.timestamp}] {ev.type}: {rid}{loc_str}{msg_snippet}")
    else:
        print("  Recent Incidents:  [OK] 0 barrier incidents recorded")

    print("\n" + "=" * 70)
    if active_rules and (hook_ok or not git_dir.is_dir()):
        print("Overall Health: [OK] Substrate operational and guardrails active.")
    elif not active_rules:
        print("Overall Health: [WARN] No active rules installed (run 'aos pack install <pack>').")
    else:
        print("Overall Health: [WARN] Git pre-commit barrier not active (run 'aos hook install').")
    print("=" * 70)
    return 0


def cmd_doctor(args: argparse.Namespace) -> int:
    """Run diagnostic health check on substrate and agent environment."""
    return cmd_status(args)


def cmd_rules_list(args: argparse.Namespace) -> int:
    """List rules matching the requested status filter."""
    engine = RuleEngine(root_dir=args.root)
    rules = engine.get_rules(status=args.status)

    if not rules:
        status_label = f" with status '{args.status}'" if args.status else ""
        print(f"No rules found{status_label}.")
        return 0

    print(f"Found {len(rules)} rule(s):")
    for r in rules:
        loc = f" ({r.file_path})" if r.file_path else ""
        print(f"[{r.status.upper()}] {r.id} (v{r.version}){loc}")
        print(f"  Statement:   {r.invariant.statement}")
        print(f"  Enforcement: {r.invariant.enforcement}")
        if r.scope.paths:
            print(f"  Paths:       {', '.join(r.scope.paths)}")
        if r.scope.languages:
            print(f"  Languages:   {', '.join(r.scope.languages)}")
        print()
    return 0


def cmd_rules_check(args: argparse.Namespace) -> int:
    """Check which active invariant rules match target files."""
    engine = RuleEngine(root_dir=args.root)
    matches_by_file = engine.match_files(args.files, status="active")

    total_matches = 0
    for file_path, matched_rules in matches_by_file.items():
        print(f"File: {file_path}")
        if not matched_rules:
            print("  No active invariant rules matched.")
        else:
            for rule in matched_rules:
                total_matches += 1
                print(f"  Matched Rule: [{rule.id}] {rule.invariant.statement}")
                print(f"    Enforcement: {rule.invariant.enforcement}")
                print(f"    Rationale:   {rule.invariant.rationale}")
        print()

    if getattr(args, "fix", False):
        total_fixed = 0
        for f in args.files:
            fixes = auto_fix_file(f, root_dir=args.root)
            if fixes:
                total_fixed += len(fixes)
                print(f"Auto-fixed {f}:")
                for fix in fixes:
                    print(f"  - {fix}")
        if total_fixed > 0:
            print(f"Successfully applied {total_fixed} automated fix(es).")

    if args.enforce:
        violations = enforce_all(args.files, root_dir=args.root)
        if violations:
            print("Violations detected:")
            for v in violations:
                loc = f":{v.line_number}" if v.line_number else ""
                print(f"- [{v.rule_id}] {v.file_path}{loc}: {v.message}")
            return 1

    return 0 if total_matches == 0 else 1 if args.fail_on_match else 0


def cmd_enforce(args: argparse.Namespace) -> int:
    """Deterministically validate files against all active rules."""
    if getattr(args, "fix", False):
        total_fixed = 0
        for f in args.files:
            fixes = auto_fix_file(f, root_dir=args.root)
            if fixes:
                total_fixed += len(fixes)
                print(f"Auto-fixed {f}:")
                for fix in fixes:
                    print(f"  - {fix}")
        if total_fixed > 0:
            print(f"Successfully applied {total_fixed} automated fix(es).")

    violations = enforce_all(args.files, root_dir=args.root)
    if not violations:
        print("All files passed invariant verification.")
        return 0

    print(f"Detected {len(violations)} invariant violation(s):")
    for v in violations:
        loc = f":{v.line_number}" if v.line_number else ""
        print(f"- [{v.rule_id}] {v.file_path}{loc}: {v.message} ({v.enforcement})")
    return 1


def cmd_sync(args: argparse.Namespace) -> int:
    """Sync active substrate rules into target agent harness configurations."""
    harness_list = [h.strip() for h in args.harnesses.split(",")] if args.harnesses else None
    synced = sync_harnesses(root_dir=args.root, harnesses=harness_list)
    print(f"Synced {len(synced)} agent harness configuration(s):")
    for name, path in synced.items():
        print(f"- {name}: {path}")
    return 0


def cmd_hook_install(args: argparse.Namespace) -> int:
    """Install AOS pre-commit git hook."""
    hook_path = install_git_hook(root_dir=args.root)
    print(f"Installed AOS pre-commit hook at {hook_path}")
    return 0


def cmd_hook_uninstall(args: argparse.Namespace) -> int:
    """Uninstall AOS pre-commit git hook."""
    removed = uninstall_git_hook(root_dir=args.root)
    if removed:
        print("Uninstalled AOS pre-commit hook.")
    else:
        print("No AOS hook found to uninstall.")
    return 0


def cmd_hook_run(args: argparse.Namespace) -> int:
    """Run pre-commit check on staged files."""
    return run_pre_commit_check(root_dir=args.root)


def cmd_mcp(args: argparse.Namespace) -> int:
    """Start standard Model Context Protocol (MCP) server over stdio."""
    run_mcp_server(root_dir=args.root)
    return 0


def cmd_daemon_start(args: argparse.Namespace) -> int:
    """Start background autonomous auditor and curator daemon."""
    daemon = SubstrateDaemon(
        root_dir=args.root,
        poll_interval=args.interval,
        curation_interval=args.curation_interval,
    )
    if args.once:
        reactions = daemon.tick()
        print(f"Daemon executed single tick: generated {len(reactions)} reaction(s).")
        return 0

    print(f"Starting AOS background daemon (polling every {args.interval}s)...")
    daemon.run()
    return 0


def cmd_mesh_simulate(args: argparse.Namespace) -> int:
    """Simulate unprompted peer-to-peer agent mesh coordination."""
    result = simulate_mesh_cycle(
        root_dir=args.root,
        intent_id=args.intent_id or "",
        description=args.desc,
        target_files=args.files,
    )
    print(f"Peer Mesh Simulation: Intent '{result.intent_id}' - Status: {result.status.upper()}")
    print(f"Emitted {len(result.events)} event(s) to blackboard:")
    for ev in result.events:
        print(f"- [{ev.type}] From: {ev.sender}")
    return 0 if result.status == "converged" else 1


def cmd_ci_run(args: argparse.Namespace) -> int:
    """Run CI pipeline check on modified files."""
    report = run_ci_check(
        files=args.files,
        base_ref=args.base,
        auto_sync=args.auto_sync,
        root_dir=args.root,
    )
    print(report.to_markdown())
    return 0 if report.status == "passed" else 1


def cmd_ci_review(args: argparse.Namespace) -> int:
    """Analyze a pull request diff and generate inline review comments."""
    if getattr(args, "diff", None):
        diff_text = Path(args.diff).read_text(encoding="utf-8")
    else:
        diff_text = sys.stdin.read()
    result = review_pr_diff(diff_text, root_dir=args.root)
    print(f"PR Review Status: {result['status'].upper()} ({result['comments_count']} comment(s))")
    for c in result["comments"]:
        print(f"- {c['file_path']}:{c['line_number']} [{c['rule_id']}]: {c['message']}")
    return 0 if result["status"] == "approved" else 1


def cmd_ci_install(args: argparse.Namespace) -> int:
    """Install GitHub Actions invariant verification workflow."""
    wf_path = install_ci_workflow(root_dir=args.root)
    print(f"Installed GitHub Actions workflow: {wf_path}")
    return 0


def cmd_ci_uninstall(args: argparse.Namespace) -> int:
    """Remove GitHub Actions invariant verification workflow."""
    removed = uninstall_ci_workflow(root_dir=args.root)
    if removed:
        print("Uninstalled GitHub Actions workflow.")
    else:
        print("No GitHub Actions workflow found to uninstall.")
    return 0



def cmd_fleet_list(args: argparse.Namespace) -> int:
    """List rules in enterprise fleet ledger."""
    rules = list_fleet_rules(fleet_db_path=args.db)
    if not rules:
        print("Fleet ledger empty.")
        return 0
    print(f"Found {len(rules)} fleet rule(s):")
    for r in rules:
        print(f"- [{r['status'].upper()}] {r['id']} (Origin: {r['origin_repo']}, Published: {r['published_at']})")
    return 0


def cmd_fleet_publish(args: argparse.Namespace) -> int:
    """Publish an active rule to enterprise fleet ledger."""
    ok = publish_to_fleet(
        rule_id=args.rule_id,
        repo_root=args.root,
        origin_repo_id=args.repo_id,
        fleet_db_path=args.db,
    )
    if ok:
        print(f"Published rule '{args.rule_id}' to fleet ledger at {args.db}")
        return 0
    print(f"Failed: rule '{args.rule_id}' not found in active substrate.", file=sys.stderr)
    return 1


def cmd_fleet_sync(args: argparse.Namespace) -> int:
    """Sync fleet rules into local substrate."""
    count = sync_from_fleet(repo_root=args.root, fleet_db_path=args.db)
    print(f"Synced {count} rule(s) from fleet ledger into .agents/substrate/active/")
    return 0


def cmd_fleet_export(args: argparse.Namespace) -> int:
    """Export fleet rules to a portable JSON bundle file."""
    count = export_fleet_bundle(fleet_db_path=args.db, output_path=args.output)
    print(f"Exported {count} fleet rule(s) to bundle at {args.output}")
    return 0


def cmd_fleet_import(args: argparse.Namespace) -> int:
    """Import fleet rules from a bundle file."""
    try:
        count = import_fleet_bundle(bundle_path=args.bundle, fleet_db_path=args.db)
        print(f"Imported {count} rule(s) from bundle into fleet ledger at {args.db}")
        return 0
    except Exception as e:
        print(f"Error importing fleet bundle: {e}", file=sys.stderr)
        return 1



def cmd_exec(args: argparse.Namespace) -> int:
    """Execute command with automatic failure autopsy synthesis."""
    code, autopsy_path = execute_and_autopsy(
        args.cmd,
        root_dir=args.root,
        auto_inscribe=not args.no_autopsy,
    )
    return code


def cmd_pack_list(args: argparse.Namespace) -> int:
    """List available curated invariant packs."""
    packs = list_available_packs()
    print("Available Curated Invariant Packs:")
    for name, count in packs.items():
        print(f"- {name} ({count} rules)")
    return 0


def cmd_pack_install(args: argparse.Namespace) -> int:
    """Install a curated invariant pack."""
    try:
        installed = install_pack(
            args.pack_name,
            root_dir=args.root,
            promote=not args.candidate,
        )
        status_str = "candidate" if args.candidate else "active"
        print(f"Installed {len(installed)} rule(s) into {status_str} substrate:")
        for p in installed:
            print(f"- {p}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_pack_uninstall(args: argparse.Namespace) -> int:
    """Uninstall a curated invariant pack by archiving or removing its rules."""
    try:
        uninstalled = uninstall_pack(
            args.pack_name,
            root_dir=args.root,
            archive=not args.delete,
        )
        action_str = "deleted" if args.delete else "archived"
        print(f"Uninstalled {len(uninstalled)} rule(s) ({action_str}):")
        for p in uninstalled:
            print(f"- {p}")
        return 0
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


def cmd_ui(args: argparse.Namespace) -> int:
    """Launch local web visualizer dashboard."""
    start_ui_server(port=args.port, root_dir=args.root)
    return 0


def cmd_autopsy(args: argparse.Namespace) -> int:
    """Conduct a failure autopsy and inscribe candidate or active rule."""
    candidate = synthesize_candidate_rule(
        rule_id=args.id,
        statement=args.statement,
        rationale=args.rationale,
        paths=args.paths,
        languages=args.languages,
        incident_id=args.incident,
        inscribing_agent=args.agent,
    )
    saved_path = inscribe_candidate(candidate, substrate_dir=Path(args.root) / ".agents" / "substrate")
    print(f"Candidate rule inscribed: {saved_path}")

    if args.promote:
        promoted_path = promote_candidate(
            rule_id=args.id,
            peer_agent="consensus-evaluator",
            substrate_dir=Path(args.root) / ".agents" / "substrate",
        )
        print(f"Rule promoted to active: {promoted_path}")

    return 0


def cmd_curate(args: argparse.Namespace) -> int:
    """Execute evolutionary pruning and subsumption on active rules."""
    actions = curate_substrate(
        substrate_dir=Path(args.root) / ".agents" / "substrate",
        dry_run=args.dry_run,
    )
    mode = " (DRY RUN)" if args.dry_run else ""
    if not actions:
        print(f"Substrate clean: zero curation actions required{mode}.")
        return 0

    print(f"Executed {len(actions)} curation action(s){mode}:")
    for act in actions:
        print(f"- [{act.action_type}] Rule '{act.rule_id}': {act.reason}")
    return 0


def cmd_blackboard_list(args: argparse.Namespace) -> int:
    """List events posted to the local blackboard."""
    events = read_events(root_dir=args.root, event_type=args.type, sender=args.sender)
    if not events:
        print("No blackboard events found.")
        return 0

    print(f"Found {len(events)} event(s):")
    for ev in events:
        print(f"[{ev.timestamp}] ({ev.type}) From: {ev.sender} (ID: {ev.event_id})")
        print(f"  Payload: {json.dumps(ev.payload)}")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    """Scan repository conventions and synthesize tailor-made invariants."""
    from aos.ingest import ingest_repository, scan_repository_conventions
    root = Path(args.root)
    if args.dry_run:
        report = scan_repository_conventions(root_dir=root)
        print(f"Detected languages: {', '.join(report.detected_languages) or 'none'}")
        print(f"Detected frameworks: {', '.join(report.detected_frameworks) or 'none'}")
        print(f"Scanned config files: {', '.join(report.scanned_config_files) or 'none'}")
        print(f"Found instruction files: {', '.join(report.existing_instruction_files) or 'none'}")
        print(f"Recommended packs: {', '.join(report.recommended_packs) or 'none'}")
        print(f"\nProposed {len(report.synthesized_rules)} invariant rule(s):")
        for r in report.synthesized_rules:
            print(f"- [{r['id']}] {r['statement']}")
        return 0

    install_packs_flag = getattr(args, "install_packs", False)
    report = ingest_repository(
        root_dir=root,
        auto_promote=args.promote,
        install_recommended_packs=install_packs_flag,
    )
    status_label = "active" if args.promote else "candidate"
    print(f"Ingested {len(report.synthesized_rules)} rule(s) as {status_label}:")
    for r in report.synthesized_rules:
        print(f"- [{r['id']}] {r['statement']}")
    if install_packs_flag and report.recommended_packs:
        print(f"Installed recommended packs: {', '.join(report.recommended_packs)}")
    return 0


def cmd_identity_list(args: argparse.Namespace) -> int:
    """List autonomous agent identities and supervisory mailboxes."""
    from aos.identity import list_identities
    identities = list_identities(root_dir=args.root)
    if not identities:
        print("No autonomous agent identities in vault. Run 'aos identity create' to initialize.")
        return 0
    print(f"Found {len(identities)} autonomous agent identity/identities in vault:")
    for ident in identities:
        print(f"- Persona:  {ident.get('persona')}")
        print(f"  Address:  {ident.get('address')}")
        print(f"  Webmail:  {ident.get('webmail_url')} (Supervision: Login with email & password)")
        print()
    return 0


def cmd_identity_create(args: argparse.Namespace) -> int:
    """Create a free programmatic mailbox for an autonomous agent persona."""
    from aos.identity import create_agent_account
    ident = create_agent_account(persona=args.persona, password=args.password, root_dir=args.root)
    print("=" * 70)
    print("AUTONOMOUS AGENT IDENTITY CREATED")
    print("=" * 70)
    print(f"Persona:       {ident['persona']}")
    print(f"Email Address: {ident['address']}")
    print(f"Password:      {ident['password']}")
    print(f"Webmail Login: {ident['webmail_url']}")
    print("Supervision:   Saved to .agents/vault/identities.json (gitignored).")
    print("=" * 70)
    return 0


def cmd_identity_inbox(args: argparse.Namespace) -> int:
    """Check incoming messages for an agent persona."""
    from aos.identity import fetch_agent_messages
    try:
        messages = fetch_agent_messages(persona_or_address=args.persona, root_dir=args.root)
    except Exception as exc:
        print(f"Error reading inbox: {exc}")
        return 1
    if not messages:
        print(f"Inbox for '{args.persona}' is empty.")
        return 0
    print(f"Found {len(messages)} message(s) for '{args.persona}':")
    for m in messages:
        sender = m.get("from", {}).get("address", "unknown")
        print(f"- ID: {m.get('id')} | From: {sender} | Subject: {m.get('subject')}")
        print(f"  Snippet: {m.get('intro')}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aos",
        description="Agent Operating Substrate: Stigmergic runtime for autonomous coding agents.",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Repository root directory (defaults to current directory).",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # aos init
    p_init = subparsers.add_parser("init", help="Initialize .agents/ substrate in target repository.")
    p_init.add_argument("--root", default=argparse.SUPPRESS, help="Repository root directory.")
    p_init.add_argument("--bare", action="store_true", help="Initialize empty substrate without installing default packs.")
    p_init.set_defaults(func=cmd_init)

    # aos status
    p_status = subparsers.add_parser("status", help="Inspect substrate health, rule counts, and harness status.")
    p_status.add_argument("--root", default=argparse.SUPPRESS, help="Repository root directory.")
    p_status.set_defaults(func=cmd_status)

    # aos doctor
    p_doctor = subparsers.add_parser("doctor", help="Run diagnostic health check on substrate and agent environment.")
    p_doctor.add_argument("--root", default=argparse.SUPPRESS, help="Repository root directory.")
    p_doctor.set_defaults(func=cmd_doctor)

    # aos rules
    p_rules = subparsers.add_parser("rules", help="Manage and inspect substrate invariant rules.")
    rules_sub = p_rules.add_subparsers(dest="rules_command", required=True)

    p_rules_list = rules_sub.add_parser("list", help="List discovered substrate rules.")
    p_rules_list.add_argument(
        "--status",
        choices=["active", "candidate", "archive"],
        default=None,
        help="Filter rules by status.",
    )
    p_rules_list.set_defaults(func=cmd_rules_list)

    p_rules_check = rules_sub.add_parser("check", help="Check target files against active rules.")
    p_rules_check.add_argument("files", nargs="+", help="File paths to check.")
    p_rules_check.add_argument(
        "--enforce",
        action="store_true",
        help="Perform deterministic content validation.",
    )
    p_rules_check.add_argument(
        "--fail-on-match",
        action="store_true",
        help="Return non-zero exit code if any active rule matches.",
    )
    p_rules_check.add_argument(
        "--fix",
        action="store_true",
        help="Automatically remediate safe invariant violations.",
    )
    p_rules_check.set_defaults(func=cmd_rules_check)

    # aos enforce
    p_enforce = subparsers.add_parser("enforce", help="Enforce active invariant rules deterministically.")
    p_enforce.add_argument("files", nargs="+", help="Files to inspect.")
    p_enforce.add_argument(
        "--fix",
        action="store_true",
        help="Automatically remediate safe invariant violations.",
    )
    p_enforce.set_defaults(func=cmd_enforce)

    # aos sync
    p_sync = subparsers.add_parser("sync", help="Sync active rules to agent harness configurations.")
    p_sync.add_argument("--harnesses", default=None, help="Comma-separated harness names (cursor,copilot,windsurf).")
    p_sync.set_defaults(func=cmd_sync)

    # aos hook
    p_hook = subparsers.add_parser("hook", help="Manage universal git pre-commit hook.")
    hook_sub = p_hook.add_subparsers(dest="hook_command", required=True)

    p_hook_inst = hook_sub.add_parser("install", help="Install git pre-commit hook.")
    p_hook_inst.set_defaults(func=cmd_hook_install)

    p_hook_uninst = hook_sub.add_parser("uninstall", help="Uninstall git pre-commit hook.")
    p_hook_uninst.set_defaults(func=cmd_hook_uninstall)

    p_hook_run = hook_sub.add_parser("run", help="Run pre-commit check on staged files.")
    p_hook_run.set_defaults(func=cmd_hook_run)

    # aos mcp
    p_mcp = subparsers.add_parser("mcp", help="Launch Model Context Protocol (MCP) stdio server.")
    p_mcp.set_defaults(func=cmd_mcp)

    # aos daemon
    p_daemon = subparsers.add_parser("daemon", help="Manage background autonomous daemon.")
    daemon_sub = p_daemon.add_subparsers(dest="daemon_command", required=True)
    p_daemon_start = daemon_sub.add_parser("start", help="Start background daemon process.")
    p_daemon_start.add_argument("--interval", type=float, default=2.0, help="Polling interval in seconds.")
    p_daemon_start.add_argument("--curation-interval", type=float, default=300.0, help="Curation interval in seconds.")
    p_daemon_start.add_argument("--once", action="store_true", help="Execute single polling cycle and exit.")
    p_daemon_start.set_defaults(func=cmd_daemon_start)

    # aos mesh
    p_mesh = subparsers.add_parser("mesh", help="Simulate autonomous peer-to-peer agent mesh.")
    mesh_sub = p_mesh.add_subparsers(dest="mesh_command", required=True)
    p_mesh_sim = mesh_sub.add_parser("simulate", help="Run unprompted multi-agent cycle.")
    p_mesh_sim.add_argument("--intent-id", default=None, help="Optional intent identifier.")
    p_mesh_sim.add_argument("--desc", default="Refactor geometric normal calculation", help="Intent description.")
    p_mesh_sim.add_argument("--files", nargs="*", default=None, help="Target file paths.")
    p_mesh_sim.set_defaults(func=cmd_mesh_simulate)

    # aos ci
    p_ci = subparsers.add_parser("ci", help="CI pipeline integration commands.")
    ci_sub = p_ci.add_subparsers(dest="ci_command", required=True)
    p_ci_run = ci_sub.add_parser("run", help="Run CI verification on modified files.")
    p_ci_run.add_argument("--base", default="origin/main", help="Base ref branch.")
    p_ci_run.add_argument("--auto-sync", action="store_true", help="Sync harness files before check.")
    p_ci_run.add_argument("--files", nargs="*", default=None, help="Specific files to evaluate.")
    p_ci_run.set_defaults(func=cmd_ci_run)

    p_ci_rev = ci_sub.add_parser("review", help="Review pull request diff and generate inline comments.")
    p_ci_rev.add_argument("--diff", help="Path to unified diff file (reads from stdin if omitted).")
    p_ci_rev.set_defaults(func=cmd_ci_review)

    p_ci_inst = ci_sub.add_parser("install", help="Install GitHub Actions guardrail workflow.")
    p_ci_inst.set_defaults(func=cmd_ci_install)

    p_ci_uninst = ci_sub.add_parser("uninstall", help="Remove GitHub Actions guardrail workflow.")
    p_ci_uninst.set_defaults(func=cmd_ci_uninstall)

    # aos fleet
    p_fleet = subparsers.add_parser("fleet", help="Enterprise cross-repository fleet invariant mesh.")
    fleet_sub = p_fleet.add_subparsers(dest="fleet_command", required=True)

    p_fleet_list = fleet_sub.add_parser("list", help="List rules in organization fleet ledger.")
    p_fleet_list.add_argument("--db", default=".agents/fleet.db", help="Path to fleet database.")
    p_fleet_list.set_defaults(func=cmd_fleet_list)

    p_fleet_pub = fleet_sub.add_parser("publish", help="Publish local rule to fleet ledger.")
    p_fleet_pub.add_argument("rule_id", help="Rule identifier to publish.")
    p_fleet_pub.add_argument("--repo-id", default="local-repo", help="Origin repository identifier.")
    p_fleet_pub.add_argument("--db", default=".agents/fleet.db", help="Path to fleet database.")
    p_fleet_pub.set_defaults(func=cmd_fleet_publish)

    p_fleet_sync = fleet_sub.add_parser("sync", help="Pull active rules from fleet ledger.")
    p_fleet_sync.add_argument("--db", default=".agents/fleet.db", help="Path to fleet database.")
    p_fleet_sync.set_defaults(func=cmd_fleet_sync)

    p_fleet_exp = fleet_sub.add_parser("export", help="Export fleet ledger to portable JSON bundle.")
    p_fleet_exp.add_argument("--db", default=".agents/fleet.db", help="Path to fleet database.")
    p_fleet_exp.add_argument("--output", default=".agents/fleet-bundle.json", help="Target output bundle path.")
    p_fleet_exp.set_defaults(func=cmd_fleet_export)

    p_fleet_imp = fleet_sub.add_parser("import", help="Import fleet bundle into local ledger.")
    p_fleet_imp.add_argument("bundle", help="Path to fleet bundle file to import.")
    p_fleet_imp.add_argument("--db", default=".agents/fleet.db", help="Path to fleet database.")
    p_fleet_imp.set_defaults(func=cmd_fleet_import)

    # aos exec
    p_exec = subparsers.add_parser("exec", help="Execute command with autonomous failure autopsy.")
    p_exec.add_argument("--no-autopsy", action="store_true", help="Disable automatic candidate inscription on failure.")
    p_exec.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute.")
    p_exec.set_defaults(func=cmd_exec)

    # aos pack
    p_pack = subparsers.add_parser("pack", help="Manage curated invariant rule packs.")
    pack_sub = p_pack.add_subparsers(dest="pack_command", required=True)

    p_pack_list = pack_sub.add_parser("list", help="List available curated invariant packs.")
    p_pack_list.set_defaults(func=cmd_pack_list)

    p_pack_inst = pack_sub.add_parser("install", help="Install a curated invariant pack.")
    p_pack_inst.add_argument("pack_name", help="Name of the pack (security-owasp, python-clean-architecture).")
    p_pack_inst.add_argument("--candidate", action="store_true", help="Install as candidate rather than active.")
    p_pack_inst.set_defaults(func=cmd_pack_install)

    p_pack_uninst = pack_sub.add_parser("uninstall", help="Uninstall a curated invariant pack.")
    p_pack_uninst.add_argument("pack_name", help="Name of the pack to uninstall.")
    p_pack_uninst.add_argument("--delete", action="store_true", help="Permanently delete rules instead of archiving.")
    p_pack_uninst.set_defaults(func=cmd_pack_uninstall)

    # aos ui
    p_ui = subparsers.add_parser("ui", help="Start local web visualizer dashboard.")
    p_ui.add_argument("--port", type=int, default=8484, help="HTTP port to listen on.")
    p_ui.set_defaults(func=cmd_ui)

    # aos autopsy
    p_autopsy = subparsers.add_parser("autopsy", help="Synthesize and inscribe an invariant rule from failure autopsy.")
    p_autopsy.add_argument("--id", required=True, help="Unique identifier for the new rule.")
    p_autopsy.add_argument("--incident", default="inc-manual", help="Incident or commit identifier.")
    p_autopsy.add_argument("--statement", required=True, help="Invariant directive statement.")
    p_autopsy.add_argument("--rationale", required=True, help="Rationale explaining the invariant.")
    p_autopsy.add_argument("--paths", nargs="+", required=True, help="Target path globs.")
    p_autopsy.add_argument("--languages", nargs="*", default=[], help="Target language identifiers.")
    p_autopsy.add_argument("--agent", default="forensic-auditor", help="Name of inscribing agent.")
    p_autopsy.add_argument("--promote", action="store_true", help="Immediately promote to active status.")
    p_autopsy.set_defaults(func=cmd_autopsy)

    # aos curate
    p_curate = subparsers.add_parser("curate", help="Prune and consolidate rules in the substrate.")
    p_curate.add_argument("--dry-run", action="store_true", help="Inspect without modifying files.")
    p_curate.set_defaults(func=cmd_curate)

    # aos blackboard
    p_bb = subparsers.add_parser("blackboard", help="Inspect and interact with the local blackboard.")
    bb_sub = p_bb.add_subparsers(dest="bb_command", required=True)

    p_bb_list = bb_sub.add_parser("list", help="List blackboard events.")
    p_bb_list.add_argument("--type", default=None, help="Filter by event type.")
    p_bb_list.add_argument("--sender", default=None, help="Filter by sender.")
    p_bb_list.set_defaults(func=cmd_blackboard_list)

    # aos ingest
    p_ingest = subparsers.add_parser("ingest", help="Scan repository conventions and synthesize tailored guardrails.")
    p_ingest.add_argument("--promote", action="store_true", help="Immediately promote synthesized rules to active status.")
    p_ingest.add_argument("--install-packs", action="store_true", help="Automatically install stack-recommended rule packs.")
    p_ingest.add_argument("--dry-run", action="store_true", help="Scan and display proposed rules without saving.")
    p_ingest.set_defaults(func=cmd_ingest)

    # aos identity
    p_ident = subparsers.add_parser("identity", help="Manage autonomous agent identities and supervisory mailboxes.")
    ident_sub = p_ident.add_subparsers(dest="identity_command", required=True)

    p_ident_list = ident_sub.add_parser("list", help="List autonomous agent identities.")
    p_ident_list.set_defaults(func=cmd_identity_list)

    p_ident_create = ident_sub.add_parser("create", help="Create a free programmatic mailbox for an agent persona.")
    p_ident_create.add_argument("--persona", default="maintainer", help="Persona name (maintainer, auditor, curator, sentry, ci).")
    p_ident_create.add_argument("--password", default=None, help="Optional custom password.")
    p_ident_create.set_defaults(func=cmd_identity_create)

    p_ident_inbox = ident_sub.add_parser("inbox", help="View incoming messages for an agent persona.")
    p_ident_inbox.add_argument("persona", help="Persona name or email address.")
    p_ident_inbox.set_defaults(func=cmd_identity_inbox)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

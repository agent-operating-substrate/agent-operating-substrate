"""Comprehensive end-to-end integration tests for developer journeys.

Verifies deterministic developer problem resolution without human babysitting:
1. The 60-Second Onboarding Journey
2. Real-World Secret Leak Interception
3. Real-World SQL Injection Interception
4. Automated Remediation Loop (aos enforce --fix)
5. Multi-Harness Synchronization Invariant
"""

from pathlib import Path
import subprocess
import yaml

from aos.autopsy import inscribe_candidate, promote_candidate, synthesize_candidate_rule
from aos.blackboard import read_events
from aos.cli import main
from aos.engine import RuleEngine
from aos.enforcer import auto_fix_file, enforce_all
from aos.harness import sync_harnesses
from aos.hook import run_pre_commit_check


def test_the_60_second_onboarding_journey(tmp_path: Path) -> None:
    """Test 1: The 60-Second Onboarding Journey.

    Simulate a developer with an existing Python codebase running 'aos init'.
    Verify active guardrails are populated, harness files are generated,
    and the pre-commit hook is installed.
    """
    # 1. Simulate an existing developer repository with git and Python code
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Developer"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "dev@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        "[project]\nname = 'sample-service'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )

    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    app_file = src_dir / "app.py"
    app_file.write_text(
        "def entrypoint() -> str:\n    return 'service ready'\n",
        encoding="utf-8",
    )

    # 2. Run 'aos init'
    exit_code = main(["init", "--root", str(tmp_path)])
    assert exit_code == 0

    # 3. Verify active guardrails are populated
    active_dir = tmp_path / ".agents" / "substrate" / "active"
    assert active_dir.is_dir()
    active_yamls = list(active_dir.glob("*.yaml"))
    assert len(active_yamls) >= 5

    engine = RuleEngine(root_dir=tmp_path)
    active_rules = engine.get_rules(status="active")
    active_rule_ids = {r.id for r in active_rules}

    # Verify key curated rules from python-core, security-core, and general-hygiene
    assert "sec-no-secrets-001" in active_rule_ids
    assert "sec-sql-injection-001" in active_rule_ids
    assert "py-no-wildcard-import-002" in active_rule_ids
    assert "gh-blast-radius-limit-003" in active_rule_ids

    # 4. Verify harness files (.cursorrules, CLAUDE.md) are generated
    cursorrules_file = tmp_path / ".cursorrules"
    claude_file = tmp_path / "CLAUDE.md"

    assert cursorrules_file.is_file()
    assert claude_file.is_file()

    cursor_content = cursorrules_file.read_text(encoding="utf-8")
    assert "<!-- AOS_INVARIANTS_START -->" in cursor_content
    assert "py-no-wildcard-import-002" in cursor_content

    claude_content = claude_file.read_text(encoding="utf-8")
    assert "<!-- AOS_INVARIANTS_START -->" in claude_content
    assert "sec-no-secrets-001" in claude_content

    # 5. Verify pre-commit hook is installed
    hook_file = tmp_path / ".git" / "hooks" / "pre-commit"
    assert hook_file.is_file()
    hook_content = hook_file.read_text(encoding="utf-8")
    assert "aos hook run" in hook_content


def test_real_world_secret_leak_interception(tmp_path: Path) -> None:
    """Test 2: Real-World Secret Leak Interception.

    Simulate an AI agent attempting to commit code with a hardcoded OpenAI
    API key or AWS secret.
    Verify run_pre_commit_check() blocks the commit deterministically.
    Verify the incident is recorded in the blackboard event stream.
    """
    # Initialize repository and substrate
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Agent"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "agent@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    init_code = main(["init", "--root", str(tmp_path)])
    assert init_code == 0

    # 1. AI agent creates a file containing a hardcoded OpenAI API key
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    raw_openai_token = "sk-" + "proj-" + "998877665544332211aabbccddeeff00"
    openai_leak_file = src_dir / "llm_client.py"
    openai_leak_file.write_text(
        f"OPENAI_API_KEY = '{raw_openai_token}'\n"
        "\n"
        "def query_model(prompt: str):\n"
        "    return f'response to {prompt}'\n",
        encoding="utf-8",
    )

    # 2. Stage the file
    subprocess.run(
        ["git", "add", "src/llm_client.py"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    # 3. Verify run_pre_commit_check() blocks the commit deterministically
    exit_code_openai = run_pre_commit_check(root_dir=tmp_path)
    assert exit_code_openai == 1

    # 4. Verify incident is recorded in the blackboard event stream
    events = read_events(root_dir=tmp_path, event_type="PRE_COMMIT_BLOCKED")
    assert len(events) >= 1

    openai_blocked_events = [
        e for e in events if e.payload.get("rule_id") == "sec-no-secrets-001"
    ]
    assert len(openai_blocked_events) >= 1
    last_event = openai_blocked_events[-1]
    assert last_event.payload.get("file_path") == "src/llm_client.py"
    assert "secret" in last_event.payload.get("message", "").lower()

    # 5. Also simulate an AWS secret key leak to verify multi-secret coverage
    subprocess.run(
        ["git", "rm", "--cached", "src/llm_client.py"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    aws_leak_file = src_dir / "s3_storage.py"
    s3_val = "".join(["wJalrXUtnFEMI/K7MDENG/", "bPxRfiCYEXAMPLEKEY"])
    aws_leak_file.write_text(
        "aws_" + f"secret = '{s3_val}'\n"
        "\n"
        "def upload_payload():\n"
        "    pass\n",
        encoding="utf-8",
    )
    subprocess.run(
        ["git", "add", "src/s3_storage.py"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    exit_code_aws = run_pre_commit_check(root_dir=tmp_path)
    assert exit_code_aws == 1

    events_after_aws = read_events(root_dir=tmp_path, event_type="PRE_COMMIT_BLOCKED")
    aws_events = [
        e for e in events_after_aws if e.payload.get("file_path") == "src/s3_storage.py"
    ]
    assert len(aws_events) >= 1
    assert any(e.payload.get("rule_id") == "sec-no-secrets-001" for e in aws_events)


def test_real_world_sql_injection_interception(tmp_path: Path, capsys) -> None:
    """Test 3: Real-World SQL Injection Interception.

    Simulate an AI agent generating unparameterized raw SQL string interpolation.
    Verify pre-commit rejects the commit with an actionable violation message.
    """
    # Initialize repository and substrate
    subprocess.run(["git", "init"], cwd=str(tmp_path), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.name", "Agent"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "agent@example.com"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    init_code = main(["init", "--root", str(tmp_path)])
    assert init_code == 0

    # 1. AI agent generates unparameterized raw SQL string interpolation
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    dao_file = src_dir / "user_dao.py"
    dao_file.write_text(
        "def get_user_by_id(cursor, user_id: int):\n"
        "    cursor.execute(f\"SELECT * FROM users WHERE id = {user_id}\")\n"
        "    return cursor.fetchone()\n",
        encoding="utf-8",
    )

    # 2. Stage file for commit
    subprocess.run(
        ["git", "add", "src/user_dao.py"],
        cwd=str(tmp_path),
        capture_output=True,
        check=True,
    )

    # 3. Run pre-commit and verify rejection with actionable violation message
    exit_code = run_pre_commit_check(root_dir=tmp_path)
    assert exit_code == 1

    captured = capsys.readouterr()
    assert "AOS COMMIT REJECTED" in captured.err
    assert "sec-sql-injection-001" in captured.err
    assert "SQL query uses unparameterized string formatting" in captured.err
    assert "src/user_dao.py:2" in captured.err

    # 4. Verify violation details directly through enforcer model
    violations = enforce_all(["src/user_dao.py"], root_dir=tmp_path)
    sqli_violations = [v for v in violations if v.rule_id == "sec-sql-injection-001"]
    assert len(sqli_violations) == 1
    sqli_violation = sqli_violations[0]
    assert sqli_violation.enforcement == "reject_diff"
    assert sqli_violation.line_number == 2
    assert "SQL query uses unparameterized string formatting" in sqli_violation.message


def test_automated_remediation_loop(tmp_path: Path) -> None:
    """Test 4: Automated Remediation Loop (aos enforce --fix).

    Simulate a file with wildcard imports ('from math import *') and raw print calls.
    Run auto_fix_file().
    Verify that wildcard import is converted to explicit import and print
    is converted to structured logging.
    """
    # Initialize substrate on a Python project repository
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.write_text(
        "[project]\nname = 'calc-service'\nversion = '0.1.0'\n",
        encoding="utf-8",
    )
    init_code = main(["init", "--root", str(tmp_path)])
    assert init_code == 0

    # 1. Create file with wildcard import and raw print call in src/
    src_dir = tmp_path / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    calc_file = src_dir / "calculator.py"
    initial_code = (
        "from math import *\n"
        "\n"
        "def compute_hypotenuse(a: float, b: float) -> float:\n"
        "    c = sqrt(a**2 + b**2)\n"
        "    print(f'Calculated hypotenuse: {c}')\n"
        "    return c\n"
    )
    calc_file.write_text(initial_code, encoding="utf-8")

    # 2. Verify violations exist prior to fix
    initial_violations = enforce_all(["src/calculator.py"], root_dir=tmp_path)
    initial_rule_ids = {v.rule_id for v in initial_violations}
    assert "py-no-wildcard-import-002" in initial_rule_ids
    assert "py-structured-logging-001" in initial_rule_ids

    # 3. Run auto_fix_file()
    applied_fixes = auto_fix_file(calc_file, root_dir=tmp_path)
    assert len(applied_fixes) >= 2

    # 4. Verify file content transformations
    remediated_code = calc_file.read_text(encoding="utf-8")

    # Wildcard import must be replaced by explicit module import
    assert "from math import *" not in remediated_code
    assert "import math" in remediated_code

    # Print call must be replaced by structured logging
    assert "print(" not in remediated_code
    assert "logging.getLogger(__name__).info(" in remediated_code

    # 5. Verify invariant enforcement passes clean for remediated rules
    recheck_violations = enforce_all(["src/calculator.py"], root_dir=tmp_path)
    recheck_ids = {v.rule_id for v in recheck_violations}
    assert "py-no-wildcard-import-002" not in recheck_ids
    assert "py-structured-logging-001" not in recheck_ids


def test_multi_harness_synchronization_invariant(tmp_path: Path) -> None:
    """Test 5: Multi-Harness Synchronization Invariant.

    Inscribe a new invariant rule into active substrate.
    Run sync_harnesses().
    Verify that Gemini, Claude, Codex, Copilot, Cursor, Windsurf, Aider,
    and Cline configurations all receive the updated invariant simultaneously.
    """
    # Initialize substrate
    init_code = main(["init", "--root", str(tmp_path)])
    assert init_code == 0

    # 1. Inscribe a new invariant rule into active substrate
    rule_id = "arch-no-global-state-005"
    statement = "Global mutable singletons and module variables are strictly prohibited."
    rationale = "Prevents concurrency race conditions and cross-test state leakage."

    new_rule = synthesize_candidate_rule(
        rule_id=rule_id,
        statement=statement,
        rationale=rationale,
        paths=["src/**/*.py"],
        languages=["python"],
        inscribing_agent="forensic-architect",
        enforcement="reject_diff",
    )
    inscribe_candidate(
        new_rule,
        substrate_dir=tmp_path / ".agents" / "substrate",
        event_log_path=tmp_path / ".agents" / "blackboard" / "events.jsonl",
    )
    promoted_file = promote_candidate(
        rule_id=rule_id,
        peer_agent="supervisory-curator",
        substrate_dir=tmp_path / ".agents" / "substrate",
        event_log_path=tmp_path / ".agents" / "blackboard" / "events.jsonl",
    )
    assert promoted_file is not None
    assert promoted_file.is_file()

    # 2. Run sync_harnesses()
    synced = sync_harnesses(root_dir=tmp_path)
    assert len(synced) >= 8

    # 3. Target mapping for all required agent harnesses
    expected_harnesses = {
        "Gemini": tmp_path / "GEMINI.md",
        "Claude": tmp_path / "CLAUDE.md",
        "Codex": tmp_path / "CODEX.md",
        "Copilot": tmp_path / ".github" / "copilot-instructions.md",
        "Cursor": tmp_path / ".cursorrules",
        "Windsurf": tmp_path / ".windsurfrules",
        "Aider": tmp_path / "CONVENTIONS.md",
        "Cline": tmp_path / ".clinerules",
    }

    # 4. Verify all harness configurations received the updated invariant simultaneously
    for harness_name, harness_path in expected_harnesses.items():
        assert harness_path.is_file(), f"Expected harness file missing: {harness_path} for {harness_name}"
        content = harness_path.read_text(encoding="utf-8")
        assert "<!-- AOS_INVARIANTS_START -->" in content, f"Missing start marker in {harness_name}"
        assert "<!-- AOS_INVARIANTS_END -->" in content, f"Missing end marker in {harness_name}"
        assert rule_id in content, f"Rule ID '{rule_id}' missing in {harness_name} config"
        assert statement in content, f"Statement missing in {harness_name} config"

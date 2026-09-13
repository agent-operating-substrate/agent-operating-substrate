"""Tests for the AOS AI Guardrail and Behavior Control Plane UI."""

from __future__ import annotations
import json
import threading
from http.server import HTTPServer
from pathlib import Path
from typing import Generator
import re
import subprocess
import urllib.request
import pytest
import yaml

from aos.blackboard import post_event
from aos.ui import DASHBOARD_HTML, DashboardRequestHandler

try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False


@pytest.fixture
def test_env(tmp_path: Path) -> Path:
    """Create isolated substrate environment for UI testing."""
    substrate_dir = tmp_path / ".agents" / "substrate"
    (substrate_dir / "active").mkdir(parents=True, exist_ok=True)
    (substrate_dir / "candidate").mkdir(parents=True, exist_ok=True)
    (substrate_dir / "archive").mkdir(parents=True, exist_ok=True)

    # Seed an active rule
    seed_rule = {
        "id": "ui-test-rule-01",
        "version": 1,
        "status": "active",
        "scope": {
            "paths": ["src/**/*.py"],
            "languages": ["python"],
        },
        "invariant": {
            "statement": "Do not hardcode secrets or api keys.",
            "rationale": "Security compliance constraint.",
            "enforcement": "reject_diff",
            "max_blast_radius_lines": 25,
        },
        "provenance": {
            "incident_id": "inc-ui-001",
            "git_commit": "HEAD",
            "inscribing_agent": "security-sentry",
            "created_at": "2026-09-08T19:00:00Z",
            "last_verified_at": "2026-09-08T19:00:00Z",
            "trigger_count": 2,
        },
    }
    with open(substrate_dir / "active" / "ui-test-rule-01.yaml", "w", encoding="utf-8") as f:
        yaml.safe_dump(seed_rule, f, sort_keys=False)

    # Seed an incident event on blackboard
    post_event(
        {
            "type": "AUTOPSY_RECORD",
            "sender": "forensic-auditor",
            "payload": {
                "incident_id": "inc-autopsy-101",
                "rule_id": "ui-test-rule-01",
                "statement": "Do not hardcode secrets or api keys.",
            },
        },
        root_dir=tmp_path,
    )
    post_event(
        {
            "type": "PEER_CRITIQUE",
            "sender": "auditor-agent",
            "payload": {
                "verdict": "REJECT_DIFF",
                "message": "Hardcoded secret detected in auth module.",
            },
        },
        root_dir=tmp_path,
    )

    # Seed a harness file
    cursor_file = tmp_path / ".cursorrules"
    cursor_file.write_text("# Cursor rules placeholder", encoding="utf-8")

    return tmp_path


@pytest.fixture
def test_server(test_env: Path) -> Generator[str, None, None]:
    """Spin up local test HTTP server on ephemeral port."""
    DashboardRequestHandler.root_dir = test_env
    server = HTTPServer(("127.0.0.1", 0), DashboardRequestHandler)
    port = server.server_port
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()

    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.shutdown()
    server.server_close()


def http_get(url: str) -> tuple[int, dict | list | str]:
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req) as resp:
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read().decode("utf-8")
            if "application/json" in content_type:
                return resp.status, json.loads(raw)
            return resp.status, raw
    except urllib.error.HTTPError as exc:
        content_type = exc.headers.get("Content-Type", "")
        raw = exc.read().decode("utf-8")
        if "application/json" in content_type:
            try:
                return exc.code, json.loads(raw)
            except Exception:
                pass
        return exc.code, raw


def http_post(url: str, payload: dict) -> tuple[int, dict]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        return exc.code, json.loads(raw)


def test_ui_serves_html_dashboard(test_server: str):
    status, html = http_get(f"{test_server}/")
    assert status == 200
    assert "AI Behavior Control Plane" in html
    assert "Real-time guardrails and permanent memory for Cursor, Copilot, and Claude Code" in html
    assert "tab-rules" in html
    assert "tab-tools" in html
    assert "tab-incidents" in html
    assert "tab-inspector" in html


def test_api_overview(test_server: str):
    status, data = http_get(f"{test_server}/api/overview")
    assert status == 200
    assert isinstance(data, dict)
    assert data["active_rules"] == 1
    assert data["total_rules"] == 1
    assert data["connected_harnesses"] >= 1
    assert data["total_blocked_incidents"] == 2


def test_api_rules_list(test_server: str):
    status, data = http_get(f"{test_server}/api/rules")
    assert status == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "ui-test-rule-01"
    assert data[0]["status"] == "active"
    assert data[0]["invariant"]["enforcement"] == "reject_diff"


def test_api_rules_create_and_validation(test_server: str, test_env: Path):
    # Valid rule creation
    new_rule = {
        "id": "ui-no-eval",
        "statement": "Never invoke eval() on untrusted strings.",
        "rationale": "Prevents remote code execution vulnerabilities.",
        "paths": "src/**/*.py, tests/**/*.py",
        "languages": "python",
        "enforcement": "BLOCK",
    }
    status, data = http_post(f"{test_server}/api/rules/create", new_rule)
    assert status == 201
    assert data["success"] is True
    assert data["rule"]["id"] == "ui-no-eval"
    assert data["rule"]["invariant"]["enforcement"] == "reject_diff"

    # Verify written to .agents/substrate/active/
    created_file = test_env / ".agents" / "substrate" / "active" / "ui-no-eval.yaml"
    assert created_file.is_file()

    # Invalid rule creation (missing id)
    bad_rule = {
        "id": "",
        "statement": "Missing ID",
    }
    status_bad, data_bad = http_post(f"{test_server}/api/rules/create", bad_rule)
    assert status_bad == 400
    assert "error" in data_bad


def test_api_rules_toggle(test_server: str, test_env: Path):
    sub = test_env / ".agents" / "substrate"

    # Toggle ui-test-rule-01 from active to archive
    status, data = http_post(f"{test_server}/api/rules/toggle", {"rule_id": "ui-test-rule-01"})
    assert status == 200
    assert data["success"] is True
    assert data["new_status"] == "archive"
    assert data["previous_status"] == "active"

    # Verify moved on disk
    assert not (sub / "active" / "ui-test-rule-01.yaml").exists()
    assert (sub / "archive" / "ui-test-rule-01.yaml").is_file()

    # Toggle back from archive to active
    status2, data2 = http_post(f"{test_server}/api/rules/toggle", {"rule_id": "ui-test-rule-01"})
    assert status2 == 200
    assert data2["new_status"] == "active"
    assert data2["previous_status"] == "archive"
    assert (sub / "active" / "ui-test-rule-01.yaml").is_file()
    assert not (sub / "archive" / "ui-test-rule-01.yaml").exists()


def test_api_harnesses(test_server: str):
    status, data = http_get(f"{test_server}/api/harnesses")
    assert status == 200
    assert isinstance(data, dict)
    assert ".cursorrules" in data
    assert data[".cursorrules"]["exists"] is True
    assert ".windsurfrules" in data
    assert ".github/copilot-instructions.md" in data
    assert ".git/hooks/pre-commit" in data
    assert len(data["harnesses"]) == 5


def test_api_harnesses_sync(test_server: str, test_env: Path):
    status, data = http_post(f"{test_server}/api/harnesses/sync", {})
    assert status == 200
    assert data["success"] is True
    assert len(data["synced"]) > 0

    # Verify .cursorrules was populated with invariants
    cursor_file = test_env / ".cursorrules"
    assert cursor_file.is_file()
    content = cursor_file.read_text(encoding="utf-8")
    assert "AOS_INVARIANTS_START" in content


def test_api_check_file(test_server: str):
    # Match matching file
    status, data = http_post(f"{test_server}/api/check", {"file_path": "src/module.py"})
    assert status == 200
    assert data["count"] == 1
    assert data["matches"][0]["id"] == "ui-test-rule-01"

    # Match non-matching file
    status2, data2 = http_post(f"{test_server}/api/check", {"file_path": "docs/readme.txt"})
    assert status2 == 200
    assert data2["count"] == 0


def test_api_incidents(test_server: str):
    status, data = http_get(f"{test_server}/api/incidents")
    assert status == 200
    assert isinstance(data, list)
    assert len(data) == 2
    types = [ev["type"] for ev in data]
    assert "AUTOPSY_RECORD" in types
    assert "PEER_CRITIQUE" in types


def test_zero_em_dashes_in_ui_and_tests():
    ui_code = Path("src/aos/ui.py").read_text(encoding="utf-8")
    test_code = Path("tests/test_ui.py").read_text(encoding="utf-8")
    assert "\u2014" not in ui_code, "Em dash found in src/aos/ui.py"
    assert "\u2013" not in ui_code, "En dash found in src/aos/ui.py"
    assert "\u2014" not in test_code, "Em dash found in tests/test_ui.py"
    assert "\u2013" not in test_code, "En dash found in tests/test_ui.py"


def test_ui_frontend_enhancements(test_server: str):
    status, html = http_get(f"{test_server}/")
    assert status == 200

    # 1. Toast Notification System
    assert "toast-container" in html
    assert "toast-success" in html
    assert "toast-error" in html
    assert "alert(" not in html

    # 2. Tab Badge Counters
    assert "tab-badge-rules" in html
    assert "tab-badge-tools" in html
    assert "tab-badge-incidents" in html
    assert "Active Guardrails" in html

    # 3. Keyboard Shortcuts
    assert "keydown" in html
    assert "Escape" in html

    # 4. Modal Polish
    assert "modal-error" in html
    assert "modal-backdrop" in html
    assert "modal-close-btn" in html

    # 5. Invariant Rule Details
    assert "toggleRuleExpand" in html
    assert "Inscribing Agent" in html
    assert "Git Commit Origin" in html
    assert "Trigger Count" in html
    assert "Last Verified" in html

    # 6. Performance Debouncing
    assert "debounce" in html
    assert "200" in html


def test_api_check_content(test_server: str):
    # 1. Valid python code complying with active rules
    valid_code = "def calculate_total(a: int, b: int) -> int:\n    return a + b\n"
    status, data = http_post(
        f"{test_server}/api/check-content",
        {"file_path": "src/calculator.py", "content": valid_code},
    )
    assert status == 200
    assert data["allowed"] is True
    assert data["violations"] == []
    assert data["matching_rules_count"] == 1

    # 2. Secret leak violation on ui-test-rule-01
    secret_code = 'api_key = "secret_key_1234567890"\n'
    status, data = http_post(
        f"{test_server}/api/check-content",
        {"file_path": "src/auth.py", "content": secret_code},
    )
    assert status == 200
    assert data["allowed"] is False
    assert len(data["violations"]) >= 1
    assert data["violations"][0]["rule_id"] == "ui-test-rule-01"

    # 3. Blast radius line limit violation (limit is 25)
    long_code = "\n".join([f"line_{i} = {i}" for i in range(30)])
    status, data = http_post(
        f"{test_server}/api/check-content",
        {"file_path": "src/large.py", "content": long_code},
    )
    assert status == 200
    assert data["allowed"] is False
    assert any("blast radius" in v["message"].lower() for v in data["violations"])

    # 4. Em-dash invariant violation after adding zero em-dash rule
    dash_rule = {
        "id": "ui-no-em-dash",
        "statement": "Zero em dashes in all comments and code.",
        "rationale": "Enforce clean punctuation.",
        "paths": "**/*",
        "enforcement": "reject_diff",
    }
    http_post(f"{test_server}/api/rules/create", dash_rule)

    em_dash_char = chr(8212)
    bad_code = f"# Bad comment containing em dash: {em_dash_char} invalid\ndef run(): pass\n"
    status, data = http_post(
        f"{test_server}/api/check-content",
        {"file_path": "src/sample.py", "content": bad_code},
    )
    assert status == 200
    assert data["allowed"] is False
    assert any(v["rule_id"] == "ui-no-em-dash" for v in data["violations"])


def test_api_packs_list_and_install(test_server: str):
    # List packs
    status, data = http_get(f"{test_server}/api/packs")
    assert status == 200
    assert isinstance(data, list)
    assert len(data) >= 3
    pack_names = [p["name"] for p in data]
    assert "security-core" in pack_names
    assert "python-core" in pack_names
    assert "general-hygiene" in pack_names

    # Install security pack
    status, resp = http_post(
        f"{test_server}/api/packs/install",
        {"pack_name": "security-core"},
    )
    assert status == 200
    assert resp["success"] is True
    assert resp["installed_count"] >= 2

    # Verify newly installed rules appear in active rules list
    status, rules = http_get(f"{test_server}/api/rules")
    assert status == 200
    rule_ids = [r["id"] for r in rules]
    assert "sec-sql-injection-001" in rule_ids
    assert "sec-no-secrets-001" in rule_ids

    # Bad pack install
    status_bad, resp_bad = http_post(
        f"{test_server}/api/packs/install",
        {"pack_name": "unknown-pack"},
    )
    assert status_bad == 400
    assert "error" in resp_bad

    # Uninstall pack
    status_uninst, resp_uninst = http_post(
        f"{test_server}/api/packs/uninstall",
        {"pack_name": "security-core"},
    )
    assert status_uninst == 200
    assert resp_uninst["success"] is True
    assert resp_uninst["uninstalled_count"] >= 2

    status, rules_after = http_get(f"{test_server}/api/rules?status=active")
    assert status == 200
    active_ids_after = [r["id"] for r in rules_after]
    assert "sec-sql-injection-001" not in active_ids_after


def test_api_harnesses_view(test_server: str):
    # Cursor view
    status, data = http_get(f"{test_server}/api/harnesses/view?id=cursor")
    assert status == 200
    assert data["id"] == "cursor"
    assert data["path"] == ".cursorrules"
    assert "content" in data

    # Claude view
    status, data = http_get(f"{test_server}/api/harnesses/view?id=claude")
    assert status == 200
    assert data["path"] == "CLAUDE.md"

    # Unknown harness
    status_bad, data_bad = http_get(f"{test_server}/api/harnesses/view?id=unknown-tool")
    assert status_bad == 404
    assert "error" in data_bad


def test_api_rules_get_yaml(test_server: str):
    # Valid rule YAML lookup
    status, data = http_get(f"{test_server}/api/rules/ui-test-rule-01/yaml")
    assert status == 200
    assert data["rule_id"] == "ui-test-rule-01"
    assert "id: ui-test-rule-01" in data["yaml"]

    # Nonexistent rule
    status_bad, data_bad = http_get(f"{test_server}/api/rules/nonexistent-rule/yaml")
    assert status_bad == 404
    assert "error" in data_bad


def test_ui_frontend_new_features(test_server: str):
    status, html = http_get(f"{test_server}/")
    assert status == 200

    # Live Code and Diff Tester
    assert "Live Guardrail" in html
    assert "runContentTester" in html
    assert "setTesterSample" in html

    # 1-Click Guardrail Templates
    assert "OWASP SQL Injection" in html
    assert "Zero Em-Dashes" in html
    assert "No Hardcoded Secrets" in html
    assert "Surgical Diff (30 Lines)" in html
    assert "applyGuardrailTemplate" in html

    # Modals
    assert "yaml-modal" in html
    assert "harness-modal" in html
    assert "how-modal" in html

    # Rule Packs Tab
    assert "tab-packs" in html
    assert "tab-btn-packs" in html
    assert "loadPacks" in html


def test_javascript_syntax_and_compilation():
    """Verify all embedded JavaScript compiles with zero syntax errors via Node.js."""
    scripts = re.findall(r"<script>(.*?)</script>", DASHBOARD_HTML, re.DOTALL)
    assert len(scripts) >= 1, "At least one script block must exist in DASHBOARD_HTML"
    for i, script in enumerate(scripts):
        proc = subprocess.run(
            ["node", "--check"],
            input=script,
            encoding="utf-8",
            capture_output=True,
        )
        assert proc.returncode == 0, f"JavaScript syntax error in script {i}: {proc.stderr}"


def test_dom_id_referential_integrity():
    """Verify every element ID accessed in JavaScript exists in the HTML body."""
    scripts = re.findall(r"<script>(.*?)</script>", DASHBOARD_HTML, re.DOTALL)
    assert len(scripts) >= 1
    js = scripts[0]
    ids_used = set(re.findall(r"document\.getElementById\(['\"]([a-zA-Z0-9_-]+)['\"]\)", js))
    ids_in_html = set(re.findall(r"id=['\"]([a-zA-Z0-9_-]+)['\"]", DASHBOARD_HTML))
    dynamic_prefixes = ("rule-card-", "rule-details-", "expand-cue-")
    missing = [
        i for i in ids_used
        if i not in ids_in_html and not any(i.startswith(p) for p in dynamic_prefixes)
    ]
    assert not missing, f"JavaScript references missing DOM IDs in HTML: {missing}"


def test_playwright_e2e_rendering_and_tabs(test_server: str):
    """Verify headless Chromium browser boots UI with zero console errors and switches tabs."""
    if not HAS_PLAYWRIGHT:
        pytest.skip("Playwright is not installed in this environment.")

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda err: errors.append(f"PAGE: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE: {msg.text}") if msg.type == "error" else None)

        page.goto(test_server)
        page.wait_for_selector(".rule-card")
        cards = page.query_selector_all(".rule-card")
        assert len(cards) >= 1

        for tab_id in ("#tab-btn-tools", "#tab-btn-packs", "#tab-btn-incidents", "#tab-btn-rules"):
            page.click(tab_id)
            page.wait_for_timeout(50)

        browser.close()

    assert not errors, f"Browser encountered errors: {errors}"


def test_playwright_e2e_interactive_flows(test_server: str):
    """Verify live interactive tester blocks em dashes, allows valid code, and template pre-fills."""
    if not HAS_PLAYWRIGHT:
        pytest.skip("Playwright is not installed in this environment.")

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda err: errors.append(f"PAGE: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE: {msg.text}") if msg.type == "error" else None)

        page.goto(test_server)

        # 1. Create a zero em-dash rule via the template UI
        page.locator("button", has_text="+ Add Guardrail").click()
        page.wait_for_selector("#add-modal.open")
        page.locator("button", has_text="Zero Em-Dashes").click()
        assert page.input_value("#form-id") == "no-em-dashes"
        page.locator("button", has_text="Save Guardrail").click()
        page.wait_for_selector(".toast-success")

        # 2. Test live code tester in inspector tab
        page.click("#tab-btn-inspector")
        page.locator("button", has_text="Test Em-Dash Violation").click()
        page.locator("#tester-verdict", has_text="BLOCKED").wait_for()

        page.locator("button", has_text="Test Valid Python Code").click()
        page.locator("#tester-verdict", has_text="ALLOWED").wait_for()

        browser.close()

    assert not errors, f"Browser encountered errors: {errors}"


def test_api_ingest_endpoints(test_server: str):
    # Scan endpoint
    status, data = http_get(f"{test_server}/api/ingest/scan")
    assert status == 200
    assert "detected_languages" in data
    assert "synthesized_rules" in data

    # Apply endpoint
    status_app, resp_app = http_post(f"{test_server}/api/ingest/apply", {"promote": True})
    assert status_app == 200
    assert resp_app["success"] is True


def test_playwright_e2e_ingest_modal(test_server: str):
    """Verify autonomous codebase scan modal opens and renders detected tech stack."""
    if not HAS_PLAYWRIGHT:
        pytest.skip("Playwright is not installed in this environment.")

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.on("pageerror", lambda err: errors.append(f"PAGE: {err}"))
        page.on("console", lambda msg: errors.append(f"CONSOLE: {msg.text}") if msg.type == "error" else None)

        page.goto(test_server)
        page.locator("button", has_text="Scan Codebase").click()
        page.wait_for_selector("#ingest-modal.open")
        page.locator("#ingest-modal", has_text="Autonomous Codebase Ingestion").wait_for()
        page.locator("#ingest-modal", has_text="Tech Stack").wait_for()
        page.locator("#ingest-modal button", has_text="Close").click()

        browser.close()

    assert not errors, f"Browser encountered errors: {errors}"


def test_api_fix_content(test_server: str):
    http_post(f"{test_server}/api/packs/install", {"pack_name": "python-core"})
    payload = {
        "file_path": "src/sample.py",
        "content": "from os import *\n\ndef main():\n    print('Running task')\n",
    }
    status, data = http_post(f"{test_server}/api/fix-content", payload)
    assert status == 200
    assert "fixed_content" in data
    assert "from os import *" not in data["fixed_content"]
    assert "import os" in data["fixed_content"]




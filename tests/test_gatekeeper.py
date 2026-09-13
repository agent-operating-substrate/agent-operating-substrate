"""Tests verifying GitHub Action PR Gatekeeper and sticky comment reporting."""

from __future__ import annotations
import io
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

from aos.ci import (
    AOS_GATEKEEPER_MARKER,
    CIReport,
    format_gatekeeper_comment,
    generate_gatekeeper_markdown,
    post_pr_comment,
    run_gatekeeper,
)
from aos.enforcer import Violation


def test_markdown_generation_passed():
    report = CIReport(
        checked_files=["src/aos/engine.py", "src/aos/ci.py"],
        violations=[],
        status="passed",
    )
    md = generate_gatekeeper_markdown(report)

    assert AOS_GATEKEEPER_MARKER in md
    assert "## 🛡️ AOS Guardrails Gatekeeper: Passed" in md
    assert "Passed" in md
    assert "Files Evaluated" in md
    assert "2" in md
    assert "Violations Detected" in md
    assert "0" in md
    assert "https://img.shields.io/badge/AOS_Gatekeeper-Passed-brightgreen" in md
    assert "\u2014" not in md

    # Method alias test
    assert report.to_gatekeeper_markdown() == md
    assert format_gatekeeper_comment(report) == md


def test_markdown_generation_failed():
    violations = [
        Violation(
            file_path="src/service.py",
            rule_id="py-clean-001",
            message="Wildcard imports are prohibited.",
            enforcement="reject_diff",
            line_number=5,
            statement="Wildcard imports are prohibited.",
        ),
        Violation(
            file_path="src/punct.md",
            rule_id="aos-punct-001",
            message="Punctuation violation: em dash detected.",
            enforcement="reject_diff",
            line_number=12,
            statement="Zero em dashes in all prose.",
        ),
    ]
    report = CIReport(
        checked_files=["src/service.py", "src/punct.md"],
        violations=violations,
        status="failed",
    )
    md = generate_gatekeeper_markdown(report)

    assert AOS_GATEKEEPER_MARKER in md
    assert "## 🛡️ AOS Guardrails Gatekeeper: Invariant Violations Detected" in md
    assert "The Gatekeeper detected 2 invariant violation(s)" in md
    assert "| Severity | Rule ID | File | Line | Message | Remediation Guidance |" in md
    assert "`py-clean-001`" in md
    assert "`src/service.py`" in md
    assert "`aos-punct-001`" in md
    assert "`src/punct.md`" in md
    assert "Run `aos enforce --fix <file>` locally" in md
    assert "https://img.shields.io/badge/AOS_Gatekeeper-Failed-red" in md
    assert "\u2014" not in md


def test_post_pr_comment_create_new():
    report = CIReport(
        checked_files=["src/sample.py"],
        violations=[],
        status="passed",
    )

    recorded_requests = []

    def fake_urlopen(req, *args, **kwargs):
        recorded_requests.append(req)
        method = req.get_method()
        if method == "GET":
            # Return existing comments list with no gatekeeper marker
            resp_bytes = json.dumps([
                {"id": 101, "body": "Welcome to the repository!"}
            ]).encode("utf-8")
            resp = io.BytesIO(resp_bytes)
            resp.status = 200
            return resp
        elif method == "POST":
            resp_bytes = json.dumps({"id": 202, "body": "created"}).encode("utf-8")
            resp = io.BytesIO(resp_bytes)
            resp.status = 201
            return resp
        raise ValueError(f"Unexpected method: {method}")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        success = post_pr_comment(
            report=report,
            pr_number=42,
            token="test-auth-token",
            repo="org/repo",
            api_url="https://api.github.com",
        )

    assert success is True
    assert len(recorded_requests) == 2
    get_req, post_req = recorded_requests

    assert get_req.get_method() == "GET"
    assert "/repos/org/repo/issues/42/comments" in get_req.full_url

    assert post_req.get_method() == "POST"
    assert "/repos/org/repo/issues/42/comments" in post_req.full_url
    post_payload = json.loads(post_req.data.decode("utf-8"))
    assert AOS_GATEKEEPER_MARKER in post_payload["body"]


def test_post_pr_comment_update_sticky():
    report = CIReport(
        checked_files=["src/sample.py"],
        violations=[],
        status="passed",
    )

    recorded_requests = []

    def fake_urlopen(req, *args, **kwargs):
        recorded_requests.append(req)
        method = req.get_method()
        if method == "GET":
            resp_bytes = json.dumps([
                {"id": 101, "body": "Welcome!"},
                {"id": 999, "body": f"{AOS_GATEKEEPER_MARKER}\n## Old comment"},
            ]).encode("utf-8")
            resp = io.BytesIO(resp_bytes)
            resp.status = 200
            return resp
        elif method == "PATCH":
            resp_bytes = json.dumps({"id": 999, "body": "updated"}).encode("utf-8")
            resp = io.BytesIO(resp_bytes)
            resp.status = 200
            return resp
        raise ValueError(f"Unexpected method: {method}")

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        success = post_pr_comment(
            report=report,
            pr_number=42,
            token="test-auth-token",
            repo="org/repo",
            api_url="https://api.github.com",
        )

    assert success is True
    assert len(recorded_requests) == 2
    get_req, patch_req = recorded_requests

    assert get_req.get_method() == "GET"
    assert patch_req.get_method() == "PATCH"
    assert "/repos/org/repo/issues/comments/999" in patch_req.full_url
    patch_payload = json.loads(patch_req.data.decode("utf-8"))
    assert AOS_GATEKEEPER_MARKER in patch_payload["body"]


def test_post_pr_comment_infer_pr_number(tmp_path: Path, monkeypatch):
    event_file = tmp_path / "event.json"
    event_file.write_text(json.dumps({"pull_request": {"number": 789}}), encoding="utf-8")

    monkeypatch.setenv("GITHUB_TOKEN", "test-auth-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "acme/substrate")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_file))

    report = CIReport(checked_files=[], violations=[], status="passed")

    recorded_urls = []

    def fake_urlopen(req, *args, **kwargs):
        recorded_urls.append(req.full_url)
        resp_bytes = json.dumps([]).encode("utf-8")
        resp = io.BytesIO(resp_bytes)
        resp.status = 200
        return resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        success = post_pr_comment(report)

    assert success is True
    assert any("/repos/acme/substrate/issues/789/comments" in u for u in recorded_urls)


def test_post_pr_comment_missing_credentials():
    report = CIReport(checked_files=[], violations=[], status="passed")
    # No token or repo
    assert post_pr_comment(report, token=None, repo=None) is False
    # Token present but no repo or pr_number
    assert post_pr_comment(report, token="test-auth-token", repo=None) is False
    # Token and repo present but no pr_number
    assert post_pr_comment(report, token="test-auth-token", repo="org/repo", pr_number=None) is False


def test_post_pr_comment_http_error():
    report = CIReport(checked_files=[], violations=[], status="passed")

    def failing_urlopen(*args, **kwargs):
        raise urllib.error.HTTPError(
            url="https://api.github.com",
            code=403,
            msg="Forbidden",
            hdrs={},
            fp=None,
        )

    with patch("urllib.request.urlopen", side_effect=failing_urlopen):
        success = post_pr_comment(
            report=report,
            pr_number=50,
            token="test-auth-token",
            repo="org/repo",
        )
    assert success is False


def test_run_gatekeeper_flow():
    passed_report = CIReport(checked_files=["a.py"], violations=[], status="passed")
    failed_report = CIReport(
        checked_files=["b.py"],
        violations=[
            Violation(
                file_path="b.py",
                rule_id="aos-punct-001",
                message="Em dash error",
                enforcement="reject_diff",
            )
        ],
        status="failed",
    )

    # 1. Passed run
    with patch("aos.ci.run_ci_check", return_value=passed_report) as mock_check, \
         patch("aos.ci.post_pr_comment", return_value=True) as mock_comment:
        exit_code = run_gatekeeper(base_ref="main", post_comment=True, fail_on_violation=True)
        assert exit_code == 0
        mock_check.assert_called_once()
        mock_comment.assert_called_once()

    # 2. Failed run with fail_on_violation=True
    with patch("aos.ci.run_ci_check", return_value=failed_report), \
         patch("aos.ci.post_pr_comment", return_value=True) as mock_comment:
        exit_code = run_gatekeeper(base_ref="main", post_comment=True, fail_on_violation=True)
        assert exit_code == 1
        mock_comment.assert_called_once()

    # 3. Failed run with fail_on_violation=False
    with patch("aos.ci.run_ci_check", return_value=failed_report), \
         patch("aos.ci.post_pr_comment", return_value=True):
        exit_code = run_gatekeeper(base_ref="main", post_comment=True, fail_on_violation=False)
        assert exit_code == 0

    # 4. Post comment disabled
    with patch("aos.ci.run_ci_check", return_value=passed_report), \
         patch("aos.ci.post_pr_comment") as mock_comment:
        exit_code = run_gatekeeper(post_comment=False)
        assert exit_code == 0
        mock_comment.assert_not_called()


def test_cli_ci_run_options(monkeypatch):
    from aos.cli import main

    mock_report = CIReport(checked_files=["file1.py"], violations=[], status="passed")

    with patch("aos.cli.run_ci_check", return_value=mock_report) as mock_check, \
         patch("aos.cli.post_pr_comment", return_value=True) as mock_comment:
        ret = main(["ci", "run", "--comment", "--pr-number", "101"])
        assert ret == 0
        mock_check.assert_called_once()
        mock_comment.assert_called_once_with(mock_report, pr_number=101, root_dir=".")

    # With GITHUB_ACTIONS and GITHUB_EVENT_NAME=pull_request
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "pull_request")

    with patch("aos.cli.run_ci_check", return_value=mock_report), \
         patch("aos.cli.post_pr_comment", return_value=True) as mock_comment:
        ret = main(["ci", "run"])
        assert ret == 0
        mock_comment.assert_called_once_with(mock_report, pr_number=None, root_dir=".")

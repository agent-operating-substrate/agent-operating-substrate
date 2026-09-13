"""Tests verifying invariant rule schema validation logic."""

import pytest
from aos.validator import validate_rule_dict


def sample_valid_rule():
    return {
        "id": "perf-simd-012",
        "version": 1,
        "status": "active",
        "scope": {
            "paths": ["src/geometry/simd/**", "include/geometry/simd/**"],
            "languages": ["cpp", "cuda"],
        },
        "invariant": {
            "statement": "PointBuffer structures passed to AVX2 kernels must be 32-byte aligned.",
            "rationale": "Unaligned memory loads trigger GP faults under high-throughput geometry sweeps.",
            "enforcement": "reject_diff",
            "max_blast_radius_lines": 20,
        },
        "provenance": {
            "incident_id": "inc-2026-09-08-01",
            "git_commit": "4f9a12c8",
            "inscribing_agent": "forensic-auditor-v2",
            "peer_consensus_agent": "rule-curator-v1",
            "created_at": "2026-09-08T18:55:00Z",
            "last_verified_at": "2026-09-08T18:55:00Z",
            "trigger_count": 3,
        },
    }


def test_valid_canonical_rule_passes():
    rule = sample_valid_rule()
    is_valid, errors = validate_rule_dict(rule)
    assert is_valid is True, f"Expected valid rule to pass, got: {errors}"
    assert len(errors) == 0


def test_non_dict_rejected():
    is_valid, errors = validate_rule_dict("not-a-dict")
    assert is_valid is False
    assert any("mapping" in err for err in errors)


def test_missing_required_fields_rejected():
    required_fields = ["id", "version", "status", "scope", "invariant", "provenance"]
    for field in required_fields:
        rule = sample_valid_rule()
        del rule[field]
        is_valid, errors = validate_rule_dict(rule)
        assert is_valid is False, f"Rule missing '{field}' should fail validation."
        assert any(field in err for err in errors)


def test_invalid_status_rejected():
    rule = sample_valid_rule()
    rule["status"] = "unverified"
    is_valid, errors = validate_rule_dict(rule)
    assert is_valid is False
    assert any("status" in err for err in errors)


def test_invalid_enforcement_rejected():
    rule = sample_valid_rule()
    rule["invariant"]["enforcement"] = "ignore_silently"
    is_valid, errors = validate_rule_dict(rule)
    assert is_valid is False
    assert any("enforcement" in err for err in errors)


def test_negative_integer_bounds_rejected():
    rule = sample_valid_rule()
    rule["version"] = 0
    is_valid, errors = validate_rule_dict(rule)
    assert is_valid is False
    assert any("version" in err for err in errors)

    rule2 = sample_valid_rule()
    rule2["provenance"]["trigger_count"] = -1
    is_valid2, errors2 = validate_rule_dict(rule2)
    assert is_valid2 is False
    assert any("trigger_count" in err for err in errors2)


def test_malformed_timestamp_rejected():
    rule = sample_valid_rule()
    rule["provenance"]["created_at"] = "not-a-timestamp"
    is_valid, errors = validate_rule_dict(rule)
    assert is_valid is False
    assert any("created_at" in err for err in errors)

"""Tests verifying globstar and language scope matching logic."""

from aos.matcher import match_path, infer_language, match_rule
from aos.models import InvariantRule, Scope, Invariant, Provenance


def create_dummy_rule(paths=None, languages=None):
    return InvariantRule(
        id="test-rule-001",
        version=1,
        status="active",
        scope=Scope(paths=paths or [], languages=languages or []),
        invariant=Invariant(
            statement="Test statement.",
            rationale="Test rationale.",
            enforcement="reject_diff",
        ),
        provenance=Provenance(
            incident_id="inc-1",
            git_commit="abcdef",
            inscribing_agent="tester",
            created_at="2026-09-08T18:00:00Z",
            last_verified_at="2026-09-08T18:00:00Z",
        ),
    )


def test_globstar_path_matching():
    pattern = "src/geometry/simd/**"
    assert match_path(pattern, "src/geometry/simd/kernel.cpp") is True
    assert match_path(pattern, "src/geometry/simd/nested/deep/kernel.cu") is True
    assert match_path(pattern, "src/geometry/other/kernel.cpp") is False
    assert match_path(pattern, "other/geometry/simd/kernel.cpp") is False


def test_windows_backslash_normalization():
    pattern = "src/geometry/simd/**"
    windows_path = "src\\geometry\\simd\\nested\\kernel.cpp"
    assert match_path(pattern, windows_path) is True


def test_language_inference_from_extensions():
    assert infer_language("src/test.cpp") == "cpp"
    assert infer_language("src/test.cu") == "cuda"
    assert infer_language("src/test.py") == "python"
    assert infer_language("src/test.rs") == "rust"
    assert infer_language("src/test.unknown_ext") is None


def test_rule_matching_path_and_language():
    rule = create_dummy_rule(
        paths=["src/geometry/simd/**"],
        languages=["cpp", "cuda"],
    )

    # Valid path and inferred valid language
    assert match_rule(rule, "src/geometry/simd/kernel.cpp") is True
    assert match_rule(rule, "src/geometry/simd/kernel.cu") is True

    # Valid path but incompatible language
    assert match_rule(rule, "src/geometry/simd/kernel.py") is False

    # Incompatible path
    assert match_rule(rule, "src/rendering/kernel.cpp") is False


def test_empty_scope_matches_any():
    rule_unconstrained = create_dummy_rule(paths=[], languages=[])
    assert match_rule(rule_unconstrained, "any/path/file.txt") is True

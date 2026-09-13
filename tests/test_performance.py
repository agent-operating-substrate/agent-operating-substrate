"""Benchmark and performance tests verifying sub-millisecond evaluation and streaming efficiency."""

import time
import tracemalloc
from pathlib import Path

from aos.enforcer import check_file_violations
from aos.engine import RuleEngine
from aos.matcher import _compile_glob, extract_path_prefix, normalize_path
from aos.models import Invariant, InvariantRule, Provenance, Scope


def test_batch_matching_1000_files_under_50ms():
    """Verify that matching 1,000 file paths against 100 rules executes in under 50ms."""
    rules: list[InvariantRule] = []

    # 100 rules across diverse scopes
    categories = [
        ("src/geometry", ["cpp", "cuda"]),
        ("src/rendering", ["cpp", "python"]),
        ("src/physics", ["rust", "cpp"]),
        ("src/network", ["go", "rust"]),
        ("src/audio", ["cpp"]),
        ("src/ui", ["typescript", "javascript"]),
        ("src/core", ["python", "rust"]),
        ("tests", ["python"]),
        ("docs", ["yaml"]),
        ("tools", ["bash", "python"]),
    ]

    for i in range(100):
        cat_idx = i % len(categories)
        cat_dir, cat_langs = categories[cat_idx]
        sub = f"sub_{i % 4}"

        if i < 5:
            # 5 universal rules
            paths = ["**/*"]
            langs = []
        else:
            paths = [f"{cat_dir}/{sub}/**"]
            langs = cat_langs

        rule = InvariantRule(
            id=f"perf-rule-{i:03d}",
            version=1,
            status="active",
            scope=Scope(paths=paths, languages=langs),
            invariant=Invariant(
                statement=f"Rule {i} invariant statement.",
                rationale="Performance verification rule.",
                enforcement="reject_diff",
            ),
            provenance=Provenance(
                incident_id=f"inc-{i}",
                git_commit="abcdef123456",
                inscribing_agent="perf-tester",
                created_at="2026-09-08T18:00:00Z",
                last_verified_at="2026-09-08T18:00:00Z",
            ),
        )
        rules.append(rule)

    engine = RuleEngine()
    engine.rules = rules

    # Generate 1,000 file paths distributed across directories
    file_paths: list[str] = []
    ext_map = {
        0: "cpp",
        1: "cu",
        2: "py",
        3: "rs",
        4: "go",
        5: "ts",
        6: "js",
        7: "yaml",
        8: "sh",
        9: "cpp",
    }
    for i in range(1000):
        cat_idx = i % len(categories)
        cat_dir, _ = categories[cat_idx]
        sub = f"sub_{i % 4}"
        ext = ext_map[cat_idx]
        file_paths.append(f"{cat_dir}/{sub}/component_{i}.{ext}")

    # Warm-up compile caches
    _ = engine.match_files(file_paths[:10])

    # Benchmark run
    t_start = time.perf_counter()
    batch_results = engine.match_files(file_paths)
    t_elapsed = time.perf_counter() - t_start

    # Execution must be under 50ms
    assert t_elapsed < 0.050, f"Batch matching took {t_elapsed * 1000:.2f}ms (must be < 50ms)"

    # Verify matching accuracy
    assert len(batch_results) == 1000
    sample_file = "src/geometry/sub_0/component_0.cpp"
    sample_matches = batch_results[sample_file]
    sample_rule_ids = {r.id for r in sample_matches}

    # Universal rules (first 5) should match
    for u_idx in range(5):
        assert f"perf-rule-{u_idx:03d}" in sample_rule_ids

    # Geometry sub_0 rules should match (i % 10 == 0 and i % 4 == 0 -> 0, 20, 40, 60, 80)
    assert "perf-rule-000" in sample_rule_ids
    assert "perf-rule-020" in sample_rule_ids
    # Geometry sub_2 rule should not match sub_0
    assert "perf-rule-010" not in sample_rule_ids


def test_single_pass_content_enforcement_efficiency(tmp_path: Path):
    """Verify single-pass content enforcement efficiency and low memory overhead."""
    # Create 15,000 line file with one forbidden em dash on line 12,345
    large_file = tmp_path / "large_source.py"
    with large_file.open("w", encoding="utf-8") as f:
        for idx in range(1, 15001):
            if idx == 12345:
                # Include forbidden em dash character via unicode escape
                f.write("# Violation on this line: \u2014 here\n")
            else:
                f.write(f"val_{idx} = {idx} * 42\n")

    punct_rule = InvariantRule(
        id="aos-punct-001",
        version=1,
        status="active",
        scope=Scope(paths=["**/*"], languages=["python"]),
        invariant=Invariant(
            statement="Zero em dashes in all prose.",
            rationale="Deterministic punctuation invariant.",
            enforcement="reject_diff",
        ),
        provenance=Provenance(
            incident_id="inc-punct-1",
            git_commit="abc123",
            inscribing_agent="perf-tester",
            created_at="2026-09-08T18:00:00Z",
            last_verified_at="2026-09-08T18:00:00Z",
        ),
    )

    engine = RuleEngine(root_dir=tmp_path)
    engine.rules = [punct_rule]

    # Measure memory and timing
    tracemalloc.start()
    tracemalloc.reset_peak()
    t_start = time.perf_counter()

    violations = check_file_violations(large_file, root_dir=tmp_path, engine=engine)

    t_elapsed = time.perf_counter() - t_start
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Peak memory must remain small (under 500 KB) because lines are streamed
    peak_kb = peak_bytes / 1024
    assert peak_kb < 500, f"Peak memory {peak_kb:.2f} KB exceeded 500 KB limit"

    # Execution time for 15k lines should be fast (sub-second, well under 250ms)
    assert t_elapsed < 0.250, f"Scanning 15k lines took {t_elapsed * 1000:.2f}ms"

    # Verify violation correctness
    assert len(violations) == 1
    assert violations[0].line_number == 12345
    assert violations[0].rule_id == "aos-punct-001"
    assert violations[0].enforcement == "reject_diff"


def test_matcher_prefix_extraction():
    """Verify glob prefix extraction utility."""
    assert extract_path_prefix("src/geometry/simd/**") == "src/geometry/simd/"
    assert extract_path_prefix("src/**/*.py") == "src/"
    assert extract_path_prefix("**/*") == ""
    assert extract_path_prefix("*.py") == ""
    assert extract_path_prefix("tests/test_perf.py") == "tests/"
    assert extract_path_prefix("setup.py") == ""
    assert extract_path_prefix("src\\models\\*.py") == "src/models/"

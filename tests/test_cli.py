from __future__ import annotations

import json

from threebody.cli import main


def test_survey_cli_writes_research_artifact(tmp_path) -> None:
    output = tmp_path / "survey.json"

    exit_code = main(
        [
            "survey",
            "--scenario",
            "figure-eight",
            "--count",
            "1",
            "--periods",
            "0.02",
            "--samples",
            "30",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["scenario"] == "general-figure-eight"
    assert payload["summary"]["trajectory_count"] == 1
    assert "chart_distribution" in payload["summary"]


def test_interpret_cli_writes_chart_local_segments(tmp_path) -> None:
    output = tmp_path / "interpret.json"

    exit_code = main(
        [
            "interpret",
            "--scenario",
            "hierarchical-flyby",
            "--periods",
            "1.0",
            "--samples",
            "80",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "trajectory-interpretation"
    assert payload["summary"]["certificate"]["local_interpretation_available"] is True
    assert payload["summary"]["certificate"]["theorem_ready"] is False
    assert payload["summary"]["segments"]
    assert payload["summary"]["unresolved_obligations"]


def test_interpretation_suite_cli_writes_certificate_coverage(tmp_path) -> None:
    output = tmp_path / "interpretation-suite.json"

    exit_code = main(["interpretation-suite", "--output", str(output)])

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "interpretation-suite"
    assert payload["summary"]["local_interpretation_rate"] == 1.0
    assert "close_encounter" in payload["summary"]["covered_chart_types"]
    assert payload["summary"]["unresolved_blockers"]


def test_atlas_benchmark_cli_writes_reproducible_cases(tmp_path) -> None:
    output = tmp_path / "atlas-benchmark.json"

    exit_code = main(
        [
            "atlas-benchmark",
            "--scenario",
            "figure-eight",
            "--periods",
            "0.02",
            "--samples",
            "30",
            "--stride",
            "10",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["metadata"]["kind"] == "atlas-benchmark"
    assert payload["metadata"]["schema_version"] == 1
    assert payload["cases"][0]["source_name"] == "figure-eight"
    assert payload["cases"][0]["initial_state"]
    assert payload["cases"][0]["chart_distribution"]
    assert "threebody interpret" in payload["cases"][0]["reproduce"]

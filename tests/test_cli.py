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
    assert payload["summary"]["segments"]
    assert payload["summary"]["unresolved_obligations"]

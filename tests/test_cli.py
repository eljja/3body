from __future__ import annotations

import hashlib
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


def test_verify_static_artifacts_cli_checks_manifest_hashes(tmp_path) -> None:
    index_path = tmp_path / "index.html"
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    index_path.write_text("<html>ThreeBody Dynamics Lab</html>", encoding="utf-8")
    certificate = {
        "certificate_schema_version": 1,
        "artifact": "threebody-static-research-certificate",
        "artifact_manifest": "manifest.json",
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
    }
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "manifest_schema_version": 1,
        "artifact": "threebody-static-site-manifest",
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
        "artifacts": {
            "index.html": {
                "sha256": _sha256(index_path),
                "bytes": index_path.stat().st_size,
            },
            "certificate.json": {
                "sha256": _sha256(certificate_path),
                "bytes": certificate_path.stat().st_size,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path)])

    assert exit_code == 0


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

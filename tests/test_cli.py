from __future__ import annotations

import hashlib
import json

import threebody.cli as cli_module
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
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "verification-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc",
            "--require-gate",
            "symbolic_passes_stride_robustness",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert receipt["verification_schema_version"] == 1
    assert receipt["verifier"] == "threebody.cli verify-static-artifacts"
    assert receipt["verified_at_utc"].endswith("Z")
    assert receipt["verified"] is True
    assert receipt["checks"]["required_commit"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["required_gates"] == ["symbolic_passes_stride_robustness"]
    assert receipt["required_gate_results"]["symbolic_passes_stride_robustness"] is True


def test_verify_static_artifacts_cli_rejects_unexpected_commit(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-commit", "wrong"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_missing_required_gate(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-gate", "missing_gate"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_checks_public_url_manifest(monkeypatch, tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }
    requested_urls: list[str] = []

    class FakeResponse:
        def __init__(self, data: bytes) -> None:
            self.data = data

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            return None

        def read(self) -> bytes:
            return self.data

    def fake_urlopen(request, timeout: int) -> FakeResponse:
        requested_urls.append(request.full_url)
        artifact_name = request.full_url.rstrip("/").rsplit("/", 1)[-1]
        return FakeResponse(artifacts[artifact_name])

    monkeypatch.setattr(cli_module, "urlopen", fake_urlopen)

    result = cli_module.verify_static_artifacts_from_url(
        "https://example.test/3body",
        require_commit="abc123",
        require_gates=["symbolic_passes_stride_robustness"],
    )

    assert result["verified"] is True
    assert result["source"] == "https://example.test/3body/"
    assert result["required_commit"] == "abc123"
    assert result["verification_schema_version"] == 1
    assert result["verified_at_utc"].endswith("Z")
    assert result["checks"]["required_commit"] is True
    assert result["checks"]["required_gates"] is True
    assert result["required_gate_results"]["symbolic_passes_stride_robustness"] is True
    assert requested_urls == [
        "https://example.test/3body/index.html",
        "https://example.test/3body/certificate.json",
        "https://example.test/3body/manifest.json",
    ]


def _write_static_artifact_bundle(site_dir) -> None:
    index_path = site_dir / "index.html"
    certificate_path = site_dir / "certificate.json"
    manifest_path = site_dir / "manifest.json"
    index_path.write_text("<html>ThreeBody Dynamics Lab</html>", encoding="utf-8")
    certificate = {
        "certificate_schema_version": 1,
        "artifact": "threebody-static-research-certificate",
        "artifact_manifest": "manifest.json",
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
        "promotion_gates": {
            "poincare_passes_permutation_control": True,
            "symbolic_passes_stride_robustness": True,
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


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

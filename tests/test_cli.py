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
            "--require-min",
            "promotion_gates.picard_contraction_reserve=0.1",
            "--require-min",
            "publication_pipeline.promotion_gate_pass_count=7",
            "--require-max",
            "metrics.picard_max_contraction=0.35",
            "--require-feature",
            "index-artifact-discoverability",
            "--require-feature",
            "active-profile-descriptor",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert receipt["verification_schema_version"] == 1
    assert receipt["verification_schema_features"] == [
        "artifact-availability",
        "json-parse-errors",
        "artifact-identity",
        "manifest-hash-algorithm",
        "index-artifact-discoverability",
        "publication-pipeline-links",
        "published-branch-line-ending-policy",
        "commit-provenance",
        "active-profile-descriptor",
        "profile-gates",
        "numeric-minimums",
        "numeric-maximums",
        "certificate-verifier-capability-digest",
    ]
    assert receipt["verification_schema_features_sha256"] == cli_module.static_artifact_verification_features_sha256(
        receipt["verification_schema_features"]
    )
    assert receipt["receipt_payload_sha256"] == cli_module.static_artifact_receipt_payload_sha256(receipt)
    retimestamped_receipt = {**receipt, "verified_at_utc": "2099-01-01T00:00:00Z"}
    assert cli_module.static_artifact_receipt_payload_sha256(retimestamped_receipt) == receipt["receipt_payload_sha256"]
    tampered_receipt = {**receipt, "verified": False}
    assert cli_module.static_artifact_receipt_payload_sha256(tampered_receipt) != receipt["receipt_payload_sha256"]
    assert receipt["certificate_verification_schema_features"] == receipt["verification_schema_features"]
    assert (
        receipt["certificate_verification_schema_features_sha256"] == receipt["verification_schema_features_sha256"]
    )
    assert receipt["required_feature_set_sha256"] is None
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["verifier"] == "threebody.cli verify-static-artifacts"
    assert receipt["verified_at_utc"].endswith("Z")
    assert receipt["verified"] is True
    assert receipt["checks"]["manifest_json"] is True
    assert receipt["checks"]["manifest_hash_algorithm"] is True
    assert receipt["checks"]["certificate_json"] is True
    assert receipt["checks"]["certificate_verification_schema_features"] is True
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is True
    assert receipt["parse_errors"] == {"certificate.json": None, "manifest.json": None}
    assert receipt["artifact_errors"] == {
        "certificate.json": None,
        "favicon.svg": None,
        ".gitattributes": None,
        "index.html": None,
        "manifest.json": None,
    }
    assert receipt["checks"]["index_available"] is True
    assert receipt["checks"]["certificate_available"] is True
    assert receipt["checks"]["favicon_available"] is True
    assert receipt["checks"]["gitattributes_available"] is True
    assert receipt["checks"]["manifest_available"] is True
    assert receipt["checks"]["required_commit"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True
    assert receipt["checks"]["required_features"] is True
    assert receipt["required_features"] == ["index-artifact-discoverability", "active-profile-descriptor"]
    assert receipt["required_feature_results"] == [
        {"feature": "index-artifact-discoverability", "passed": True},
        {"feature": "active-profile-descriptor", "passed": True},
    ]
    assert receipt["checks"]["index_certificate_link"] is True
    assert receipt["checks"]["index_manifest_link"] is True
    assert receipt["checks"]["index_favicon_link"] is True
    assert receipt["checks"]["favicon_hash"] is True
    assert receipt["checks"]["favicon_size"] is True
    assert receipt["checks"]["gitattributes_hash"] is True
    assert receipt["checks"]["gitattributes_size"] is True
    assert receipt["checks"]["gitattributes_policy"] is True
    assert receipt["required_gates"] == ["symbolic_passes_stride_robustness"]
    assert receipt["required_gate_results"]["symbolic_passes_stride_robustness"] is True
    assert receipt["required_minimum_results"][0]["path"] == "promotion_gates.picard_contraction_reserve"
    assert receipt["required_minimum_results"][0]["passed"] is True
    assert receipt["required_maximum_results"][0]["path"] == "metrics.picard_max_contraction"
    assert receipt["required_maximum_results"][0]["passed"] is True


def test_verify_static_artifacts_cli_rejects_unexpected_commit(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-commit", "wrong"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_manifest_hash_algorithm_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "hash-algorithm-receipt.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["hash_algorithm"] = "sha1"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["manifest_hash_algorithm"] is False
    assert receipt["checks"]["index_hash"] is True
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["favicon_hash"] is True


def test_verify_static_artifacts_cli_rejects_wrong_gitattributes_policy(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "gitattributes-policy-receipt.json"
    (tmp_path / ".gitattributes").write_text("* text=auto\n", encoding="utf-8", newline="\n")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-public-claim",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["gitattributes_available"] is True
    assert receipt["checks"]["gitattributes_hash"] is True
    assert receipt["checks"]["gitattributes_size"] is True
    assert receipt["checks"]["gitattributes_policy"] is False
    assert "published-branch-line-ending-policy" in receipt["verification_schema_features"]


def test_verify_static_artifacts_cli_rejects_missing_required_feature(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "missing-feature-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-feature",
            "not-a-real-feature",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_features"] is False
    assert receipt["required_features"] == ["not-a-real-feature"]
    assert receipt["required_feature_results"] == [{"feature": "not-a-real-feature", "passed": False}]
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_can_pin_current_feature_set_digest(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "current-feature-set-digest-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-current-feature-set",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["required_feature_set_sha256"] == expected_digest
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is True


def test_verify_static_artifacts_cli_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "public-claim-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-public-claim",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["required_profiles"] == ["public-claims-v1"]
    assert receipt["required_feature_set_sha256"] == expected_digest
    assert receipt["checks"]["required_profile_hashes"] is True
    assert receipt["checks"]["required_feature_set_sha256"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True


def test_verify_static_artifacts_api_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    result = cli_module.verify_static_artifacts(
        tmp_path,
        require_commit="abc123",
        require_public_claim=True,
    )
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert result["verified"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["required_feature_set_sha256"] == expected_digest
    assert result["checks"]["required_profile_hashes"] is True
    assert result["checks"]["required_feature_set_sha256"] is True
    assert result["checks"]["required_gates"] is True
    assert result["checks"]["required_minimums"] is True
    assert result["checks"]["required_maximums"] is True


def test_verify_static_artifact_bytes_api_can_require_public_claim(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        require_commit="abc123",
        require_public_claim=True,
    )
    expected_digest = cli_module.static_artifact_verification_features_sha256(
        cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )

    assert result["verified"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["required_feature_set_sha256"] == expected_digest
    assert result["checks"]["required_profile_hashes"] is True
    assert result["checks"]["required_feature_set_sha256"] is True


def test_verify_static_artifacts_cli_rejects_feature_set_digest_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "feature-set-digest-receipt.json"
    wrong_digest = "0" * 64

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-feature-set-sha256",
            wrong_digest,
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["required_feature_set_sha256"] == wrong_digest
    assert receipt["checks"]["required_feature_set_sha256"] is False
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_rejects_certificate_verifier_feature_digest_mismatch(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "certificate-feature-digest-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["verification_schema_features"] = ["artifact-availability"]
    certificate["verification_schema_features_sha256"] = "0" * 64
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["certificate_verification_schema_features"] == ["artifact-availability"]
    assert receipt["certificate_verification_schema_features_sha256"] == "0" * 64
    assert receipt["checks"]["certificate_verification_schema_features"] is False
    assert receipt["checks"]["certificate_verification_schema_features_sha256"] is False
    assert receipt["checks"]["required_profile_hashes"] is True


def test_verify_static_artifacts_cli_rejects_index_without_manifest_link(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    index_path = tmp_path / "index.html"
    receipt_path = tmp_path / "index-link-receipt.json"
    index_path.write_text(
        (
            '<html><head><link rel="icon" href="favicon.svg" type="image/svg+xml"></head>'
            '<body>ThreeBody Dynamics Lab <a href="certificate.json">certificate</a></body></html>'
        ),
        encoding="utf-8",
    )
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["index_certificate_link"] is True
    assert receipt["checks"]["index_manifest_link"] is False
    assert receipt["checks"]["index_favicon_link"] is True
    assert receipt["checks"]["index_hash"] is True


def test_verify_static_artifacts_cli_rejects_missing_required_gate(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(["verify-static-artifacts", "--site-dir", str(tmp_path), "--require-gate", "missing_gate"])

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_failed_minimum(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-min",
            "promotion_gates.picard_contraction_reserve=1.0",
        ]
    )

    assert exit_code == 1


def test_verify_static_artifacts_cli_rejects_failed_maximum(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-max",
            "metrics.picard_max_contraction=0.001",
        ]
    )

    assert exit_code == 1


def test_verify_static_artifacts_cli_applies_public_claim_profile(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    receipt_path = tmp_path / "profile-receipt.json"

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert receipt["verified"] is True
    assert receipt["checks"]["manifest_artifact"] is True
    assert receipt["checks"]["certificate_artifact"] is True
    assert receipt["checks"]["publication_pipeline_links"] is True
    assert receipt["required_profiles"] == ["public-claims-v1"]
    assert receipt["required_profile_hashes"] == {
        "public-claims-v1": cli_module.static_artifact_requirement_profile_sha256("public-claims-v1")
    }
    assert "index-artifact-discoverability" in receipt["required_profile_requirements"]["require_features"]
    assert receipt["required_profile_results"][0]["active_matches"] is True
    assert receipt["required_profile_results"][0]["active_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_hash_matches"] is True
    assert receipt["required_profile_results"][0]["hash_matches"] is True
    assert receipt["required_profile_results"][0]["passed"] is True
    assert receipt["required_profile_requirements"]["require_gates"] == [
        "picard_certified",
        "poincare_markov_significant_baseline_win",
        "poincare_passes_permutation_control",
        "poincare_passes_section_robustness",
        "symbolic_passes_stride_robustness",
    ]
    assert "publication_pipeline.promotion_gate_pass_count=7" in receipt["required_minimums"]
    assert "metrics.picard_max_contraction=0.35" in receipt["required_maximums"]
    assert "index-artifact-discoverability" in receipt["required_features"]
    assert "active-profile-descriptor" in receipt["required_features"]
    assert receipt["checks"]["required_profile_hashes"] is True
    assert receipt["checks"]["required_gates"] is True
    assert receipt["checks"]["required_minimums"] is True
    assert receipt["checks"]["required_maximums"] is True
    assert receipt["checks"]["required_features"] is True
    assert all(row["feature"] in receipt["verification_schema_features"] for row in receipt["required_feature_results"])


def test_public_claim_profile_features_are_explicitly_versioned() -> None:
    descriptor = cli_module.static_artifact_requirement_profile_descriptor("public-claims-v1")
    required_features = descriptor["requirements"]["require_features"]

    assert tuple(required_features) == cli_module.PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES
    assert required_features == list(cli_module.PUBLIC_STATIC_ARTIFACT_CLAIM_PROFILE_FEATURES)
    assert set(required_features).issubset(set(cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES))
    assert "certificate-verifier-capability-digest" in cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    assert "certificate-verifier-capability-digest" not in required_features
    assert required_features is not cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES


def test_required_feature_results_are_based_on_advertised_features() -> None:
    required = ["artifact-availability", "numeric-maximums", "missing-capability"]
    advertised = ["artifact-availability", "numeric-maximums"]

    results = cli_module._required_feature_results(required, advertised)

    assert results == [
        {"feature": "artifact-availability", "passed": True},
        {"feature": "numeric-maximums", "passed": True},
        {"feature": "missing-capability", "passed": False},
    ]


def test_verification_feature_digest_is_order_sensitive() -> None:
    features = ["artifact-availability", "numeric-maximums"]

    assert cli_module.static_artifact_verification_features_sha256(features) != (
        cli_module.static_artifact_verification_features_sha256(list(reversed(features)))
    )


def test_verify_static_artifacts_cli_rejects_inactive_required_profile(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "inactive-profile-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["publication_pipeline"]["verification_profile"] = "local-draft-profile"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["required_profile_results"][0]["active_matches"] is False
    assert receipt["required_profile_results"][0]["active_hash_matches"] is False
    assert receipt["required_profile_results"][0]["descriptor_matches"] is True
    assert receipt["required_profile_results"][0]["passed"] is False


def test_verify_static_artifacts_cli_rejects_tampered_profile_descriptor(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "tampered-profile-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["verification_profiles"]["public-claims-v1"]["requirements"]["require_gates"] = [
        "picard_certified",
    ]
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["required_profile_results"][0]["active_matches"] is True
    assert receipt["required_profile_results"][0]["active_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_hash_matches"] is True
    assert receipt["required_profile_results"][0]["descriptor_matches"] is False
    assert receipt["required_profile_results"][0]["passed"] is False


def test_verify_static_artifacts_cli_rejects_mismatched_publication_pipeline_links(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    receipt_path = tmp_path / "pipeline-link-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    certificate["publication_pipeline"]["integrity_manifest"] = "draft-manifest.json"
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    _refresh_manifest_hashes(tmp_path)

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["favicon_hash"] is True
    assert receipt["checks"]["publication_pipeline_links"] is False
    assert receipt["checks"]["required_profile_hashes"] is True


def test_verify_static_artifacts_cli_reports_invalid_nested_json_shapes(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "invalid-shapes-receipt.json"
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    certificate["build_provenance"] = "not-an-object"
    manifest["build_provenance"] = "not-an-object"
    manifest["artifacts"] = []
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["commit_sha"] is None
    assert receipt["commit_sha_short"] is None
    assert receipt["checks"]["provenance_commit_match"] is False
    assert receipt["checks"]["required_commit"] is False
    assert receipt["checks"]["index_hash"] is False
    assert receipt["checks"]["certificate_hash"] is False
    assert receipt["checks"]["favicon_hash"] is False
    assert receipt["checks"]["index_size"] is False
    assert receipt["checks"]["certificate_size"] is False
    assert receipt["checks"]["favicon_size"] is False


def test_verify_static_artifacts_cli_reports_invalid_json_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    receipt_path = tmp_path / "invalid-json-receipt.json"
    certificate_path.write_text("{not-json", encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["artifacts"]["certificate.json"]["sha256"] = _sha256(certificate_path)
    manifest["artifacts"]["certificate.json"]["bytes"] = certificate_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["manifest_json"] is True
    assert receipt["checks"]["certificate_json"] is False
    assert receipt["checks"]["certificate_hash"] is True
    assert receipt["checks"]["certificate_size"] is True
    assert receipt["checks"]["required_profile_hashes"] is False
    assert receipt["parse_errors"]["manifest.json"] is None
    assert "Expecting property name" in receipt["parse_errors"]["certificate.json"]


def test_verify_static_artifacts_cli_reports_missing_local_artifact_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    favicon_path = tmp_path / "favicon.svg"
    receipt_path = tmp_path / "missing-favicon-receipt.json"
    favicon_path.unlink()

    exit_code = main(
        [
            "verify-static-artifacts",
            "--site-dir",
            str(tmp_path),
            "--require-commit",
            "abc123",
            "--require-profile",
            "public-claims-v1",
            "--output",
            str(receipt_path),
        ]
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    assert exit_code == 1
    assert receipt["verified"] is False
    assert receipt["checks"]["favicon_available"] is False
    assert receipt["checks"]["favicon_hash"] is False
    assert receipt["checks"]["favicon_size"] is False
    assert receipt["checks"]["manifest_available"] is True
    assert receipt["checks"]["required_profile_hashes"] is True
    assert "favicon.svg" in receipt["artifact_errors"]["favicon.svg"]


def test_verify_static_artifacts_from_url_reports_fetch_error(monkeypatch, tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

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
        artifact_name = request.full_url.rstrip("/").rsplit("/", 1)[-1]
        if artifact_name == "favicon.svg":
            raise OSError("simulated missing favicon")
        return FakeResponse(artifacts[artifact_name])

    monkeypatch.setattr(cli_module, "urlopen", fake_urlopen)

    result = cli_module.verify_static_artifacts_from_url(
        "https://example.test/3body",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
        require_features=["manifest-hash-algorithm"],
        require_feature_set_sha256=cli_module.static_artifact_verification_features_sha256(
            cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
        ),
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["manifest_available"] is True
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "simulated missing favicon"


def test_verify_static_artifact_bytes_reports_missing_direct_artifact_key(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "artifact missing from provided bytes"


def test_verify_static_artifact_bytes_does_not_let_partial_error_map_hide_missing_key(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        artifact_errors={"index.html": None, "certificate.json": None, "manifest.json": None},
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["artifact_errors"]["favicon.svg"] == "artifact missing from provided bytes"


def test_verify_static_artifact_bytes_reports_malformed_error_map_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,
        source="direct-bytes",
        artifact_errors=["not", "a", "mapping"],  # type: ignore[arg-type]
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["index_available"] is False
    assert result["checks"]["index_hash"] is True
    assert result["artifact_errors"]["index.html"] == "artifact_errors is list, expected mapping"


def test_verify_static_artifact_bytes_reports_non_bytes_payload_without_crashing(tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": "<svg></svg>",
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
        "manifest.json": (tmp_path / "manifest.json").read_bytes(),
    }

    result = cli_module.verify_static_artifact_bytes(
        artifacts,  # type: ignore[arg-type]
        source="direct-bytes",
        require_commit="abc123",
        require_profiles=["public-claims-v1"],
    )

    assert result["verified"] is False
    assert result["checks"]["favicon_available"] is False
    assert result["checks"]["favicon_hash"] is False
    assert result["checks"]["favicon_size"] is False
    assert result["checks"]["required_profile_hashes"] is True
    assert result["artifact_errors"]["favicon.svg"] == "artifact payload is str, expected bytes-like"


def test_verify_static_artifacts_cli_checks_public_url_manifest(monkeypatch, tmp_path) -> None:
    _write_static_artifact_bundle(tmp_path)
    artifacts = {
        "index.html": (tmp_path / "index.html").read_bytes(),
        "certificate.json": (tmp_path / "certificate.json").read_bytes(),
        "favicon.svg": (tmp_path / "favicon.svg").read_bytes(),
        ".gitattributes": (tmp_path / ".gitattributes").read_bytes(),
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
        require_profiles=["public-claims-v1"],
        require_features=["manifest-hash-algorithm"],
        require_feature_set_sha256=cli_module.static_artifact_verification_features_sha256(
            cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
        ),
    )

    assert result["verified"] is True
    assert result["source"] == "https://example.test/3body/"
    assert result["required_commit"] == "abc123"
    assert result["verification_schema_version"] == 1
    assert "index-artifact-discoverability" in result["verification_schema_features"]
    assert "active-profile-descriptor" in result["verification_schema_features"]
    assert "manifest-hash-algorithm" in result["required_features"]
    assert "index-artifact-discoverability" in result["required_features"]
    assert result["required_feature_set_sha256"] == result["verification_schema_features_sha256"]
    assert result["checks"]["required_feature_set_sha256"] is True
    assert all(row["passed"] for row in result["required_feature_results"])
    assert result["verified_at_utc"].endswith("Z")
    assert result["checks"]["manifest_artifact"] is True
    assert result["checks"]["manifest_hash_algorithm"] is True
    assert result["checks"]["certificate_artifact"] is True
    assert result["checks"]["publication_pipeline_links"] is True
    assert result["required_profiles"] == ["public-claims-v1"]
    assert result["checks"]["required_commit"] is True
    assert result["checks"]["required_profile_hashes"] is True
    assert result["required_profile_results"][0]["active_profile"] == "public-claims-v1"
    assert result["checks"]["required_gates"] is True
    assert result["checks"]["required_minimums"] is True
    assert result["checks"]["required_maximums"] is True
    assert result["checks"]["index_certificate_link"] is True
    assert result["checks"]["index_manifest_link"] is True
    assert result["checks"]["index_favicon_link"] is True
    assert result["checks"]["favicon_hash"] is True
    assert result["checks"]["favicon_size"] is True
    assert result["checks"]["gitattributes_hash"] is True
    assert result["checks"]["gitattributes_size"] is True
    assert result["checks"]["gitattributes_policy"] is True
    assert result["required_gate_results"]["picard_certified"] is True
    assert result["required_minimum_results"][0]["passed"] is True
    assert result["required_maximum_results"][0]["passed"] is True
    assert requested_urls == [
        "https://example.test/3body/index.html",
        "https://example.test/3body/certificate.json",
        "https://example.test/3body/favicon.svg",
        "https://example.test/3body/.gitattributes",
        "https://example.test/3body/manifest.json",
    ]


def _write_static_artifact_bundle(site_dir) -> None:
    index_path = site_dir / "index.html"
    certificate_path = site_dir / "certificate.json"
    favicon_path = site_dir / "favicon.svg"
    gitattributes_path = site_dir / ".gitattributes"
    manifest_path = site_dir / "manifest.json"
    index_path.write_text(
        (
            '<html><head><link rel="icon" href="favicon.svg" type="image/svg+xml"></head>'
            '<body>ThreeBody Dynamics Lab <a href="certificate.json">certificate</a> '
            '<a href="manifest.json">manifest</a></body></html>'
        ),
        encoding="utf-8",
    )
    favicon_path.write_text("<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 64 64\"></svg>\n", encoding="utf-8")
    gitattributes_path.write_text("* text eol=lf\n", encoding="utf-8", newline="\n")
    profile_sha256 = cli_module.static_artifact_requirement_profile_sha256("public-claims-v1")
    verifier_feature_set = list(cli_module.STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    verifier_feature_set_sha256 = cli_module.static_artifact_verification_features_sha256(verifier_feature_set)
    certificate = {
        "certificate_schema_version": 1,
        "artifact": "threebody-static-research-certificate",
        "artifact_manifest": "manifest.json",
        "publication_pipeline": {
            "engine": "threebody.ui.static_site",
            "integrity_manifest": "manifest.json",
            "machine_readable_certificate": "certificate.json",
            "promotion_gate_pass_count": 7,
            "verification_profile": "public-claims-v1",
            "verification_profile_sha256": profile_sha256,
        },
        "verification_profiles": {
            "public-claims-v1": {
                **cli_module.static_artifact_requirement_profile_descriptor("public-claims-v1"),
                "sha256": profile_sha256,
            },
        },
        "verification_schema_features": verifier_feature_set,
        "verification_schema_features_sha256": verifier_feature_set_sha256,
        "metrics": {
            "general_max_energy_drift": 1.0e-10,
            "picard_max_contraction": 0.01,
            "restricted_max_jacobi_drift": 1.0e-12,
        },
        "build_provenance": {
            "commit_sha": "abc123",
            "commit_sha_short": "abc123",
        },
        "promotion_gates": {
            "picard_certified": True,
            "picard_contraction_reserve": 0.3437,
            "poincare_markov_significant_baseline_win": True,
            "poincare_passes_permutation_control": True,
            "poincare_passes_section_robustness": True,
            "poincare_section_robust_pass_fraction": 1.0,
            "symbolic_passes_stride_robustness": True,
            "symbolic_stride_robust_pass_fraction": 1.0,
        },
    }
    certificate_path.write_text(json.dumps(certificate, indent=2, sort_keys=True), encoding="utf-8")
    manifest = {
        "manifest_schema_version": 1,
        "artifact": "threebody-static-site-manifest",
        "hash_algorithm": "sha256",
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
            "favicon.svg": {
                "sha256": _sha256(favicon_path),
                "bytes": favicon_path.stat().st_size,
            },
            ".gitattributes": {
                "sha256": _sha256(gitattributes_path),
                "bytes": gitattributes_path.stat().st_size,
            },
        },
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _refresh_manifest_hashes(site_dir) -> None:
    manifest_path = site_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for artifact_name in ("index.html", "certificate.json", "favicon.svg", ".gitattributes"):
        artifact_path = site_dir / artifact_name
        manifest["artifacts"][artifact_name]["sha256"] = _sha256(artifact_path)
        manifest["artifacts"][artifact_name]["bytes"] = artifact_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

from __future__ import annotations

import hashlib
import json

from threebody.cli import (
    STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES,
    static_artifact_requirement_profile_sha256,
    static_artifact_verification_features_sha256,
)
from threebody_engine import (
    audit_public_static_artifact_bytes,
    audit_public_static_artifacts,
    audit_public_static_artifacts_from_url,
    public_static_artifact_audit_report_payload_sha256,
    validate_public_static_artifact_receipt_contract,
    verify_public_static_artifact_bytes,
    verify_public_static_artifacts,
    verify_public_static_artifacts_from_url,
)
from threebody.ui.static_site import build_static_site


def test_static_site_builder_writes_index(monkeypatch, tmp_path) -> None:
    index_path = build_static_site(tmp_path)

    assert index_path.name == "index.html"
    assert index_path.exists()
    assert (tmp_path / ".nojekyll").exists()
    certificate_path = tmp_path / "certificate.json"
    favicon_path = tmp_path / "favicon.svg"
    manifest_path = tmp_path / "manifest.json"
    gitattributes_path = tmp_path / ".gitattributes"
    assert certificate_path.exists()
    assert favicon_path.exists()
    assert manifest_path.exists()
    assert gitattributes_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "ThreeBody Dynamics Lab" in content
    assert '<body class="lang-en">' in content
    assert 'class="language-toggle"' in content
    assert 'data-language="en"' in content
    assert 'data-language="ko"' in content
    assert "삼체 목표시각 답변" in content
    assert "원래 문제의 답: t 시각 위치 또는 분포" in content
    assert '<link rel="icon" href="favicon.svg" type="image/svg+xml">' in content
    assert '<meta name="theme-color" content="#16212f">' in content
    assert 'class="floating-nav"' in content
    assert 'aria-label="Content panel navigation"' in content
    assert 'data-panel-target="threebody-answer"' in content
    assert 'data-panel-target="closed-form-route"' in content
    assert 'data-panel-target="riemann-hypothesis"' in content
    assert 'data-panel-target="collatz-conjecture"' in content
    assert 'data-panel-target="goldbach-conjecture"' in content
    assert 'data-panel-target="twin-prime"' in content
    assert "Research content workspace" in content
    assert "Global closed-form route" in content
    assert "Sundman-style regularized convergent series contract" in content
    assert "Riemann Hypothesis" in content
    assert "Collatz Conjecture" in content
    assert "Goldbach Conjecture" in content
    assert "Twin Prime Workbench" in content
    assert "Proof Workbench" not in content
    assert 'href="https://github.com/eljja/3body"' in content
    assert 'target="_blank" rel="noopener noreferrer">GitHub repo</a>' in content
    assert "General three-body figure-eight" in content
    assert "autoscale extent" in content
    assert "scaleanchor" not in content
    assert "Jacobi escape-cone theorem candidate" in content
    assert "Verification engine upgrades" in content
    assert "Research progress map" in content
    assert "Original problem answer: position or distribution at t" in content
    assert "target-time geometry" in content
    assert "solve_three_body_target_positions" in content
    assert "seeded random three-body challenge" in content
    assert "certificate.json.random_prediction_demo" in content
    assert "target_sensitivity_budget" in content
    assert "target_readout_decision" in content
    assert "Current change ledger" in content
    assert "Random target demo" in content
    assert "Position or distribution" in content
    assert "Sundman route scoped" in content
    assert "Certificate validation" in content
    assert "Permutation confidence" in content
    assert "Poincare sweep" in content
    assert "Picard contraction tuning" in content
    assert "Markov baseline test" in content
    assert "Poincare memory" in content
    assert "Section robustness" in content
    assert "Stride robustness" in content
    assert "Evidence publication pipeline" not in content
    assert "Public verification ladder" not in content
    assert "Research certificate status" not in content
    assert "Public claim audit chain" in content
    assert "Canonical public claim profile" in content
    assert "Verifier capability set" in content
    assert "Commit-pinned build" in content
    assert "Bounded numerical drift" in content
    assert "Active profile digest" in content
    assert "Build provenance" in content
    assert "Open machine-readable certificate JSON" in content
    assert "Open artifact integrity manifest" in content
    assert 'href="certificate.json"' in content
    assert 'href="manifest.json"' in content
    assert "verify-static-artifacts --base-url https://eljja.github.io/3body/" in content
    assert "--require-commit local" in content
    assert "--require-public-claim" in content
    assert "--require-profile public-claims-v1" not in content
    assert "--require-current-feature-set" not in content
    assert "--require-feature-set-sha256" not in content
    assert "--output .runtime/research_runs/pages-verification-receipt.json" in content
    assert (
        "verify-static-artifacts --site-dir site --require-commit local --require-public-claim"
    ) in content
    assert "audit_public_static_artifacts_from_url" in content
    assert "public_static_artifact_claim_contract" in content
    assert "audit = audit_public_static_artifacts_from_url" in content
    assert "CLI and threebody_engine API callers can apply the same public claim contract" in content
    assert "jacobi_parameter_interval_box_margin" not in content
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    verifier_feature_set_sha256 = static_artifact_verification_features_sha256(
        STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES
    )
    assert certificate["certificate_schema_version"] == 1
    assert certificate["artifact"] == "threebody-static-research-certificate"
    assert certificate["artifact_manifest"] == "manifest.json"
    assert certificate["publication_pipeline"]["promotion_gate_pass_count"] == 7
    assert certificate["publication_pipeline"]["engine"] == "threebody.ui.static_site"
    assert certificate["publication_pipeline"]["machine_readable_certificate"] == "certificate.json"
    assert certificate["publication_pipeline"]["integrity_manifest"] == "manifest.json"
    assert certificate["publication_pipeline"]["verification_profile"] == "public-claims-v1"
    assert certificate["publication_pipeline"]["verification_profile_sha256"] == static_artifact_requirement_profile_sha256(
        "public-claims-v1"
    )
    assert certificate["verification_profiles"]["public-claims-v1"]["sha256"] == certificate["publication_pipeline"][
        "verification_profile_sha256"
    ]
    assert certificate["verification_profiles"]["public-claims-v1"]["requirements"]["require_maximums"]
    assert certificate["verification_profiles"]["public-claims-v1"]["requirements"]["require_features"]
    assert "index-artifact-discoverability" in certificate["verification_profiles"]["public-claims-v1"][
        "requirements"
    ]["require_features"]
    assert certificate["verification_schema_features"] == list(STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES)
    assert certificate["verification_schema_features_sha256"] == verifier_feature_set_sha256
    assert verifier_feature_set_sha256 in content
    assert certificate["recent_change_ledger"]
    assert certificate["recent_change_ledger"][0]["title"] == "Random target demo"
    assert certificate["recent_change_ledger"][0]["status"] == "passed"
    assert certificate["recent_change_ledger"][1]["title"] == "Position or distribution"
    assert certificate["recent_change_ledger"][1]["value"] == "r_i(t)_or_Law(X_t)"
    assert certificate["recent_change_ledger"][2]["value"] == "closed_form_contract"
    assert certificate["recent_change_ledger"][-1]["value"] == verifier_feature_set_sha256[:12]
    assert certificate["public_change_summary"]
    assert certificate["public_change_summary"][-1]["title"] == "Active profile digest"
    assert "public verifier shortcut" in certificate["public_change_summary"][-1]["detail"]
    assert certificate["promotion_gates"]["symbolic_passes_stride_robustness"] is True
    assert certificate["target_prediction_answer"]["claim"] in {
        "target-position-and-distribution",
        "distributional-target-position",
        "deterministic-target-position",
        "unresolved-target-position",
    }
    assert certificate["target_prediction_answer"]["target_readout_decision"]["decision_type"] == (
        "three-body-target-readout-decision"
    )
    assert certificate["target_prediction_answer"]["target_sensitivity_budget"]["budget_type"] == (
        "three-body-target-sensitivity-budget"
    )
    assert certificate["target_prediction_answer"]["target_prediction_certificate"]["certificate_type"] == (
        "three-body-target-prediction-reproducibility"
    )
    assert certificate["random_prediction_demo"]["demo_type"] == "random-three-body-prediction-demo"
    assert certificate["random_prediction_demo"]["success_report"]["success"] is True
    assert certificate["random_prediction_demo"]["success_report"]["point_forecast_max_body_position_error"] <= 1.0e-6
    assert certificate["random_prediction_demo"]["approaches"][0]["approach"] == "adaptive-flow-final-state"
    assert certificate["build_provenance"]["generator"] == "threebody.ui.static_site"
    assert "analysis_atlas_snapshot" in certificate
    assert "interval_box_margin_lower" in certificate["jacobi_escape_cone"]["parameter_box_latest"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_schema_version"] == 1
    assert manifest["artifact"] == "threebody-static-site-manifest"
    assert manifest["hash_algorithm"] == "sha256"
    assert manifest["artifacts"]["index.html"]["sha256"] == _sha256(index_path)
    assert manifest["artifacts"]["certificate.json"]["sha256"] == _sha256(certificate_path)
    assert manifest["artifacts"]["certificate.json"]["bytes"] == certificate_path.stat().st_size
    assert manifest["artifacts"]["favicon.svg"]["sha256"] == _sha256(favicon_path)
    assert manifest["artifacts"]["favicon.svg"]["bytes"] == favicon_path.stat().st_size
    assert manifest["artifacts"][".gitattributes"]["sha256"] == _sha256(gitattributes_path)
    assert manifest["artifacts"][".gitattributes"]["bytes"] == gitattributes_path.stat().st_size
    assert 'viewBox="0 0 64 64"' in favicon_path.read_text(encoding="utf-8")
    assert b"\r\n" not in index_path.read_bytes()
    assert b"\r\n" not in certificate_path.read_bytes()
    assert b"\r\n" not in manifest_path.read_bytes()
    assert b"\r\n" not in favicon_path.read_bytes()
    assert gitattributes_path.read_text(encoding="utf-8") == "* text eol=lf\n"
    assert b"\r\n" not in gitattributes_path.read_bytes()
    public_api_receipt = verify_public_static_artifacts(tmp_path, require_commit="local")
    public_api_audit = audit_public_static_artifacts(tmp_path, require_commit="local")
    direct_bytes_receipt = verify_public_static_artifact_bytes(
        {
            "index.html": index_path.read_bytes(),
            "certificate.json": certificate_path.read_bytes(),
            "favicon.svg": favicon_path.read_bytes(),
            ".gitattributes": gitattributes_path.read_bytes(),
            "manifest.json": manifest_path.read_bytes(),
        },
        require_commit="local",
    )
    direct_bytes_audit = audit_public_static_artifact_bytes(
        {
            "index.html": index_path.read_bytes(),
            "certificate.json": certificate_path.read_bytes(),
            "favicon.svg": favicon_path.read_bytes(),
            ".gitattributes": gitattributes_path.read_bytes(),
            "manifest.json": manifest_path.read_bytes(),
        },
        require_commit="local",
    )
    artifacts = {
        "index.html": index_path.read_bytes(),
        "certificate.json": certificate_path.read_bytes(),
        "favicon.svg": favicon_path.read_bytes(),
        ".gitattributes": gitattributes_path.read_bytes(),
        "manifest.json": manifest_path.read_bytes(),
    }

    class FakeResponse:
        def __init__(self, data: bytes) -> None:
            self.data = data

        def __enter__(self) -> "FakeResponse":
            return self

        def __exit__(self, exc_type, exc, traceback) -> None:
            return None

        def read(self) -> bytes:
            return self.data

    def fake_urlopen(request, timeout: int) -> FakeResponse:
        artifact_name = str(request.full_url).rstrip("/").rsplit("/", 1)[-1]
        return FakeResponse(artifacts[artifact_name])

    monkeypatch.setattr("threebody.cli.urlopen", fake_urlopen)
    public_url_receipt = verify_public_static_artifacts_from_url("https://example.test/3body/", require_commit="local")
    public_url_audit = audit_public_static_artifacts_from_url("https://example.test/3body/", require_commit="local")

    assert public_api_receipt["verified"] is True
    assert isinstance(public_api_receipt["receipt_payload_sha256"], str)
    assert len(public_api_receipt["receipt_payload_sha256"]) == 64
    assert public_api_receipt["required_profiles"] == ["public-claims-v1"]
    assert public_api_receipt["required_feature_set_sha256"] == verifier_feature_set_sha256
    assert validate_public_static_artifact_receipt_contract(public_api_receipt)["verified"] is True
    assert public_api_audit["verified"] is True
    assert public_api_audit["contract"]["profile"] == "public-claims-v1"
    assert public_api_audit["audit_payload_sha256"] == public_static_artifact_audit_report_payload_sha256(
        public_api_audit
    )
    retimestamped_audit = {
        **public_api_audit,
        "receipt": {**public_api_audit["receipt"], "verified_at_utc": "2099-01-01T00:00:00Z"},
    }
    assert (
        public_static_artifact_audit_report_payload_sha256(retimestamped_audit)
        == public_api_audit["audit_payload_sha256"]
    )
    tampered_audit = {**public_api_audit, "verified": False}
    assert public_static_artifact_audit_report_payload_sha256(tampered_audit) != public_api_audit["audit_payload_sha256"]
    assert public_api_audit["receipt_contract_validation"]["verified"] is True
    assert public_api_audit["receipt_contract_validation"]["checks"]["receipt_payload_sha256_matches"] is True
    assert direct_bytes_receipt["verified"] is True
    assert direct_bytes_receipt["required_profiles"] == ["public-claims-v1"]
    assert direct_bytes_audit["verified"] is True
    assert direct_bytes_audit["receipt"]["required_feature_set_sha256"] == verifier_feature_set_sha256
    assert public_url_receipt["verified"] is True
    assert public_url_receipt["required_profiles"] == ["public-claims-v1"]
    assert public_url_receipt["required_feature_set_sha256"] == verifier_feature_set_sha256
    assert validate_public_static_artifact_receipt_contract(public_url_receipt)["verified"] is True
    assert public_url_audit["verified"] is True
    assert public_url_audit["receipt_contract_validation"]["checks"]["certificate_feature_set_sha256_matches"] is True


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

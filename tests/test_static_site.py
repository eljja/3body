from __future__ import annotations

import hashlib
import json

from threebody.cli import (
    STATIC_ARTIFACT_VERIFICATION_SCHEMA_FEATURES,
    static_artifact_requirement_profile_sha256,
    static_artifact_verification_features_sha256,
)
from threebody.ui.static_site import build_static_site


def test_static_site_builder_writes_index(tmp_path) -> None:
    index_path = build_static_site(tmp_path)

    assert index_path.name == "index.html"
    assert index_path.exists()
    assert (tmp_path / ".nojekyll").exists()
    certificate_path = tmp_path / "certificate.json"
    favicon_path = tmp_path / "favicon.svg"
    manifest_path = tmp_path / "manifest.json"
    assert certificate_path.exists()
    assert favicon_path.exists()
    assert manifest_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "ThreeBody Dynamics Lab" in content
    assert '<link rel="icon" href="favicon.svg" type="image/svg+xml">' in content
    assert '<meta name="theme-color" content="#16212f">' in content
    assert "General three-body figure-eight" in content
    assert "autoscale extent" in content
    assert "scaleanchor" not in content
    assert "Jacobi escape-cone theorem candidate" in content
    assert "Verification engine upgrades" in content
    assert "Research progress map" in content
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
    assert "require_public_claim=True" in content
    assert "CLI and Python API callers can apply the same public claim contract" in content
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
    assert certificate["public_change_summary"]
    assert certificate["public_change_summary"][-1]["title"] == "Active profile digest"
    assert "public-claim shortcut" in certificate["public_change_summary"][-1]["detail"]
    assert certificate["promotion_gates"]["symbolic_passes_stride_robustness"] is True
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
    assert 'viewBox="0 0 64 64"' in favicon_path.read_text(encoding="utf-8")


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

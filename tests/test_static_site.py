from __future__ import annotations

import hashlib
import json

from threebody.ui.static_site import build_static_site


def test_static_site_builder_writes_index(tmp_path) -> None:
    index_path = build_static_site(tmp_path)

    assert index_path.name == "index.html"
    assert index_path.exists()
    assert (tmp_path / ".nojekyll").exists()
    certificate_path = tmp_path / "certificate.json"
    manifest_path = tmp_path / "manifest.json"
    assert certificate_path.exists()
    assert manifest_path.exists()
    content = index_path.read_text(encoding="utf-8")
    assert "ThreeBody Dynamics Lab" in content
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
    assert "promotion_gates" in content
    assert "hysteresis_significant_baseline_win" in content
    assert "bootstrap_comparison" in content
    assert "hysteresis_selected_markov_order" in content
    assert "order_selection" in content
    assert "poincare_section_word" in content
    assert "word_mode" in content
    assert "poincare_section_sweep" in content
    assert "poincare_best_crossing_count" in content
    assert "poincare_coordinate_sweep" in content
    assert "poincare_best_coordinate_crossing_count" in content
    assert "poincare_markov" in content
    assert "Poincare memory" in content
    assert "heldout_binary_phase" in content
    assert "poincare_heldout_phase_validation" in content
    assert "poincare_markov_significant_baseline_win" in content
    assert "permutation_control" in content
    assert "poincare_passes_permutation_control" in content
    assert "section_robustness" in content
    assert "poincare_passes_section_robustness" in content
    assert "Section robustness" in content
    assert "stride_robustness" in content
    assert "symbolic_passes_stride_robustness" in content
    assert "Stride robustness" in content
    assert "Evidence publication pipeline" in content
    assert "Public verification ladder" in content
    assert "Claim-level receipt" in content
    assert "Numerical evidence" in content
    assert "Public artifacts" in content
    assert "Python engine" in content
    assert "Gate suite" in content
    assert "Integrity manifest" in content
    assert "Build provenance" in content
    assert "build_provenance" in content
    assert "generated_at_utc" in content
    assert "Open machine-readable certificate JSON" in content
    assert "Open artifact integrity manifest" in content
    assert "verify-static-artifacts --base-url https://eljja.github.io/3body/" in content
    assert "--require-commit local" in content
    assert "--require-profile public-claims-v1" in content
    assert "--output .runtime/research_runs/pages-verification-receipt.json" in content
    assert "verify-static-artifacts --site-dir site" in content
    assert "jacobi_parameter_interval_box_margin" not in content
    assert "interval_box_margin_lower" in content
    certificate = json.loads(certificate_path.read_text(encoding="utf-8"))
    assert certificate["certificate_schema_version"] == 1
    assert certificate["artifact"] == "threebody-static-research-certificate"
    assert certificate["artifact_manifest"] == "manifest.json"
    assert certificate["publication_pipeline"]["promotion_gate_pass_count"] == 7
    assert certificate["publication_pipeline"]["integrity_manifest"] == "manifest.json"
    assert certificate["publication_pipeline"]["verification_profile"] == "public-claims-v1"
    assert certificate["public_audit_ladder"]
    assert certificate["public_audit_ladder"][-1]["title"] == "Claim-level receipt"
    assert certificate["promotion_gates"]["symbolic_passes_stride_robustness"] is True
    assert certificate["build_provenance"]["generator"] == "threebody.ui.static_site"
    assert "analysis_atlas_snapshot" in certificate
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["manifest_schema_version"] == 1
    assert manifest["artifact"] == "threebody-static-site-manifest"
    assert manifest["artifacts"]["index.html"]["sha256"] == _sha256(index_path)
    assert manifest["artifacts"]["certificate.json"]["sha256"] == _sha256(certificate_path)
    assert manifest["artifacts"]["certificate.json"]["bytes"] == certificate_path.stat().st_size


def _sha256(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

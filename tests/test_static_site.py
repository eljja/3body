from __future__ import annotations

from threebody.ui.static_site import build_static_site


def test_static_site_builder_writes_index(tmp_path) -> None:
    index_path = build_static_site(tmp_path)

    assert index_path.name == "index.html"
    assert index_path.exists()
    assert (tmp_path / ".nojekyll").exists()
    content = index_path.read_text(encoding="utf-8")
    assert "ThreeBody Dynamics Lab" in content
    assert "General three-body figure-eight" in content
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
    assert "Build provenance" in content
    assert "build_provenance" in content
    assert "generated_at_utc" in content
    assert "jacobi_parameter_interval_box_margin" not in content
    assert "interval_box_margin_lower" in content

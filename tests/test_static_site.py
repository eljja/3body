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
    assert "Picard contraction tuning" in content
    assert "Markov baseline test" in content
    assert "promotion_gates" in content
    assert "hysteresis_significant_baseline_win" in content
    assert "bootstrap_comparison" in content
    assert "hysteresis_selected_markov_order" in content
    assert "order_selection" in content
    assert "jacobi_parameter_interval_box_margin" not in content
    assert "interval_box_margin_lower" in content

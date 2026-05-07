from __future__ import annotations

from threebody.experiments import TheoremSuite


def test_theorem_suite_reports_candidates_and_benchmarks() -> None:
    result = TheoremSuite().run()
    summary = result.as_dict()

    assert summary["theorem_candidates"]
    assert summary["benchmarks"]
    assert any(candidate["proven"] is False for candidate in summary["theorem_candidates"])
    assert any(candidate["name"] == "Impulse-Exchange Hierarchy Boundary Conjecture" for candidate in summary["theorem_candidates"])
    assert any(benchmark["name"] == "low_crossing_scattering_map_score" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "low_crossing_scattering_map_selection" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "best_low_crossing_model_validation" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "best_hysteresis_width_model_validation" for benchmark in summary["benchmarks"])

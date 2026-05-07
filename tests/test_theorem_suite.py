from __future__ import annotations

from threebody.experiments import TheoremSuite


def test_theorem_suite_reports_candidates_and_benchmarks() -> None:
    result = TheoremSuite().run()
    summary = result.as_dict()

    assert summary["theorem_candidates"]
    assert summary["benchmarks"]
    assert any(candidate["proven"] is False for candidate in summary["theorem_candidates"])
    assert any(benchmark["name"] == "low_crossing_scattering_map_validation" for benchmark in summary["benchmarks"])

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
    assert any(benchmark["name"] == "transition_word_stability" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "transition_word_nontriviality" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "transition_word_validation_diversity" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "refined_transition_word_stability" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "refined_transition_word_validation_diversity" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "return_word_stability" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "return_word_validation_diversity" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "high_crossing_grammar_outcome_validation" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "hysteresis_width_grammar_outcome_validation" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "grammar_branch_training_signal" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "grammar_branch_validation_support" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "grammar_branch_artifact_pass_rate" for benchmark in summary["benchmarks"])
    assert any(benchmark["name"] == "grammar_branch_artifact_min_score" for benchmark in summary["benchmarks"])

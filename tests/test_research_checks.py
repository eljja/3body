from __future__ import annotations

from threebody.experiments import (
    ClassifierArtifactStudy,
    FigureEightStabilityProbe,
    GrammarBranchArtifactStudy,
    IntegratorComparisonStudy,
    KnownBenchmarkSuite,
    RegimeProbeSuite,
)


def test_classifier_artifact_study_varies_classifier_settings() -> None:
    rows = ClassifierArtifactStudy().run(duration=3.0, samples=180)

    assert len(rows) >= 4
    assert {row.label for row in rows} >= {"baseline", "strict_hierarchy", "loose_hierarchy"}
    assert all(row.transition_count >= 0 for row in rows)


def test_grammar_branch_artifact_study_varies_classifier_settings() -> None:
    rows = GrammarBranchArtifactStudy().run(duration=3.0, samples=120)

    assert {row.label for row in rows} >= {"baseline", "strict_hierarchy", "loose_hierarchy"}
    assert all(row.minimum_score is None or isinstance(row.minimum_score, float) for row in rows)
    assert all(row.minimum_certified_fraction is None or row.minimum_certified_fraction >= 0.0 for row in rows)
    assert all(row.minimum_negative_control_gap is None or isinstance(row.minimum_negative_control_gap, float) for row in rows)


def test_integrator_comparison_reports_regularization_gap() -> None:
    result = IntegratorComparisonStudy().run(periods=0.05, step_size=5.0e-3)

    assert result.adaptive_energy_drift >= 0.0
    assert result.structure_energy_drift >= 0.0
    assert result.endpoint_separation >= 0.0
    assert result.regularized_available is False


def test_known_benchmarks_and_regime_probes_return_rows() -> None:
    benchmarks = KnownBenchmarkSuite().run()
    regimes = RegimeProbeSuite().run()
    stability = FigureEightStabilityProbe().run(periods=0.05)

    assert any(row.name == "restricted_l4" and row.passed for row in benchmarks)
    assert any(row.name == "figure_eight_return" for row in benchmarks)
    assert {row.name for row in regimes} >= {"lagrange_neck", "shape_close_encounter", "escape_scattering"}
    assert stability.spectral_radius > 0.0

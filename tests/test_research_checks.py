from __future__ import annotations

from threebody.experiments import (
    ClassifierArtifactStudy,
    CloseEncounterResidualGridStudy,
    CloseEncounterResidualStudy,
    FigureEightStabilityProbe,
    GrammarBranchArtifactStudy,
    InterpretationSuite,
    IntegratorComparisonStudy,
    KnownBenchmarkSuite,
    NearCollisionScalingStudy,
    RegimeProbeSuite,
)


def test_classifier_artifact_study_varies_classifier_settings() -> None:
    rows = ClassifierArtifactStudy().run(duration=3.0, samples=180)

    assert len(rows) >= 4
    assert {row.label for row in rows} >= {"baseline", "strict_hierarchy", "loose_hierarchy"}
    assert all(row.transition_count >= 0 for row in rows)


def test_interpretation_suite_covers_certificate_regimes() -> None:
    result = InterpretationSuite().run()

    assert result.rows
    assert result.local_interpretation_rate == 1.0
    assert {"escape_transport", "close_encounter", "restricted_lagrange"}.issubset(result.covered_chart_types)
    assert result.resolved_obligations
    assert result.unresolved_blockers


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


def test_close_encounter_residual_study_validates_integrated_probe() -> None:
    result = CloseEncounterResidualStudy().run()

    assert result.flow_defined is True
    assert result.residual_resolved is True
    assert result.equivalence_resolved is True
    assert result.maximum_finite_difference_residual is not None
    assert result.maximum_finite_difference_residual <= result.residual_threshold
    assert result.maximum_equivalence_acceleration_residual < 1.0e-7


def test_close_encounter_residual_grid_validates_declared_cases() -> None:
    result = CloseEncounterResidualGridStudy().run()

    assert len(result.rows) >= 4
    assert result.pass_rate == 1.0
    assert result.equivalence_pass_rate == 1.0
    assert result.maximum_residual is not None
    assert result.maximum_residual <= result.residual_threshold
    assert result.maximum_equivalence_acceleration_residual is not None
    assert result.maximum_equivalence_acceleration_residual < 1.0e-7
    assert all(row.flow_defined for row in result.rows)


def test_near_collision_scaling_study_controls_normalized_residual() -> None:
    result = NearCollisionScalingStudy().run()

    assert len(result.rows) >= 5
    assert result.scaling_resolved is True
    assert result.minimum_pair_distance is not None
    assert result.minimum_pair_distance <= 0.0081
    assert result.maximum_residual is not None
    assert result.maximum_residual <= result.residual_threshold
    assert result.maximum_normalized_residual is not None
    assert result.maximum_normalized_residual <= result.normalized_residual_threshold
    assert result.normalized_residual_scaling_exponent is not None
    assert result.normalized_residual_scaling_exponent >= result.minimum_allowed_normalized_slope
    assert result.absolute_residual_scaling_exponent is not None


def test_known_benchmarks_and_regime_probes_return_rows() -> None:
    benchmarks = KnownBenchmarkSuite().run()
    regimes = RegimeProbeSuite().run()
    stability = FigureEightStabilityProbe().run(periods=0.05)

    assert any(row.name == "restricted_l4" and row.passed for row in benchmarks)
    assert any(row.name == "figure_eight_return" for row in benchmarks)
    assert {row.name for row in regimes} >= {"lagrange_neck", "shape_close_encounter", "escape_scattering"}
    assert stability.spectral_radius > 0.0

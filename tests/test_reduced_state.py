from __future__ import annotations

from threebody.analysis import (
    center_of_mass_reduction_certificate,
    lagrange_jacobi_identity_certificate,
    reduced_state_series,
    reduced_three_body_state,
    sundman_inequality_certificate,
)
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_reduced_three_body_state_reports_shared_atlas_coordinates() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(samples=50)

    reduced = reduced_three_body_state(scenario.system, scenario.initial_state)

    assert reduced.hyperradius > 0.0
    assert reduced.nearest_distance > 0.0
    assert reduced.hierarchy_ratio > 1.0
    assert reduced.reduced_regime_hint in {
        "collision_boundary",
        "escape_boundary",
        "hierarchy_chart",
        "democratic_shape",
        "transition_region",
    }


def test_reduced_state_series_tracks_trajectory_time() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=1.0, samples=80)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    series = reduced_state_series(scenario.system, trajectory, stride=10)

    assert len(series) == 8
    assert series[0].time == trajectory.t[0]
    assert series[-1].time == trajectory.t[70]


def test_center_of_mass_reduction_certificate_resolves_recentered_figure_eight() -> None:
    scenario = OrbitLibrary().general_figure_eight(periods=0.2, samples=120)
    trajectory = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = center_of_mass_reduction_certificate(scenario.system, trajectory, stride=10)

    assert certificate.sample_count == 12
    assert certificate.reduction_resolved is True
    assert certificate.maximum_center_norm < certificate.tolerance
    assert certificate.maximum_linear_momentum_norm < certificate.tolerance


def test_lagrange_jacobi_identity_certificate_resolves_newtonian_trajectory() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=0.5, samples=120)
    trajectory = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = lagrange_jacobi_identity_certificate(scenario.system, trajectory, stride=12)

    assert certificate.sample_count == 10
    assert certificate.identity_resolved is True
    assert certificate.maximum_relative_residual < certificate.tolerance


def test_sundman_inequality_certificate_resolves_newtonian_trajectory() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=0.5, samples=120)
    trajectory = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = sundman_inequality_certificate(scenario.system, trajectory, stride=12)

    assert certificate.sample_count == 10
    assert certificate.inequality_resolved is True
    assert certificate.maximum_ratio <= 1.0 + certificate.tolerance
    assert certificate.maximum_violation <= certificate.tolerance

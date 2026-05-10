from __future__ import annotations

import numpy as np

from threebody.analysis import (
    collision_regularization_certificate,
    gateway_transit_estimate,
    levi_civita_binary_chart,
    levi_civita_chart_certificate,
    levi_civita_flow_certificate,
    levi_civita_regularized_flow_state,
    mcgehee_collision_diagnostic,
    restricted_chart_certificate,
)
from threebody.systems import GeneralThreeBodySystem, RestrictedThreeBodySystem
from threebody.types import TrajectoryResult


def test_mcgehee_collision_diagnostic_flags_binary_collision_candidate() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.0]], dtype=float),
        np.zeros((3, 2), dtype=float),
    )

    diagnostic = mcgehee_collision_diagnostic(system, state)

    assert diagnostic.regularization_required is True
    assert diagnostic.collision_type == "binary_collision_candidate"
    assert diagnostic.minimum_pair_distance > 0.0


def test_collision_regularization_certificate_aggregates_interval() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.0]], dtype=float),
        np.zeros((3, 2), dtype=float),
    )
    trajectory = TrajectoryResult(
        t=np.array([0.0, 1.0]),
        y=np.vstack([state, state]),
        success=True,
        message="synthetic",
    )

    certificate = collision_regularization_certificate(system, trajectory)

    assert certificate.regularization_required is True
    assert certificate.levi_civita_chart_resolved is True
    assert certificate.levi_civita_pair == (0, 1)
    assert certificate.levi_civita_flow_defined is True
    assert certificate.minimum_pair_distance > 0.0
    assert "binary_collision_candidate" in certificate.collision_types


def test_levi_civita_binary_chart_reconstructs_relative_position() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.003, 0.004], [1.0, 0.0]], dtype=float),
        np.array([[0.0, 0.0], [0.1, -0.2], [0.0, 0.0]], dtype=float),
    )

    chart = levi_civita_binary_chart(system, state, (0, 1))

    assert chart.radius == np.linalg.norm(chart.relative_position)
    assert chart.regularized_radius == np.sqrt(chart.radius)
    assert chart.reconstruction_error < 1.0e-14


def test_levi_civita_chart_certificate_resolves_interval_chart() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.0]], dtype=float),
        np.zeros((3, 2), dtype=float),
    )
    trajectory = TrajectoryResult(
        t=np.array([0.0, 1.0]),
        y=np.vstack([state, state]),
        success=True,
        message="synthetic",
    )

    certificate = levi_civita_chart_certificate(system, trajectory)

    assert certificate.pair == (0, 1)
    assert certificate.chart_resolved is True
    assert certificate.maximum_reconstruction_error < 1.0e-14


def test_levi_civita_chart_certificate_selects_continuous_branch() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    states = []
    for y in (-1.0e-4, 1.0e-4):
        states.append(
            system.flatten_state(
                np.array([[0.0, 0.0], [-1.0, y], [3.0, 0.0]], dtype=float),
                np.zeros((3, 2), dtype=float),
            )
        )
    trajectory = TrajectoryResult(
        t=np.array([0.0, 1.0]),
        y=np.vstack(states),
        success=True,
        message="branch cut crossing",
    )

    certificate = levi_civita_chart_certificate(system, trajectory, pair=(0, 1))

    assert certificate.chart_resolved is True
    assert certificate.maximum_branch_jump < 1.0e-3


def test_levi_civita_regularized_flow_state_is_finite() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 2.0, 0.5), dimension=2)
    state = system.flatten_state(
        np.array([[0.0, 0.0], [0.005, 0.0], [1.0, 0.1]], dtype=float),
        np.array([[0.0, 0.0], [0.0, 0.2], [0.0, -0.1]], dtype=float),
    )

    flow = levi_civita_regularized_flow_state(system, state, (0, 1))

    assert np.all(np.isfinite(flow.u_double_prime))
    assert flow.relative_acceleration_norm > 0.0
    assert flow.perturbation_acceleration_norm > 0.0


def test_levi_civita_flow_certificate_reports_defined_rhs() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 1.0), dimension=2)
    states = []
    for offset in (0.0, 1.0e-4, 2.0e-4):
        states.append(
            system.flatten_state(
                np.array([[0.0, 0.0], [0.005 + offset, 0.0], [1.0, 0.0]], dtype=float),
                np.zeros((3, 2), dtype=float),
            )
        )
    trajectory = TrajectoryResult(
        t=np.array([0.0, 0.5, 1.0]),
        y=np.vstack(states),
        success=True,
        message="synthetic flow",
    )

    certificate = levi_civita_flow_certificate(system, trajectory, pair=(0, 1))

    assert certificate.flow_defined is True
    assert certificate.maximum_rhs_norm > 0.0
    assert certificate.maximum_perturbation_acceleration_norm > 0.0
    assert certificate.maximum_finite_difference_residual is not None


def test_gateway_transit_estimate_reports_neck_openness() -> None:
    system = RestrictedThreeBodySystem()
    l1 = system.lagrange_points()["L1"]
    state = np.array([l1[0] + 0.01, l1[1], 0.0, 0.08], dtype=float)

    estimate = gateway_transit_estimate(system, state)

    assert estimate.lagrange_point == "L1"
    assert isinstance(estimate.neck_open, bool)
    assert estimate.transit_likelihood >= 0.0


def test_restricted_chart_certificate_reports_lagrange_jacobi_control() -> None:
    system = RestrictedThreeBodySystem()
    l4 = system.lagrange_points()["L4"]
    state = np.array([l4[0] + 0.001, l4[1], 0.0, 0.0], dtype=float)
    trajectory = TrajectoryResult(
        t=np.array([0.0, 1.0]),
        y=np.vstack([state, state]),
        success=True,
        message="synthetic restricted lagrange",
    )

    certificate = restricted_chart_certificate(system, trajectory)

    assert certificate.nearest_lagrange == "L4"
    assert certificate.certificate_kind == "lagrange_neighborhood"
    assert certificate.routh_stable_triangular is True
    assert certificate.max_abs_jacobi_drift == 0.0
    assert certificate.min_gateway_margin is None


def test_restricted_chart_certificate_reports_gateway_transit() -> None:
    system = RestrictedThreeBodySystem()
    l1 = system.lagrange_points()["L1"]
    state = np.array([l1[0] + 0.01, l1[1], 0.0, 0.08], dtype=float)
    trajectory = TrajectoryResult(
        t=np.array([0.0, 1.0]),
        y=np.vstack([state, state]),
        success=True,
        message="synthetic restricted gateway",
    )

    certificate = restricted_chart_certificate(system, trajectory)

    assert certificate.nearest_lagrange == "L1"
    assert certificate.certificate_kind == "gateway_neck"
    assert certificate.max_transit_likelihood >= 0.0

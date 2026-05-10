from __future__ import annotations

import numpy as np

from threebody.analysis import (
    collision_regularization_certificate,
    gateway_transit_estimate,
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
    assert certificate.minimum_pair_distance > 0.0
    assert "binary_collision_candidate" in certificate.collision_types


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

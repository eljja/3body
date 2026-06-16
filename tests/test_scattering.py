from __future__ import annotations

import numpy as np

from threebody.analysis import escape_asymptotic_certificate, periapsis_scattering_map
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import GeneralThreeBodySystem
from threebody.types import Scenario


def test_periapsis_scattering_map_uses_trajectory_closest_approach() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=260)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    scattering = periapsis_scattering_map(scenario.system, trajectory)

    assert 0 <= scattering.periapsis_index < len(trajectory.t)
    assert scattering.periapsis_distance > 0.0
    assert 0.0 <= scattering.binary_phase_at_periapsis <= 2.0 * np.pi
    assert scattering.outgoing_eccentricity >= 0.0
    assert scattering.outgoing_periapsis_distance > 0.0
    assert scattering.deflection_angle >= 0.0


def test_escape_asymptotic_certificate_detects_outgoing_escape_tail() -> None:
    system = GeneralThreeBodySystem(masses=(1.0, 1.0, 0.1), dimension=2)
    positions = np.array([[-0.1, 0.0], [0.1, 0.0], [4.0, 0.0]], dtype=float)
    velocities = np.array([[0.0, 0.6], [0.0, -0.6], [2.0, 0.1]], dtype=float)
    scenario = Scenario(
        name="escape-tail",
        system=system,
        initial_state=system.flatten_state(positions, velocities),
        t_span=(0.0, 1.0),
        t_eval=np.linspace(0.0, 1.0, 120),
    )
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = escape_asymptotic_certificate(system, trajectory)

    assert certificate.tail_sample_count >= 3
    assert certificate.outgoing_energy > 0.0
    assert certificate.radius_growth_fraction >= 0.8
    assert certificate.escape_speed_at_infinity > 0.0


def test_verify_scattering_analytic_bounds_certifies_theoretical_quadrupole() -> None:
    from threebody.analysis import verify_scattering_analytic_bounds

    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=260)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )

    certificate = verify_scattering_analytic_bounds(scenario.system, trajectory)

    assert certificate.inner_pair == (0, 1)
    assert certificate.outer_body == 2
    assert certificate.observed_energy_exchange >= 0.0
    assert certificate.theoretical_quadrupole_bound > 0.0
    assert certificate.observed_deflection_angle >= 0.0
    assert certificate.theoretical_deflection_bound > 0.0
    assert certificate.bounds_satisfied is True


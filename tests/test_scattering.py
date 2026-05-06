from __future__ import annotations

import numpy as np

from threebody.analysis import periapsis_scattering_map
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


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

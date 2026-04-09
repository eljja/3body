from __future__ import annotations

import numpy as np

from threebody.diagnostics import InvariantMonitor
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator
from threebody.systems import RestrictedThreeBodySystem


def test_lagrange_points_include_triangular_closed_form() -> None:
    system = RestrictedThreeBodySystem(mass_ratio=0.0121505856)
    lagrange = system.lagrange_points()

    assert np.allclose(lagrange["L4"], [0.5 - system.mass_ratio, np.sqrt(3.0) / 2.0])
    assert np.allclose(lagrange["L5"], [0.5 - system.mass_ratio, -np.sqrt(3.0) / 2.0])


def test_restricted_problem_nearly_preserves_jacobi_constant() -> None:
    library = OrbitLibrary()
    scenario = library.restricted_l4(periods=5.0, samples=2000)
    integrator = AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13)

    trajectory = integrator.integrate(scenario.system, scenario.t_span, scenario.initial_state, t_eval=scenario.t_eval)
    monitor = InvariantMonitor(scenario.system)
    invariants = monitor.evaluate(trajectory)

    assert np.max(np.abs(invariants["jacobi_drift"])) < 1.0e-8

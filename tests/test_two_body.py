from __future__ import annotations

import numpy as np

from threebody.diagnostics import InvariantMonitor
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator, AnalyticTwoBodySolver, StructureAwareIntegrator


def test_two_body_analytic_matches_adaptive() -> None:
    library = OrbitLibrary()
    scenario = library.two_body_elliptic(eccentricity=0.3, periods=1.0, samples=1500)
    adaptive = AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13)
    analytic = AnalyticTwoBodySolver()

    numerical = adaptive.integrate(scenario.system, scenario.t_span, scenario.initial_state, t_eval=scenario.t_eval)
    exact = analytic.propagate(scenario.system, scenario.initial_state, scenario.t_eval)

    error = np.linalg.norm(numerical.y[:, :2] - exact.y[:, :2], axis=1)
    assert np.max(error) < 1.0e-7


def test_two_body_structure_aware_preserves_energy() -> None:
    library = OrbitLibrary()
    scenario = library.two_body_elliptic(eccentricity=0.1, periods=3.0, samples=2000)
    integrator = StructureAwareIntegrator(step_size=1.0e-3)

    trajectory = integrator.integrate(scenario.system, scenario.t_span, scenario.initial_state)
    monitor = InvariantMonitor(scenario.system)
    invariants = monitor.evaluate(trajectory)

    assert np.max(np.abs(invariants["energy_drift"])) < 2.0e-5

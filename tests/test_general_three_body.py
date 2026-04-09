from __future__ import annotations

import numpy as np

from threebody.diagnostics import InvariantMonitor, StabilityAnalyzer
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_figure_eight_returns_close_to_initial_configuration() -> None:
    library = OrbitLibrary()
    scenario = library.general_figure_eight(periods=1.0, samples=3000)
    integrator = AdaptiveIntegrator(rtol=1.0e-11, atol=1.0e-13)

    trajectory = integrator.integrate(scenario.system, scenario.t_span, scenario.initial_state, t_eval=scenario.t_eval)
    positions_initial, _velocities_initial = scenario.system.split_state(trajectory.y[0])
    positions_final, _velocities_final = scenario.system.split_state(trajectory.y[-1])

    assert np.linalg.norm(positions_final - positions_initial) < 5.0e-3


def test_figure_eight_energy_and_sensitivity_tools_work() -> None:
    library = OrbitLibrary()
    reference = library.general_figure_eight(periods=0.5, samples=2000, perturbation_scale=0.0)
    perturbed = library.general_figure_eight(periods=0.5, samples=2000, perturbation_scale=1.0e-3)
    integrator = AdaptiveIntegrator(rtol=1.0e-10, atol=1.0e-12)

    reference_traj = integrator.integrate(reference.system, reference.t_span, reference.initial_state, t_eval=reference.t_eval)
    perturbed_traj = integrator.integrate(perturbed.system, perturbed.t_span, perturbed.initial_state, t_eval=perturbed.t_eval)

    monitor = InvariantMonitor(reference.system)
    invariants = monitor.evaluate(reference_traj)
    stability = StabilityAnalyzer().finite_time_lyapunov(reference_traj, perturbed_traj)

    assert np.max(np.abs(invariants["energy_drift"])) < 1.0e-7
    assert stability["finite_time_lyapunov"] >= 0.0

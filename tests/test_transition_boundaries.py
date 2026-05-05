from __future__ import annotations

from threebody.analysis import AnalysisAtlas, estimate_transition_boundaries
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_transition_boundary_estimate_uses_perturbation_strength() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=500)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    reports = AnalysisAtlas().analyze_trajectory(scenario.system, trajectory, stride=20)

    estimates = estimate_transition_boundaries({"flyby": reports})

    assert estimates
    assert all(estimate.coordinate == "hierarchy_perturbation_strength" for estimate in estimates)
    assert any(estimate.crossing_mean > 0.0 for estimate in estimates)

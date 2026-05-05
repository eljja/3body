from __future__ import annotations

from threebody.analysis import AnalysisAtlas, detect_hysteresis_loops, estimate_transition_boundaries
from threebody.experiments import OrbitLibrary
from threebody.solvers import AdaptiveIntegrator


def test_hierarchical_flyby_exposes_hysteresis_loop() -> None:
    scenario = OrbitLibrary().general_hierarchical_flyby(duration=8.0, samples=500)
    trajectory = AdaptiveIntegrator(rtol=1.0e-9, atol=1.0e-11).integrate(
        scenario.system,
        scenario.t_span,
        scenario.initial_state,
        t_eval=scenario.t_eval,
    )
    reports = AnalysisAtlas().analyze_trajectory(scenario.system, trajectory, stride=20)
    estimates = estimate_transition_boundaries({"flyby": reports})

    loops = detect_hysteresis_loops(estimates)

    assert loops
    assert loops[0].coordinate == "hierarchy_perturbation_strength"
    assert loops[0].width >= 0.0
